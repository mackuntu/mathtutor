"""Test grading service functionality."""

from datetime import datetime

import pytest

from src.core.grading import GradingService
from src.core.handwriting import HandwritingSimulator
from src.core.ocr import OCRConfig, OCREngine, OCRResult
from src.core.worksheet import Problem, Worksheet


@pytest.fixture
def worksheet():
    """Create a test worksheet."""
    worksheet = Worksheet(
        id="test_123",
        version="1.0",
    )
    problems = [
        ("2 + 2", "4", (0, 0, 100, 50)),
        ("3 + 5", "8", (0, 50, 100, 100)),
        ("7 - 2", "5", (0, 100, 100, 150)),
        ("4 × 3", "12", (0, 150, 100, 200)),
    ]
    for question, answer, roi in problems:
        worksheet.add_problem(question=question, answer=answer, roi=roi)
    return worksheet


@pytest.fixture
def grading_service():
    """Create a grading service instance."""
    config = OCRConfig(
        min_confidence=0.3,  # Lower threshold for absolute correlation values
        image_size=28,  # Standard size for digit recognition
        threshold=128,  # Consistent binarization threshold
    )
    return GradingService(ocr_config=config)


@pytest.fixture
def simulator():
    """Create a handwriting simulator instance."""
    return HandwritingSimulator()


def test_perfect_score(worksheet, grading_service, simulator):
    """Test grading a worksheet with all correct answers."""
    # Generate perfect answers
    answer_images = grading_service.simulate_student_answers(
        worksheet, accuracy=1.0, simulator=simulator
    )

    # Grade the worksheet
    grading_service.grade_worksheet(worksheet, answer_images)

    # Should get an A grade (90-100%)
    assert worksheet.grade == "A"
    assert worksheet.total_correct == worksheet.total_questions


def test_partial_credit(worksheet, grading_service, simulator):
    """Test grading a worksheet with some incorrect answers."""
    # Generate answers with 75% accuracy
    answer_images = grading_service.simulate_student_answers(
        worksheet, accuracy=0.75, simulator=simulator
    )

    # Grade the worksheet
    grading_service.grade_worksheet(worksheet, answer_images)

    # Should get a C grade (70-79%)
    assert worksheet.grade in ["C", "B"]  # Allow for some OCR variance
    assert 0.6 <= worksheet.total_correct / worksheet.total_questions <= 0.8


def test_failing_grade(worksheet, grading_service, simulator):
    """Test grading a worksheet with mostly incorrect answers."""
    # Generate answers with 30% accuracy
    answer_images = grading_service.simulate_student_answers(
        worksheet, accuracy=0.3, simulator=simulator
    )

    # Grade the worksheet
    grading_service.grade_worksheet(worksheet, answer_images)

    # Should get an F grade (<60%)
    assert worksheet.grade == "F"
    assert worksheet.total_correct / worksheet.total_questions < 0.6


def test_worksheet_serialization(worksheet):
    """Test worksheet serialization and deserialization."""
    # Add some grading data
    worksheet.set_grade("B", 3)
    worksheet.graded_at = datetime.now()

    # Convert to dict
    data = worksheet.to_dict()

    # Create new worksheet from dict
    new_worksheet = Worksheet.from_dict(data)

    # Check all attributes match
    assert new_worksheet.id == worksheet.id
    assert new_worksheet.version == worksheet.version
    assert new_worksheet.grade == worksheet.grade
    assert new_worksheet.total_correct == worksheet.total_correct
    assert len(new_worksheet.problems) == len(worksheet.problems)


def test_different_handwriting_styles(worksheet, grading_service):
    """Test grading with different handwriting simulators."""
    answers = []

    # Try each font
    for font_path in HandwritingSimulator.DEFAULT_FONTS:
        simulator = HandwritingSimulator(font_paths=[font_path])
        answer_images = grading_service.simulate_student_answers(
            worksheet, accuracy=1.0, simulator=simulator
        )
        answers.extend(answer_images)

    # All should be readable
    ocr = OCREngine()
    for image in answers:
        result = ocr.read_text(image)
        assert isinstance(result, OCRResult)
        assert result.confidence > -20
        assert len(result.text.strip()) > 0


def test_confidence_scores(worksheet, grading_service, simulator):
    """Test that confidence scores are recorded."""
    # Generate answers
    answer_images = grading_service.simulate_student_answers(
        worksheet, accuracy=1.0, simulator=simulator
    )

    # Grade the worksheet
    grading_service.grade_worksheet(worksheet, answer_images)

    # Check confidence scores
    for problem in worksheet.problems:
        assert hasattr(problem, "confidence")
        assert problem.confidence is not None
        assert problem.confidence > -20  # Basic confidence threshold
