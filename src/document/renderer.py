"""Module for rendering worksheets and answer keys."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from reportlab.lib.pagesizes import letter, portrait
from reportlab.pdfgen import canvas

from src.document.template import LayoutChoice, TemplateManager

logger = logging.getLogger(__name__)


class DocumentRenderer:
    """Renders worksheets and answer keys as PDFs."""

    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """Initialize document renderer.

        Args:
            template_manager: Optional template manager. If None, creates a new one.
        """
        self.template_manager = template_manager or TemplateManager()

    def _render_text(
        self,
        pdf: canvas.Canvas,
        positions: List[Tuple[int, int, int]],
        rois: List[Tuple[int, int, int, int]],
        problems: List[str],
        answers: Optional[List[str]] = None,
        render_answers: bool = False,
    ) -> None:
        """Render problems and optionally answers into the PDF.

        Args:
            pdf: PDF canvas to draw on.
            positions: List of (x_problem, y, x_answer) tuples.
            rois: List of (x1, y1, x2, y2) tuples for answer boxes.
            problems: List of problem strings.
            answers: Optional list of answer strings.
            render_answers: Whether to render answers.
        """
        for i, ((x_problem, y, x_answer), roi) in enumerate(zip(positions, rois)):
            problem = problems[i]
            answer = answers[i] if render_answers and answers else None

            # Render problem number
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x_problem, y, f"{i + 1}.")
            pdf.setFont("Helvetica", 12)

            # Handle word problems
            is_word_problem = len(problem) > 30 or "?" in problem
            if is_word_problem:
                # Split into words and wrap text
                words = problem.split()
                lines = []
                current_line = []
                current_width = 0
                max_width = 250  # Width for word problems

                for word in words:
                    word_width = pdf.stringWidth(word, "Helvetica", 12)
                    space_width = pdf.stringWidth(" ", "Helvetica", 12)
                    if current_width + word_width <= max_width:
                        current_line.append(word)
                        current_width += word_width + space_width
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                        current_width = word_width

                if current_line:
                    lines.append(" ".join(current_line))

                # Draw wrapped text
                for j, line in enumerate(lines):
                    pdf.drawString(x_problem + 35, y - j * 15, line)

                # Draw answer box below the text
                x1, y1, x2, y2 = roi
                box_y = y - (len(lines) * 15) - 10  # Position box below text
                pdf.rect(x1, box_y, x2 - x1, y2 - y1, stroke=1, fill=0)

                # Render answer if needed
                if render_answers and answer:
                    pdf.drawString(x_answer, box_y + 5, str(answer))
            else:
                # Regular single-line problem
                pdf.drawString(x_problem + 35, y, problem)
                x1, y1, x2, y2 = roi
                pdf.rect(x1, y1, x2 - x1, y2 - y1, stroke=1, fill=0)

                # Render answer if needed
                if render_answers and answer:
                    pdf.drawString(x_answer, y, str(answer))

    def create_worksheet(
        self,
        filename: str,
        problems: List[str],
        worksheet_id: str,
        layout: Optional[LayoutChoice] = None,
    ) -> None:
        """Generate a math worksheet PDF.

        Args:
            filename: Output PDF path.
            problems: List of problem strings.
            worksheet_id: Worksheet ID.
            layout: Optional layout choice. If None, automatically chosen.
        """
        # Create PDF
        pdf = canvas.Canvas(filename, pagesize=portrait(letter))
        width, height = letter

        # Add header
        pdf.setFont("Helvetica", 18)
        pdf.drawString(200, 750, "Math Worksheet")
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.drawString(50, 720, f"Name: _______________    Date: {current_datetime}")

        # Calculate layout
        positions, rois = self.template_manager.calculate_layout(
            len(problems), problems, layout
        )

        # Render problems
        self._render_text(pdf, positions, rois, problems)

        pdf.save()

    def create_answer_key(
        self,
        filename: str,
        problems: List[str],
        answers: List[str],
        worksheet_id: str,
        layout: Optional[LayoutChoice] = None,
    ) -> None:
        """Generate an answer key PDF.

        Args:
            filename: Output PDF path.
            problems: List of problem strings.
            answers: List of answer strings.
            worksheet_id: Worksheet ID.
            layout: Optional layout choice. If None, automatically chosen.

        Raises:
            ValueError: If number of problems and answers don't match.
        """
        if len(problems) != len(answers):
            raise ValueError(
                f"Number of problems ({len(problems)}) doesn't match "
                f"number of answers ({len(answers)})"
            )

        # Create PDF
        pdf = canvas.Canvas(filename, pagesize=portrait(letter))
        width, height = letter

        # Add header
        pdf.setFont("Helvetica", 18)
        pdf.drawString(200, 750, "Math Worksheet - Answer Key")

        # Calculate layout
        positions, rois = self.template_manager.calculate_layout(
            len(problems), problems, layout
        )

        # Render problems and answers
        self._render_text(pdf, positions, rois, problems, answers, render_answers=True)

        pdf.save()
