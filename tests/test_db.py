"""Tests for the Postgres connection layer and schema."""

import psycopg
import pytest
from psycopg.rows import dict_row

from src.database import db as db_module

TABLES = {"users", "children", "sessions", "worksheets", "device_tokens"}


def _table_names(conn):
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).fetchall()
    return {r["table_name"] for r in rows}


def test_ensure_schema_is_idempotent(app, db):
    with app.app_context():
        conn = db_module.get_conn()
        db_module.ensure_schema(conn)
        db_module.ensure_schema(conn)
        assert TABLES <= _table_names(conn)


def test_get_conn_requires_database_url(app, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with app.app_context():
        with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
            db_module.get_conn()


def test_database_url_prefers_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://primary/db")
    monkeypatch.setenv("MATHTUTOR_DB_DATABASE_URL", "postgresql://neon/db")
    assert db_module.database_url() == "postgresql://primary/db"


def test_database_url_falls_back_to_neon_integration_var(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("MATHTUTOR_DB_DATABASE_URL", "postgresql://neon/db")
    assert db_module.database_url() == "postgresql://neon/db"


def test_database_url_none_when_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert db_module.database_url() is None


def test_get_conn_is_cached_per_app_context(app, db):
    with app.app_context():
        assert db_module.get_conn() is db_module.get_conn()


def test_close_conn_closes_connection(app, db):
    with app.app_context():
        conn = db_module.get_conn()
    assert conn.closed


def test_cold_start_route_creates_schema(client, db, monkeypatch):
    """A first request on an empty database creates the tables itself."""
    with psycopg.connect(db, autocommit=True, row_factory=dict_row) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
        assert not TABLES & _table_names(conn)
    monkeypatch.setattr(db_module, "_schema_applied", False)

    # Session lookup for the cookie is the request's first DB access.
    client.set_cookie("session_token", "no-such-session")
    response = client.get("/children/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
    with psycopg.connect(db, autocommit=True, row_factory=dict_row) as conn:
        assert TABLES <= _table_names(conn)
    assert db_module._schema_applied is True


def test_ensure_schema_waits_for_advisory_lock(db):
    """Concurrent cold starts serialize on SCHEMA_LOCK_KEY."""
    with psycopg.connect(db) as holder, psycopg.connect(db, autocommit=True) as other:
        holder.execute("SELECT pg_advisory_xact_lock(%s)", (db_module.SCHEMA_LOCK_KEY,))
        other.execute("SET lock_timeout = '100ms'")
        with pytest.raises(psycopg.errors.LockNotAvailable):
            db_module.ensure_schema(other)
