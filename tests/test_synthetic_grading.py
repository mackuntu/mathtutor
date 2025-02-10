"""Test synthetic worksheet grading."""

import os
import tempfile
from pathlib import Path

import pytest
from pdf2image import convert_from_path
from PIL import Image

from src.core.grading import GradingService
from src.core.handwriting import HandwritingSimulator
from src.core.ocr import OCRConfig
from src.core.worksheet import Worksheet
from src.document.renderer import DocumentRenderer
from src.document.template import LayoutChoice, TemplateManager


@pytest.fixture
def sample_worksheet():
    """Create a sample worksheet with problems and answers."""
    # Create temporary files for worksheet and answer key
    worksheet_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    answer_key_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)

    # Generate problems and answers
    problems = [
        ("5 + 7", "12", (50, 680, 150, 720)),
        ("12 - 4", "8", (50, 640, 150, 680)),
        ("3 × 5", "15", (50, 600, 150, 640)),
        ("8 + 3", "11", (50, 560, 150, 600)),
        ("9 - 5", "4", (300, 680, 400, 720)),
        ("2 × 6", "12", (300, 640, 400, 680)),
        ("15 - 8", "7", (300, 600, 400, 640)),
        ("4 + 9", "13", (300, 560, 400, 600)),
        ("10 - 3", "7", (300, 520, 400, 560)),
        ("7 × 2", "14", (300, 480, 400, 520)),
    ]

    # Create worksheet
    renderer = DocumentRenderer()
    template_id = renderer.create_worksheet(
        worksheet_file.name,
        [p[0] for p in problems],
        worksheet_id="test_synthetic",
        layout=LayoutChoice.TWO_COLUMN,
    )
    renderer.create_answer_key(
        answer_key_file.name,
        [p[0] for p in problems],
        [p[1] for p in problems],
        worksheet_id="test_synthetic",
        layout=LayoutChoice.TWO_COLUMN,
    )

    # Create worksheet object with ROIs
    worksheet = Worksheet(
        id="test_synthetic",
        version="1.0",
        template_id=template_id,
    )
    for question, answer, roi in problems:
        worksheet.add_problem(question=question, answer=answer, roi=roi)

    return {
        "worksheet_path": worksheet_file.name,
        "answer_key_path": answer_key_file.name,
        "problems": [p[0] for p in problems],
        "answers": [p[1] for p in problems],
        "rois": [p[2] for p in problems],
        "template_id": template_id,
        "worksheet": worksheet,
    }


@pytest.fixture
def handwriting_fonts():
    """Get list of available handwriting fonts."""
    return [
        "data/fonts/Childrens-Handwriting.ttf",
        "data/fonts/KidsHandwriting.ttf",
        "data/fonts/MessyHandwriting.ttf",
    ]


def create_synthetic_filled_worksheet(worksheet_data, font_path, accuracy=1.0):
    """Create a synthetic filled worksheet using handwriting simulation.

    Args:
        worksheet_data: Dictionary containing worksheet information.
        font_path: Path to font file for handwriting simulation.
        accuracy: Probability of writing correct answers (0.0 to 1.0).

    Returns:
        Path to filled worksheet image.
    """
    # Create handwriting simulator with specified font
    simulator = HandwritingSimulator(font_paths=[font_path])

    # Create grading service
    config = OCRConfig(
        model_name="microsoft/trocr-small-handwritten",
        device="cpu",
        min_confidence=-20,
        max_new_tokens=5,
    )
    grading_service = GradingService(ocr_config=config)

    # Generate synthetic answers
    answer_images = grading_service.simulate_student_answers(
        worksheet_data["worksheet"], accuracy=accuracy, simulator=simulator
    )

    # Convert PDF to image
    worksheet_images = convert_from_path(worksheet_data["worksheet_path"])
    worksheet_image = worksheet_images[0]  # Get first page

    # Create output image
    output_path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name

    # Composite answer images onto worksheet
    for i, answer_image in enumerate(answer_images):
        x, y = worksheet_data["rois"][i][:2]  # Get position from ROI
        worksheet_image.paste(answer_image, (int(x), int(y)), answer_image)

    worksheet_image.save(output_path)
    return output_path


def test_synthetic_grading_perfect(sample_worksheet, handwriting_fonts):
    """Test grading with synthetic perfectly filled worksheets."""
    config = OCRConfig(
        model_name="microsoft/trocr-small-handwritten",
        device="cpu",
        min_confidence=-20,
        max_new_tokens=5,
    )
    grading_service = GradingService(ocr_config=config)

    for font_path in handwriting_fonts:
        # Create synthetic filled worksheet with perfect accuracy
        filled_worksheet_path = create_synthetic_filled_worksheet(
            sample_worksheet, font_path, accuracy=1.0
        )

        # Grade the worksheet
        worksheet = sample_worksheet["worksheet"]
        filled_image = Image.open(filled_worksheet_path)
        grading_service.grade_worksheet(worksheet, [filled_image])

        # Check results
        assert worksheet.grade == "A"
        assert worksheet.total_correct == len(sample_worksheet["problems"])

        # Cleanup
        os.unlink(filled_worksheet_path)


def test_synthetic_grading_partial(sample_worksheet, handwriting_fonts):
    """Test grading with synthetic partially correct worksheets."""
    config = OCRConfig(
        model_name="microsoft/trocr-small-handwritten",
        device="cpu",
        min_confidence=-20,
        max_new_tokens=5,
    )
    grading_service = GradingService(ocr_config=config)

    accuracies = [0.8, 0.7, 0.6]  # Should result in B, C, D grades
    expected_grades = ["B", "C", "D"]

    for font_path in handwriting_fonts:
        for accuracy, expected_grade in zip(accuracies, expected_grades):
            # Create synthetic filled worksheet with partial accuracy
            filled_worksheet_path = create_synthetic_filled_worksheet(
                sample_worksheet, font_path, accuracy=accuracy
            )

            # Grade the worksheet
            worksheet = sample_worksheet["worksheet"]
            filled_image = Image.open(filled_worksheet_path)
            grading_service.grade_worksheet(worksheet, [filled_image])

            # Check results
            assert worksheet.grade == expected_grade
            expected_correct = int(accuracy * len(sample_worksheet["problems"]))
            assert abs(worksheet.total_correct - expected_correct) <= 1

            # Cleanup
            os.unlink(filled_worksheet_path)


def test_synthetic_grading_messy_placement(sample_worksheet, handwriting_fonts):
    """Test grading with synthetic worksheets where answers are messily placed."""
    config = OCRConfig(
        model_name="microsoft/trocr-small-handwritten",
        device="cpu",
        min_confidence=-20,
        max_new_tokens=5,
    )
    grading_service = GradingService(ocr_config=config)

    for font_path in handwriting_fonts:
        # Create synthetic filled worksheet with random placement offsets
        filled_worksheet_path = create_synthetic_filled_worksheet(
            sample_worksheet, font_path, accuracy=1.0
        )

        # Grade the worksheet
        worksheet = sample_worksheet["worksheet"]
        filled_image = Image.open(filled_worksheet_path)
        grading_service.grade_worksheet(worksheet, [filled_image])

        # Even with messy placement, OCR should still work
        assert worksheet.total_correct > 0
        assert worksheet.grade is not None

        # Cleanup
        os.unlink(filled_worksheet_path)
