"""Strategy for Roman numeral problems (grade 3)."""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_expression

_VALUES = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]


def int_to_roman(n: int) -> str:
    result = ""
    for value, symbol in _VALUES:
        while n >= value:
            result += symbol
            n -= value
    return result


class RomanNumeralStrategy(ProblemStrategy):
    """Convert between Roman numerals and integers."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        if difficulty < 0.4:
            num = random.randint(1, 20)
        elif difficulty < 0.7:
            num = random.randint(1, 49)
        else:
            num = random.randint(1, 100)

        roman = int_to_roman(num)
        if random.random() < 0.5:
            # Roman -> number
            return make_expression(roman, prompt="Write the number"), str(num)
        # Number -> Roman
        return make_expression(str(num), prompt="Roman numeral"), roman
