"""Worksheet management routes for the MathTutor application."""

import json
import logging
import time
from typing import List

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from ..database import get_repository
from ..generator import ProblemGenerator
from ..models import Worksheet
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
repository = get_repository()
generator = ProblemGenerator()

# Create blueprint
bp = Blueprint("worksheets", __name__, url_prefix="/worksheets")


@bp.route("/preview", methods=["POST"])
def preview_problems():
    """Generate a preview of problems based on current settings."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

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
        return redirect(url_for("auth.login"))

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


@bp.route("/generate")
def generate_worksheet_route():
    """Generate a worksheet for a child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    child_id = request.args.get("child_id")
    if not child_id:
        flash("Please select a child.", "error")
        return redirect(url_for("pages.index"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
        return redirect(url_for("pages.index"))

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


@bp.route("/<worksheet_id>/submit", methods=["POST"])
def submit_worksheet(worksheet_id):
    """Submit answers for a worksheet."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    worksheet = repository.get_worksheet(worksheet_id)
    if not worksheet:
        flash("Worksheet not found.", "error")
        return redirect(url_for("pages.index"))

    child = repository.get_child_by_id(worksheet.child_id)
    if not child or child.parent_email != user.email:
        flash("Access denied.", "error")
        return redirect(url_for("pages.index"))

    try:
        answers = []
        incorrect_problems = []
        # Handle problems which could be a list or a string
        if isinstance(worksheet.problems, str):
            problems = json.loads(worksheet.problems)
        else:
            problems = worksheet.problems

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

    return redirect(url_for("worksheets.view_worksheet", worksheet_id=worksheet_id))


@bp.route("/<worksheet_id>")
def view_worksheet(worksheet_id):
    """View a completed worksheet."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    worksheet = repository.get_worksheet(worksheet_id)
    if not worksheet:
        flash("Worksheet not found.", "error")
        return redirect(url_for("pages.index"))

    child = repository.get_child_by_id(worksheet.child_id)
    if not child or child.parent_email != user.email:
        flash("Access denied.", "error")
        return redirect(url_for("pages.index"))

    # Handle problems which could be a list or a string
    if isinstance(worksheet.problems, str):
        problems = json.loads(worksheet.problems)
    else:
        problems = worksheet.problems
    problem_list = [{"text": p} for p in problems]

    answers = json.loads(worksheet.answers) if worksheet.answers else None

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


@bp.route("/past/<child_id>")
def past_worksheets(child_id):
    """View past worksheets for a child."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    if not child_id:
        flash("Please select a child first.", "warning")
        return redirect(url_for("pages.index"))

    child = repository.get_child_by_id(child_id)
    if not child or child.parent_email != user.email:
        flash("Child not found.", "error")
        return redirect(url_for("pages.index"))

    worksheets = repository.get_child_worksheets(child_id)
    worksheets.sort(key=lambda w: w.created_at, reverse=True)

    # Calculate past scores for the chart
    past_scores = []
    past_dates = []

    # First collect all completed worksheets with scores
    scored_worksheets = []
    for worksheet in worksheets:
        if worksheet.completed and worksheet.score is not None:
            scored_worksheets.append(worksheet)

    # Sort by date (oldest first) for the chart
    scored_worksheets.sort(key=lambda w: w.created_at)

    # Extract scores and dates in chronological order
    for worksheet in scored_worksheets:
        past_scores.append(round(worksheet.score, 1))
        past_dates.append(worksheet.created_at.strftime("%Y-%m-%d"))

    return render_template(
        "past_worksheets.html",
        user=user,
        child=child,
        worksheets=worksheets,
        past_scores=past_scores,
        past_dates=past_dates,
    )


@bp.route("/<worksheet_id>/grade")
def grade_worksheet(worksheet_id):
    """Grade a worksheet."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    worksheet = repository.get_worksheet(worksheet_id)
    if not worksheet:
        flash("Worksheet not found.", "error")
        return redirect(url_for("pages.index"))

    child = repository.get_child_by_id(worksheet.child_id)
    if not child or child.parent_email != user.email:
        flash("Access denied.", "error")
        return redirect(url_for("pages.index"))

    # Get past scores for sparkline
    past_worksheets = repository.get_child_worksheets(child.id)
    past_scores = []
    past_dates = []

    for w in past_worksheets:
        if w.incorrect_problems is not None:  # Only include graded worksheets
            # Handle problems which could be a list or a string
            if isinstance(w.problems, str):
                problems = json.loads(w.problems)
            else:
                problems = w.problems

            total = len(problems)
            incorrect = len(w.incorrect_problems)
            score = ((total - incorrect) / total) * 100
            past_scores.append(score)
            past_dates.append(w.created_at.strftime("%Y-%m-%d"))

    # Handle problems which could be a list or a string
    if isinstance(worksheet.problems, str):
        problems = json.loads(worksheet.problems)
    else:
        problems = worksheet.problems

    # Generate problems and answers for the answer key view
    problem_list = []
    answers = []

    # Process each problem to extract text and calculate answers
    for p in problems:
        if isinstance(p, dict):
            # If problem is a dictionary, extract text and answer if available
            problem_text = p.get("text", "")
            problem_list.append({"text": problem_text})

            # If answer is already in the problem dictionary, use it
            if "answer" in p:
                answers.append(p["answer"])
            else:
                # Otherwise calculate the answer from the problem text
                try:
                    # Replace × with * and ÷ with / for evaluation
                    calc_text = problem_text.replace("×", "*").replace("÷", "/")
                    # Remove any spaces
                    calc_text = calc_text.replace(" ", "")
                    # Evaluate the expression
                    answer = eval(calc_text)
                    answers.append(answer)
                except Exception as e:
                    # If evaluation fails, append None
                    logger.warning(
                        f"Failed to evaluate problem: {problem_text}. Error: {str(e)}"
                    )
                    answers.append(None)
        elif isinstance(p, str):
            # If problem is a string, use it directly
            problem_list.append({"text": p})

            # Calculate the answer from the problem text
            try:
                # Replace × with * and ÷ with / for evaluation
                calc_text = p.replace("×", "*").replace("÷", "/")
                # Remove any spaces
                calc_text = calc_text.replace(" ", "")
                # Evaluate the expression
                answer = eval(calc_text)
                answers.append(answer)
            except Exception as e:
                # If evaluation fails, append None
                logger.warning(f"Failed to evaluate problem: {p}. Error: {str(e)}")
                answers.append(None)

    return render_template(
        "grade_worksheet.html",
        user=user,
        child=child,
        problems=problem_list,
        answers=answers,
        worksheet=worksheet,
        incorrect_problems=worksheet.incorrect_problems,
        past_scores=past_scores[-10:],  # Show last 10 scores
        past_dates=past_dates[-10:],
        is_answer_key=True,
    )


@bp.route("/<worksheet_id>/submit_grades", methods=["POST"])
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

        # Update worksheet with incorrect problems and mark as completed
        worksheet.incorrect_problems = incorrect_problems
        worksheet.completed = True
        repository.update_worksheet(worksheet)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/<worksheet_id>/delete", methods=["POST"])
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


@bp.route("/bulk_delete", methods=["POST"])
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
