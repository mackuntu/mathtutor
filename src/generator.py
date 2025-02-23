"""Module for generating math problems."""

import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProblemGenerator:
    """Generates age-appropriate math problems."""

    # Problem types by age group
    PROBLEM_TYPES = {
        6: {  # First grade
            "addition": (1, 20),  # Numbers up to 20
            "subtraction": (1, 20),  # Numbers up to 20
        },
        7: {  # Second grade
            "addition": (1, 50),
            "subtraction": (1, 50),
            "multiplication": (1, 5),
        },
        8: {  # Third grade
            "addition": (1, 100),
            "subtraction": (1, 100),
            "multiplication": (1, 10),
            "division": (1, 10),
        },
        9: {  # Fourth grade
            "addition": (1, 1000),
            "subtraction": (1, 1000),
            "multiplication": (1, 12),
            "division": (1, 12),
            "fractions": (1, 10),
        },
    }

    # Operators for each problem type
    OPERATORS = {
        "addition": "+",
        "subtraction": "-",
        "multiplication": "×",
        "division": "÷",
    }

    def __init__(self, seed: Optional[int] = None):
        """Initialize problem generator."""
        if seed is not None:
            random.seed(seed)

    def get_school_year_month(self) -> int:
        """Calculate current month in school year (1-10)."""
        current_month = datetime.now().month
        if current_month >= 8:  # August to December
            return current_month - 7
        else:  # January to July
            return current_month + 5

    def _generate_number_range(
        self, min_val: int, max_val: int, month: int
    ) -> Tuple[int, int]:
        """Calculate number range based on school year progress."""
        progress = month / 10  # 0.1 to 1.0
        adjusted_max = max(min_val + 1, min_val + int((max_val - min_val) * progress))
        return min_val, adjusted_max

    def _generate_problem(
        self, problem_type: str, range_tuple: Tuple[int, int], month: int
    ) -> Tuple[str, str]:
        """Generate a single problem of specified type."""
        min_val, max_val = self._generate_number_range(*range_tuple, month)

        if problem_type in ["addition", "subtraction"]:
            # Generate both numbers in the full range
            num1 = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)

            # For subtraction, ensure first number is larger
            if problem_type == "subtraction":
                num1, num2 = max(num1, num2), min(num1, num2)

            # Create problem string and calculate answer
            operator = self.OPERATORS[problem_type]
            problem = f"{num1} {operator} {num2}"

            if problem_type == "addition":
                answer = num1 + num2
            else:  # subtraction
                answer = num1 - num2

            return problem, str(answer)

        elif problem_type == "multiplication":
            num1 = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)
            operator = self.OPERATORS[problem_type]
            return f"{num1} {operator} {num2}", str(num1 * num2)

        elif problem_type == "division":
            # Generate division problems with whole number answers
            answer = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)
            num1 = answer * num2
            operator = self.OPERATORS[problem_type]
            return f"{num1} {operator} {num2}", str(answer)

        elif problem_type == "fractions":
            denominator = random.randint(2, max_val)
            numerator = random.randint(1, denominator)
            return f"{numerator}/{denominator}", str(numerator / denominator)

        raise ValueError(f"Invalid problem type: {problem_type}")

    def generate_math_problems(
        self, age: int, count: Optional[int] = 30
    ) -> Tuple[List[str], List[str]]:
        """Generate age-appropriate math problems.

        Args:
            age: Age of student.
            count: Number of problems to generate (default 30).

        Returns:
            Tuple of (problems, answers) lists.

        Raises:
            ValueError: If age group is not supported.
        """
        if age not in self.PROBLEM_TYPES:
            raise ValueError(
                f"Age {age} not supported. Supported ages: {list(self.PROBLEM_TYPES.keys())}"
            )

        # Get available problem types and ranges for age
        problem_types = self.PROBLEM_TYPES[age]

        # Calculate school year progress
        month = self.get_school_year_month()

        # Generate problems with a good mix of types
        problems = []
        answers = []
        types_list = list(problem_types.keys())
        used_problems = set()  # Keep track of problems we've already generated

        attempts = 0
        max_attempts = count * 10  # Allow some retries to find unique problems

        while len(problems) < count and attempts < max_attempts:
            attempts += 1
            # Cycle through problem types to ensure a good mix
            problem_type = types_list[len(problems) % len(types_list)]
            range_tuple = problem_types[problem_type]

            try:
                problem, answer = self._generate_problem(
                    problem_type, range_tuple, month
                )
                # Only add if we haven't seen this problem before
                if problem not in used_problems:
                    problems.append(problem)
                    answers.append(answer)
                    used_problems.add(problem)
            except ValueError as e:
                logger.warning(f"Failed to generate problem: {e}")
                continue

        if len(problems) < count:
            logger.warning(
                f"Could only generate {len(problems)} unique problems out of {count} requested"
            )

        return problems, answers
