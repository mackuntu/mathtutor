# MathTutor on Vercel — Hosting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Serve MathTutor at `https://mathtutor.mackuntu.com` on Vercel, backed by Neon Postgres, owner-only Google login, with device tokens for the Pi and the iPhone app.

**Architecture:** Strip removed features first so less code has to move. Then a plain-SQL `PostgresRepository` (psycopg v3) replaces `DynamoDBRepository` behind the same `get_repository()` and method names. One connection per request (`flask.g`), with the schema applied idempotently on the process's first DB use. Vercel runs the Flask WSGI app from `api/index.py`, and every path is rewritten to it.

**Tech Stack:** Python 3.12, Flask 3.1, psycopg 3 (`psycopg[binary]`), Neon Postgres, pytest against a Docker Postgres, Vercel Python runtime.

**Spec:** `docs/superpowers/specs/2026-11-08-vercel-hosting-design.md`

**Previous todo** (grade-3 visuals, finished) is in git history at `9c6b4ed:tasks/todo.md`.

## Global Constraints

- Never change the layout of `src/templates/problem_grid.html`. Printed output must look the same as today.
- Postgres only. No boto3, moto, DynamoDB Local, `create_tables`, or `.ebextensions` anywhere.
- Owner only: Google OAuth, allowlisted by env var `ALLOWED_EMAILS` (comma-separated). No signup, and no Facebook or X login.
- Strip subscriptions, payments/Stripe, ads (AdSense and Facebook Audience) and admin as code. Don't feature-flag them.
- Delete the old OCR grader, its routes (`/upload-for-grading`, `/grade-results`, `/review-grading`, `/update-grade`, `/submit-reviewed-grades`), its templates and tests, and the easyocr/torch/opencv deps.
- Keep manual grading (`/<id>/grade`, `/<id>/submit_grades`, `/<id>/submit`).
- Config comes from env vars only: `DATABASE_URL`, `FLASK_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`, `ALLOWED_EMAILS`. On Vercel, a missing `FLASK_SECRET_KEY` or `DATABASE_URL` must fail fast.
- `/auth/test-auth` is disabled on Vercel, previews included (env `VERCEL` is set there).
- Start with a fresh database; no data migration.
- Vercel installs only `requirements.txt`. The deploy bundle must contain no torch, easyocr or opencv.
- Commit messages follow conventional commits (`feat:`, `refactor:`, `chore:` …).

## Review Focus

1. **Expired or unknown session cookie:** the user is redirected to login, not shown a 500, and the expired row is deleted. Test in Task 4.
2. **Allowlist email matching:** a Google email that differs only in case or surrounding spaces from an `ALLOWED_EMAILS` entry is allowed. An unlisted email gets a 403 page, and no user row or session is created. Test in Task 6.
3. **Cold start on an empty preview branch:** the first request against a brand-new database creates the schema and `/` renders. Running the schema twice is harmless. Test in Task 3.
4. **Device token misuse:** each of these returns 401: a revoked token, a wrong token, a bearer token sent to a non-`/api` route, and a token on an `/api` route with no `Bearer ` prefix. `last_used_at` updates only on success. Test in Task 7.
5. **Deleting a child:** the child's worksheets go too (FK `ON DELETE CASCADE`), and the history pages for the other children still render. Test in Task 4.

---

## File Structure

| Path | Responsibility |
|---|---|
| `src/database/schema.sql` | Idempotent DDL for all tables |
| `src/database/db.py` | `get_conn()` per request, `ensure_schema()`, teardown |
| `src/database/repository.py` | `PostgresRepository` (replaces Dynamo version, same file) |
| `src/database/models.py` | Plain model classes, no Dynamo serialization |
| `src/database/__init__.py` | Re-exports `get_repository`, `init_db` |
| `src/device_tokens.py` | Create/verify/revoke tokens; `require_device_or_session` decorator |
| `src/routes/settings.py` | `/settings/devices` page |
| `src/templates/settings_devices.html` | Token list/create/revoke UI |
| `api/index.py` | Vercel entrypoint: `from src import create_app; app = create_app()` |
| `vercel.json`, `.vercelignore` | Routing, function config, bundle exclusions |
| `docker-compose.yml` | Local + test Postgres 16 on port 5432 |
| `requirements.txt` / `requirements-dev.txt` | Runtime / test+lint deps |
| `tests/conftest.py` | Postgres fixtures (schema per session, TRUNCATE per test) |

---

### Task 1: Delete the OCR grader and the PDF renderer CLI

**Files:**
- Delete: `src/grading/`, `src/templates/upload_worksheet.html`, `src/templates/review_grading.html`, `src/templates/grade_results.html`, `tests/test_image_alignment.py`, `tests/test_image_preprocessing.py`, `tests/test_paper_rectification.py`, `src/document/renderer.py`, `src/main.py`, `tests/test_document_renderer.py`, `tests/generate_test_pdf.py`, `worksheets.db`, `test-downloads/`
- Modify: `src/routes/worksheets.py`. Remove the 5 OCR routes (lines ~626–1094) and the `DocumentRenderer` import on line 26. Keep `LayoutChoice` from `src/document/template.py`, because worksheets.py uses it.
- Modify: `src/templates/past_worksheets.html` and any other template linking to the removed endpoints (find them with `grep -rn "upload_for_grading\|grade_results\|review_ocr_grading" src/templates`).
- Modify: `tests/conftest.py`: drop the `DocumentRenderer` import and its fixture.
- Modify: `src/database/models.py`. Drop the OCR-only Worksheet fields `student_answers`, `answer_regions`, `pdf_dimensions` and `answer_images`.

**Interfaces:**
- Produces: `Worksheet(child_id, problems, answers, completed, incorrect_problems, correct_answers)`. These are the only fields left for later tasks.

- [x] **Step 1:** Delete the files listed and remove the routes and imports.
- [x] **Step 2:** `grep -rnE "grading|easyocr|cv2|torch|reportlab|DocumentRenderer|student_answers|answer_regions|answer_images|pdf_dimensions" src tests` prints nothing. The exceptions are manual-grading names (`grade_worksheet`, `submit_grades`) and `test_generator.py` text.
- [x] **Step 3:** `python -c "from src.routes import worksheets"` exits 0.
- [x] **Step 4:** `pytest tests/test_generator.py -q` passes.
- [x] **Step 5:** Commit `refactor: remove OCR grader and unused PDF renderer`.

### Task 2: Strip subscriptions, payments, ads, admin, Facebook/X, and split deps

**Files:**
- Delete: `src/routes/subscription.py`, `src/routes/admin.py`, `src/templates/subscription.html`, `src/templates/admin/`, `src/database.py` (legacy duplicate), `src/config_prod.py`, `setup_dynamodb.py`, `scripts/create_dynamodb_tables.py`, `scripts/test_dynamodb_connection.py`, `.ebextensions/`, `Procfile`, `DEPLOYMENT_CHECKLIST.md`, `DEPLOYMENT_GUIDE.md`, `dynamodb-local-metadata.json`, `tests/ui/` (Selenium against DynamoDB; out of scope)
- Modify: `src/routes/__init__.py` (unregister the subscription and admin blueprints), `src/routes/pages.py:9,35-61` and `src/routes/worksheets.py:24,120-129,213-223,381-386` (remove every Subscription use, so generation is always allowed), `src/database/models.py` and `src/database/repository.py` (drop `Subscription`, `Payment` and their repo methods), `src/config.py` (drop the facebook/x providers, AdSense/FB ad vars and AWS vars), `src/auth.py` (drop the `_verify_facebook_token` and `_verify_x_token` paths and the PKCE helpers that only X uses), `src/routes/auth.py` (drop the `/oauth/facebook` and `/oauth/x` routes), `src/templates/base.html:30-47,110-111` and `login.html`, `index.html`, `children.html`, `terms.html`, `blog_article.html` (remove the ad blocks, the subscription nav, and the FB/X buttons)
- Modify: `requirements.txt` becomes runtime only: `Flask`, `Werkzeug`, `python-dotenv`, `requests`, `google-auth`, `google-auth-oauthlib`, `oauthlib`, `requests-oauthlib`, `markdown`, `python-frontmatter`, plus `boto3`/`botocore` **temporarily** (Task 4 removes them). Leave out Pillow, numpy and gunicorn.
- Create: `requirements-dev.txt` containing `-r requirements.txt`, then pytest, pytest-cov, black, flake8, mypy, pre-commit, types-requests, plus `moto` temporarily (Task 4 removes it).
- Blog: keep it. `src/blog/manager.py` reads markdown from `src/content/blog`, so it is static and trivial.

- [x] **Step 1:** Delete the files and make the edits above.
- [x] **Step 2:** `grep -rniE "subscription|payment|adsense|adsbygoogle|facebook|FACEBOOK_|X_CLIENT|twitter|oauth_x|admin" src` prints nothing.
- [x] **Step 3:** `pip install -r requirements-dev.txt` runs in a fresh `.venv`, and `python -c "from src import create_app"` succeeds.
- [x] **Step 4:** `pytest tests/test_generator.py -q` passes.
- [x] **Step 5:** Commit `refactor: strip subscriptions, payments, ads, admin, FB/X login; split deps`.

### Task 3: Postgres schema, connection layer, test harness

**Files:**
- Create: `docker-compose.yml` with the `postgres:16` service `db`, `POSTGRES_PASSWORD=mathtutor`, `POSTGRES_DB=mathtutor`, and port `5432:5432`.
- Create: `src/database/schema.sql`.
- Create: `src/database/db.py`.
- Modify: `requirements.txt` to add `psycopg[binary]>=3.2,<4`.
- Modify: `tests/conftest.py` to add the Postgres fixtures alongside the moto ones (Task 4 deletes the moto ones). Create `tests/test_db.py`.

**Schema (exact):**
```sql
CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY, name TEXT NOT NULL, picture TEXT,
  created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL);
CREATE TABLE IF NOT EXISTS children (
  id TEXT PRIMARY KEY, parent_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
  name TEXT NOT NULL, age INT NOT NULL, grade INT NOT NULL, preferred_color TEXT,
  birthday DATE, created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL);
CREATE INDEX IF NOT EXISTS children_parent_idx ON children(parent_email);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY, user_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
  expires_at BIGINT NOT NULL);
CREATE TABLE IF NOT EXISTS worksheets (
  id TEXT PRIMARY KEY, child_id TEXT NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  serial TEXT NOT NULL, problems JSONB NOT NULL, answers JSONB,
  completed BOOLEAN NOT NULL DEFAULT FALSE, incorrect_problems JSONB NOT NULL DEFAULT '[]',
  correct_answers JSONB, created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL);
CREATE INDEX IF NOT EXISTS worksheets_child_idx ON worksheets(child_id, created_at DESC);
CREATE INDEX IF NOT EXISTS worksheets_serial_idx ON worksheets(serial);
CREATE TABLE IF NOT EXISTS device_tokens (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE,
  created_at BIGINT NOT NULL, last_used_at BIGINT, revoked_at BIGINT);
```
(Timestamps stay epoch-seconds `BIGINT`, so existing `utc_now()` callers and templates are unchanged.)

**Interfaces:**
- Produces: `src.database.db.get_conn() -> psycopg.Connection`. It is cached on `flask.g`, uses `autocommit=True` and `row_factory=dict_row`, reads the DSN from env `DATABASE_URL`, and calls `ensure_schema(conn)` the first time in each process.
- Produces: `ensure_schema(conn) -> None`, which runs `schema.sql`.
- Produces: `close_conn(exc=None) -> None`, registered with `app.teardown_appcontext` by `init_db(app)`.
- Produces: `conftest.py` fixtures. `pg_url` is session-scoped: it reads env `TEST_DATABASE_URL`, defaulting to `postgresql://postgres:mathtutor@localhost:5432/mathtutor_test`, and creates the database if missing. `db` is per-test: it sets `DATABASE_URL`, then runs `TRUNCATE users, children, sessions, worksheets, device_tokens CASCADE`. `app` gives `create_app()` with `TESTING=True`. `client` is `app.test_client()`.

- [x] **Step 1: Write failing tests** in `tests/test_db.py`:
  - `test_ensure_schema_is_idempotent`: call `ensure_schema` twice on the same connection. No error, and `information_schema.tables` lists all 5 tables.
  - `test_cold_start_empty_database_renders_index`: drop and recreate the public schema, reset the module's "schema applied" flag, then `client.get("/")`. Status is 200 or 302, and the tables exist afterwards.
- [x] **Step 2:** `docker compose up -d db && pytest tests/test_db.py -v` fails because `src.database.db` doesn't exist yet.
- [x] **Step 3:** Implement `schema.sql` and `db.py` as specified.
- [x] **Step 4:** `pytest tests/test_db.py -v` passes.
- [x] **Step 5:** Commit `feat(db): Postgres schema, per-request connection, test harness`.

### Task 4: `PostgresRepository`

**Files:**
- Modify: `src/database/repository.py`. Replace `DynamoDBRepository` wholesale.
- Modify: `src/database/models.py`. Rename the base class to `Model`, keeping `generate_id()` and `utc_now()`. Delete the `to_item/from_item/to_dynamodb_item/from_dynamodb_item` methods and add `from_row(cls, row: dict)` on each model. `Worksheet` gains `serial: str`, set in `__init__` to `f"WS-{self.id[:8]}"`. `serial_number` returns `self.serial`, and the id setter in `from_row` keeps them consistent.
- Modify: `src/database/__init__.py` to export `get_repository() -> PostgresRepository` and `init_db(app)`, with no boto3.
- Delete: `src/database/dynamodb.py`, `src/database/create_tables.py`, `src/database/config.py`.
- Test: `tests/test_repository.py`. Rewrite `tests/test_worksheet.py`, `tests/test_child_registration.py`, `tests/test_auth.py` and `tests/test_new_features.py` onto the `db` fixture, and delete the cases for removed features.

**Interfaces (method names unchanged from today; these are all that remain after Tasks 1–2):**
`get_user_by_email(email) -> User|None`, `create_user(user)`, `update_user(user)`, `get_child_by_id(id) -> Child|None`, `get_children_by_parent(email) -> list[Child]` (by name), `create_child(child)`, `update_child(child)`, `delete_child(id)`, `get_session(token) -> Session|None`, `create_session(s)`, `delete_session(token)`, `delete_expired_sessions(now: int) -> int` (new), `get_worksheet(id) -> Worksheet|None`, `get_child_worksheets(child_id) -> list[Worksheet]` (newest first), `get_worksheets_by_serial(serial) -> list[Worksheet]` (new; for the grader), `create_worksheet(w)`, `update_worksheet(w)`, `delete_worksheet(id)`. Drop `scan_*` and `get_user_sessions` unless something still calls them (grep).
JSONB columns are written with `psycopg.types.json.Jsonb(...)`. Every query is parameterized, with no string formatting of values.

- [x] **Step 1: Write failing tests** in `tests/test_repository.py`:
  - `test_user_roundtrip`: create, then fetch; `name` and `picture` are equal.
  - `test_children_by_parent_only_returns_that_parents_children`.
  - `test_worksheet_roundtrip_preserves_jsonb`: problems is a list of dicts, `correct_answers == ["12", "3:05"]`, and `serial == "WS-" + id[:8]`.
  - `test_get_worksheets_by_serial`.
  - `test_child_worksheets_newest_first`.
  - `test_update_worksheet_persists_grades`: `completed=True, incorrect_problems=[2, 5]`.
  - `test_delete_child_cascades_worksheets` (Review Focus 5): afterwards `get_worksheet(w.id) is None`.
  - `test_delete_expired_sessions_removes_only_expired`.
  - `test_expired_session_cookie_redirects_to_login` (Review Focus 1): insert a session with `expires_at = now - 1` and set the cookie. `client.get("/children/")` returns a 302 to `/auth/login`, and the session row is gone.
- [x] **Step 2:** `pytest tests/test_repository.py -v` fails.
- [x] **Step 3:** Implement the repository and model changes. `AuthManager.create_session` calls `delete_expired_sessions(now)` before inserting. Remove the session token from the debug log at `src/routes/common.py:22`.
- [x] **Step 4:** Remove `boto3`/`botocore` from `requirements.txt`, `moto` from `requirements-dev.txt`, and the moto fixtures from `conftest.py`. `pytest tests/ -q` is fully green, and `grep -rnE "boto|moto|dynamo" -i src tests requirements*.txt` prints nothing.
- [x] **Step 5:** Commit `feat(db): PostgresRepository replaces DynamoDB`.

### Task 5: Local end-to-end smoke test

- [x] **Step 1:** `docker compose up -d db`, then `DATABASE_URL=postgresql://postgres:mathtutor@localhost:5432/mathtutor FLASK_ENV=development FLASK_APP=src flask run --debug --port 8080`.
- [x] **Step 2:** Log in through `/auth/test-auth` (local only), create a child, generate a worksheet, then open the print view and the answer key. The print view is visually identical to `cd3a160` (screenshot both and compare). Check that the serial is shown top-right, that history lists the sheet, and that manual grading saves a score.
- [x] **Step 3:** Update `CLAUDE.md` Build & Run (docker compose plus `flask run`, `pip install -r requirements-dev.txt`, Postgres tests), its Architecture section (blueprints are auth, children, worksheets, pages, settings; models are User, Child, Session, Worksheet), its Testing section (real Postgres, no moto), and the OAuth line (Google only). Update `.env.example` with the 6 env vars plus `TEST_DATABASE_URL`.
- [x] **Step 4:** Commit `docs: local dev on Postgres`.

### Task 6: Owner-only login and production config

**Files:**
- Modify: `src/config.py` to add `ALLOWED_EMAILS: frozenset[str]`, parsed from env with each entry stripped and lowercased, empty entries dropped. `OAUTH_REDIRECT_URI` keeps its env default.
- Modify: `src/routes/auth.py` callback. Lowercase the Google email, and if it's not in `ALLOWED_EMAILS`, render `403` with the text "This MathTutor is private." No `get_or_create_user`, no session. Set the session cookie with `secure=True` when `request.is_secure` or `VERCEL` is set, plus `samesite="Lax"`. In the test-auth gate, also return 404 when `os.environ.get("VERCEL")` is set.
- Modify: `src/__init__.py`. If `VERCEL` is set and either `FLASK_SECRET_KEY` or `DATABASE_URL` is empty, raise `RuntimeError` naming the missing var. Remove the unused `auth_manager` and `repository` locals.
- Test: `tests/test_auth.py`.

- [x] **Step 1: Write failing tests** (mock `AuthManager.exchange_code_for_token` and `verify_oauth_token`):
  - `test_allowlisted_email_logs_in`: returns 302 and sets the `session_token` cookie.
  - `test_allowlist_match_ignores_case_and_spaces` (Review Focus 2): with `ALLOWED_EMAILS=" Me@X.com ,other@y.com"`, Google `me@x.com` is allowed.
  - `test_unlisted_email_rejected_without_user_or_session`: returns 403, the `users` and `sessions` tables are empty, and no cookie is set.
  - `test_test_auth_disabled_on_vercel`: with `VERCEL=1` and `FLASK_ENV=development`, `/auth/test-auth` returns 404.
  - `test_create_app_fails_fast_on_vercel_without_secret`: with `VERCEL=1` and no `FLASK_SECRET_KEY`, `create_app()` raises `RuntimeError` matching `FLASK_SECRET_KEY`.
- [x] **Step 2:** The tests fail.
- [x] **Step 3:** Implement.
- [x] **Step 4:** `pytest tests/ -q` passes.
- [x] **Step 5:** Commit `feat(auth): owner-only Google login, fail-fast prod config`.

### Task 7: Device tokens

**Files:**
- Create: `src/device_tokens.py`, `src/routes/settings.py`, `src/templates/settings_devices.html`.
- Modify: `src/routes/__init__.py` to register `settings` at `/settings`, and `src/database/repository.py` to add the token methods. Add a "Devices" nav link in `base.html` (navigation only; the worksheet templates are untouched).
- Test: `tests/test_device_tokens.py`.

**Interfaces:**
- Repository: `create_device_token(id, name, token_hash, created_at)`, `list_device_tokens() -> list[dict]` (newest first, no hashes returned), `get_active_device_token_by_hash(token_hash) -> dict|None` (`revoked_at IS NULL`), `touch_device_token(id, now)`, `revoke_device_token(id, now)`.
- `src.device_tokens.issue_token(name: str) -> str` returns the raw token, `secrets.token_urlsafe(32)` with the prefix `mt_`. Only `hashlib.sha256(raw).hexdigest()` is stored.
- `src.device_tokens.require_api_auth(view)` is a decorator for `/api/*` views. It accepts `Authorization: Bearer <token>` (the active hash matches, and `last_used_at` updates) or a valid Google session cookie. Otherwise it returns `401 {"error": "unauthorized"}`. It sets `g.user` to the owner, which is the first `ALLOWED_EMAILS` entry, loaded or created via the repository.
- Browser routes never look at the `Authorization` header (the existing `login_required` stays unchanged).
- `/settings/devices` (GET) lists tokens. A POST with `name` creates a token and shows the raw token once. `/settings/devices/<id>/revoke` (POST) revokes. All of these need `login_required`.
- Create: `GET /api/ping`, wrapped in `require_api_auth`, returns `{"ok": true}`. It's used for the tests and by the Pi/iOS to check a token.

- [x] **Step 1: Write failing tests** (Review Focus 4):
  - `test_issued_token_authorizes_api_ping_and_updates_last_used`.
  - `test_revoked_token_401`.
  - `test_wrong_token_401`.
  - `test_token_without_bearer_prefix_401`.
  - `test_bearer_token_does_not_authorize_browser_route`: `/children/` with only a bearer header redirects to login.
  - `test_raw_token_never_stored`: no `device_tokens` row contains the raw token.
  - `test_settings_page_requires_login`.
  - `test_create_shows_token_once_then_list_hides_it`.
- [x] **Step 2:** The tests fail.
- [x] **Step 3:** Implement. Compare with `hmac.compare_digest` after the hash lookup.
- [x] **Step 4:** `pytest tests/ -q` passes.
- [x] **Step 5:** Commit `feat: revocable device tokens for /api clients`.

### Task 8: Vercel packaging

**Files:**
- Create: `api/index.py` containing `from src import create_app` and `app = create_app()`.
- Create: `vercel.json`:
  ```json
  {
    "rewrites": [{ "source": "/(.*)", "destination": "/api/index" }],
    "functions": { "api/index.py": { "maxDuration": 60, "includeFiles": "src/**" } }
  }
  ```
  `maxDuration` is 60 because the grader needs about 15 s per call, and it's set now so the grader reuses it. Confirm the current Python-runtime config keys against the Vercel docs (`vercel:vercel-functions` skill) before you commit.
- Create: `.vercelignore` with `tests/`, `docs/`, `tasks/`, `assets/`, `data/`, `scripts/`, `DynamoDBLocal*`, `*.db`, `test-downloads/`, `test-reports/`, `.venv/`, `run_ui_tests.sh`, `test_blog_manager.py`, `setup.py`.
- Modify: `wsgi.py` stays as is for local use.
- Rewrite: `DEPLOYMENT.md` to cover only Vercel. It holds the owner actions from the spec, the env var table, and how to apply the schema (automatic on first request).

- [x] **Step 1:** Link the project with `vercel link` (needs the owner's `vercel login`, Owner Action 1). Then `vercel build`, and confirm that `.vercel/output/functions/api/index.func` contains no `torch`, `easyocr` or `cv2` (`find .vercel/output -iname "*torch*" -o -iname "*easyocr*" -o -iname "cv2*"` prints nothing), and that it contains `src/templates/problem_grid.html` and `src/static/`.
- [x] **Step 2:** `vercel dev` with `DATABASE_URL` set to local Docker: `/` renders and `/static/...` serves CSS.
- [x] **Step 3:** Commit `chore: Vercel entrypoint and config`.

### Task 9: Deploy (owner actions + verification)

Owner actions, from the spec:
1. `vercel login`.
2. Add Neon from the Marketplace with branch-per-preview on.
3. DNS CNAME `mathtutor` pointing to Vercel.
4. Add the Google redirect URIs `https://mathtutor.mackuntu.com/auth/oauth/callback` and `http://localhost:8080/auth/oauth/callback`.
5. Set the Production env vars `FLASK_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`, `ALLOWED_EMAILS`. Neon provides `DATABASE_URL`.

- [ ] **Step 1:** Push the branch to get a preview deploy. On the preview URL, `/` renders, `/auth/login` shows the Google button, `/auth/test-auth` returns 404, and the Neon preview branch has 5 tables.
- [ ] **Step 2:** Merge to main and deploy to production. Then at `https://mathtutor.mackuntu.com`:
  - the owner logs in with Google
  - creates a child
  - generates and prints a worksheet (print preview matches the local one)
  - views history
  - manually grades it, and the score shows
- [ ] **Step 3:** Log in with a Google account that isn't on the allowlist; it gets the 403 page.
- [ ] **Step 4:** Create the token "iPhone" on `/settings/devices`. `curl -H "Authorization: Bearer <token>" https://mathtutor.mackuntu.com/api/ping` returns `{"ok":true}`. Revoke the token, and the same request returns 401.
- [ ] **Step 5:** Fill in the Review section below.

## Review
Tasks 1–8 done (subagent-driven, each task reviewed; final whole-branch review + one fix wave, re-review clean). 140 tests pass (`pytest tests/ -q -W error`).
- Postgres via `PostgresRepository`; schema auto-applied on first DB use under an advisory lock; Neon-pooler safe (`prepare_threshold=None`, 10s connect timeout).
- Owner-only Google login: `ALLOWED_EMAILS` (fail closed when empty), requires `email_verified`, re-checked on every session; fail-fast config on Vercel; `/auth/test-auth` 404 on Vercel.
- Device tokens: `/settings/devices`, Bearer on `/api/*` only, sha256 stored, no-store pages, `/api/ping`.
- Vercel: zero-config Flask via root `wsgi.py`; `vercel.json` only sets `maxDuration: 60` (doc-backed deviation from plan's `api/index.py` + rewrites). Bundle 37MB, no torch/easyocr/opencv/numpy/boto3.
- Fixed pre-existing bugs found along the way: hard-coded `SECRET_KEY` overrode the real one; child birthday never saved / edit set current age instead of end-of-school-year age; Generate button disabled after subscription removal; `.env` not loaded before config import.
- Print templates unchanged since 9c6b4ed (diff-verified + headless screenshots).
- Task 9 (deploy) pending owner actions.
