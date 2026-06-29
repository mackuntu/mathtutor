"""Strategy for measurement/unit-conversion problems (grade 3)."""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_expression

# (from_unit, to_unit, factor): 1 from_unit == factor to_unit
_CONVERSIONS = [
    ("ft", "in", 12),
    ("yd", "ft", 3),
    ("m", "cm", 100),
    ("km", "m", 1000),
    ("kg", "g", 1000),
    ("lb", "oz", 16),
    ("L", "mL", 1000),
    ("gal", "qt", 4),
]


class MeasurementStrategy(ProblemStrategy):
    """Convert a whole number of the larger unit to the smaller unit."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        from_unit, to_unit, factor = random.choice(_CONVERSIONS)
        count = random.randint(2, 9 if difficulty < 0.5 else 12)
        answer = count * factor
        text = f"{count} {from_unit} = ? {to_unit}"
        return make_expression(text), str(answer)
