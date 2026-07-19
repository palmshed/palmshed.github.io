# auth

Authentication backend for the Palmshed site. Deploys to Vercel as a separate
project from the GitHub Pages site.

This folder is self-contained. Full deployment, environment, schema, and CORS
details are in the root [`AUTH.md`](../AUTH.md).

## Layout

- `api/` — Vercel functions: `config`, `register`, `login`, `forgot-password`, `reset-password`
- `api/_lib/` — `db`, `auth`, `captcha`, `http` helpers
- `db/schema.sql` — Postgres schema
- `vercel.json` — runtime/region config

## Local

```sh
cd auth
vercel dev          # local server with env from .env.local
psql "$DATABASE_URL" -f db/schema.sql
```

## Deploy

```sh
cd auth
vercel deploy --prod
```

Set environment variables in the Vercel dashboard (or `vercel env add`):
`DATABASE_URL`, `HCAPTCHA_SITE_KEY`, `CAPTCHA_SECRET`, `CAPTCHA_PROVIDER`,
`RESEND_API_KEY`, `RESEND_FROM`, `PUBLIC_BASE_URL`, `ALLOWED_ORIGIN`.
