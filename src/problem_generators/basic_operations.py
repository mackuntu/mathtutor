"""Strategies for generating addition and subtraction problems."""

import random
from typing import Dict, Tuple

from src.problem_strategy import (
    ProblemStrategy,
    adjust_range_by_difficulty,
    make_expression,
    make_operands,
)
from src.problem_types import OPERATORS


# Probability of emitting a missing-operand variant (grade 3+, by difficulty).
def _missing_operand_chance(age: int, difficulty: float) -> float:
    if age < 8:
        return 0.0
    return 0.15 + 0.2 * difficulty  # 0.15 -> 0.35


class AdditionStrategy(ProblemStrategy):
    """Strategy for generating addition problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        """Generate an addition problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem_dict, answer)
        """
        min_val, max_val = adjust_range_by_difficulty(min_val, max_val, difficulty, age)

        # For age 5, ensure the sum is within their range
        if age == 5:
            # For lower difficulties, keep one number single-digit
            if difficulty <= 0.3:
                num1 = random.randint(min_val, min(9, max_val))
                num2 = random.randint(min_val, min(max_val - num1, max_val))
            else:
                # For higher difficulties, allow both numbers to be double-digit
                num1 = random.randint(min_val, max_val - 1)
                num2 = random.randint(min_val, min(max_val - num1, max_val))
        elif age == 8:
            # Grade 3: 3-4 digit addition with regrouping; no trivial operands.
            if difficulty < 0.3:
                num1 = random.randint(100, 999)
                num2 = random.randint(10, 99)
            elif difficulty < 0.7:
                num1 = random.randint(100, 999)
                num2 = random.randint(100, 999)
            else:
                num1 = random.randint(1000, 9999)
                num2 = random.randint(1000, 9999)
        else:
            # Generate both numbers in the full range
            num1 = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)

        operator = OPERATORS["addition"]

        # Grade 3+: sometimes hide an operand -> "94 + ? = 103" (answer = hidden).
        # Uses compact 2-digit operands so the inline expression fits one column.
        if random.random() < _missing_operand_chance(age, difficulty):
            a = random.randint(11, 99)
            b = random.randint(11, 99)
            total = a + b
            if random.random() < 0.5:
                return make_expression(f"{a} {operator} ? = {total}"), str(b)
            return make_expression(f"? {operator} {b} = {total}"), str(a)

        problem = f"{num1} {operator} {num2}"
        return make_operands(problem), str(num1 + num2)


class SubtractionStrategy(ProblemStrategy):
    """Strategy for generating subtraction problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        """Generate a subtraction problem.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem_dict, answer)
        """
        min_val, max_val = adjust_range_by_difficulty(min_val, max_val, difficulty, age)

        # For age 5, ensure the difference is appropriate
        if age == 5:
            # For subtraction, ensure first number is larger and result is positive
            if difficulty <= 0.3:
                # For lower difficulties, keep second number single-digit
                num2 = random.randint(min_val, min(9, max_val - 1))
                num1 = random.randint(max(num2 + 1, min_val), max_val)
            else:
                # For higher difficulties, allow both numbers to be double-digit
                num1 = random.randint(max(min_val + 1, min_val), max_val)
                num2 = random.randint(min_val, max(num1 - 1, min_val))
        elif age == 8:
            # Grade 3: 3-4 digit subtraction (borrow across zeros); positive result.
            if difficulty < 0.3:
                num1 = random.randint(100, 999)
                num2 = random.randint(10, 99)
            elif difficulty < 0.7:
                num1 = random.randint(200, 999)
                num2 = random.randint(100, num1 - 1)
            else:
                num1 = random.randint(1000, 9999)
                num2 = random.randint(100, num1 - 1)
        else:
            # Generate both numbers in the full range
            num1 = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)

            # Ensure first number is larger
            if num1 <= num2:
                num1, num2 = num2, num1

        operator = OPERATORS["subtraction"]

        # Grade 3+: sometimes hide an operand -> "? - 12 = 30" / "50 - ? = 18".
        # Uses compact 2-digit operands so the inline expression fits one column.
        if random.random() < _missing_operand_chance(age, difficulty):
            a = random.randint(40, 99)
            b = random.randint(10, a - 1)
            diff = a - b
            if random.random() < 0.5:
                return make_expression(f"? {operator} {b} = {diff}"), str(a)
            return make_expression(f"{a} {operator} ? = {diff}"), str(b)

        problem = f"{num1} {operator} {num2}"
        return make_operands(problem), str(num1 - num2)
