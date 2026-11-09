"""Owner settings: manage device tokens."""

from datetime import datetime, timezone

from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from ..database import get_repository
from ..database.models import Model
from ..device_tokens import issue_token
from .common import login_required

bp = Blueprint("settings", __name__, url_prefix="/settings")

MAX_NAME_LENGTH = 50


@bp.after_request
def no_store(response):
    """Keep token pages out of browser/bfcache so the secret can't be restored."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@bp.app_template_filter("timestamp_or_dash")
def timestamp_or_dash(epoch):
    """Format epoch seconds as UTC text; '-' when never set."""
    if epoch is None:
        return "-"
    return datetime.fromtimestamp(int(epoch), timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )


def _render(status=200, **context):
    return (
        render_template(
            "settings_devices.html",
            user=g.user,
            tokens=get_repository().list_device_tokens(),
            max_name_length=MAX_NAME_LENGTH,
            **context,
        ),
        status,
    )


@bp.route("/devices")
@login_required
def devices():
    return _render()


@bp.route("/devices", methods=["POST"])
@login_required
def create_device():
    name = request.form.get("name", "").strip()
    if not name or len(name) > MAX_NAME_LENGTH:
        return _render(
            400, error=f"Name is required (at most {MAX_NAME_LENGTH} characters)."
        )
    # Rendered directly (not flashed) so the raw token never enters the cookie.
    return _render(new_token=issue_token(name), new_token_name=name)


@bp.route("/devices/<token_id>/revoke", methods=["POST"])
@login_required
def revoke_device(token_id: str):
    if not get_repository().revoke_device_token(token_id, Model.utc_now()):
        abort(404)
    return redirect(url_for("settings.devices"))
