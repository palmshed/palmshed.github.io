# palmshed.github.io

Organization homepage for Palmshed. Lists projects, applications, and repositories. Static site, no framework.

## Structure

- `.github/site/` — the site, a set of static HTML pages served from GitHub Pages.
- `auth/` — the authentication backend (separate Vercel project). See `auth/README.md` and `AUTH.md`.

## Development

The site is plain HTML/CSS. Open any page in `.github/site/` directly, or serve the folder:

```sh
python -m http.server -d .github/site
```

## Deployment

Pushing to `main` deploys the site via GitHub Pages (see `.github/workflows/deploy-site.yml`), which publishes `.github/site/`.

## Captcha

The sign-in page uses [hCaptcha](https://www.hcaptcha.com) for bot protection.
See hCaptcha's [privacy policy](https://www.hcaptcha.com/privacy) and
[terms](https://hcaptcha.com/terms).
