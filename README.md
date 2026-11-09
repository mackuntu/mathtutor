# MathTutor

A web application for generating, printing and grading math worksheets for children.

## Quick Start

Prerequisites: Python 3.12, Docker (for local Postgres), and Google OAuth credentials (optional locally).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # then edit values

docker compose up -d db         # Postgres on localhost:5432
FLASK_ENV=development FLASK_APP=src flask run --debug --port 8080
```

The database schema is applied automatically on first use. Open http://localhost:8080.

For local development without Google login, visit
`/auth/test-auth?bypass_key=test-bypass-key-for-selenium` (only works when `FLASK_ENV=development`).

## Configuration

All configuration is read from environment variables (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string |
| `FLASK_ENV` | `development` or `production` |
| `FLASK_SECRET_KEY` | Session signing key |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `OAUTH_REDIRECT_URI` | OAuth callback URL |
| `TEST_DATABASE_URL` | Test database for pytest (name must end in `_test`) |

### Google OAuth setup

1. In [Google Cloud Console](https://console.cloud.google.com), create an OAuth 2.0 Client ID (Web application).
2. Add `http://localhost:8080/auth/oauth/callback` as an authorized redirect URI.
3. Put the client ID and secret in `.env`.

## Project Structure

```
src/
├── __init__.py            # App factory
├── auth.py                # Authentication manager
├── config.py              # Configuration
├── problem_generator.py   # Math problem generation
├── problem_generators/    # Strategy classes per problem family
├── database/              # Postgres: db.py, schema.sql, models.py, repository.py
├── routes/                # Blueprints: auth, children, worksheets, pages
├── blog/ content/         # Blog articles
├── static/ templates/     # Frontend assets
tests/                     # pytest suite (real Postgres)
```

## Features

- Google sign-in with secure sessions
- Child profiles (grade, birthday, preferred color)
- Grade-appropriate, print-ready worksheets with answer keys and serial numbers
- Worksheet history, manual grading and score tracking

## Testing

```bash
docker compose up -d db
pytest tests/ -W error
```

## Troubleshooting

- **Database connection errors**: make sure `docker compose up -d db` is running and `DATABASE_URL` matches it.
- **OAuth login problems**: check the Google credentials and that `OAUTH_REDIRECT_URI` matches the console.

## License

MIT License
