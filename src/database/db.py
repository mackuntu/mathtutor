"""Postgres connection layer: one connection per app context, schema applied once."""

import os
from pathlib import Path

import psycopg
from flask import g
from psycopg.rows import dict_row

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# Reset to False in tests that recreate the database.
_schema_applied = False


def ensure_schema(conn: psycopg.Connection) -> None:
    """Create all tables and indexes if they do not exist (idempotent)."""
    conn.execute(SCHEMA_PATH.read_text())


def get_conn() -> psycopg.Connection:
    """Return the Postgres connection for the current app context."""
    global _schema_applied
    if "db_conn" in g:
        return g.db_conn

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")

    conn = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
    try:
        if not _schema_applied:
            ensure_schema(conn)
            _schema_applied = True
    except Exception:
        conn.close()
        raise
    g.db_conn = conn
    return conn


def close_conn(exc=None) -> None:
    """Close the app-context connection, if one was opened."""
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()
