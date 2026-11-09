"""Common functionality for route handlers."""

import logging
from functools import wraps

from flask import g, redirect, request, url_for

from ..auth import AuthManager
from ..database import get_repository

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
auth_manager = AuthManager()
repository = get_repository()


def get_current_user():
    """Get the current user from the session."""
    token = request.cookies.get("session_token")
    user = auth_manager.validate_session(token)
    logger.debug(f"Validated user: {user}")
    return user


def login_required(view):
    """Redirect to login unless the session cookie is valid; sets ``g.user``."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for("auth.login"))
        g.user = user
        return view(*args, **kwargs)

    return wrapped
