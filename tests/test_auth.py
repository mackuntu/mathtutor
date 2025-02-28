"""Tests for authentication functionality."""

from datetime import datetime, timedelta, timezone

import pytest

from src.auth import AuthManager
from src.database.models import Session, User


def test_verify_google_token(auth_manager):
    """Test Google token verification."""
    # Test invalid token
    valid, user_info = auth_manager.verify_oauth_token("google", "invalid_token")
    assert not valid
    assert user_info is None


def test_session_management(auth_manager, test_user, cleanup_sessions):
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


def test_get_user_sessions(repository, test_user, cleanup_sessions):
    """Test retrieving all sessions for a user."""
    # Create two sessions
    session1 = Session(
        token="token1",
        user_email=test_user.email,
        expires_at=int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
    )
    session2 = Session(
        token="token2",
        user_email=test_user.email,
        expires_at=int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
    )
    repository.create_session(session1)
    repository.create_session(session2)

    # Get sessions for user
    sessions = repository.get_user_sessions(test_user.email)
    assert len(sessions) == 2
    assert any(s.token == "token1" for s in sessions)
    assert any(s.token == "token2" for s in sessions)


def test_delete_session(repository, test_session):
    """Test deleting a session."""
    # Delete session
    repository.delete_session(test_session.token)

    # Verify session was deleted
    deleted_session = repository.get_session(test_session.token)
    assert deleted_session is None


def test_session_expiration(auth_manager, repository, test_user, cleanup_sessions):
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
