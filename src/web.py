"""Web interface for math worksheet generation."""

import base64
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

import weasyprint
from flask import Flask, Response, jsonify, render_template, request, send_file, url_for
from werkzeug.utils import safe_join, secure_filename

from src.document.template import LayoutChoice
from src.generator import ProblemGenerator
from src.main import MathTutor

app = Flask(__name__)

# Configure absolute paths
app.config["BASE_DIR"] = os.path.abspath(os.path.dirname(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(app.config["BASE_DIR"], "..", "data/uploads")
app.config["WORKSHEET_FOLDER"] = os.path.join(
    app.config["BASE_DIR"], "..", "data/worksheets"
)
app.config["ANSWER_KEY_FOLDER"] = os.path.join(
    app.config["BASE_DIR"], "..", "data/answer_keys"
)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
for directory in [
    app.config["UPLOAD_FOLDER"],
    app.config["WORKSHEET_FOLDER"],
    app.config["ANSWER_KEY_FOLDER"],
]:
    os.makedirs(directory, exist_ok=True)

# Initialize components
generator = ProblemGenerator()


@app.route("/")
def index():
    """Render the main page."""
    return render_template(
        "index.html",
        ages=list(range(6, 10)),  # Ages 6-9
        default_age=6,  # Set default age to 6
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
        problems, _ = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )
        preview_problems = problems[:5]  # Only show first 5 problems

        # Convert problems to dictionary format
        problem_list = []
        for problem in preview_problems:
            problem_list.append({"text": problem})

        # Generate preview HTML using the same template as worksheet
        preview_html = render_template(
            "problem_grid.html", problems=problem_list, is_preview=True
        )

        return jsonify(
            {
                "success": True,
                "html": preview_html,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e), "success": False})


@app.route("/debug/view-worksheet", methods=["POST"])
def debug_view_worksheet():
    """Debug route to view the worksheet HTML directly before PDF conversion."""
    try:
        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )
        pdf_type = request.form.get("type", "worksheet")

        # Generate unique ID and problems
        worksheet_id = f"math_worksheet_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
        problems, answers = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )

        # Convert problems to dictionary format
        problem_list = []
        for problem in problems:
            problem_list.append({"text": problem})

        # Create QR code
        qr_code = generator.create_qr_code(worksheet_id)
        qr_code_b64 = base64.b64encode(qr_code.getvalue()).decode()

        # Generate HTML
        is_answer_key = pdf_type == "answer_key"
        html_content = render_template(
            "worksheet.html",
            problems=problem_list,
            answers=answers if is_answer_key else None,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qr_code=qr_code_b64,
            is_answer_key=is_answer_key,
            is_preview=False,
        )

        # Return the HTML directly
        return html_content

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/generate", methods=["POST"])
def generate_worksheet():
    """Generate a worksheet or answer key PDF for printing."""
    try:
        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )
        pdf_type = request.form.get("type", "worksheet")  # 'worksheet' or 'answer_key'

        # Generate unique ID and problems
        worksheet_id = f"math_worksheet_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
        problems, answers = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )

        # Convert problems to dictionary format
        problem_list = []
        for problem in problems:
            problem_list.append({"text": problem})

        # Create QR code
        qr_code = generator.create_qr_code(worksheet_id)
        qr_code_b64 = base64.b64encode(qr_code.getvalue()).decode()

        # Generate HTML
        is_answer_key = pdf_type == "answer_key"
        html_content = render_template(
            "worksheet.html",
            problems=problem_list,
            answers=answers if is_answer_key else None,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qr_code=qr_code_b64,
            is_answer_key=is_answer_key,
            is_preview=False,
        )

        # Convert HTML to PDF using WeasyPrint
        pdf = weasyprint.HTML(string=html_content).write_pdf()

        # Create response with PDF
        response = Response(pdf, mimetype="application/pdf")
        filename = "answer_key.pdf" if is_answer_key else "worksheet.pdf"
        response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        app.logger.error(f"Error generating worksheet: {str(e)}")
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
