"""Web interface for math worksheet generation."""

import base64
import os
from datetime import datetime
from pathlib import Path

import weasyprint
from flask import Flask, jsonify, render_template, request, send_file, url_for
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
        age = int(request.form["age"])
        count = min(
            5, int(request.form.get("count", 30))
        )  # Limit preview to 5 problems
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )

        # Generate problems
        problems, answers = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )

        # Convert problems to dictionary format with metadata
        problem_list = []
        for problem in problems:
            is_word_problem = len(problem) > 30 or "?" in problem
            problem_list.append(
                {
                    "text": problem,
                    "is_word_problem": is_word_problem,
                }
            )

        # Render preview template
        html = render_template(
            "worksheet.html",
            problems=problem_list,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qr_code="",  # No QR code needed for preview
        )

        return jsonify(
            {
                "success": True,
                "html": html,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e), "success": False})


@app.route("/generate", methods=["POST"])
def generate_worksheet():
    """Generate a worksheet based on form data."""
    try:
        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )

        # Generate unique ID
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        worksheet_id = f"math_worksheet_{timestamp}"

        # Generate problems
        problems, answers = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )

        # Convert problems to dictionary format with metadata
        problem_list = []
        for problem in problems:
            is_word_problem = len(problem) > 30 or "?" in problem
            problem_list.append(
                {
                    "text": problem,
                    "is_word_problem": is_word_problem,
                }
            )

        # Create QR code
        qr_code = generator.create_qr_code(worksheet_id)
        qr_code_b64 = base64.b64encode(qr_code.getvalue()).decode()

        # Generate worksheet PDF
        worksheet_html = render_template(
            "worksheet.html",
            problems=problem_list,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qr_code=qr_code_b64,
        )

        # Use absolute paths for files
        worksheet_path = os.path.join(
            app.config["WORKSHEET_FOLDER"], f"{worksheet_id}.pdf"
        )
        css_path = os.path.join(app.config["BASE_DIR"], "static/css/worksheet.css")

        # Generate PDF with WeasyPrint
        html = weasyprint.HTML(string=worksheet_html)
        html.write_pdf(worksheet_path, stylesheets=[weasyprint.CSS(css_path)])

        # Generate answer key PDF
        answer_key_html = render_template(
            "worksheet.html",
            problems=problem_list,
            answers=answers,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qr_code=qr_code_b64,
            is_answer_key=True,
        )

        answer_key_path = os.path.join(
            app.config["ANSWER_KEY_FOLDER"], f"{worksheet_id}_key.pdf"
        )
        html = weasyprint.HTML(string=answer_key_html)
        html.write_pdf(answer_key_path, stylesheets=[weasyprint.CSS(css_path)])

        # Return file paths
        return jsonify(
            {
                "success": True,
                "worksheet": url_for("download_file", filename=f"{worksheet_id}.pdf"),
                "answer_key": url_for(
                    "download_file", filename=f"{worksheet_id}_key.pdf"
                ),
            }
        )

    except Exception as e:
        app.logger.error(f"Error generating worksheet: {str(e)}")
        return jsonify({"error": str(e), "success": False})


@app.route("/download/<filename>")
def download_file(filename):
    """Download a generated file."""
    try:
        # Secure the filename
        filename = secure_filename(filename)

        # Determine which directory to look in based on filename
        if filename.endswith("_key.pdf"):
            directory = app.config["ANSWER_KEY_FOLDER"]
        else:
            directory = app.config["WORKSHEET_FOLDER"]

        # Use safe_join to prevent directory traversal
        file_path = safe_join(directory, filename)

        if not file_path or not os.path.isfile(file_path):
            app.logger.error(f"File not found: {file_path}")
            return "File not found", 404

        # Send file with explicit PDF mimetype
        return send_file(
            file_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        return f"Error downloading file: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
