"""Strategy for order-of-operations problems (grade 3)."""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_expression


class OrderOfOperationsStrategy(ProblemStrategy):
    """Two-operation expressions evaluated with correct precedence."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        a = random.randint(2, 9)
        b = random.randint(2, 9)
        c = random.randint(2, 9)

        forms = [
            (f"{a} + {b} × {c}", a + b * c),
            (f"{a} × {b} + {c}", a * b + c),
            (f"{a} × {b} − {c}", a * b - c),
        ]
        if difficulty >= 0.5:
            # Parentheses change precedence -> harder.
            forms.append((f"({a} + {b}) × {c}", (a + b) * c))
            forms.append((f"{a} × ({b} + {c})", a * (b + c)))

        text, answer = random.choice(forms)
        return make_expression(text), str(answer)
