from datetime import datetime
from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from layout_utils import (
    ANSWER_BOX_DIMENSIONS,
    LAYOUT_CONFIGS,
    ROW_SPACING,
    X_POSITIONS,
    Y_START,
    LayoutChoice,
)
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
    def calculate_layout(problems, layout_choice):
        """
        Precompute positions and ROIs based on a flexible layout choice.

        Args:
            problems (list): List of problems.
            layout_choice (str): Layout type (e.g., "2_column", "1_column", "mixed").

        Returns:
            tuple: Positions of problems [(x_problem, y, x_answer)] and ROIs [(x1, y1, x2, y2)].
        """
        # Fetch layout configuration
        layout_config = LAYOUT_CONFIGS[layout_choice]
        columns = layout_config["columns"]
        column_limits = layout_config["column_limits"]

        positions = []
        rois = []
        y_positions = {col: Y_START for col in columns}
        problem_index = 0

        for col_index, column in enumerate(columns):
            x_problem = X_POSITIONS[f"{column}_problem"]
            x_answer = X_POSITIONS[f"{column}_answer"]
            limit = column_limits[col_index]

            for _ in range(limit):
                if problem_index >= len(problems):
                    break

                y_position = y_positions[column]

                # Add problem and ROI positions
                positions.append((x_problem, y_position, x_answer))
                x1, y1_offset, x2, y2_offset = ANSWER_BOX_DIMENSIONS
                rois.append(
                    (
                        x_answer,
                        y_position + y1_offset,
                        x_answer + x2,
                        y_position + y2_offset,
                    )
                )

                # Update y_position
                y_positions[column] -= ROW_SPACING
                problem_index += 1

        return positions, rois

    @staticmethod
    def render_text(pdf, positions, rois, problems, answers=None, render_answers=False):
        """
        Render problems and optionally answers into the PDF.

        Args:
            pdf (Canvas): The PDF canvas.
            positions (list): Precomputed positions for problems [(x_problem, y, x_answer), ...].
            rois (list): Precomputed ROIs [(x1, y1, x2, y2), ...].
            problems (list): List of problems.
            answers (list, optional): List of answers. Defaults to None.
            render_answers (bool, optional): Whether to render answers. Defaults to False.
        """
        decoration_index = 0

        for i, ((x_problem, y, x_answer), roi) in enumerate(zip(positions, rois)):
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

            if render_answers:
                pdf.drawString(x_answer, y, f"{answer}")

            # Use ROI for bounding box (debugging or highlighting)
            x1, y1, x2, y2 = roi
            pdf.setStrokeColorRGB(1, 0, 0)  # Red color for debugging
            pdf.rect(x1, y1, x2 - x1, y2 - y1, stroke=1, fill=0)

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

        positions, rois = WorksheetRenderer.calculate_layout(
            problems, LayoutChoice.TWO_COLUMN
        )
        template_id = ROITemplateManager.find_or_create_template(rois)

        WorksheetRenderer.render_text(pdf, positions, rois, problems)

        pdf.save()
        return template_id

    @staticmethod
    def create_answer_key(filename, problems, answers, qr_code_stream):
        """Generate an answer key."""
        pdf = canvas.Canvas(filename, pagesize=portrait(letter))
        pdf.setFont("Helvetica", 18)

        pdf.drawString(200, 750, "Math Worksheet Answer Key")
        pdf.drawImage(ImageReader(qr_code_stream), 550, 700, width=40, height=40)

        positions, rois = WorksheetRenderer.calculate_layout(
            problems, LayoutChoice.TWO_COLUMN
        )

        WorksheetRenderer.render_text(
            pdf, positions, rois, problems, answers, render_answers=True
        )

        pdf.save()
