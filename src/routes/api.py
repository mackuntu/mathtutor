"""JSON API routes for device clients (Raspberry Pi, iOS app)."""

from flask import Blueprint, g, jsonify

from .. import worksheet_service
from ..database import PostgresRepository
from ..device_tokens import require_api_auth

bp = Blueprint("api", __name__, url_prefix="/api")


def _not_found():
    return jsonify({"error": "not found"}), 404


@bp.route("/ping")
@require_api_auth
def ping():
    """Lets a client verify its credentials."""
    return jsonify({"ok": True})


@bp.route("/children")
@require_api_auth
def list_children():
    """The owner's children, as the minimal fields a device needs."""
    children = PostgresRepository().get_children_by_parent(g.user.email)
    return jsonify(
        {
            "children": [
                {"id": c.id, "name": c.name, "age": c.age, "grade": c.grade}
                for c in children
            ]
        }
    )


@bp.route("/children/<child_id>/worksheets", methods=["POST"])
@require_api_auth
def new_worksheet(child_id):
    """Generate a new worksheet for a child and return it as printable HTML."""
    child = PostgresRepository().get_child_by_id(child_id)
    if child is None or child.parent_email != g.user.email:
        return _not_found()
    worksheet = worksheet_service.generate_for_child(child)
    html = worksheet_service.render_printable(worksheet, child)
    return (
        jsonify(
            {
                "worksheet_id": worksheet.id,
                "serial": worksheet.serial_number,
                "html": html,
            }
        ),
        201,
    )
