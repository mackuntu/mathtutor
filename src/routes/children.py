"""Child management routes for the MathTutor application."""

import logging
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from ..database import get_repository
from ..database.models import Child
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
repository = get_repository()

# Create blueprint
bp = Blueprint("children", __name__, url_prefix="/children")


def calculate_age_at_end_of_school_year(birthday_date: datetime) -> int:
    """Calculate the age a child will be at the end of the current school year.

    School year typically ends in May/June, so we use June 30th as the reference date.
    This ensures consistent age calculation throughout the school year.

    Args:
        birthday_date: The child's birthday

    Returns:
        The age the child will be at the end of the current school year
    """
    today = datetime.now()

    # Determine the end of the current school year
    # If we're before June, use June 30th of current year
    # If we're June or later, use June 30th of next year
    if today.month < 6:
        school_year_end = datetime(today.year, 6, 30)
    else:
        school_year_end = datetime(today.year + 1, 6, 30)

    # Calculate age at the end of school year
    age = (
        school_year_end.year
        - birthday_date.year
        - (
            (school_year_end.month, school_year_end.day)
            < (birthday_date.month, birthday_date.day)
        )
    )

    return age


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
        # Calculate age from birthday (age at end of school year)
        birthday_date = datetime.strptime(birthday, "%Y-%m-%d")
        age = calculate_age_at_end_of_school_year(birthday_date)

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
            message = "Please fill in all required fields."
            if request.args.get("ajax"):
                return jsonify({"success": False, "message": message})
            flash(message, "error")
        else:
            try:
                # Calculate age from birthday (age at end of school year)
                birthday_date = datetime.strptime(birthday, "%Y-%m-%d")
                age = calculate_age_at_end_of_school_year(birthday_date)

                if age < 4 or age > 18:
                    message = "Child must be between 4 and 18 years old."
                    if request.args.get("ajax"):
                        return jsonify({"success": False, "message": message})
                    flash(message, "error")
                else:
                    child.name = name
                    child.birthday = birthday_date
                    child.grade = int(grade_level)
                    child.preferred_color = preferred_color
                    repository.update_child(child)

                    if request.args.get("ajax"):
                        return jsonify(
                            {"success": True, "message": "Child updated successfully!"}
                        )

                    flash("Child updated successfully!", "success")
                    return redirect(url_for("children.list_children"))
            except ValueError:
                message = "Please enter valid values for all fields."
                if request.args.get("ajax"):
                    return jsonify({"success": False, "message": message})
                flash(message, "error")

    # For AJAX requests, return just the form
    if request.args.get("ajax"):
        return render_template("edit_child_form.html", user=user, child=child)

    # For regular requests, return the full page
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
