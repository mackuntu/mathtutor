"""Script to generate a test PDF file for UI tests."""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.models import Worksheet
from src.generator import ProblemGenerator


def generate_test_pdf():
    """Generate a test PDF file for UI tests."""
    try:
        import html2pdf
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        print("Please install the required packages: jinja2, html2pdf")
        print("pip install jinja2 html2pdf")
        return

    # Create the test-downloads directory if it doesn't exist
    download_dir = Path("test-downloads")
    download_dir.mkdir(exist_ok=True)

    # Generate some math problems
    generator = ProblemGenerator()
    problems, answers = generator.generate_math_problems(
        age=8, count=10, difficulty=0.5
    )

    # Create a Jinja2 environment
    env = Environment(loader=FileSystemLoader("src/templates"))

    # Load the worksheet template
    template = env.get_template("worksheet.html")

    # Render the worksheet HTML
    problem_list = [{"text": p} for p in problems]
    worksheet_html = template.render(
        problems=problem_list,
        answers=None,
        is_answer_key=False,
        is_preview=False,
        serial_number="TEST-123",
    )

    # Create a temporary HTML file
    temp_html_path = download_dir / "temp_worksheet.html"
    with open(temp_html_path, "w") as f:
        f.write(worksheet_html)

    # Generate the PDF
    pdf_path = download_dir / "worksheet.pdf"

    try:
        # Try to use html2pdf
        from html2pdf import HTMLToPDF

        converter = HTMLToPDF()
        converter.convert(temp_html_path, pdf_path)
    except Exception as e:
        print(f"Error using html2pdf: {e}")
        try:
            # Fallback to using weasyprint
            from weasyprint import HTML

            HTML(temp_html_path).write_pdf(pdf_path)
        except Exception as e:
            print(f"Error using weasyprint: {e}")
            print("Could not generate PDF. Please install weasyprint or html2pdf.")
            return

    # Clean up the temporary HTML file
    temp_html_path.unlink()

    print(f"Generated test PDF at: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_test_pdf()
