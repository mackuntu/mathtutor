"""Web routes for the MathTutor application."""

import json
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
from .database.models import Child
from .generator import ProblemGenerator
from .models import Worksheet  # Use the model with create() method

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
        num_worksheets = int(request.form.get("num_worksheets", 1))
        child_id = request.form.get("child_id")

        if not child_id:
            return {"error": "Child ID is required"}, 400

        child = repository.get_child_by_id(child_id)
        if not child or child.parent_email != user.email:
            return {"error": "Child not found"}, 404

        # Generate multiple worksheets
        worksheets_data = []
        for _ in range(num_worksheets):
            # Generate problems
            prob_start = time.time()
            problems, answers = generator.generate_math_problems(
                age=age,
                count=count,
                difficulty=difficulty,
            )
            prob_time = time.time() - prob_start
            logger.info(f"Problem generation took: {prob_time:.2f} seconds")

            # Create worksheet in database
            worksheet = Worksheet.create(
                child_id=child_id, problems=json.dumps(problems)
            )
            repository.create_worksheet(worksheet)

            problem_list = [{"text": p} for p in problems]

            # Generate worksheet HTML
            html_start = time.time()
            worksheet_html = render_template(
                "worksheet.html",
                problems=problem_list,
                answers=None,
                is_answer_key=False,
                is_preview=False,
                serial_number=worksheet.serial_number,
            )

            # Generate answer key HTML
            answer_key_html = render_template(
                "worksheet.html",
                problems=problem_list,
                answers=answers,
                is_answer_key=True,
                is_preview=False,
                serial_number=worksheet.serial_number,
            )
            html_time = time.time() - html_start
            logger.info(f"HTML generation took: {html_time:.2f} seconds")

            worksheets_data.append(
                {
                    "worksheet": worksheet_html,
                    "answer_key": answer_key_html,
                    "serial_number": worksheet.serial_number,
                }
            )

        total_time = time.time() - start_time
        logger.info(f"Total request took: {total_time:.2f} seconds")

        return jsonify({"worksheets": worksheets_data})

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
        answers = []
        incorrect_problems = []
        problems = json.loads(worksheet.problems)

        for i in range(len(problems)):
            student_answer = request.form.get(f"answer_{i}")
            if student_answer:
                student_answer = float(student_answer)
                answers.append(student_answer)
                # Check if answer is incorrect
                if "answer" in problems[i] and student_answer != problems[i]["answer"]:
                    incorrect_problems.append(i)
            else:
                answers.append(None)

        worksheet.answers = json.dumps(answers)
        worksheet.incorrect_problems = incorrect_problems
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

    problems = json.loads(worksheet.problems)
    answers = json.loads(worksheet.answers) if worksheet.answers else None

    # Format problems to match the expected structure
    problem_list = [{"text": p} for p in problems]

    return render_template(
        "worksheet.html",
        user=user,
        child=child,
        problems=problem_list,
        answers=answers,
        worksheet_id=worksheet.id,
        serial_number=worksheet.serial_number,
        incorrect_problems=worksheet.incorrect_problems,
        is_answer_key=request.args.get("print") == "true",
    )


@bp.route("/terms")
def terms():
    """Render Terms of Service page."""
    return render_template("terms.html")


@bp.route("/privacy")
def privacy():
    """Render Privacy Policy page."""
    return render_template("privacy.html")


@bp.route("/past_worksheets/", defaults={"child_id": None})
@bp.route("/past_worksheets/<child_id>")
def past_worksheets(child_id):
    """View past worksheets for a child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    if not child_id:
        flash("Please select a child first.", "warning")
        return redirect(url_for("web.index"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
        return redirect(url_for("web.index"))

    worksheets = repository.get_child_worksheets(child_id)
    worksheets.sort(key=lambda w: w.created_at, reverse=True)

    return render_template(
        "past_worksheets.html",
        user=user,
        child=child,
        worksheets=worksheets,
    )


@bp.route("/worksheets/<worksheet_id>/grade")
def grade_worksheet(worksheet_id):
    """Grade a worksheet."""
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

    # Get past scores for sparkline
    past_worksheets = repository.get_child_worksheets(child.id)
    past_scores = []
    past_dates = []

    for w in past_worksheets:
        if w.incorrect_problems is not None:  # Only include graded worksheets
            total = len(json.loads(w.problems))
            incorrect = len(w.incorrect_problems)
            score = ((total - incorrect) / total) * 100
            past_scores.append(score)
            past_dates.append(w.created_at.strftime("%Y-%m-%d"))

    problems = json.loads(worksheet.problems)
    problem_list = [{"text": p} for p in problems]

    return render_template(
        "grade_worksheet.html",
        user=user,
        child=child,
        worksheet=worksheet,
        problems=problem_list,
        past_scores=past_scores[-10:],  # Show last 10 scores
        past_dates=past_dates[-10:],
    )


@bp.route("/worksheets/<worksheet_id>/submit_grades", methods=["POST"])
def submit_grades(worksheet_id):
    """Submit grades for a worksheet."""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    worksheet = repository.get_worksheet(worksheet_id)
    if not worksheet:
        return jsonify({"success": False, "error": "Worksheet not found"}), 404

    child = repository.get_child_by_id(worksheet.child_id)
    if not child or child.parent_email != user.email:
        return jsonify({"success": False, "error": "Access denied"}), 403

    try:
        data = request.get_json()
        incorrect_problems = data.get("incorrect_problems", [])

        # Update worksheet with incorrect problems
        worksheet.incorrect_problems = incorrect_problems
        repository.update_worksheet(worksheet)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/worksheets/<worksheet_id>/delete", methods=["POST"])
def delete_worksheet(worksheet_id):
    """Delete a worksheet."""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    worksheet = repository.get_worksheet(worksheet_id)
    if not worksheet:
        return jsonify({"success": False, "error": "Worksheet not found"}), 404

    child = repository.get_child_by_id(worksheet.child_id)
    if not child or child.parent_email != user.email:
        return jsonify({"success": False, "error": "Access denied"}), 403

    repository.delete_worksheet(worksheet_id)
    flash("Worksheet deleted successfully!", "success")
    return jsonify({"success": True})


@bp.route("/worksheets/bulk_delete", methods=["POST"])
def bulk_delete_worksheets():
    """Delete multiple worksheets."""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json()
    worksheet_ids = data.get("worksheet_ids", [])

    if not worksheet_ids:
        return jsonify({"success": False, "error": "No worksheets selected"}), 400

    # Verify ownership of all worksheets before deleting
    for worksheet_id in worksheet_ids:
        worksheet = repository.get_worksheet(worksheet_id)
        if not worksheet:
            continue

        child = repository.get_child_by_id(worksheet.child_id)
        if not child or child.parent_email != user.email:
            return jsonify({"success": False, "error": "Access denied"}), 403

    # Delete all worksheets
    for worksheet_id in worksheet_ids:
        repository.delete_worksheet(worksheet_id)

    flash(f"{len(worksheet_ids)} worksheets deleted successfully!", "success")
    return jsonify({"success": True})
