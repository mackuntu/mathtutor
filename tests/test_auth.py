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


def _callback(client, email, state="good-state", email_verified=True):
    info = {
        "email": email,
        "name": "Someone",
        "picture": None,
        "email_verified": email_verified,
    }
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


@pytest.mark.parametrize("verified", [False, None, "true"])
def test_unverified_google_email_rejected(client, owner_env, db, verified):
    _start_oauth(client)
    resp = _callback(client, "me@x.com", email_verified=verified)
    assert resp.status_code == 403
    assert b"This MathTutor is private." in resp.data
    assert _count(db, "users") == 0
    assert _count(db, "sessions") == 0
    assert "session_token" not in resp.headers.get("Set-Cookie", "")


def test_verify_google_token_propagates_email_verified(auth_manager):
    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"email": "a@b.c", "name": "A", "email_verified": True}

    with patch("src.auth.requests.get", return_value=Resp()):
        valid, info = auth_manager.verify_oauth_token("google", "t")
    assert valid and info["email_verified"] is True


def test_cookie_not_secure_on_plain_http_without_vercel(client, owner_env):
    _start_oauth(client)
    resp = _callback(client, "me@x.com")
    assert "Secure" not in resp.headers["Set-Cookie"]


def test_oauth_state_cleared_on_mismatch(client, owner_env):
    _start_oauth(client, state="good-state")
    _callback(client, "me@x.com", state="forged")
    with client.session_transaction() as sess:
        assert "oauth_state" not in sess


def test_get_or_create_user_is_atomic_against_concurrent_insert(auth_manager):
    """A row inserted between lookup and insert must not raise."""
    repo = auth_manager.repository
    real_get = repo.get_user_by_email
    raced = []

    def racing_get(email):
        # A lookup that sees no row loses the race: another request inserts
        # the same user right after this read.
        existing = real_get(email)
        if existing is None and not raced:
            raced.append(email)
            repo.create_user(User(email=email, name="Winner"))
        return existing

    with patch.object(repo, "get_user_by_email", side_effect=racing_get):
        user = auth_manager.get_or_create_user("race@example.com", "Loser")

    assert user.email == "race@example.com"


def test_google_login_fills_name_of_owner_created_by_bearer(auth_manager):
    """Owner row created by an API call (name == email) gets the Google profile."""
    auth_manager.get_or_create_user("me@x.com", "me@x.com")

    user = auth_manager.get_or_create_user("me@x.com", "Me", "https://p/me.png")

    assert user.name == "Me"
    assert user.picture == "https://p/me.png"
    saved = auth_manager.repository.get_user_by_email("me@x.com")
    assert (saved.name, saved.picture) == ("Me", "https://p/me.png")


def test_verify_google_token_falls_back_to_email_for_missing_name(auth_manager):
    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"email": "a@b.c", "email_verified": True}

    with patch("src.auth.requests.get", return_value=Resp()):
        valid, info = auth_manager.verify_oauth_token("google", "t")

    assert valid and info["name"] == "a@b.c"


# --- Allowlist enforced on every request -------------------------------------


def test_session_rejected_and_deleted_once_email_leaves_allowlist(
    auth_manager, test_user, monkeypatch
):
    monkeypatch.delenv("VERCEL", raising=False)
    token = auth_manager.create_session(test_user.email)
    monkeypatch.setenv("ALLOWED_EMAILS", "someone-else@example.com")

    assert auth_manager.validate_session(token) is None
    assert auth_manager.repository.get_session(token) is None


def test_session_accepted_for_allowlisted_email(auth_manager, test_user, monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("ALLOWED_EMAILS", "Test@Example.com")
    token = auth_manager.create_session(test_user.email)

    assert auth_manager.validate_session(token).email == test_user.email


def test_session_not_allowlist_checked_in_dev_without_allowlist(
    auth_manager, test_user, monkeypatch
):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("ALLOWED_EMAILS", raising=False)
    token = auth_manager.create_session(test_user.email)

    assert auth_manager.validate_session(token).email == test_user.email


def test_session_rejected_on_vercel_without_allowlist(
    auth_manager, test_user, monkeypatch
):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("ALLOWED_EMAILS", raising=False)
    token = auth_manager.create_session(test_user.email)

    assert auth_manager.validate_session(token) is None
    assert auth_manager.repository.get_session(token) is None


def test_test_auth_session_works_in_dev_without_allowlist(client, db, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("ALLOWED_EMAILS", raising=False)
    client.get("/auth/test-auth?bypass_key=test-bypass-key-for-selenium")

    assert client.get("/children/").status_code == 200


def test_test_auth_signs_in_as_owner_when_allowlist_set(client, db, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("ALLOWED_EMAILS", "me@x.com")
    client.get("/auth/test-auth?bypass_key=test-bypass-key-for-selenium")

    assert client.get("/children/").status_code == 200
