"""Tests for new worksheet features."""

import json
from datetime import datetime

import pytest

from src.database.models import Worksheet
from src.generator import ProblemGenerator


def test_worksheet_serial_number():
    """Test that worksheets are created with a serial number."""
    worksheet = Worksheet(
        child_id="test_child",
        problems=[{"text": "1 + 1"}, {"text": "2 + 2"}],
    )
    assert worksheet.id is not None
    assert isinstance(worksheet.id, str)


def test_incorrect_problems_tracking():
    """Test tracking of incorrect problems."""
    worksheet = Worksheet(
        child_id="test_child",
        problems=[{"text": "1 + 1"}, {"text": "2 + 2"}, {"text": "3 + 3"}],
    )

    # Initially no answers
    assert worksheet.answers is None

    # Add some answers
    worksheet.answers = [2, 4, 7]  # Last one is wrong
    worksheet.completed = True

    # Convert to item and back to verify persistence
    data = worksheet.to_item()
    restored = Worksheet.from_item(data)

    assert restored.answers == [2, 4, 7]
    assert restored.completed is True


def test_age_5_problem_generation():
    """Test problem generation for age 5."""
    generator = ProblemGenerator(seed=42)  # Use seed for reproducibility
    problems, answers = generator.generate_math_problems(age=5, count=10)

    assert len(problems) == 10
    assert len(answers) == 10

    for problem, answer in zip(problems, answers):
        # Check that problems only contain addition and subtraction
        assert any(op in problem for op in ["+", "-"])
        # Check that numbers are within appropriate range (1-10)
        nums = [int(n) for n in problem.replace("+", " ").replace("-", " ").split()]
        assert all(1 <= n <= 10 for n in nums)
        # For addition, check sum is within range
        if "+" in problem:
            assert int(answer) <= 10
        # For subtraction, check result is positive
        if "-" in problem:
            assert int(answer) >= 0


def test_age_5_difficulty_levels():
    """Test different difficulty levels for age 5."""
    generator = ProblemGenerator(seed=42)

    # Test easy difficulty (0.0)
    problems, answers = generator.generate_math_problems(
        age=5, count=10, difficulty=0.0
    )
    for problem in problems:
        nums = [int(n) for n in problem.replace("+", " ").replace("-", " ").split()]
        assert all(1 <= n <= 5 for n in nums)  # Should use numbers 1-5

    # Test medium difficulty (0.5)
    problems, answers = generator.generate_math_problems(
        age=5, count=10, difficulty=0.5
    )
    for problem in problems:
        nums = [int(n) for n in problem.replace("+", " ").replace("-", " ").split()]
        assert all(1 <= n <= 7 for n in nums)  # Should use numbers 1-7

    # Test hard difficulty (1.0)
    problems, answers = generator.generate_math_problems(
        age=5, count=10, difficulty=1.0
    )
    for problem in problems:
        nums = [int(n) for n in problem.replace("+", " ").replace("-", " ").split()]
        assert all(1 <= n <= 10 for n in nums)  # Should use numbers 1-10


def test_multiple_worksheet_generation(repository, test_child_dynamodb):
    """Test generating multiple worksheets at once."""
    # Generate 3 worksheets
    worksheets = []
    for _ in range(3):
        worksheet = Worksheet(
            child_id=test_child_dynamodb.id,
            problems=[{"text": "1 + 1"}, {"text": "2 + 2"}],
        )
        repository.create_worksheet(worksheet)
        worksheets.append(worksheet)

    # Verify all worksheets were created with unique IDs
    worksheet_ids = set()
    for worksheet in worksheets:
        assert worksheet.id is not None
        assert worksheet.id not in worksheet_ids
        worksheet_ids.add(worksheet.id)

    # Verify we can retrieve all worksheets for the child
    child_worksheets = repository.get_child_worksheets(test_child_dynamodb.id)
    assert len(child_worksheets) == 3
    assert all(w.id in worksheet_ids for w in child_worksheets)
