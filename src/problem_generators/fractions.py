"""Strategies for generating fraction problems."""

import random
from typing import Tuple

from src.problem_strategy import ProblemStrategy, adjust_range_by_difficulty


class FractionStrategy(ProblemStrategy):
    """Strategy for generating fraction problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate a fraction problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        min_val, max_val = adjust_range_by_difficulty(min_val, max_val, difficulty, age)

        denominator = random.randint(2, max_val)
        numerator = random.randint(1, denominator)
        problem = f"{numerator}/{denominator}"

        return problem, str(round(numerator / denominator, 3))
