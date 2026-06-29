"""Strategy for money problems (grade 3)."""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_expression

_COINS = {"penny": 1, "pennies": 1, "nickel": 5, "dime": 10, "quarter": 25}
_COIN_NAMES = ["nickel", "dime", "quarter"]


def _fmt(cents: int) -> str:
    return f"${cents / 100:.2f}"


class MoneyStrategy(ProblemStrategy):
    """Add money, make change, or convert coins to cents."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        kind = random.choice(["add", "change", "coins"])

        if kind == "add":
            a = random.randrange(25, 500, 5)
            b = random.randrange(25, 500, 5)
            text = f"{_fmt(a)} + {_fmt(b)}"
            return make_expression(text), _fmt(a + b)

        if kind == "change":
            total = random.choice([100, 200, 500])
            paid = random.randrange(25, total, 5)
            text = f"{_fmt(total)} − {_fmt(paid)}"
            return make_expression(text), _fmt(total - paid)

        # coins -> cents
        name = random.choice(_COIN_NAMES)
        count = random.randint(2, 9)
        plural = name + "s"
        answer = count * _COINS[name]
        text = f"{count} {plural} = ? ¢"
        return make_expression(text), str(answer)
