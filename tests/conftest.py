"""Test configuration and fixtures."""

import os
from datetime import datetime, timedelta, timezone

import psycopg
import psycopg.conninfo
import pytest
from psycopg import sql

from src.auth import AuthManager
from src.database.models import Child, Session, User, Worksheet
from src.database.repository import PostgresRepository

DEFAULT_TEST_DATABASE_URL = (
    "postgresql://postgres:mathtutor@localhost:5432/mathtutor_test"
)
TEST_DB_SUFFIX = "_test"


def assert_test_database(url: str) -> None:
    """Refuse to touch any database whose name does not end with ``_test``."""
    dbname = psycopg.conninfo.conninfo_to_dict(url).get("dbname", "")
    if not dbname.endswith(TEST_DB_SUFFIX):
        raise RuntimeError(
            f"Refusing to use database {dbname!r}: test database names "
            f"must end with {TEST_DB_SUFFIX!r} (check TEST_DATABASE_URL)"
        )


@pytest.fixture(autouse=True)
def isolate_auth_env(monkeypatch):
    """Ignore owner/Vercel settings a developer's ``.env`` may have loaded."""
    monkeypatch.delenv("ALLOWED_EMAILS", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("MATHTUTOR_DB_DATABASE_URL", raising=False)


@pytest.fixture(scope="session")
def pg_url():
    """URL of the Postgres test database, created if missing."""
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    assert_test_database(url)
    info = psycopg.conninfo.conninfo_to_dict(url)
    dbname = info["dbname"]
    admin_url = psycopg.conninfo.make_conninfo(url, dbname="postgres")
    with psycopg.connect(admin_url, autocommit=True) as admin:
        exists = admin.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)
        ).fetchone()
        if not exists:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    return url


@pytest.fixture
def db(pg_url, monkeypatch):
    """Point the app at the test database with all tables empty."""
    from src.database import db as db_module

    assert_test_database(pg_url)
    monkeypatch.setenv("DATABASE_URL", pg_url)
    with psycopg.connect(pg_url, autocommit=True) as conn:
        db_module.ensure_schema(conn)
        conn.execute(
            "TRUNCATE users, children, sessions, worksheets, device_tokens CASCADE"
        )
    yield pg_url


@pytest.fixture
def app():
    from src import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def repository(app, db):
    """A repository bound to an app context on the empty test database."""
    with app.app_context():
        yield PostgresRepository()


@pytest.fixture
def auth_manager(repository):
    """Create an auth manager instance."""
    return AuthManager()


@pytest.fixture
def test_user(repository):
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/picture.jpg",
    )
    repository.create_user(user)
    return user


@pytest.fixture
def test_child(repository, test_user):
    """Create a test child."""
    child = Child(
        parent_email=test_user.email,
        name="Test Child",
        age=8,
        grade=3,
        preferred_color="#FF5733",
    )
    repository.create_child(child)
    return child


@pytest.fixture
def test_worksheet(repository, test_child):
    """Create a test worksheet."""
    worksheet = Worksheet(
        child_id=test_child.id,
        problems=[
            {"type": "addition", "a": 5, "b": 3},
            {"type": "subtraction", "a": 10, "b": 4},
        ],
    )
    repository.create_worksheet(worksheet)
    return worksheet


@pytest.fixture
def test_session(repository, test_user):
    """Create a test session."""
    session = Session(
        token="test_token",
        user_email=test_user.email,
        expires_at=int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
    )
    repository.create_session(session)
    return session


OWNER = "owner@example.com"


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner_env(monkeypatch):
    """Configure OWNER as the first (and only) allowed email."""
    monkeypatch.setenv("ALLOWED_EMAILS", OWNER)


@pytest.fixture
def owner(owner_env, auth_manager):
    return auth_manager.get_or_create_user(OWNER, "Owner")


@pytest.fixture
def logged_in(client, auth_manager, owner):
    client.set_cookie("session_token", auth_manager.create_session(owner.email))
    return client
