from datetime import datetime
from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from marker_utils import MarkerUtils
from roi_template_manager import ROITemplateManager


class WorksheetRenderer:
    SPACE_DECORATIONS = [
        "assets/rocket.png",
        "assets/moon.png",
        "assets/star.png",
        "assets/shining_star.png",
        "assets/planet.png",
        "assets/galaxy.png",
    ]

    @staticmethod
    def create_qr_code(worksheet_id, version):
        """
        Generate a QR code for the worksheet ID and version.
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data({"worksheet_id": worksheet_id, "version": version})
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        byte_stream = BytesIO()
        qr_image.save(byte_stream, format="PNG")
        byte_stream.seek(0)
        return byte_stream

    @staticmethod
    def calculate_layout(problems, x_positions, y_start, row_spacing):
        """Precompute positions and ROIs."""
        positions = []
        rois = []
        y_position = y_start
        half = len(problems) // 2

        for i, problem in enumerate(problems):
            # Determine column based on index
            if i < half:
                x_problem = x_positions["column_1_problem"]
                x_answer = x_positions["column_1_answer"]
            else:
                x_problem = x_positions["column_2_problem"]
                x_answer = x_positions["column_2_answer"]
                if i == half:  # Reset y_position when switching to the second column
                    y_position = y_start

            # Append positions and ROIs
            positions.append((x_problem, y_position, x_answer))
            rois.append((x_answer, y_position - 10, x_answer + 100, y_position + 10))

            # Update y_position
            y_position -= row_spacing

        return positions, rois

    @staticmethod
    def render_text(pdf, positions, problems, answers=None, render_answers=False):
        """Render problems and optionally answers into the PDF."""
        decoration_index = 0

        for i, (x_problem, y, x_answer) in enumerate(positions):
            problem = problems[i]
            answer = answers[i] if render_answers and answers else None

            # Render problem
            try:
                decoration_path = WorksheetRenderer.SPACE_DECORATIONS[decoration_index]
                decoration_index = (decoration_index + 1) % len(
                    WorksheetRenderer.SPACE_DECORATIONS
                )
                decoration = ImageReader(decoration_path)
                pdf.drawImage(decoration, x_problem - 30, y - 3, width=18, height=18)
            except Exception as e:
                print(f"Warning: Failed to load decoration: {e}")

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x_problem, y, f"{i + 1}.")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(x_problem + 20, y, problem)

            if render_answers and answer:
                pdf.drawString(x_answer, y, f"{answer}")

            # Debug bounding box for answers
            pdf.setStrokeColorRGB(1, 0, 0)
            pdf.rect(x_answer, y - 10, 100, 20, stroke=1, fill=0)

    @staticmethod
    def create_math_worksheet(filename, problems, qr_code_stream):
        """Generate a math worksheet."""
        pdf = canvas.Canvas(filename, pagesize=portrait(letter))
        pdf.setFont("Helvetica", 18)

        MarkerUtils.draw_alignment_markers(pdf)
        pdf.drawString(200, 750, "Math Worksheet")
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.drawString(50, 720, f"Name: _______________    Date: {current_datetime}")
        pdf.drawImage(ImageReader(qr_code_stream), 550, 700, width=40, height=40)

        x_positions = {
            "column_1_problem": 50,
            "column_1_answer": 150,
            "column_2_problem": 300,
            "column_2_answer": 400,
        }
        y_start = 680
        row_spacing = 30

        positions, rois = WorksheetRenderer.calculate_layout(
            problems, x_positions, y_start, row_spacing
        )
        template_id = ROITemplateManager.find_or_create_template(rois)

        WorksheetRenderer.render_text(pdf, positions, problems)

        pdf.save()
        return template_id

    @staticmethod
    def create_answer_key(filename, problems, answers, qr_code_stream):
        """Generate an answer key."""
        pdf = canvas.Canvas(filename, pagesize=portrait(letter))
        pdf.setFont("Helvetica", 18)

        pdf.drawString(200, 750, "Math Worksheet Answer Key")
        pdf.drawImage(ImageReader(qr_code_stream), 550, 700, width=40, height=40)

        x_positions = {
            "column_1_problem": 50,
            "column_1_answer": 150,
            "column_2_problem": 300,
            "column_2_answer": 400,
        }
        y_start = 680
        row_spacing = 30

        positions, _ = WorksheetRenderer.calculate_layout(
            problems, x_positions, y_start, row_spacing
        )

        WorksheetRenderer.render_text(
            pdf, positions, problems, answers, render_answers=True
        )

        pdf.save()
