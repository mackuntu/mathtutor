"""Tests for authentication functionality."""

from datetime import datetime, timedelta, timezone

from src.database.models import Session, User


def test_verify_google_token(auth_manager):
    """Test Google token verification."""
    # Test invalid token
    valid, user_info = auth_manager.verify_oauth_token("google", "invalid_token")
    assert not valid
    assert user_info is None


def test_session_management(auth_manager, test_user):
    """Test session creation and validation."""
    # Create session
    token = auth_manager.create_session(test_user.email)
    assert token is not None

    # Validate session
    user = auth_manager.validate_session(token)
    assert user is not None
    assert user.email == test_user.email

    # Test invalid session
    invalid_user = auth_manager.validate_session("invalid_token")
    assert invalid_user is None

    # Test expired session
    expired_session = Session(
        token="expired_token",
        user_email=test_user.email,
        expires_at=int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp()),
    )
    auth_manager.repository.create_session(expired_session)
    expired_user = auth_manager.validate_session(expired_session.token)
    assert expired_user is None

    # Verify expired session was deleted
    deleted_session = auth_manager.repository.get_session(expired_session.token)
    assert deleted_session is None


def test_create_user(repository):
    """Test creating a new user."""
    user = User(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/avatar.jpg",
    )
    repository.create_user(user)

    # Verify user was created
    saved_user = repository.get_user_by_email(user.email)
    assert saved_user is not None
    assert saved_user.name == "Test User"
    assert saved_user.picture == "https://example.com/avatar.jpg"


def test_create_session(repository, test_user):
    """Test creating a new session."""
    session = Session(
        token="test_token",
        user_email=test_user.email,
        expires_at=int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
    )
    repository.create_session(session)

    # Verify session was created
    saved_session = repository.get_session(session.token)
    assert saved_session is not None
    assert saved_session.user_email == test_user.email


def test_delete_session(repository, test_session):
    """Test deleting a session."""
    # Delete session
    repository.delete_session(test_session.token)

    # Verify session was deleted
    deleted_session = repository.get_session(test_session.token)
    assert deleted_session is None


def test_session_expiration(auth_manager, repository, test_user):
    """Test that expired sessions are handled correctly."""
    # Create an expired session
    expired_session = Session(
        token="expired_token",
        user_email=test_user.email,
        expires_at=int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp()),
    )
    repository.create_session(expired_session)

    # Verify expired session is not valid
    user = auth_manager.validate_session(expired_session.token)
    assert user is None

    # Verify expired session was deleted
    deleted_session = repository.get_session(expired_session.token)
    assert deleted_session is None


def test_get_or_create_user(auth_manager):
    """Test get_or_create_user functionality."""
    # Create new user
    user = auth_manager.get_or_create_user(
        email="new@example.com", name="New User", picture="https://example.com/new.jpg"
    )
    assert user is not None
    assert user.email == "new@example.com"

    # Get existing user
    same_user = auth_manager.get_or_create_user(
        email="new@example.com",
        name="Updated Name",
        picture="https://example.com/updated.jpg",
    )
    assert same_user is not None
    assert same_user.email == user.email
    assert same_user.name == "New User"  # Name should not be updated
    assert (
        same_user.picture == "https://example.com/new.jpg"
    )  # Picture should not be updated


# --- Owner-only Google login -------------------------------------------------

import pytest  # noqa: E402
from unittest.mock import patch  # noqa: E402


def _start_oauth(client, state="good-state"):
    with client.session_transaction() as sess:
        sess["oauth_state"] = state
        sess["oauth_provider"] = "google"
    return state


def _callback(client, email, state="good-state"):
    info = {"email": email, "name": "Someone", "picture": None}
    with patch(
        "src.routes.auth.auth_manager.exchange_code_for_token", return_value="tok"
    ), patch(
        "src.routes.auth.auth_manager.verify_oauth_token", return_value=(True, info)
    ):
        return client.get(f"/auth/oauth/callback?code=abc&state={state}")


def _count(db, table):
    import psycopg

    with psycopg.connect(db) as conn:
        return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


@pytest.fixture
def owner_env(db, monkeypatch):
    monkeypatch.setenv("ALLOWED_EMAILS", " Me@X.com ,other@y.com")
    monkeypatch.delenv("VERCEL", raising=False)


def test_allowlisted_email_logs_in(client, owner_env):
    _start_oauth(client)
    resp = _callback(client, "me@x.com")
    assert resp.status_code == 302
    cookie = resp.headers.get("Set-Cookie", "")
    assert "session_token=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_allowlist_match_ignores_case_and_spaces(client, owner_env):
    _start_oauth(client)
    resp = _callback(client, "ME@x.COM")
    assert resp.status_code == 302


def test_unlisted_email_rejected_without_user_or_session(client, owner_env, db):
    _start_oauth(client)
    resp = _callback(client, "stranger@z.com")
    assert resp.status_code == 403
    assert b"This MathTutor is private." in resp.data
    assert _count(db, "users") == 0
    assert _count(db, "sessions") == 0
    assert "session_token" not in resp.headers.get("Set-Cookie", "")


def test_empty_allowlist_fails_closed(client, db, monkeypatch):
    monkeypatch.delenv("ALLOWED_EMAILS", raising=False)
    _start_oauth(client)
    resp = _callback(client, "me@x.com")
    assert resp.status_code == 403
    assert _count(db, "users") == 0


def test_state_mismatch_creates_no_session(client, owner_env, db):
    _start_oauth(client, state="good-state")
    resp = _callback(client, "me@x.com", state="forged")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
    assert "session_token" not in resp.headers.get("Set-Cookie", "")
    assert _count(db, "sessions") == 0


def test_cookie_secure_on_vercel(client, owner_env, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    _start_oauth(client)
    resp = _callback(client, "me@x.com")
    assert "Secure" in resp.headers["Set-Cookie"]


def test_test_auth_disabled_on_vercel(client, db, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("FLASK_ENV", "development")
    resp = client.get("/auth/test-auth?bypass_key=test-bypass-key-for-selenium")
    assert resp.status_code == 404


def test_test_auth_cookie_flags(client, db, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.delenv("VERCEL", raising=False)
    resp = client.get("/auth/test-auth?bypass_key=test-bypass-key-for-selenium")
    cookie = resp.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie


def test_create_app_fails_fast_on_vercel_without_secret(monkeypatch):
    from src import create_app

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://x/y")
    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        create_app()


def test_create_app_fails_fast_on_vercel_without_database_url(monkeypatch):
    from src import create_app

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("FLASK_SECRET_KEY", "s")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        create_app()


def test_secret_key_is_not_the_public_default(monkeypatch):
    from src import create_app

    monkeypatch.setenv("FLASK_SECRET_KEY", "real-secret")
    assert create_app().secret_key == "real-secret"
