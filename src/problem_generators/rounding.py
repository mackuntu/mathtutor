"""Strategy for rounding problems (grade 3)."""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_expression


def _round_half_up(n: int, base: int) -> int:
    """Round ``n`` to the nearest multiple of ``base`` (half rounds up)."""
    return (n + base // 2) // base * base


class RoundingStrategy(ProblemStrategy):
    """Round a number to the nearest 10 or 100."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        if difficulty < 0.5:
            base = 10
            num = random.randint(11, 199)
        else:
            base = random.choice([10, 100])
            num = random.randint(25, 999)

        answer = _round_half_up(num, base)
        return make_expression(f"{num:,}", prompt=f"Round to {base}"), str(answer)
