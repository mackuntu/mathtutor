"""Authentication routes for the MathTutor application."""

import logging
import os
import secrets
from typing import Optional

from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..auth import AuthManager
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
auth_manager = AuthManager()

# Create blueprint
bp = Blueprint("auth", __name__, url_prefix="/auth")

# Test authentication bypass key - should match the one in conftest.py
TEST_BYPASS_KEY = os.environ.get("TEST_BYPASS_KEY", "test-bypass-key-for-selenium")


@bp.route("/test-auth")
def test_auth():
    """Test-only endpoint for authentication bypass during UI testing."""
    # Only allow this in development/testing environments
    if (
        os.environ.get("FLASK_ENV") != "development"
        and os.environ.get("TESTING") != "true"
    ):
        return "Not available in production", 403

    # Verify the bypass key
    bypass_key = request.args.get("bypass_key")
    if bypass_key != TEST_BYPASS_KEY:
        return "Invalid bypass key", 403

    # Get the user type from the request
    user_type = request.args.get("user", "test-teacher")

    # Create a test user based on the user type
    if user_type == "test-teacher":
        email = "test-teacher@example.com"
        name = "Test Teacher"
    elif user_type == "test-parent":
        email = "test-parent@example.com"
        name = "Test Parent"
    else:
        email = "test-user@example.com"
        name = "Test User"

    # Create or get the user
    user = auth_manager.get_or_create_user(email, name)

    # Create a session for the user
    session_token = auth_manager.create_session(user.email)

    # Set the session cookie
    response = make_response(redirect(url_for("pages.index")))
    response.set_cookie("session_token", session_token, httponly=True, path="/")

    logger.info(f"Test authentication successful for {email}")
    return response


@bp.route("/login")
def login():
    """Render login page."""
    if get_current_user():
        return redirect(url_for("pages.index"))

    # State token to prevent CSRF
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    return render_template("login.html")


@bp.route("/oauth/google")
def oauth_google():
    """Initiate Google OAuth flow."""
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    session["oauth_provider"] = "google"
    auth_url = auth_manager.get_oauth_url("google", state)
    return redirect(auth_url)


@bp.route("/oauth/facebook")
def oauth_facebook():
    """Initiate Facebook OAuth flow."""
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    session["oauth_provider"] = "facebook"
    auth_url = auth_manager.get_oauth_url("facebook", state)
    return redirect(auth_url)


@bp.route("/oauth/x")
def oauth_x():
    """Initiate X (Twitter) OAuth flow."""
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    session["oauth_provider"] = "x"
    auth_url = auth_manager.get_oauth_url("x", state)
    return redirect(auth_url)


@bp.route("/oauth/callback")
def oauth_callback():
    """Handle OAuth callback."""
    error = request.args.get("error")
    if error:
        flash(f"Authentication failed: {error}", "error")
        return redirect(url_for("auth.login"))

    # Verify state token
    state = request.args.get("state")
    if not state or state != session.get("oauth_state"):
        flash("Invalid state token. Please try again.", "error")
        return redirect(url_for("auth.login"))

    # Get authorization code
    code = request.args.get("code")
    if not code:
        flash("Authentication failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    # Get provider from session
    provider = session.get("oauth_provider")
    if not provider:
        flash("Invalid OAuth flow. Please try again.", "error")
        return redirect(url_for("auth.login"))

    try:
        # Exchange code for token
        token = auth_manager.exchange_code_for_token(provider, code)
        if not token:
            flash("Failed to authenticate. Please try again.", "error")
            return redirect(url_for("auth.login"))

        # Verify token and get user info
        valid, user_info = auth_manager.verify_oauth_token(provider, token)
        if not valid or not user_info:
            flash("Failed to verify authentication. Please try again.", "error")
            return redirect(url_for("auth.login"))

        # Create or get user
        user = auth_manager.get_or_create_user(
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
        )

        # Create session
        session_token = auth_manager.create_session(user.email)
        response = make_response(redirect(url_for("pages.index")))
        response.set_cookie(
            "session_token",
            session_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )

        # Clean up session
        session.pop("oauth_state", None)
        session.pop("oauth_provider", None)

        return response

    except Exception as e:
        logger.error(f"OAuth error: {str(e)}")
        flash("Authentication failed. Please try again.", "error")
        return redirect(url_for("auth.login"))


@bp.route("/logout")
def logout():
    """Log out user."""
    token = request.cookies.get("session_token")
    if token:
        auth_manager.logout(token)

    response = make_response(redirect(url_for("auth.login")))
    response.delete_cookie("session_token")
    return response
