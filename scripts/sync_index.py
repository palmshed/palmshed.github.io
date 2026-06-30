#!/usr/bin/env python3
import os
import sys
import time
import requests
from datetime import datetime, timezone
import html
import logging

# Config via environment
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
ORG = os.environ.get('ORG_NAME', 'palmshed')

# thresholds in days
ACTIVE_DAYS = int(os.environ.get('ACTIVE_DAYS', '180'))      # <= Active
LOW_ACTIVITY_DAYS = int(os.environ.get('LOW_ACTIVITY_DAYS', '365'))  # <= Low
# whether to include contributors (each repo will do one additional API call)
INCLUDE_CONTRIBS = os.environ.get('INCLUDE_CONTRIBS', '1') != '0'
MAX_CONTRIBS = int(os.environ.get('MAX_CONTRIBS', '3'))

API_URL = f'https://api.github.com/orgs/{ORG}/repos'
HEADERS = {'Accept': 'application/vnd.github.v3+json'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

# Respect a brief pause between per-repo contributor requests to avoid bursts
PER_REPO_DELAY = float(os.environ.get('PER_REPO_DELAY', '0.15'))


def fetch_all_repos():
    repos = []
    page = 1
    per_page = 100
    while True:
        resp = requests.get(API_URL, params={'per_page': per_page, 'page': page, 'type': 'all'}, headers=HEADERS)
        if resp.status_code != 200:
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


def fetch_top_contributors(repo):
    if not INCLUDE_CONTRIBS:
        return []
    url = repo.get('contributors_url')
    if not url:
        return []
    try:
        resp = requests.get(url, params={'per_page': MAX_CONTRIBS}, headers=HEADERS)
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [c.get('login') for c in data if c.get('login')]
    except Exception:
        return []


def status_from_pushed_at(repo):
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


def make_li(repo):
    name = repo.get('name')
    url = repo.get('html_url') or f'https://github.com/{ORG}/{name}'
    desc = (repo.get('description') or '').strip()
    desc = html.escape(desc)
    archived = bool(repo.get('archived'))
    status = status_from_pushed_at(repo)
    status_text = {
        'archived': 'Archived',
        'active': 'Actively maintained',
        'low': 'Low activity',
        'inactive': 'Looking for maintainer',
        'unknown': 'Unknown status'
    }.get(status, 'Unknown status')

    # contributors
    contributors = fetch_top_contributors(repo)
    # small backoff to avoid hitting abuse/rate limits if many repos
    time.sleep(PER_REPO_DELAY)

    if contributors:
        contrib_html = ' by ' + ', '.join([f'<a href="https://github.com/{html.escape(c)}">{html.escape(c)}</a>' for c in contributors])
    else:
        contrib_html = ' by <span class="no-maintainer">(no known maintainers)</span>'

    pushed = repo.get('pushed_at') or repo.get('updated_at') or ''
    pushed_short = pushed.split('T')[0] if pushed else 'unknown'

    archived_span = '<span class="archived">archived</span>' if archived else ''
    note = f'<span class="repo-note">{desc}</span>' if desc else '<span class="repo-note"></span>'

    li = f'        <li data-status="{status}" class="repo-item{" archived" if archived else ""}>'
    li += f'<a class="repo-name" href="{url}">{html.escape(name)}</a>'
    li += f'{note}{archived_span}'
    li += '\n          <div class="repo-meta">'
    li += f'\n            <span class="repo-contribs">{contrib_html}</span>'
    li += f'\n            <span class="repo-updated">Last pushed: {pushed_short}</span>'
    li += f'\n            <span class="repo-status">{status_text}</span>'
    li += '\n          </div>'
    li += '</li>'
    return li


def main():
    repos = fetch_all_repos()
    repos_sorted = sorted(repos, key=lambda r: r.get('name', '').lower())
    lis = [make_li(r) for r in repos_sorted]
    new_list_html = "\n".join(lis) + "\n"

    path = 'index.html'
    if not os.path.exists(path):
        logging.error('index.html not found in repo root')
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    pattern = re.compile(r'(<ul class="repo-list">)(.*?)(</ul>)', re.DOTALL)
    if not pattern.search(content):
        logging.error('Could not find <ul class="repo-list"> in index.html')
        sys.exit(1)

    replacement = r"\1\n" + new_list_html + r"    \3"
    new_content = pattern.sub(replacement, content, count=1)

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
