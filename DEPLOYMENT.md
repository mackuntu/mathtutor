# Deploying MathTutor to Vercel

MathTutor runs as a single Flask function on the Vercel Python runtime, backed by
Neon Postgres (via the Vercel Marketplace), served at
`https://mathtutor.mackuntu.com`.

## How it is packaged

- Vercel auto-detects Flask from `requirements.txt` and loads `app` from the
  root `wsgi.py` (a supported zero-config entrypoint). No `api/` directory or
  rewrites are needed.
- `vercel.json` only raises the function `maxDuration` to 60 s (Hobby max is 300 s).
- Python version comes from `.python-version` (3.12).
- Vercel installs only `requirements.txt`; `.vercelignore` keeps tests, docs and
  local data out of the bundle. Templates (`src/templates`), static files
  (`src/static`), blog markdown (`src/content/blog`) and `src/database/schema.sql`
  ship with the function.
- With `VERCEL` set (automatic on Vercel), the app refuses to start unless
  `FLASK_SECRET_KEY` and `DATABASE_URL` are set, and `/auth/test-auth` is disabled.

## Owner actions (one time)

1. `vercel login`, then `vercel link` in this repo (create project `mathtutor`).
2. Add Neon Postgres from the Vercel Marketplace (Storage tab) and connect it to the
   project. Enable branch-per-preview so previews get their own database branch.
   This provides `DATABASE_URL`. Note the Neon region (e.g. `aws-us-east-1`).
3. DNS: add a CNAME record `mathtutor` -> the target Vercel shows after adding
   `mathtutor.mackuntu.com` under Project -> Settings -> Domains.
4. Google Cloud Console -> Credentials -> your OAuth client -> Authorized redirect URIs:
   - `https://mathtutor.mackuntu.com/auth/oauth/callback`
   - `http://localhost:8080/auth/oauth/callback`
5. Set the function region to match the Neon region (Project -> Settings ->
   Functions -> Function Region, e.g. `iad1` for `aws-us-east-1`) so every query
   avoids a cross-region round trip.
6. Set environment variables (Project -> Settings -> Environment Variables, or
   `vercel env add`) as in the table below, for **Production and Preview**.
   Previews also run with `VERCEL` set, so a preview without `FLASK_SECRET_KEY`
   fails to start and one without `ALLOWED_EMAILS` lets nobody log in.
7. Deploy: `vercel --prod` (or push to the connected Git branch).

## Checking a preview

```bash
curl -s -o /dev/null -w "%{http_code}\n" -b session_token=x <preview-url>/children/
```

`302` (redirect to login) proves the app booted and the database is reachable
with the schema applied: the bogus session token is looked up in Postgres before
redirecting. A `500` means a missing env var or an unreachable database.

## Environment variables

Set each for both the Production and Preview environments.

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | Neon Postgres connection string (set by the Neon integration) |
| `FLASK_SECRET_KEY` | yes | Long random string for signing sessions, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ALLOWED_EMAILS` | yes | Comma-separated emails allowed to log in. The **first** entry is the owner identity that device-token (`/api`) requests act as. |
| `GOOGLE_CLIENT_ID` | for Google login | Google OAuth client ID (optional on Preview if you only test via API tokens) |
| `GOOGLE_CLIENT_SECRET` | for Google login | Google OAuth client secret |
| `OAUTH_REDIRECT_URI` | for Google login | `https://mathtutor.mackuntu.com/auth/oauth/callback` |

Never commit secrets; `.env` is git-ignored and excluded from the bundle.

## Database schema

`src/database/schema.sql` is applied automatically (idempotently) on the first
request after a cold start. No manual migration step is needed.

## Device tokens (API clients)

Log in, open `/settings/devices`, and create a token for each device. Verify a token:

```bash
curl -H "Authorization: Bearer <token>" https://mathtutor.mackuntu.com/api/ping
```

Revoke tokens from the same page.

## Local development

```bash
docker compose up -d db
cp .env.example .env     # then edit values
flask --app wsgi run --debug --port 8080   # http://localhost:8080 (reads .env)
pytest tests/
```
