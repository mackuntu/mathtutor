"""Base strategy for problem generation."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple


def make_operands(text: str) -> Dict[str, str]:
    """Two-operand arithmetic problem rendered with the legacy vertical layout.

    This is the ``kind == "operands"`` branch in ``problem_grid.html`` and keeps
    the byte-for-byte layout that existing worksheets rely on.
    """
    return {"text": text, "kind": "operands"}


def make_expression(text: str, prompt: Optional[str] = None) -> Dict[str, str]:
    """Inline expression rendered as-is (no operator split).

    Used for order-of-operations, missing-operand, roman numerals, conversions,
    place value, etc. ``prompt`` is an optional tiny instruction line.
    """
    problem: Dict[str, str] = {"text": text, "kind": "expression"}
    if prompt:
        problem["prompt"] = prompt
    return problem


def make_visual(
    svg: str, prompt: Optional[str] = None, text: str = ""
) -> Dict[str, str]:
    """Tiny inline-SVG problem (geometry, graphing, clock, fraction-identify)."""
    problem: Dict[str, str] = {"text": text, "kind": "visual", "svg": svg}
    if prompt:
        problem["prompt"] = prompt
    return problem


class ProblemStrategy(ABC):
    """Base strategy for generating math problems."""

    @abstractmethod
    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        """Generate a math problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem_dict, answer). The dict always has ``text`` and
            ``kind`` keys (see ``make_operands`` / ``make_expression`` /
            ``make_visual``).
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
    # Ensure we have valid input ranges
    if min_val >= max_val:
        return max(1, min_val), max(min_val + 1, max_val)

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
        # Scale ranges more conservatively with difficulty
        if difficulty > 0.5:  # For higher difficulties, extend the maximum
            extension_factor = (
                1.0 + (difficulty - 0.5) * 0.5
            )  # Up to 0.5x extension (more conservative)
            adjusted_max = int(max_val * extension_factor)
        else:
            adjusted_max = max_val

        # Adjust minimum value to make problems harder
        if difficulty > 0.7:  # For very high difficulties, raise the minimum
            adjusted_min = min_val + int(
                range_size * 0.1
            )  # Start from 10% of range (more conservative)
        else:
            adjusted_min = min_val

        # Ensure we don't have invalid ranges
        if adjusted_min >= adjusted_max:
            adjusted_min = min_val
            adjusted_max = max_val

        # Final safety check
        if adjusted_min >= adjusted_max:
            adjusted_min = 1
            adjusted_max = max(2, max_val)

        return int(adjusted_min), int(adjusted_max)
