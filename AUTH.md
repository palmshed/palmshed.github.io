# Authentication

The site is served from GitHub Pages (static). Real login needs a backend, which
lives in the **`auth/` folder** of this repo and deploys to a separate Vercel
project. The site calls it cross-origin.

## Layout

- `auth/` ~ the Vercel backend project (self-contained)
  - `package.json`, `vercel.json`
  - `db/schema.sql` ~ Postgres schema (run once)
  - `api/config.js` ~ public captcha config
  - `api/register.js` ~ create account
  - `api/login.js` ~ verify + set session cookie
  - `api/forgot-password.js` ~ issue reset token + email
  - `api/reset-password.js` ~ apply new password
  - `api/_lib/*` ~ db, auth, captcha, http (CORS) helpers
- `.github/site/login.html` ~ the UI; `API_BASE` points at the Vercel URL

## Deploy the backend (one time)

```bash
cd auth
vercel link            # link or create a Vercel project (e.g. palmshed-auth)
vercel env add DATABASE_URL         # paste Vercel Postgres URL
vercel env add HCAPTCHA_SITE_KEY
vercel env add CAPTCHA_SECRET
vercel env add CAPTCHA_PROVIDER hcaptcha
vercel env add RESEND_API_KEY
vercel env add RESEND_FROM auth@palmshed.io
vercel env add PUBLIC_BASE_URL https://palmshed.github.io
vercel env add ALLOWED_ORIGIN https://palmshed.github.io
vercel deploy --prod
```

Note the deployed URL (e.g. `https://palmshed-auth.vercel.app`) and set
`API_BASE` at the top of `.github/site/login.html` to match.

## Database

```bash
cd auth
psql "$DATABASE_URL" -f db/schema.sql
```

## CORS

Every function returns `Access-Control-Allow-Origin: <ALLOWED_ORIGIN>` with
`Access-Control-Allow-Credentials: true`, and answers `OPTIONS` preflight with
204. Cookies are HttpOnly + SameSite=Lax.

## Notes

- Passwords: scrypt + per-user salt. No plaintext stored.
- Captcha verified server-side only.
- `RESEND_DISABLED=true` logs reset links instead of emailing (local/dev).
- `CAPTCHA_DISABLED=true` skips captcha verification (local/dev).
