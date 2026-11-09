"""JSON API routes for device clients (Raspberry Pi, iOS app)."""

from flask import Blueprint, jsonify

from ..device_tokens import require_api_auth

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/ping")
@require_api_auth
def ping():
    """Lets a client verify its credentials."""
    return jsonify({"ok": True})
