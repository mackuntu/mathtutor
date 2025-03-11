"""Tests for the problem generator."""

import pytest

from src.generator import ProblemGenerator


def test_age_5_problem_ranges():
    """Test that age 5 problems use appropriate ranges based on difficulty."""
    generator = ProblemGenerator(seed=42)  # Use a fixed seed for reproducibility

    # Test low difficulty (should use numbers 1-10)
    problems, answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.2
    )
    for problem in problems:
        # Extract numbers from the problem
        parts = problem.split()
        num1 = int(parts[0])
        num2 = int(parts[2])

        # Check that numbers are within expected range
        assert (
            1 <= num1 <= 10
        ), f"Number {num1} in problem {problem} is outside expected range for low difficulty"
        assert (
            1 <= num2 <= 10
        ), f"Number {num2} in problem {problem} is outside expected range for low difficulty"

    # Test medium difficulty (should use numbers 1-15)
    problems, answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.5
    )
    for problem in problems:
        # Extract numbers from the problem
        parts = problem.split()
        num1 = int(parts[0])
        num2 = int(parts[2])

        # Check that numbers are within expected range
        assert (
            1 <= num1 <= 15
        ), f"Number {num1} in problem {problem} is outside expected range for medium difficulty"
        assert (
            1 <= num2 <= 15
        ), f"Number {num2} in problem {problem} is outside expected range for medium difficulty"

    # Test high difficulty (should use numbers 1-20)
    problems, answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.8
    )
    for problem in problems:
        # Extract numbers from the problem
        parts = problem.split()
        num1 = int(parts[0])
        num2 = int(parts[2])

        # Check that numbers are within expected range
        assert (
            1 <= num1 <= 20
        ), f"Number {num1} in problem {problem} is outside expected range for high difficulty"
        assert (
            1 <= num2 <= 20
        ), f"Number {num2} in problem {problem} is outside expected range for high difficulty"


def test_age_5_vs_age_6():
    """Test that age 5 and age 6 problems are appropriately differentiated."""
    generator = ProblemGenerator(seed=42)  # Use a fixed seed for reproducibility

    # Generate problems for age 5 and age 6 at the same difficulty
    age5_problems, age5_answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.8
    )
    age6_problems, age6_answers = generator.generate_math_problems(
        age=6, count=20, difficulty=0.8
    )

    # Check that age 5 problems use numbers up to 20
    for problem in age5_problems:
        parts = problem.split()
        num1 = int(parts[0])
        num2 = int(parts[2])
        assert (
            1 <= num1 <= 20
        ), f"Number {num1} in age 5 problem {problem} is outside expected range"
        assert (
            1 <= num2 <= 20
        ), f"Number {num2} in age 5 problem {problem} is outside expected range"

    # Check that age 6 problems can use numbers beyond 20 at high difficulty
    has_larger_numbers = False
    for problem in age6_problems:
        parts = problem.split()
        num1 = int(parts[0])
        num2 = int(parts[2])
        if num1 > 20 or num2 > 20:
            has_larger_numbers = True
            break

    # At high difficulty, age 6 should have at least some problems with numbers > 20
    assert (
        has_larger_numbers
    ), "Age 6 problems at high difficulty should include some numbers > 20"


def test_age_5_problem_distribution():
    """Test that age 5 problems have an appropriate distribution of addition and subtraction."""
    generator = ProblemGenerator(seed=42)  # Use a fixed seed for reproducibility

    # Generate problems at different difficulty levels
    low_problems, _ = generator.generate_math_problems(age=5, count=100, difficulty=0.2)
    med_problems, _ = generator.generate_math_problems(age=5, count=100, difficulty=0.5)
    high_problems, _ = generator.generate_math_problems(
        age=5, count=100, difficulty=0.8
    )

    # Count addition and subtraction problems
    low_add = sum(1 for p in low_problems if "+" in p)
    low_sub = sum(1 for p in low_problems if "-" in p)

    med_add = sum(1 for p in med_problems if "+" in p)
    med_sub = sum(1 for p in med_problems if "-" in p)

    high_add = sum(1 for p in high_problems if "+" in p)
    high_sub = sum(1 for p in high_problems if "-" in p)

    # At low difficulty, should have more addition than subtraction
    assert (
        low_add > low_sub
    ), f"Expected more addition than subtraction at low difficulty, got {low_add} addition and {low_sub} subtraction"

    # At medium difficulty, should be more balanced
    assert (
        0.4 <= med_add / 100 <= 0.6
    ), f"Expected balanced distribution at medium difficulty, got {med_add}% addition"
    assert (
        0.4 <= med_sub / 100 <= 0.6
    ), f"Expected balanced distribution at medium difficulty, got {med_sub}% subtraction"

    # At high difficulty, should be roughly equal
    assert (
        0.4 <= high_add / 100 <= 0.6
    ), f"Expected balanced distribution at high difficulty, got {high_add}% addition"
    assert (
        0.4 <= high_sub / 100 <= 0.6
    ), f"Expected balanced distribution at high difficulty, got {high_sub}% subtraction"
