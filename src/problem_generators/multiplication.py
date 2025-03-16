"""Strategies for generating multiplication and division problems."""

import random
from typing import Tuple

from src.problem_strategy import ProblemStrategy, adjust_range_by_difficulty
from src.problem_types import OPERATORS


class MultiplicationStrategy(ProblemStrategy):
    """Strategy for generating multiplication problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate a multiplication problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        min_val, max_val = adjust_range_by_difficulty(min_val, max_val, difficulty, age)

        num1 = random.randint(min_val, max_val)
        num2 = random.randint(min_val, max_val)

        operator = OPERATORS["multiplication"]
        problem = f"{num1} {operator} {num2}"
        answer = num1 * num2

        return problem, str(answer)


class DivisionStrategy(ProblemStrategy):
    """Strategy for generating division problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate a division problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        min_val, max_val = adjust_range_by_difficulty(min_val, max_val, difficulty, age)

        # Generate division problems with whole number answers
        answer = random.randint(min_val, max_val)
        num2 = random.randint(min_val, max_val)
        num1 = answer * num2

        operator = OPERATORS["division"]
        problem = f"{num1} {operator} {num2}"

        return problem, str(answer)
