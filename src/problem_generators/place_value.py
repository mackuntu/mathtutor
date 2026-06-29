"""Strategy for place-value problems (grade 3)."""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_expression

_PLACES = {0: "ones", 1: "tens", 2: "hundreds", 3: "thousands"}


class PlaceValueStrategy(ProblemStrategy):
    """Generate place-value questions: value of a digit, or which digit."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        # 3-digit numbers for easy, up to 4-digit as difficulty rises.
        hi = 999 if difficulty < 0.5 else 9999
        num = random.randint(100, hi)
        digits = str(num)
        n_places = len(digits)

        # Pick a place; prefer a non-zero digit so the value is meaningful.
        pos = random.randint(0, n_places - 1)
        for _ in range(5):
            if int(digits[n_places - 1 - pos]) != 0:
                break
            pos = random.randint(0, n_places - 1)
        digit = int(digits[n_places - 1 - pos])
        place = _PLACES[pos]
        display = f"{num:,}"

        if random.random() < 0.5:
            # Value of the digit in a given place.
            value = digit * (10**pos)
            return make_expression(display, prompt=f"Value of {place} digit"), str(value)

        # Which digit sits in a given place.
        return make_expression(display, prompt=f"{place.capitalize()} digit?"), str(digit)
