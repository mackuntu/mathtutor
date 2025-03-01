"""Static page routes for the MathTutor application."""

import logging

from flask import Blueprint, redirect, render_template, request, url_for

from ..database import get_repository
from ..generator import ProblemGenerator
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
repository = get_repository()
generator = ProblemGenerator()

# Create blueprint
bp = Blueprint("pages", __name__, url_prefix="")


@bp.route("/")
def index():
    """Render the main page."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    children = repository.get_children_by_parent(user.email)
    active_child_id = request.args.get("child_id")
    active_child = None

    if active_child_id:
        active_child = repository.get_child_by_id(active_child_id)
    elif children:
        active_child = children[0]

    return render_template(
        "index.html",
        user=user,
        children=children,
        active_child=active_child,
        ages=list(range(6, 10)),  # Ages 6-9
        default_age=active_child.age if active_child else None,
        default_difficulty=generator.get_school_year_progress(),
    )


@bp.route("/terms")
def terms():
    """Render Terms of Service page."""
    return render_template("terms.html")


@bp.route("/privacy")
def privacy():
    """Render Privacy Policy page."""
    return render_template("privacy.html")
