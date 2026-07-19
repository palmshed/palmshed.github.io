# Authentication backend

The site is served from GitHub Pages (static, no server). Real username/password
login, captcha verification, and password-reset email require a backend. That
backend lives in a **separate Vercel project** (this repo stays static).

The login page is `.github/site/login.html`. It calls `API_BASE` (a Vercel URL)
defined at the top of its scripts. Set that to your Vercel deployment.

## Backend project (deploy separately to Vercel)

Files needed in the Vercel project root:

- `package.json` — deps: `drizzle-orm`, `postgres`, `dotenv`
- `vercel.json` — runtime nodejs20.x, functions `api/*.js`
- `db/schema.sql` — run once against Vercel Postgres
- `api/_lib/{db,auth,captcha,http,schema}.js`
- `api/{config,login,forgot-password,reset-password}.js`

### CORS (required — browser on github.io calls a different origin)

Every function response must include:

```
Access-Control-Allow-Origin: https://palmshed.github.io
Access-Control-Allow-Credentials: true
Access-Control-Allow-Headers: content-type
Access-Control-Allow-Methods: POST, OPTIONS
```

Handle `OPTIONS` preflight by returning 204 with the headers above.

### Environment variables (Vercel project settings)

```
DATABASE_URL            # Vercel Postgres
HCAPTCHA_SITE_KEY       # public, returned by /api/config
CAPTCHA_SECRET          # server-side hCaptcha verify
CAPTCHA_PROVIDER=hcaptcha
RESEND_API_KEY          # transactional email
RESEND_FROM=auth@palmshed.io
PUBLIC_BASE_URL=https://palmshed.github.io   # used in reset links
# RESEND_DISABLED=true   # log reset links instead of sending (dev)
# CAPTCHA_DISABLED=true  # skip captcha verify (dev)
```

### Database

`db/schema.sql` creates `users`, `sessions`, `password_resets`.
Run with: `psql "$DATABASE_URL" -f db/schema.sql`

### Endpoint summary

- `GET  /api/config` — returns public `{ captchaSiteKey, captchaProvider }`
- `POST /api/login` — `{ username, password, captcha }` → sets httpOnly session cookie
- `POST /api/forgot-password` — `{ username, captcha }` → emails reset link
- `POST /api/reset-password` — `{ token, password }` → updates password

Passwords are hashed with scrypt + per-user salt. Sessions are httpOnly,
SameSite=Lax cookies. Captcha is verified server-side; never trusted client-side.
