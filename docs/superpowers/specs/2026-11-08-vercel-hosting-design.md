# MathTutor on Vercel — Hosting Design

Date: 2026-11-08 · Branch: `mackuntu/host-on-vercel`

## Intent

MathTutor today runs only on the owner's Mac: DynamoDB Local (Java, port 8000)
plus `flask run --port 8080`. The owner prints worksheets for their kids from
there. Goal: host it at **https://mathtutor.mackuntu.com** on Vercel so it is
always reachable — the foundation for two follow-on projects:

1. **Raspberry Pi button** (next): kid presses a button each morning, Pi fetches
   a fresh worksheet from the hosted site and prints it.
2. **Grader** (after): grade completed worksheets. Design TBD in a separate
   brainstorm.

## Who uses it

Exactly one human user: the owner. Plus, later, one machine client (the Pi).
No public signups, no customers. This drives every simplification below.

## Goals

- App deploys to Vercel (Python runtime, Flask WSGI) and serves at
  `mathtutor.mackuntu.com`.
- Database is Postgres (Neon via Vercel Marketplace), replacing DynamoDB.
- Owner logs in with Google; only the owner's email is allowed.
- Worksheet generation, printing (browser HTML print view, as today), child
  profiles, and worksheet history keep working exactly as now.
- Local dev stays a one-command server, with local Postgres replacing the
  DynamoDB Local Java process.

## Non-goals

- The old OCR grader. It never worked and is being replaced by the photo
  grader (`2026-11-08-photo-grader-design.md`, Claude Sonnet vision via a
  server API). **Delete** `src/grading/`, the OCR routes (`/upload-for-grading`,
  `/grade-results`, `/review-grading`, `/update-grade`,
  `/submit-reviewed-grades`), their templates and tests, and the
  easyocr/torch/opencv deps. No `requirements-grading.txt`.
- **Manual grading stays** (`/<id>/grade`, `/<id>/submit_grades`,
  `/<id>/submit`, "Grade" button on history): no OCR deps, part of history.
  Its data goes through the Postgres repository. *(Builder's call, flagged.)*
- The Pi's endpoint. Pi project designs it (it reuses Device tokens below).
- Migrating existing local DynamoDB data. **Start fresh.**
- Multi-user support, scaling, high availability.

## Anti-goals (failure even if it "works")

- Worksheet layout changes. `src/templates/problem_grid.html` layout is
  immutable (project rule). Printed output must look identical to today.
- Site usable by anyone other than the owner (open signup, unlisted emails
  getting in).
- Deploy that silently drags in torch/easyocr and blows the size limit, or
  only works because of a stale build cache.
- Secrets committed to git.

## Decisions (made with owner)

| Area | Decision |
|---|---|
| Host | Vercel, custom domain `mathtutor.mackuntu.com` |
| DB | Postgres, Neon via Vercel Marketplace (provides `DATABASE_URL`) |
| DynamoDB | Removed entirely — boto3, moto, DynamoDB Local, create_tables, `.ebextensions` |
| Data | Start fresh, no migration |
| Users | Owner only |
| Login | Google OAuth only, allowlisted to owner email (env `ALLOWED_EMAILS`) |
| Removed features | Subscriptions, payments/Stripe, ads (AdSense + Facebook Audience), Facebook & X login, signup. **Strip the code**, not feature-flag it. |
| Kept | Child profiles, worksheet generate/print/answer key, worksheet history (incl. stored correct answers — grader needs them) |

## Constraints & known facts from the codebase

- App factory `src/__init__.py:create_app()`; `wsgi.py` exposes `app`.
- Data access mostly via `DynamoDBRepository` (`src/database/repository.py`,
  ~30 methods) obtained through `get_repository()`. Direct boto3/Dynamo also in
  `src/database/__init__.py`, `src/database.py` (legacy duplicate),
  `src/database/dynamodb.py`, `src/database/create_tables.py`,
  `src/auth.py`, `src/child_registration.py`, tests (`conftest.py` uses moto).
- Models in `src/database/models.py`: User, Child, Session, Worksheet,
  Subscription, Payment. Subscription & Payment go away.
- Sessions: DynamoDB TTL (`expires_at`) auto-expired them. Postgres
  replacement: reject expired sessions on read; delete expired rows
  opportunistically (e.g., on login). No cron needed.
- Worksheets print from HTML (`render_template` of worksheet/answer key);
  browser print. `reportlab` is imported by `src/document/renderer.py` but not
  in `requirements.txt` — fix (add it, or drop the renderer if unreferenced
  after cleanup; builder's call after checking usage).
- Grading imported lazily inside `upload_for_grading` in
  `src/routes/worksheets.py` — the web app imports cleanly without OCR deps.
- Vercel filesystem read-only except `/tmp`; no persistent local files.
  Anything writing to disk at request time (e.g., `worksheets.db`,
  `test-downloads/`) must not be relied on in production.
- Python 3.12 (`.python-version`).
- `TEST_BYPASS_KEY` route (`/auth/test-auth`) must stay disabled in
  production (already gated on `FLASK_ENV`/`TESTING`; verify).
- Vercel CLI installed (v50, outdated) but **not logged in**. Owner must run
  `vercel login`. Docker available locally; no local Postgres install.

## Shape of the solution

- **Dependencies split:** `requirements.txt` = web app only (Flask, psycopg,
  google-auth, requests, markdown/frontmatter if blog kept, reportlab if kept).
  `requirements-dev.txt` = pytest,
  linters. Vercel installs only `requirements.txt`.
- **Repository:** `PostgresRepository` with the same method names the routes
  use today (minus subscription/payment), behind `get_repository()`. Plain SQL
  via `psycopg` (v3); no ORM. One `schema.sql` (idempotent `CREATE TABLE IF NOT
  EXISTS`) applied by a small script / CLI command. Worksheet problems/answers
  as JSONB.
- **Connections:** serverless-friendly — Neon pooled connection string; open
  per request or small module-level pool; no long-lived assumptions.
- **Config:** env vars only — `DATABASE_URL`, `FLASK_SECRET_KEY`,
  `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`,
  `ALLOWED_EMAILS`. `.env.example` updated. Production fails fast if
  `FLASK_SECRET_KEY` or `DATABASE_URL` missing.
- **Vercel config:** `vercel.json` / Python entrypoint pointing at the Flask
  app; static files served correctly; `.vercelignore` excluding grading,
  tests, data, `DynamoDBLocal*`, assets not needed at runtime.
- **Local dev:** `docker run postgres` (or compose file) + `flask run`.
  Update `CLAUDE.md` build/run section accordingly.
- **Tests:** replace moto with a real Postgres (Docker, or `pytest-postgresql`).
  Delete tests for removed features. Existing generator/renderer tests keep
  passing.

## Owner actions (can't be automated)

1. `vercel login`; link project.
2. Add Neon Postgres from Vercel Marketplace to the project.
3. DNS: CNAME `mathtutor` → Vercel target, at whoever hosts mackuntu.com DNS.
4. Google Cloud console, existing OAuth client: add redirect URIs
   `https://mathtutor.mackuntu.com/auth/oauth/callback` and
   `http://localhost:8080/auth/oauth/callback`.
5. Set env vars in Vercel.

## Device tokens *(my call, flagged — shared by Pi and iOS grader)*

Non-browser clients (Raspberry Pi, iPhone grader app) can't do Google OAuth.
Hosting builds the one mechanism both use:
- `device_tokens` table: id, name ("Pi", "iPhone"), sha256 hash of token,
  created_at, last_used_at, revoked_at. Raw token shown once at creation.
- Settings page (Google-login only): create / list / revoke tokens.
- `Authorization: Bearer <token>` accepted on `/api/*` routes only, acting as
  the owner. Browser routes still require the Google session.

## Environments *(builder's calls, flagged)*

| Env | DB | Login |
|---|---|---|
| Local | Docker Postgres | Google, localhost redirect URI (registered above) |
| Preview | Neon **branch per preview** (integration default) — previews never write into real history | No Google login (redirect URIs can't wildcard). Preview checks: app boots, schema applies, unauthenticated pages + login redirect work. `/auth/test-auth` stays **disabled** on Vercel (incl. preview). |
| Production | Neon main branch | Google, allowlisted |

Schema applied idempotently (`CREATE TABLE IF NOT EXISTS`) on cold start /
first DB use, so fresh preview branches just work. `OAUTH_REDIRECT_URI`
derived from env var per environment.

## Left to the builder

- File/module layout of the Postgres layer; exact schema columns (mirror
  current model fields).
- Whether blog and admin pages survive. Default: **remove admin** (single
  user, admin views were users/subscriptions/payments); **keep blog** only if
  it's trivially static, else remove.
- Postgres test harness choice.
- Whether to keep `src/main.py` CLI path.
- Cleanup of stale deploy docs (`DEPLOYMENT*.md`, `.ebextensions`, `Procfile`)
  — replace with one short `DEPLOYMENT.md` for Vercel.

## Done means

- `pytest tests/` green locally against Postgres.
- Local: log in, create child, generate + print a worksheet, view history.
- Preview deploy boots on its own Neon branch (see Environments).
- Production: full flow (login, child, generate + print, history, manual
  grade) works end-to-end.
- Production serves at `https://mathtutor.mackuntu.com`; a non-allowlisted
  Google account is rejected.
- Deploy bundle contains no torch/easyocr/opencv.
- Worksheets table has an indexed `serial` column (`WS-` + first 8 of id) —
  the photo grader looks sheets up by it.
