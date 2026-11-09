# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # includes requirements.txt
cp .env.example .env

# Start Postgres (docker-compose.yml service `db`, port 5432)
docker compose up -d db

# Run the app (http://localhost:8080); schema is applied automatically on first DB use
FLASK_ENV=development FLASK_APP=src flask run --debug --port 8080

# Local login bypass (development only): /auth/test-auth?bypass_key=test-bypass-key-for-selenium

# Run tests (need the Postgres container above; creates a `mathtutor_test` DB)
pytest tests/                    # All tests
pytest tests/ -k "test_name"     # Single test
```

## Architecture

**Flask app with blueprint-based routing:**
- `src/__init__.py` - App factory (`create_app()`)
- `src/routes/` - Blueprints: auth, children, worksheets, pages (settings is added with device tokens)
- `src/database/` - Postgres: `db.py` (per-request connection from `DATABASE_URL`), `schema.sql`, `models.py`, `repository.py` (`PostgresRepository`)
- `src/problem_generators/` - Strategy pattern for math problems (basic_operations.py, multiplication.py, fractions.py)

**Problem generation flow:**
1. `ProblemGenerator.generate_math_problems(age, count, difficulty)` in `src/problem_generator.py`
2. Gets problem types for age from `src/problem_types.py`
3. Uses strategy classes in `src/problem_generators/` to create problems
4. Difficulty (0.0-1.0) maps to school year progress (August start)

**Key data models in `src/database/models.py`:** User, Child, Session, Worksheet

## Testing

- Tests run against a real Postgres database (no mocking of the DB); `tests/conftest.py` creates and migrates `mathtutor_test`
- Override the URL with `TEST_DATABASE_URL`; the database name must end in `_test` or the suite refuses to run
- Run with `-W error`: `pytest tests/ -W error`

## Important Constraints

- **Never modify the layout of `src/templates/problem_grid.html`** - this template controls worksheet problem display
- Child ages use end-of-school-year calculation (not current age)
- OAuth supports Google only; all config comes from environment variables (see `.env.example`)
