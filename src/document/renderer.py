"""Module for rendering worksheets and answer keys."""

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.utils import ImageReader
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

    def _create_qr_code(self, worksheet_id: str) -> BytesIO:
        """Generate a QR code for worksheet identification.

        Args:
            worksheet_id: Unique identifier for worksheet.

        Returns:
            BytesIO containing QR code image.
        """
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
        )
        qr.add_data(worksheet_id)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        byte_stream = BytesIO()
        qr_image.save(byte_stream, format="PNG")
        byte_stream.seek(0)

        return byte_stream

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

            # Render problem number and text with more spacing
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x_problem, y, f"{i + 1}.")
            pdf.setFont("Helvetica", 12)
            # Increased spacing from 20 to 35 pixels after the problem number
            pdf.drawString(x_problem + 35, y, problem)

            # Render answer if needed
            if render_answers and answer:
                pdf.drawString(x_answer, y, str(answer))

            # Draw answer box
            x1, y1, x2, y2 = roi
            pdf.setStrokeColorRGB(0.8, 0.8, 0.8)  # Light gray
            pdf.rect(x1, y1, x2 - x1, y2 - y1, stroke=1, fill=0)

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

        # Add QR code
        qr_code = self._create_qr_code(worksheet_id)
        pdf.drawImage(ImageReader(qr_code), 550, 400, width=40, height=40)

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

        # Add QR code
        qr_code = self._create_qr_code(worksheet_id)
        pdf.drawImage(ImageReader(qr_code), 550, 700, width=40, height=40)

        # Calculate layout
        positions, rois = self.template_manager.calculate_layout(
            len(problems), problems, layout
        )

        # Render problems and answers
        self._render_text(pdf, positions, rois, problems, answers, render_answers=True)

        pdf.save()
