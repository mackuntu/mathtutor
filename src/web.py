"""Web interface for math worksheet generation."""

import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from src.document.template import LayoutChoice
from src.main import MathTutor

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "data/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["WORKSHEET_FOLDER"] = "data/worksheets"
app.config["ANSWER_KEY_FOLDER"] = "data/answer_keys"

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["WORKSHEET_FOLDER"], exist_ok=True)
os.makedirs(app.config["ANSWER_KEY_FOLDER"], exist_ok=True)

# Initialize MathTutor
tutor = MathTutor()


@app.route("/")
def index():
    """Render the main page."""
    return render_template(
        "index.html",
        ages=list(range(6, 10)),  # Ages 6-9
    )


@app.route("/generate", methods=["POST"])
def generate_worksheet():
    """Generate a worksheet based on form data."""
    try:
        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))

        # Generate worksheet
        worksheet_path, answer_key_path = tutor.generate_worksheet(
            age=age,
            count=count,
        )

        # Return both files
        return {
            "worksheet": url_for("download_file", filename=Path(worksheet_path).name),
            "answer_key": url_for("download_file", filename=Path(answer_key_path).name),
            "success": True,
        }

    except Exception as e:
        return {"error": str(e), "success": False}


@app.route("/download/<filename>")
def download_file(filename):
    """Download a generated file."""
    # Determine which directory to look in based on filename
    if filename.endswith("_key.pdf"):
        directory = app.config["ANSWER_KEY_FOLDER"]
    else:
        directory = app.config["WORKSHEET_FOLDER"]

    # Use absolute path by joining with project root
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), directory, filename
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    # Run on all interfaces
    app.run(host="0.0.0.0", port=8080, debug=True)
