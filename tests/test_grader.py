from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.grader import AnswerGrader


@pytest.fixture
def sample_worksheet():
    """Fixture to create a sample worksheet for testing."""
    return {
        "id": "test_worksheet_1",
        "problems": [
            {"question": "2 + 2", "answer": "4", "roi": (100, 100, 200, 200)},
            {"question": "3 + 5", "answer": "8", "roi": (100, 250, 200, 350)},
        ],
    }


@pytest.fixture
def mock_image():
    """Fixture to create a mock image with simulated answers."""
    return np.zeros((1000, 1000), dtype=np.uint8)


def test_grade_answers():
    """Test the basic grading functionality."""
    # Test perfect score (100% -> A)
    student_answers = ["4", "8", "3"]
    correct_answers = ["4", "8", "3"]
    total_correct, total_questions, grade = AnswerGrader.grade_answers(
        student_answers, correct_answers
    )
    assert total_correct == 3
    assert total_questions == 3
    assert grade == "A"

    # Test partial correctness (66.67% -> D)
    student_answers = ["4", "7", "3"]
    correct_answers = ["4", "8", "3"]
    total_correct, total_questions, grade = AnswerGrader.grade_answers(
        student_answers, correct_answers
    )
    assert total_correct == 2
    assert total_questions == 3
    assert grade == "D"  # 66.67% falls between 60% (D) and 70% (C)


@patch("src.grader.TrOCRProcessor")
@patch("src.grader.VisionEncoderDecoderModel")
def test_parse_student_answers(mock_model_class, mock_processor_class, mock_image):
    """Test answer extraction with mocked OCR."""
    # Setup mocks
    mock_processor = MagicMock()
    mock_processor.batch_decode.return_value = ["4", "8"]
    mock_processor_class.from_pretrained.return_value = mock_processor

    mock_model = MagicMock()
    mock_model.generate.return_value = ["dummy_ids"]
    mock_model_class.from_pretrained.return_value = mock_model

    # Test answer extraction
    rois = [(100, 100, 200, 200), (100, 250, 200, 350)]
    with patch("PIL.Image.open") as mock_open:
        mock_open.return_value = MagicMock()
        answers = AnswerGrader.parse_student_answers("dummy_path.jpg", rois)
        assert len(answers) == 2
        assert all(isinstance(answer, str) for answer in answers)


def test_grade_scale():
    """Test grade scale boundaries."""
    test_cases = [
        (["1", "1"], ["1", "1"], "A"),  # 100% -> A
        (["1", "1", "1", "0"], ["1", "1", "1", "1"], "C"),  # 75% -> C
        (["1", "1", "0", "0"], ["1", "1", "1", "1"], "F"),  # 50% -> F
        (
            ["1", "1", "1", "1", "1", "1", "1", "0", "0", "0"],
            ["1"] * 10,
            "C",
        ),  # 70% -> C
    ]

    for student_answers, correct_answers, expected_grade in test_cases:
        _, _, grade = AnswerGrader.grade_answers(student_answers, correct_answers)
        assert grade == expected_grade
