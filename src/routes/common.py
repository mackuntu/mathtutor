"""Common functionality for route handlers."""

import logging

from flask import request

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
