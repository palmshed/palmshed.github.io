#!/usr/bin/env python3
import os
import sys
import requests
from datetime import datetime
import html

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
ORG = os.environ.get('ORG_NAME', 'palmshed')
API_URL = f'https://api.github.com/orgs/{ORG}/repos'

HEADERS = {}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'
HEADERS['Accept'] = 'application/vnd.github.v3+json'


def fetch_all_repos():
    repos = []
    page = 1
    per_page = 100
    while True:
        resp = requests.get(API_URL, params={'per_page': per_page, 'page': page, 'type': 'all'}, headers=HEADERS)
        if resp.status_code != 200:
            print('Failed to fetch repos:', resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return repos


def make_li(repo):
    name = repo.get('name')
    url = repo.get('html_url') or f'https://github.com/{ORG}/{name}'
    desc = repo.get('description') or ''
    desc = html.escape(desc)
    archived = repo.get('archived', False)
    archived_span = '<span class="archived">archived</span>' if archived else ''
    note = f'<span class="repo-note">{desc}</span>' if desc else '<span class="repo-note"></span>'
    return f'        <li><a class="repo-name" href="{url}">{html.escape(name)}</a>{note}{archived_span}</li>'


def main():
    repos = fetch_all_repos()
    # sort by name
    repos_sorted = sorted(repos, key=lambda r: r.get('name','').lower())
    lis = [make_li(r) for r in repos_sorted]
    new_list_html = "\n".join(lis) + "\n"

    # read index.html
    path = 'index.html'
    if not os.path.exists(path):
        print('index.html not found in repo root', file=sys.stderr)
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    # replace the repo-list contents
    pattern = re.compile(r'(<ul class="repo-list">)(.*?)(</ul>)', re.DOTALL)
    if not pattern.search(content):
        print('Could not find <ul class="repo-list"> in index.html', file=sys.stderr)
        sys.exit(1)

    replacement = r"\1\n" + new_list_html + r"    \3"
    new_content = pattern.sub(replacement, content, count=1)

    # update footer date
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
