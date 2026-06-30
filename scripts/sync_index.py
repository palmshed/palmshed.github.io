#!/usr/bin/env python3
"""
Sync script (renderer only).

- Reads organization metadata from data/projects.json (compact schema_version=1 + projects map).
- Fetches GitHub repo facts via the API (description, archived, pushed_at, stars, license, etc.).
- Combines org metadata (in-memory) with GitHub facts while rendering index.html.

Design constraints enforced here:
- No contributor inference or per-repo contributor API calls.
- data/projects.json is the single source of org-owned metadata.
- Lightweight validation: fail only on malformed JSON, invalid enum values, or incorrect field types.
- No merged artifacts are written; only index.html may be updated.
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
import html
import logging
import re

# Basic logging config to surface messages clearly in workflow logs
logging.basicConfig(level=logging.INFO)

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
ORG = os.environ.get('ORG_NAME', 'palmshed')
API_URL = f'https://api.github.com/orgs/{ORG}/repos'
HEADERS = {'Accept': 'application/vnd.github.v3+json',
           'User-Agent': 'palmshed-sync-script/1.0 (+https://github.com/palmshed/palmshed.github.io)'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

# Activity thresholds (days)
ACTIVE_DAYS = int(os.environ.get('ACTIVE_DAYS', '180'))
LOW_ACTIVITY_DAYS = int(os.environ.get('LOW_ACTIVITY_DAYS', '365'))

# Allowed enums for lightweight validation
ALLOWED_STATUS = {'active', 'experimental', 'archived', 'seeking-maintainer', 'deprecated', 'unknown'}
ALLOWED_STAGE = {'prototype', 'experimental', 'beta', 'stable'}

OVERRIDES_PATH = 'data/projects.json'

# Use a session for connection reuse and consistent headers
_session = requests.Session()
_session.headers.update(HEADERS)


def load_overrides():
    """Load and lightly validate data/projects.json.

    Expected shape:
      {
        "schema_version": 1,
        "projects": { "repo-name": { ... } }
      }

    Validates types and enum values. Exits with non-zero on malformed JSON or invalid types/enum.
    Returns a dict normalized to lowercase repo name -> metadata dict (may be empty).
    """
    if not os.path.exists(OVERRIDES_PATH):
        logging.info('%s not found — proceeding with empty overrides', OVERRIDES_PATH)
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

    schema_version = data.get('schema_version')
    if schema_version is None:
        logging.error('%s must include "schema_version": 1', OVERRIDES_PATH)
        sys.exit(1)
    if not isinstance(schema_version, int) or schema_version != 1:
        logging.error('%s: unsupported schema_version %r (expected integer 1)', OVERRIDES_PATH, schema_version)
        sys.exit(1)

    projects = data.get('projects')
    if not isinstance(projects, dict):
        logging.error('%s: "projects" object is required and must be a map', OVERRIDES_PATH)
        sys.exit(1)

    # Validate entries
    for repo, meta in projects.items():
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
        maintainers = meta.get('maintainers') or meta.get('maintainer')
        if maintainers is not None and not (isinstance(maintainers, list) or isinstance(maintainers, str)):
            logging.error('maintainers for %s must be a string or list of strings', repo)
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
    normalized = {k.lower(): v for k, v in projects.items()}
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


def status_from_pushed_at(repo):
    """Derive a lightweight activity status from pushed_at and archived flag."""
    if repo.get('archived'):
        return 'archived'
    pushed = repo.get('pushed_at') or repo.get('updated_at') or repo.get('created_at')
    if not pushed:
        return 'unknown'
    try:
        dt = datetime.fromisoformat(pushed.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days = (now - dt).days
        if days <= ACTIVE_DAYS:
            return 'active'
        if days <= LOW_ACTIVITY_DAYS:
            return 'low'
        return 'inactive'
    except Exception:
        return 'unknown'


def make_li(repo, overrides):
    """Render a single <li> using org overrides first, then GitHub facts as fallback."""
    name = repo.get('name')
    url = repo.get('html_url') or f'https://github.com/{ORG}/{name}'

    meta = overrides.get(name.lower(), {}) if overrides else {}
    # Org-owned summary preferred; else use GitHub description
    summary = meta.get('summary') or repo.get('description') or ''
    maintainers = meta.get('maintainers') or meta.get('maintainer')
    status_override = meta.get('status')
    stage = meta.get('stage')
    featured = meta.get('featured')

    desc = (summary or '').strip()
    desc = html.escape(desc)
    archived = bool(repo.get('archived'))

    status = status_override or status_from_pushed_at(repo)
    status_text = {
        'archived': 'Archived',
        'active': 'Actively maintained',
        'low': 'Low activity',
        'inactive': 'Looking for maintainer',
        'experimental': 'Experimental',
        'seeking-maintainer': 'Seeking maintainer',
        'deprecated': 'Deprecated',
        'unknown': 'Unknown status'
    }.get(status, str(status))

    if maintainers:
        if isinstance(maintainers, str):
            maintainers = [maintainers]
        maintainers = [m for m in maintainers if m]

    if maintainers:
        maint_html = ', '.join([f'<a href="https://github.com/{html.escape(m)}">{html.escape(m)}</a>' for m in maintainers])
    else:
        maint_html = '<span class="no-maintainer">Maintainer not specified</span>'

    pushed = repo.get('pushed_at') or repo.get('updated_at') or ''
    pushed_short = pushed.split('T')[0] if pushed else 'unknown'

    archived_span = '<span class="archived">archived</span>' if archived else ''
    note = f'<span class="repo-note">{desc}</span>' if desc else '<span class="repo-note"></span>'

    featured_span = '<span class="featured">featured</span>' if featured else ''

    li = f'        <li data-status="{html.escape(str(status))}" class="repo-item{" archived" if archived else ""}>'
    li += f'<a class="repo-name" href="{url}">{html.escape(name)}</a>'
    li += f'{note}{archived_span}{featured_span}'
    li += '\n          <div class="repo-meta">'
    li += f'\n            <span class="repo-maintainers">{maint_html}</span>'
    li += f'\n            <span class="repo-updated">Last pushed: {pushed_short}</span>'
    li += f'\n            <span class="repo-status">{status_text}</span>'
    if stage:
        li += f'\n            <span class="repo-stage">Stage: {html.escape(stage)}</span>'
    li += '\n          </div>'
    li += '</li>'
    return li


def main():
    overrides = load_overrides()
    repos = fetch_all_repos()
    repos_sorted = sorted(repos, key=lambda r: r.get('name', '').lower())
    lis = [make_li(r, overrides) for r in repos_sorted]
    new_list_html = "\n".join(lis) + "\n"

    path = 'index.html'
    if not os.path.exists(path):
        logging.error('index.html not found in repo root')
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Prefer explicit markers in index.html for the repo list. This is the contract:
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
        logging.error('Could not find repo-list markers %r and %r in index.html; please add them around the <ul class="repo-list"> block.', start_marker, end_marker)
        sys.exit(1)

    today = datetime.utcnow().strftime('%Y-%m-%d')
    new_content = re.sub(r'updated \d{4}-\d{2}-\d{2}\.', f'updated {today}.', new_content)

    if new_content == content:
        print('No changes needed')
        return

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('index.html updated')


if __name__ == '__main__':
    main()
