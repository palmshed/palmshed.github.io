# palmshed.github.io

Organization homepage for Palmshed. Lists projects, applications, and repositories. Static site, no framework.

## Structure

- `.github/site/` — the site, a set of static HTML pages served from GitHub Pages.
- `auth/` — the authentication backend (separate Vercel project). See `auth/README.md` and `AUTH.md`.
- `scripts/sync_index.py` — generates the repository archive in `index.html`.
- `data/` — source data for generated sections.

## Development

The site is plain HTML/CSS. Open any page in `.github/site/` directly, or serve the folder:

```sh
python -m http.server -d .github/site
```

## Deployment

Pushing to `main` deploys the site via GitHub Pages (see `.github/workflows/deploy-site.yml`), which publishes `.github/site/`.

## Repository archive

The repo list between the `<!-- repo-list-start -->` and `<!-- repo-list-end -->` markers in `index.html` is generated:

```sh
python scripts/sync_index.py
```

Requires `GITHUB_TOKEN` and `requests`. Run daily via GitHub Actions (see `.github/workflows/sync-org-page.yml`).

## Captcha

The sign-in page uses [hCaptcha](https://www.hcaptcha.com) for bot protection.
See hCaptcha's [privacy policy](https://www.hcaptcha.com/privacy) and
[terms](https://hcaptcha.com/terms).
