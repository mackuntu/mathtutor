"""Strategies for generating fraction problems."""

import random
from math import gcd
from typing import Dict, Tuple

from src.problem_strategy import (
    ProblemStrategy,
    adjust_range_by_difficulty,
    make_expression,
    make_operands,
    make_visual,
)


def _fraction_bar_svg(num: int, den: int) -> str:
    """A horizontal bar split into ``den`` cells with ``num`` shaded."""
    width = 56
    height = 22
    cell = width / den
    cells = []
    for i in range(den):
        x = i * cell
        fill = "#4a7fb5" if i < num else "white"
        cells.append(
            f'<rect x="{x:.2f}" y="0" width="{cell:.2f}" height="{height}" '
            f'fill="{fill}" stroke="black" stroke-width="1"/>'
        )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(cells)}</svg>'
    )


class FractionStrategy(ProblemStrategy):
    """Strategy for generating fraction problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        """Generate a fraction problem.

        Grade 3 (age 8) gets a mix of compare / equivalent / like-denominator
        add-sub / identify (visual). Ages 9+ keep the original decimal behavior.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem_dict, answer)
        """
        if age >= 9:
            # Original decimal behavior, rendered exactly as before (operands).
            min_val, max_val = adjust_range_by_difficulty(
                min_val, max_val, difficulty, age
            )
            denominator = random.randint(2, max_val)
            numerator = random.randint(1, denominator)
            problem = f"{numerator}/{denominator}"
            return make_operands(problem), str(round(numerator / denominator, 3))

        # Grade 3 fraction concepts.
        kind = random.choice(["compare", "equivalent", "addsub", "identify"])

        if kind == "compare":
            a = self._random_fraction()
            b = self._random_fraction()
            left = a[0] / a[1]
            right = b[0] / b[1]
            if abs(left - right) < 1e-9:
                answer = "="
            elif left > right:
                answer = ">"
            else:
                answer = "<"
            text = f"{a[0]}/{a[1]} ◯ {b[0]}/{b[1]}"
            return make_expression(text, prompt="Compare (> < =)"), answer

        if kind == "equivalent":
            num, den = self._random_fraction()
            factor = random.randint(2, 4)
            text = f"{num}/{den} = ?/{den * factor}"
            return make_expression(text), str(num * factor)

        if kind == "addsub":
            den = random.choice([2, 3, 4, 5, 6, 8])
            if random.random() < 0.5:
                # Addition with like denominators (sum stays <= den).
                n1 = random.randint(1, den - 1)
                n2 = random.randint(1, den - n1) if den - n1 >= 1 else 1
                text = f"{n1}/{den} + {n2}/{den}"
                return make_expression(text), f"{n1 + n2}/{den}"
            # Subtraction with like denominators.
            n1 = random.randint(2, den)
            n2 = random.randint(1, n1 - 1)
            text = f"{n1}/{den} - {n2}/{den}"
            return make_expression(text), f"{n1 - n2}/{den}"

        # identify: shaded bar -> name the fraction.
        den = random.choice([2, 3, 4, 5, 6, 8])
        num = random.randint(1, den - 1)
        return (
            make_visual(_fraction_bar_svg(num, den), prompt="Name the fraction"),
            f"{num}/{den}",
        )

    @staticmethod
    def _random_fraction() -> Tuple[int, int]:
        """A small proper-ish fraction with denominator in 2..8."""
        den = random.choice([2, 3, 4, 5, 6, 8])
        num = random.randint(1, den)
        # Keep the displayed form lightly reduced for readability.
        g = gcd(num, den)
        if g > 1 and random.random() < 0.5:
            num //= g
            den //= g
        return num, den
