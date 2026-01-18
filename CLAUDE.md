# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Start DynamoDB Local (separate terminal)
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

# Initialize database tables
python src/database/create_tables.py

# Run the app (http://localhost:8080)
python -m src.web

# Run tests
pytest tests/                    # Unit tests
pytest tests/ui -m pdf           # PDF-specific tests
pytest tests/ -k "test_name"     # Single test
```

## Architecture

**Flask app with blueprint-based routing:**
- `src/__init__.py` - App factory (`create_app()`)
- `src/routes/` - Blueprints: auth, children, worksheets, subscription, admin, pages
- `src/database/` - DynamoDB models and repository pattern
- `src/document/` - PDF generation (renderer.py, template.py)
- `src/problem_generators/` - Strategy pattern for math problems (basic_operations.py, multiplication.py, fractions.py)

**Problem generation flow:**
1. `ProblemGenerator.generate_math_problems(age, count, difficulty)` in `src/problem_generator.py`
2. Gets problem types for age from `src/problem_types.py`
3. Uses strategy classes in `src/problem_generators/` to create problems
4. Difficulty (0.0-1.0) maps to school year progress (August start)

**Key data models in `src/database/models.py`:** User, Child, Session, Worksheet, Subscription, Payment

## Testing

- Unit tests mock DynamoDB using `moto` library (see `tests/conftest.py`)
- UI tests use Selenium with Page Object Models in `tests/ui/pages/`
- Test markers: `@pytest.mark.ui`, `@pytest.mark.pdf`, `@pytest.mark.slow`

## Important Constraints

- **Never modify the layout of `src/templates/problem_grid.html`** - this template controls worksheet problem display
- Child ages use end-of-school-year calculation (not current age)
- OAuth supports Google, Facebook, and X (Twitter) providers
