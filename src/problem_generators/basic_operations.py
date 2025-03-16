"""Strategies for generating addition and subtraction problems."""

import random
from typing import Tuple

from src.problem_strategy import ProblemStrategy, adjust_range_by_difficulty
from src.problem_types import OPERATORS


class AdditionStrategy(ProblemStrategy):
    """Strategy for generating addition problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate an addition problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        min_val, max_val = adjust_range_by_difficulty(min_val, max_val, difficulty, age)

        # For age 5, ensure the sum is within their range
        if age == 5:
            # For lower difficulties, keep one number single-digit
            if difficulty <= 0.5:
                num1 = random.randint(min_val, 9)
                num2 = random.randint(min_val, min(max_val - num1, max_val))
            else:
                # For higher difficulties, allow both numbers to be double-digit
                num1 = random.randint(min_val, max_val - 1)
                num2 = random.randint(min_val, min(max_val - num1, max_val))
        else:
            # Generate both numbers in the full range
            num1 = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)

        operator = OPERATORS["addition"]
        problem = f"{num1} {operator} {num2}"
        answer = num1 + num2

        return problem, str(answer)


class SubtractionStrategy(ProblemStrategy):
    """Strategy for generating subtraction problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate a subtraction problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        min_val, max_val = adjust_range_by_difficulty(min_val, max_val, difficulty, age)

        # For age 5, ensure the difference is appropriate
        if age == 5:
            # For subtraction, ensure first number is larger and result is positive
            if difficulty <= 0.5:
                # For lower difficulties, keep second number single-digit
                num2 = random.randint(min_val, 9)
                num1 = random.randint(num2 + 1, max_val)
            else:
                # For higher difficulties, allow both numbers to be double-digit
                num1 = random.randint(min_val + 1, max_val)
                num2 = random.randint(min_val, num1 - 1)
        else:
            # Generate both numbers in the full range
            num1 = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)

            # Ensure first number is larger
            num1, num2 = max(num1, num2), min(num1, num2)

        operator = OPERATORS["subtraction"]
        problem = f"{num1} {operator} {num2}"
        answer = num1 - num2

        return problem, str(answer)
