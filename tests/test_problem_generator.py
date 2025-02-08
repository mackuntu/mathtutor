from unittest.mock import patch

import pytest

from src.problem_generator import ProblemGenerator
from src.problem_templates import ProblemTemplates


@pytest.fixture
def problem_generator():
    """Fixture to create a problem generator instance."""
    return ProblemGenerator()


def test_generate_math_problems():
    """Test generation of math problems."""
    generator = ProblemGenerator()
    questions, answers = generator.generate_math_problems(age=6)

    assert isinstance(questions, list)
    assert isinstance(answers, list)
    assert len(questions) == len(answers)
    assert len(questions) > 0


def test_problem_difficulty_progression():
    """Test that problems get progressively harder through the school year."""
    generator = ProblemGenerator()

    # Mock different months to test progression
    with patch("src.problem_generator.datetime") as mock_datetime:
        # September (early in school year)
        mock_datetime.now.return_value.month = 9
        early_questions, early_answers = generator.generate_math_problems(age=6)

        # May (late in school year)
        mock_datetime.now.return_value.month = 5
        late_questions, late_answers = generator.generate_math_problems(age=6)

        # Late year problems should be more complex
        assert len(late_questions) >= len(early_questions)


def test_age_appropriate_problems():
    """Test that problems are appropriate for the given age."""
    generator = ProblemGenerator()

    # Test for 6-year-old
    questions, answers = generator.generate_math_problems(age=6)

    # Check if problems are appropriate (e.g., simple arithmetic)
    for question in questions:
        # Should only contain basic arithmetic operators
        assert any(op in question for op in ["+", "-", "×", "÷"])
        # Should not contain complex mathematical notation
        assert not any(
            complex_op in question for complex_op in ["^", "√", "sin", "cos"]
        )


def test_answer_validation():
    """Test that generated problems have correct answers."""
    generator = ProblemGenerator()
    questions, answers = generator.generate_math_problems(age=6)

    # Test a few sample calculations
    for question, expected_answer in zip(questions[:5], answers[:5]):
        # Parse and evaluate the question
        if "+" in question:
            nums = [int(n.strip()) for n in question.split("+")]
            calculated_answer = sum(nums)
        elif "-" in question:
            nums = [int(n.strip()) for n in question.split("-")]
            calculated_answer = nums[0] - nums[1]
        elif "×" in question:
            nums = [int(n.strip()) for n in question.split("×")]
            calculated_answer = nums[0] * nums[1]
        elif "÷" in question:
            nums = [int(n.strip()) for n in question.split("÷")]
            calculated_answer = nums[0] // nums[1]

        assert calculated_answer == expected_answer


def test_school_year_month_calculation():
    """Test the calculation of school year month."""
    generator = ProblemGenerator()

    # Test different months
    test_cases = [
        (8, 1),  # August -> Month 1
        (12, 5),  # December -> Month 5
        (1, 6),  # January -> Month 6
        (5, 10),  # May -> Month 10
    ]

    for month, expected_school_month in test_cases:
        with patch("src.problem_generator.datetime") as mock_datetime:
            mock_datetime.now.return_value.month = month
            assert generator.get_school_year_month() == expected_school_month
