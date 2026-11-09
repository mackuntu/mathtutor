"""Guard that the Vercel entrypoint (root ``wsgi.py``) keeps working."""

import importlib
import sys

import pytest
from flask import Flask


@pytest.fixture
def entrypoint(db, monkeypatch):
    """Import ``wsgi`` fresh with Vercel-style env pointing at the test DB."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    monkeypatch.delitem(sys.modules, "wsgi", raising=False)
    module = importlib.import_module("wsgi")
    yield module
    sys.modules.pop("wsgi", None)


def test_entrypoint_exposes_flask_app(entrypoint):
    assert isinstance(entrypoint.app, Flask)


def test_login_page_renders_through_entrypoint(entrypoint):
    response = entrypoint.app.test_client().get("/auth/login")
    assert response.status_code == 200


def test_vercel_fails_fast_without_database_url(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("FLASK_SECRET_KEY", "x")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delitem(sys.modules, "wsgi", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        importlib.import_module("wsgi")
    sys.modules.pop("wsgi", None)
