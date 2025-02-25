"""Web interface for math worksheet generation."""

import logging
import os
import time

from flask import Flask, jsonify, render_template, request

from src.generator import ProblemGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure absolute paths
app.config["BASE_DIR"] = os.path.abspath(os.path.dirname(__file__))

# Initialize components
generator = ProblemGenerator()


@app.route("/")
def index():
    """Render the main page."""
    return render_template(
        "index.html",
        ages=list(range(6, 10)),  # Ages 6-9
        default_age=6,
        default_difficulty=generator.get_school_year_progress(),
    )


@app.route("/preview", methods=["POST"])
def preview_problems():
    """Generate a preview of problems based on current settings."""
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


@app.route("/generate_both", methods=["POST"])
def generate_both():
    """Generate both worksheet and answer key HTML."""
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
