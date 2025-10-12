"""Base strategy for problem generation."""

from abc import ABC, abstractmethod
from typing import Tuple


class ProblemStrategy(ABC):
    """Base strategy for generating math problems."""

    @abstractmethod
    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate a math problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        pass


def adjust_range_by_difficulty(
    min_val: int, max_val: int, difficulty: float, age: int
) -> Tuple[int, int]:
    """Adjust number range based on difficulty level.

    Args:
        min_val: Minimum value for the range
        max_val: Maximum value for the range
        difficulty: Difficulty level from 0.0 to 1.0
        age: Student age for context-appropriate scaling

    Returns:
        Tuple of (adjusted_min, adjusted_max)
    """
    from src.problem_types import PROBLEM_TYPES

    range_size = max_val - min_val

    # For age 5, provide a more gradual progression to double-digit numbers
    if age == 5:
        if difficulty <= 0.3:
            # Very easy: numbers 1-5
            return 1, 5
        elif difficulty <= 0.6:
            # Medium: numbers 1-7
            return 1, 7
        else:
            # Hard: numbers 1-10
            return 1, 10
    else:
        # Scale ranges more aggressively with difficulty
        if difficulty > 0.5:  # For higher difficulties, extend the maximum
            extension_factor = 1.0 + (difficulty - 0.5) * 1.5  # Up to 1.5x extension
            adjusted_max = int(max_val * extension_factor)
        else:
            adjusted_max = max_val

        # Adjust minimum value to make problems harder
        if difficulty > 0.7:  # For very high difficulties, raise the minimum
            adjusted_min = min_val + int(range_size * 0.2)  # Start from 20% of range
        else:
            adjusted_min = min_val

        # Ensure we don't have invalid ranges
        if adjusted_min >= adjusted_max:
            adjusted_min = min_val
            adjusted_max = max_val

        return int(adjusted_min), int(adjusted_max)
