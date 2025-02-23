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

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize MathTutor
tutor = MathTutor()


@app.route("/")
def index():
    """Render the main page."""
    return render_template(
        "index.html",
        ages=list(range(6, 10)),  # Ages 6-9
        layouts=[layout.value for layout in LayoutChoice],
    )


@app.route("/generate", methods=["POST"])
def generate_worksheet():
    """Generate a worksheet based on form data."""
    try:
        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        layout = LayoutChoice(request.form.get("layout", LayoutChoice.TWO_COLUMN.value))

        # Generate worksheet
        worksheet_path, answer_key_path = tutor.generate_worksheet(
            age=age,
            count=count,
            layout=layout,
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
        directory = "data/answer_keys"
    else:
        directory = "data/worksheets"

    return send_file(
        Path(directory) / filename,
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(debug=True)
