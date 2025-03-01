"""Child management routes for the MathTutor application."""

import logging
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..database import get_repository
from ..database.models import Child
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
repository = get_repository()

# Create blueprint
bp = Blueprint("children", __name__, url_prefix="/children")


@bp.route("/")
def list_children():
    """Render children management page."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    children = repository.get_children_by_parent(user.email)
    return render_template("children.html", user=user, children=children)


@bp.route("/", methods=["POST"])
def register_child():
    """Register a new child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    name = request.form.get("name")
    birthday = request.form.get("birthday")
    grade_level = request.form.get("grade_level")
    preferred_color = request.form.get("preferred_color")

    if not all([name, birthday, grade_level]):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("children.list_children"))

    try:
        # Calculate age from birthday
        birthday_date = datetime.strptime(birthday, "%Y-%m-%d")
        today = datetime.now()
        age = (
            today.year
            - birthday_date.year
            - ((today.month, today.day) < (birthday_date.month, birthday_date.day))
        )

        child = Child(
            parent_email=user.email,
            name=name,
            age=age,
            grade=int(grade_level),
            preferred_color=preferred_color,
        )
        repository.create_child(child)
        flash("Child added successfully!", "success")
        return redirect(url_for("children.list_children"))
    except (ValueError, TypeError) as e:
        flash(str(e), "error")
        return redirect(url_for("children.list_children"))


@bp.route("/<child_id>/edit", methods=["GET", "POST"])
def edit_child(child_id):
    """Edit a child's information."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
        return redirect(url_for("children.list_children"))

    if request.method == "POST":
        name = request.form.get("name")
        birthday = request.form.get("birthday")
        grade_level = request.form.get("grade_level")
        preferred_color = request.form.get("preferred_color")

        if not all([name, birthday, grade_level]):
            flash("Please fill in all required fields.", "error")
        else:
            try:
                # Calculate age from birthday
                birthday_date = datetime.strptime(birthday, "%Y-%m-%d")
                today = datetime.now()
                age = (
                    today.year
                    - birthday_date.year
                    - (
                        (today.month, today.day)
                        < (birthday_date.month, birthday_date.day)
                    )
                )

                if age < 4 or age > 18:
                    flash("Child must be between 4 and 18 years old.", "error")
                else:
                    child.name = name
                    child.birthday = birthday_date
                    child.grade = int(grade_level)
                    child.preferred_color = preferred_color
                    repository.update_child(child)
                    flash("Child updated successfully!", "success")
                    return redirect(url_for("children.list_children"))
            except ValueError:
                flash("Please enter valid values for all fields.", "error")

    return render_template("edit_child.html", user=user, child=child)


@bp.route("/<child_id>/delete", methods=["POST"])
def delete_child(child_id):
    """Delete a child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
    else:
        repository.delete_child(child_id)
        flash("Child deleted successfully!", "success")

    return redirect(url_for("children.list_children"))
