"""Database package: Postgres repository and Flask wiring."""

from .db import close_conn
from .repository import PostgresRepository

# Stateless: every method fetches the app-context connection itself.
_repository = PostgresRepository()


def get_repository() -> PostgresRepository:
    """Return the shared repository instance."""
    return _repository


def init_db(app):
    """Register per-request connection cleanup on the Flask app."""
    app.teardown_appcontext(close_conn)
