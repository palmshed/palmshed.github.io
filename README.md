# palmshed.github.io

Organization homepage for Palmshed. Lists projects, applications, and repositories. Built as a single HTML file with no framework.

## Sections

Everything before the repository archive is hand-maintained. The repo list between <!-- repo-list-start --> and <!-- repo-list-end --> markers is generated from GitHub data.

## Generation

```sh
python scripts/sync_index.py
```

Requires `GITHUB_TOKEN` and `requests`. Run daily via GitHub Actions (see `.github/workflows/sync-org-page.yml`).
