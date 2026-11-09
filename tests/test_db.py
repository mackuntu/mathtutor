"""Tests for the Postgres connection layer and schema."""

import pytest

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


def test_get_conn_is_cached_per_app_context(app, db):
    with app.app_context():
        assert db_module.get_conn() is db_module.get_conn()


def test_close_conn_closes_connection(app, db):
    with app.app_context():
        conn = db_module.get_conn()
    assert conn.closed


def test_cold_start_empty_database_renders_index(app, client, db):
    with app.app_context():
        conn = db_module.get_conn()
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
    db_module._schema_applied = False

    with app.app_context():
        conn = db_module.get_conn()
        assert TABLES <= _table_names(conn)

    # Routes still use the Dynamo repository until Task 4; this proves boot only.
    assert client.get("/").status_code in (200, 302)
