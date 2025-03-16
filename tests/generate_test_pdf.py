"""Script to generate a test PDF file for UI tests."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.problem_generator import ProblemGenerator


def generate_test_pdf():
    """Generate a test PDF file for UI tests."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        print("Please install the required package: reportlab")
        print("pip install reportlab")
        return

    # Create the test-downloads directory if it doesn't exist
    download_dir = Path("test-downloads")
    download_dir.mkdir(exist_ok=True)

    # Generate some math problems
    generator = ProblemGenerator()
    problems, answers = generator.generate_math_problems(
        age=8, count=10, difficulty=0.5
    )

    # Create a PDF document
    pdf_path = download_dir / "worksheet.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        topMargin=0.4 * 72,
        leftMargin=0.4 * 72,
        rightMargin=0.4 * 72,
        bottomMargin=0.4 * 72,
    )

    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal_style = styles["Normal"]

    # Create content
    content = []

    # Add title
    content.append(Paragraph("MathTutor Worksheet", title_style))
    content.append(Spacer(1, 12))

    # Add info row
    info_data = [
        [
            Paragraph("Name: ___________________", normal_style),
            Paragraph("Date: ___________________", normal_style),
            Paragraph("Score: _____/10", normal_style),
        ]
    ]
    info_table = Table(info_data, colWidths=[doc.width / 3.0] * 3)
    info_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    content.append(info_table)
    content.append(Spacer(1, 24))

    # Create problem grid (5 columns x 2 rows)
    problem_data = []
    row = []
    for i, problem in enumerate(problems):
        # Create a cell with the problem and answer space
        problem_text = Paragraph(problem, normal_style)
        cell_content = [problem_text, Paragraph("_______", normal_style)]
        row.append(cell_content)

        # Start a new row after every 5 problems
        if (i + 1) % 5 == 0:
            problem_data.append(row)
            row = []

    # Add any remaining problems
    if row:
        # Fill the row with empty cells if needed
        while len(row) < 5:
            row.append(["", ""])
        problem_data.append(row)

    # Create the problem grid table
    problem_grid = Table(problem_data, colWidths=[doc.width / 5.0] * 5)
    problem_grid.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ]
        )
    )
    content.append(problem_grid)

    # Build the PDF
    doc.build(content)

    print(f"Generated test PDF at: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_test_pdf()
