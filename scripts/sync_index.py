#!/usr/bin/env python3
"""
Sync script (renderer only).

- Reads project metadata from data/projects.json (map of repo name -> overrides).
- Fetches GitHub repo facts via the API (description, archived, pushed_at, etc.).
- Combines overrides with GitHub facts and renders the repo list into projects.html.

Design constraints:
- data/projects.json is the single source of org-owned metadata.
- Lightweight validation: fail only on malformed JSON or invalid field types.
- Only projects.html may be modified.
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
import html
import logging
import re

logging.basicConfig(level=logging.INFO)

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
ORG = os.environ.get('ORG_NAME', 'palmshed')
API_URL = f'https://api.github.com/orgs/{ORG}/repos'
HEADERS = {'Accept': 'application/vnd.github.v3+json',
           'User-Agent': 'palmshed-sync-script/1.0 (+https://github.com/palmshed/palmshed.github.io)'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

ALLOWED_STATUS = {'active', 'experimental', 'archived', 'seeking-maintainer', 'deprecated', 'unknown'}
ALLOWED_STAGE = {'prototype', 'experimental', 'beta', 'stable'}

OVERRIDES_PATH = 'data/projects.json'

# Use a session for connection reuse and consistent headers
_session = requests.Session()
_session.headers.update(HEADERS)


def load_overrides():
    """Load and validate data/projects.json.

    Expected shape: { "repo-name": { "status": ..., "stage": ..., ... } }

    Validates types and enum values. Exits with non-zero on malformed JSON or invalid types.
    Returns a dict normalized to lowercase repo name -> metadata dict (may be empty).
    """
    if not os.path.exists(OVERRIDES_PATH):
        logging.info('%s not found -- proceeding with empty overrides', OVERRIDES_PATH)
        return {}

    try:
        with open(OVERRIDES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error('Malformed JSON in %s: %s', OVERRIDES_PATH, e)
        sys.exit(1)

    if not isinstance(data, dict):
        logging.error('%s must be a JSON object at top level', OVERRIDES_PATH)
        sys.exit(1)

    # Validate entries
    for repo, meta in data.items():
        if not isinstance(meta, dict):
            logging.error('Project entry %r must be an object', repo)
            sys.exit(1)
        status = meta.get('status')
        if status is not None and status not in ALLOWED_STATUS:
            logging.error('Invalid status for %s: %r. Allowed: %s', repo, status, sorted(ALLOWED_STATUS))
            sys.exit(1)
        stage = meta.get('stage')
        if stage is not None and stage not in ALLOWED_STAGE:
            logging.error('Invalid stage for %s: %r. Allowed: %s', repo, stage, sorted(ALLOWED_STAGE))
            sys.exit(1)
        maintainers = meta.get('maintainers')
        if maintainers is not None and not isinstance(maintainers, list):
            logging.error('maintainers for %s must be a list of strings', repo)
            sys.exit(1)
        featured = meta.get('featured')
        if featured is not None and not isinstance(featured, bool):
            logging.error('featured for %s must be a boolean', repo)
            sys.exit(1)
        summary = meta.get('summary')
        if summary is not None and not isinstance(summary, str):
            logging.error('summary for %s must be a string', repo)
            sys.exit(1)

    # Normalize keys to lowercase for case-insensitive lookup
    normalized = {k.lower(): v for k, v in data.items()}
    return normalized


def fetch_all_repos():
    """Paginate and return the list of repository objects from the GitHub API."""
    repos = []
    page = 1
    per_page = 100
    while True:
        resp = _session.get(API_URL, params={'per_page': per_page, 'page': page, 'type': 'all'}, timeout=30)
        if resp.status_code != 200:
            # Friendly messages for common failure modes
            if resp.status_code == 403:
                remaining = resp.headers.get('X-RateLimit-Remaining')
                reset = resp.headers.get('X-RateLimit-Reset')
                if remaining == '0':
                    logging.error('GitHub API rate limit exceeded (X-RateLimit-Remaining=0). Reset epoch: %s', reset)
                else:
                    logging.error('Access forbidden (403). Check that GITHUB_TOKEN has repo and workflow scopes and that the token is valid.')
            else:
                logging.error('Failed to fetch repos: %s %s', resp.status_code, resp.text)
            sys.exit(1)
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return repos


def make_li(repo, overrides):
    """Render a single <li> using org overrides first, then GitHub facts as fallback."""
    name = repo.get('name')
    url = repo.get('html_url') or f'https://github.com/{ORG}/{name}'

    meta = overrides.get(name.lower(), {}) if overrides else {}
    # Org-owned summary preferred; else use GitHub description
    summary = meta.get('summary') or repo.get('description') or ''
    maintainers = meta.get('maintainers')
    status_override = meta.get('status')
    stage = meta.get('stage')
    featured = meta.get('featured')

    desc = (summary or '').strip()
    desc = html.escape(desc)
    archived = bool(repo.get('archived'))

    status = status_override or 'unknown'
    status_text = {
        'archived': 'Archived',
        'active': 'Actively maintained',
        'experimental': 'Experimental',
        'seeking-maintainer': 'Seeking maintainer',
        'deprecated': 'Deprecated',
        'unknown': None,
    }.get(status, None)

    if maintainers:
        maintainers = [m for m in maintainers if m]

    pushed = repo.get('pushed_at') or repo.get('updated_at') or ''
    pushed_short = pushed.split('T')[0] if pushed else 'unknown'

    archived_span = '<span class="archived">archived</span>' if archived else ''
    note = f'<span class="repo-note">{desc}</span>' if desc else '<span class="repo-note"></span>'

    featured_span = '<span class="featured">featured</span>' if featured else ''

    li = f'        <li{" archived" if archived else ""}>'
    li += f'<a class="repo-name" href="{url}">{html.escape(name)}</a>'
    li += f'{note}{archived_span}{featured_span}'
    li += '\n          <div class="repo-meta">'
    if maintainers:
        maint_html = ', '.join([f'<a href="https://github.com/{html.escape(m)}">{html.escape(m)}</a>' for m in maintainers])
        li += f'\n            <span>{maint_html}</span>'
    li += f'\n            <span>Last pushed: {pushed_short}</span>'
    if status_text:
        li += f'\n            <span class="repo-status">{status_text}</span>'
    if stage:
        li += f'\n            <span>Stage: {html.escape(stage)}</span>'
    li += '\n          </div>'
    li += '</li>'
    return li


def main():
    overrides = load_overrides()
    repos = fetch_all_repos()
    repos_sorted = sorted(repos, key=lambda r: r.get('name', '').lower())
    lis = [make_li(r, overrides) for r in repos_sorted]
    new_list_html = '        <ul class="repo-list">\n' + "\n".join(lis) + '\n        </ul>\n'

    path = 'projects.html'
    if not os.path.exists(path):
        logging.error('projects.html not found in repo root')
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Prefer explicit markers in projects.html for the repo list. This is the contract:
    #   <!-- repo-list-start -->
    #   <ul class="repo-list"> ... </ul>
    #   <!-- repo-list-end -->
    start_marker = '<!-- repo-list-start -->'
    end_marker = '<!-- repo-list-end -->'

    if start_marker in content and end_marker in content:
        before, rest = content.split(start_marker, 1)
        _, after = rest.split(end_marker, 1)
        new_content = before + start_marker + "\n" + new_list_html + "    " + end_marker + after
    else:
        logging.error('Could not find repo-list markers %r and %r in projects.html; please add them around the <ul class="repo-list"> block.', start_marker, end_marker)
        sys.exit(1)

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    new_content = re.sub(r'(Last updated<\/dt><dd>)\d{4}-\d{2}-\d{2}', rf'\1{today}', new_content)

    if new_content == content:
        print('No changes needed')
        return

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('projects.html updated')


if __name__ == '__main__':
    main()
