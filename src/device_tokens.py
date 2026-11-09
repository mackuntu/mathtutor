"""Revocable device tokens for non-browser API clients."""

import hashlib
import hmac
import logging
import secrets
from functools import wraps
from typing import Optional

from flask import g, jsonify, request

from .auth import AuthManager
from .config import owner_email
from .database import get_repository
from .database.models import Model
from .routes.common import get_current_user

logger = logging.getLogger(__name__)

TOKEN_PREFIX = "mt_"
BEARER_PREFIX = "Bearer "


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def issue_token(name: str) -> str:
    """Create a device token; return the raw value (only its hash is stored)."""
    raw = TOKEN_PREFIX + secrets.token_urlsafe(32)
    get_repository().create_device_token(
        Model.generate_id(), name, hash_token(raw), Model.utc_now()
    )
    return raw


def _unauthorized():
    return jsonify({"error": "unauthorized"}), 401


def _owner():
    """The owner user row (created on demand), or None if no owner is configured."""
    email = owner_email()
    if not email:
        return None
    return AuthManager().get_or_create_user(email, email)


def _authenticate_bearer(header: str):
    """Return the owner for a valid ``Bearer <token>`` header, else None."""
    if not header.startswith(BEARER_PREFIX):
        return None
    raw = header[len(BEARER_PREFIX) :]
    if not raw or raw != raw.strip():
        return None
    repository = get_repository()
    computed = hash_token(raw)
    record = repository.get_active_device_token_by_hash(computed)
    if not record or not hmac.compare_digest(record["token_hash"], computed):
        return None
    owner = _owner()
    if owner is None:
        return None
    repository.touch_device_token(record["id"], Model.utc_now())
    return owner


def require_api_auth(view):
    """Accept a device bearer token or a valid session cookie; else 401 JSON.

    An Authorization header, if present, must be valid: no cookie fallback.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        header: Optional[str] = request.headers.get("Authorization")
        user = (
            _authenticate_bearer(header) if header is not None else (get_current_user())
        )
        if not user:
            return _unauthorized()
        g.user = user
        return view(*args, **kwargs)

    return wrapped
