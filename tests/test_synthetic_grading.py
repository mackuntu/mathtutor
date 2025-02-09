import os
import tempfile
from datetime import datetime
from io import BytesIO

import cv2
import numpy as np
import pytest
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont

from src.db_handler import DatabaseHandler
from src.grader import AnswerGrader
from src.problem_generator import ProblemGenerator
from src.renderer import WorksheetRenderer
from src.utils.marker_utils import MarkerUtils


@pytest.fixture
def handwriting_fonts():
    """Fixture providing a list of handwriting-like fonts."""
    return [
        "data/fonts/Childrens-Handwriting.ttf",
        "data/fonts/KidsHandwriting.ttf",
        "data/fonts/MessyHandwriting.ttf",
    ]


@pytest.fixture
def sample_worksheet():
    """Generate a sample worksheet with known problems and answers."""
    generator = ProblemGenerator()
    problems, answers = generator.generate_math_problems(age=6)

    # Create temporary files for worksheet and answer key
    with tempfile.NamedTemporaryFile(
        suffix=".pdf", delete=False
    ) as worksheet_file, tempfile.NamedTemporaryFile(
        suffix=".pdf", delete=False
    ) as answer_key_file:

        # Create QR code
        worksheet_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        qr_code = WorksheetRenderer.create_qr_code(worksheet_id, "1.0")

        # Generate worksheet and answer key
        template_id = WorksheetRenderer.create_math_worksheet(
            worksheet_file.name, problems, qr_code
        )
        WorksheetRenderer.create_answer_key(
            answer_key_file.name, problems, answers, qr_code
        )

        # Save worksheet data to database
        DatabaseHandler.save_worksheet(
            worksheet_id, "1.0", problems, answers, template_id
        )

        yield {
            "worksheet_path": worksheet_file.name,
            "answer_key_path": answer_key_file.name,
            "problems": problems,
            "answers": answers,
            "worksheet_id": worksheet_id,
            "version": "1.0",
            "template_id": template_id,
        }

        # Cleanup
        os.unlink(worksheet_file.name)
        os.unlink(answer_key_file.name)


def create_synthetic_filled_worksheet(worksheet_info, font_path, accuracy=1.0):
    """
    Create a synthetic filled worksheet using a handwriting-like font.
    """
    # Convert PDF to image with high DPI for better QR code and marker recognition
    pdf_path = worksheet_info["worksheet_path"]
    images = convert_from_path(
        pdf_path,
        dpi=300,
        fmt="png",
        size=(2550, 3300),  # Letter size at 300 DPI (8.5x11 inches)
        use_cropbox=False,  # Use MediaBox instead of CropBox
        transparent=False,  # Disable transparency
        grayscale=False,  # Keep color information
        thread_count=1,  # Single thread for better consistency
        first_page=1,
        last_page=1,
        strict=True,  # Strict PDF parsing
        poppler_path=None,  # Use system poppler
        output_folder=None,  # No output folder needed
        use_pdftocairo=True,  # Use pdftocairo for better quality
        output_file=None,  # No output file needed
        paths_only=False,  # Return PIL images
    )

    if not images:
        raise ValueError("Failed to convert PDF to image")

    # We only need the first page
    image = images[0]

    # Create a temporary file for the filled worksheet
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        draw = ImageDraw.Draw(image)

        # Load handwriting font
        try:
            font = ImageFont.truetype(font_path, size=36)  # Larger font size
        except OSError:
            print(f"Warning: Could not load font {font_path}, using default")
            font = ImageFont.load_default()

        # Get ROIs from template
        rois = DatabaseHandler.fetch_roi_template(worksheet_info["template_id"])

        # Fill in answers with some randomization
        for roi, answer in zip(rois, worksheet_info["answers"]):
            x1, y1, x2, y2 = roi

            # Scale ROI coordinates for higher DPI
            x1, y1, x2, y2 = [int(coord * 300 / 72) for coord in [x1, y1, x2, y2]]

            # Randomly decide whether to write the correct answer based on accuracy
            if np.random.random() < accuracy:
                text = str(answer)
            else:
                # Write an incorrect answer (within reasonable range)
                text = str(int(answer) + np.random.randint(1, 5))

            # Add some random offset to simulate messy handwriting
            x_offset = np.random.randint(
                -10, 10
            )  # Reduced range for better readability
            y_offset = np.random.randint(-10, 10)

            # Calculate center position for text
            text_width = draw.textlength(text, font=font)
            text_x = x1 + (x2 - x1 - text_width) / 2 + x_offset
            text_y = y1 + (y2 - y1 - font.size) / 2 + y_offset

            # Draw the text
            draw.text((text_x, text_y), text, font=font, fill="black")

        # Save the image with high quality
        image.save(img_file.name, "PNG", dpi=(300, 300), quality=95)

        # Debug: Save a copy of the image for inspection
        debug_path = "debug_worksheet.png"
        image.save(debug_path, "PNG", dpi=(300, 300), quality=95)
        print(f"Debug: Saved worksheet image to {debug_path}")

        # Debug: Save a grayscale version for marker detection testing
        gray_image = image.convert("L")
        gray_image.save("debug_worksheet_gray.png", "PNG", dpi=(300, 300), quality=95)
        print("Debug: Saved grayscale version to debug_worksheet_gray.png")

        # Debug: Try to detect markers in the saved image
        try:
            markers = MarkerUtils.detect_alignment_markers(img_file.name)
            print(f"Debug: Successfully detected {len(markers)} markers")
            print(f"Debug: Marker positions: {markers}")
        except Exception as e:
            print(f"Debug: Failed to detect markers: {str(e)}")

        return img_file.name


def test_synthetic_grading_perfect(sample_worksheet, handwriting_fonts):
    """Test grading with synthetic perfectly filled worksheets."""
    for font_path in handwriting_fonts:
        # Create synthetic filled worksheet with perfect accuracy
        filled_worksheet_path = create_synthetic_filled_worksheet(
            sample_worksheet, font_path, accuracy=1.0
        )

        # Grade the worksheet
        result = AnswerGrader.grade_worksheet(filled_worksheet_path)

        # Check results
        assert result["grade"] == "A"
        assert result["total_correct"] == result["total_questions"]

        # Cleanup
        os.unlink(filled_worksheet_path)


def test_synthetic_grading_partial(sample_worksheet, handwriting_fonts):
    """Test grading with synthetic partially correct worksheets."""
    accuracies = [0.8, 0.7, 0.6]  # Should result in B, C, D grades
    expected_grades = ["B", "C", "D"]

    for font_path in handwriting_fonts:
        for accuracy, expected_grade in zip(accuracies, expected_grades):
            # Create synthetic filled worksheet with partial accuracy
            filled_worksheet_path = create_synthetic_filled_worksheet(
                sample_worksheet, font_path, accuracy=accuracy
            )

            # Grade the worksheet
            result = AnswerGrader.grade_worksheet(filled_worksheet_path)

            # Check results
            assert result["grade"] == expected_grade
            assert result["total_correct"] < result["total_questions"]

            # Cleanup
            os.unlink(filled_worksheet_path)


def test_synthetic_grading_messy_placement(sample_worksheet, handwriting_fonts):
    """Test grading with synthetic worksheets where answers are messily placed."""
    for font_path in handwriting_fonts:
        # Create synthetic filled worksheet with random placement offsets
        filled_worksheet_path = create_synthetic_filled_worksheet(
            sample_worksheet, font_path, accuracy=1.0
        )

        # Grade the worksheet
        result = AnswerGrader.grade_worksheet(filled_worksheet_path)

        # Even with messy placement, OCR should still work
        assert result["total_correct"] > 0

        # Cleanup
        os.unlink(filled_worksheet_path)
