# Contributing

## Design principles

This site follows an understated, institutional tone. See AGENTS.md for full guidelines. The short version: prefer short sentences, avoid decorative punctuation and promotional language, and let the content speak for itself.

## Section guide

| Section | Maintained | How to add a project |
|---|---|---|
| What We Build | Hand-edited | Add an `<li>` under the relevant domain column |
| Technologies | Hand-edited | Add to the appropriate `<p>` tag |
| Featured Projects | Hand-edited | Add a new `.featured-card` block + add entry to `data/projects.json` |
| What You'll Build | Hand-edited | Add an `<li>` to the list |
| Repository Archive | Generated | Nothing to edit — runs daily via GitHub Actions |

## Adding a project to Featured Projects

1. Add a `.featured-card` block in `index.html` inside the `.featured-grid` div. Each card shows: name, description, platform badges, action links, and metadata.
2. Add an entry to `data/projects.json` if the project needs custom metadata (maintainer, stage, featured flag). The GitHub API fills in everything else.

## Running the sync script locally

```sh
export GITHUB_TOKEN=your_token
export ORG_NAME=palmshed
pip install requests
python scripts/sync_index.py
```

The script updates only the repo list between `<!-- repo-list-start -->` and `<!-- repo-list-end -->` in `index.html`.
