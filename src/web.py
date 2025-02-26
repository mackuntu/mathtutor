"""Web routes for the MathTutor application."""

import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import requests
from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .auth import AuthManager
from .database import get_repository
from .database.models import Child, Worksheet
from .generator import ProblemGenerator

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
generator = ProblemGenerator()
auth_manager = AuthManager()
repository = get_repository()

bp = Blueprint("web", __name__, url_prefix="")


def get_current_user():
    """Get the current user from the session."""
    token = request.cookies.get("session_token")
    logger.debug(f"Session token from cookie: {token}")
    user = auth_manager.validate_session(token)
    logger.debug(f"Validated user: {user}")
    return user


@bp.route("/login")
def login():
    """Render login page."""
    if get_current_user():
        return redirect(url_for("web.index"))

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
        return redirect(url_for("web.login"))

    # Verify state token
    state = request.args.get("state")
    if not state or state != session.get("oauth_state"):
        flash("Invalid state token. Please try again.", "error")
        return redirect(url_for("web.login"))

    # Get authorization code
    code = request.args.get("code")
    if not code:
        flash("Authentication failed. Please try again.", "error")
        return redirect(url_for("web.login"))

    # Get provider from session
    provider = session.get("oauth_provider")
    if not provider:
        flash("Invalid OAuth flow. Please try again.", "error")
        return redirect(url_for("web.login"))

    try:
        # Exchange code for token
        token = auth_manager.exchange_code_for_token(provider, code)
        if not token:
            flash("Failed to authenticate. Please try again.", "error")
            return redirect(url_for("web.login"))

        # Verify token and get user info
        valid, user_info = auth_manager.verify_oauth_token(provider, token)
        if not valid or not user_info:
            flash("Failed to verify authentication. Please try again.", "error")
            return redirect(url_for("web.login"))

        # Create or get user
        user = auth_manager.get_or_create_user(
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
        )

        # Create session
        session_token = auth_manager.create_session(user.email)
        response = make_response(redirect(url_for("web.index")))
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
        return redirect(url_for("web.login"))


@bp.route("/logout")
def logout():
    """Log out user."""
    token = request.cookies.get("session_token")
    if token:
        auth_manager.logout(token)

    response = make_response(redirect(url_for("web.login")))
    response.delete_cookie("session_token")
    return response


@bp.route("/children")
def children():
    """Render children management page."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    children = repository.get_children_by_parent(user.email)
    return render_template("children.html", user=user, children=children)


@bp.route("/children", methods=["POST"])
def register_child():
    """Register a new child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    name = request.form.get("name")
    birthday = request.form.get("birthday")
    grade_level = request.form.get("grade_level")
    preferred_color = request.form.get("preferred_color")

    if not all([name, birthday, grade_level]):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("web.children"))

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
        return redirect(url_for("web.children"))
    except (ValueError, TypeError) as e:
        flash(str(e), "error")
        return redirect(url_for("web.children"))


@bp.route("/children/<child_id>/edit", methods=["GET", "POST"])
def edit_child(child_id):
    """Edit a child's information."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
        return redirect(url_for("web.children"))

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
                    return redirect(url_for("web.children"))
            except ValueError:
                flash("Please enter valid values for all fields.", "error")

    return render_template("edit_child.html", user=user, child=child)


@bp.route("/children/<child_id>/delete", methods=["POST"])
def delete_child(child_id):
    """Delete a child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
    else:
        repository.delete_child(child_id)
        flash("Child deleted successfully!", "success")

    return redirect(url_for("web.children"))


@bp.route("/")
def index():
    """Render the main page."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

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


@bp.route("/preview", methods=["POST"])
def preview_problems():
    """Generate a preview of problems based on current settings."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    try:
        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )

        # Generate problems but only use first 5 for preview
        problems, _ = generator.generate_math_problems(age, count, difficulty)
        preview_problems = [{"text": p} for p in problems[:5]]

        # Generate preview HTML
        preview_html = render_template(
            "problem_grid.html", problems=preview_problems, is_preview=True
        )

        return jsonify({"success": True, "html": preview_html})

    except Exception as e:
        return jsonify({"error": str(e), "success": False})


@bp.route("/generate_both", methods=["POST"])
def generate_both():
    """Generate both worksheet and answer key HTML."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    try:
        start_time = time.time()

        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )

        # Generate problems (only once for both HTMLs)
        prob_start = time.time()
        problems, answers = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )
        prob_time = time.time() - prob_start
        logger.info(f"Problem generation took: {prob_time:.2f} seconds")

        problem_list = [{"text": p} for p in problems]

        # Generate worksheet HTML
        html_start = time.time()
        worksheet_html = render_template(
            "worksheet.html",
            problems=problem_list,
            answers=None,
            is_answer_key=False,
            is_preview=False,
        )

        # Generate answer key HTML
        answer_key_html = render_template(
            "worksheet.html",
            problems=problem_list,
            answers=answers,
            is_answer_key=True,
            is_preview=False,
        )
        html_time = time.time() - html_start
        logger.info(f"HTML generation took: {html_time:.2f} seconds")

        # Return both HTMLs
        response = jsonify(
            {
                "worksheet": worksheet_html,
                "answer_key": answer_key_html,
            }
        )

        total_time = time.time() - start_time
        logger.info(f"Total request took: {total_time:.2f} seconds")

        return response

    except Exception as e:
        logger.error(f"Error generating HTMLs: {str(e)}")
        return {"error": str(e)}, 500


@bp.route("/generate_worksheet")
def generate_worksheet_route():
    """Generate a worksheet for a child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    child_id = request.args.get("child_id")
    if not child_id:
        flash("Please select a child.", "error")
        return redirect(url_for("web.index"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
        return redirect(url_for("web.index"))

    problems, answers = generator.generate_math_problems(
        age=child.age,
        count=30,  # default count
        difficulty=generator.get_school_year_progress(),
    )

    worksheet = Worksheet(child_id=child.id, problems=problems)
    repository.create_worksheet(worksheet)

    return render_template(
        "worksheet.html",
        user=user,
        child=child,
        problems=[{"text": p} for p in problems],
        worksheet_id=worksheet.id,
    )


@bp.route("/worksheets/<worksheet_id>/submit", methods=["POST"])
def submit_worksheet(worksheet_id):
    """Submit answers for a worksheet."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    worksheet = repository.get_worksheet(worksheet_id)
    if not worksheet:
        flash("Worksheet not found.", "error")
        return redirect(url_for("web.index"))

    child = repository.get_child_by_id(worksheet.child_id)
    if not child or child.parent_email != user.email:
        flash("Access denied.", "error")
        return redirect(url_for("web.index"))

    try:
        answers = [
            float(request.form.get(f"answer_{i}"))
            for i in range(len(worksheet.problems))
        ]
        worksheet.answers = answers
        worksheet.completed = True
        repository.update_worksheet(worksheet)
        flash("Worksheet submitted successfully!", "success")
    except (TypeError, ValueError):
        flash("Please enter valid numbers for all answers.", "error")

    return redirect(url_for("web.view_worksheet", worksheet_id=worksheet_id))


@bp.route("/worksheets/<worksheet_id>")
def view_worksheet(worksheet_id):
    """View a completed worksheet."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    worksheet = repository.get_worksheet(worksheet_id)
    if not worksheet:
        flash("Worksheet not found.", "error")
        return redirect(url_for("web.index"))

    child = repository.get_child_by_id(worksheet.child_id)
    if not child or child.parent_email != user.email:
        flash("Access denied.", "error")
        return redirect(url_for("web.index"))

    return render_template(
        "worksheet.html",
        user=user,
        child=child,
        problems=worksheet.problems,
        answers=worksheet.answers,
        completed=worksheet.completed,
        worksheet_id=worksheet.id,
    )


@bp.route("/terms")
def terms():
    """Render Terms of Service page."""
    return render_template("terms.html")


@bp.route("/privacy")
def privacy():
    """Render Privacy Policy page."""
    return render_template("privacy.html")
