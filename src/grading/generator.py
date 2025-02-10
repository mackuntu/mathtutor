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
            "addition": (1, 10),  # Numbers from 1 to 10
            "subtraction": (1, 10),
        },
        7: {  # Second grade
            "addition": (1, 20),
            "subtraction": (1, 20),
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
        "multiplication": "×",
        "subtraction": "-",
        "division": "÷",
    }

    def __init__(self, seed: Optional[int] = None):
        """Initialize problem generator.

        Args:
            seed: Optional random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)

    def get_school_year_month(self) -> int:
        """Calculate current month in school year (1-10).

        Returns:
            Month number in school year (1 = August, 10 = May).
        """
        current_month = datetime.now().month
        if current_month >= 8:  # August to December
            return current_month - 7
        else:  # January to July
            return current_month + 5

    def _generate_number_range(
        self, min_val: int, max_val: int, month: int
    ) -> Tuple[int, int]:
        """Calculate number range based on school year progress.

        Args:
            min_val: Minimum value for range.
            max_val: Maximum value for range.
            month: Current month in school year (1-10).

        Returns:
            Tuple of (adjusted_min, adjusted_max).
        """
        # Scale max value based on progress through school year
        progress = month / 10  # 0.1 to 1.0
        adjusted_max = min_val + int((max_val - min_val) * progress)
        return min_val, adjusted_max

    def _generate_problem(
        self, problem_type: str, range_tuple: Tuple[int, int], month: int
    ) -> Tuple[str, str]:
        """Generate a single problem of specified type.

        Args:
            problem_type: Type of problem to generate.
            range_tuple: Tuple of (min_val, max_val).
            month: Current month in school year.

        Returns:
            Tuple of (problem_string, answer_string).

        Raises:
            ValueError: If problem type is invalid.
        """
        min_val, max_val = self._generate_number_range(*range_tuple, month)

        if problem_type == "fractions":
            denominator = random.randint(2, max_val)
            numerator = random.randint(1, denominator)
            return f"{numerator}/{denominator}", str(numerator / denominator)

        num1 = random.randint(min_val, max_val)
        num2 = random.randint(min_val, max_val)

        if problem_type not in self.OPERATORS:
            raise ValueError(f"Invalid problem type: {problem_type}")

        operator = self.OPERATORS[problem_type]

        # Ensure subtraction and division problems have valid answers
        if problem_type == "subtraction":
            num1, num2 = max(num1, num2), min(num1, num2)
        elif problem_type == "division":
            answer = random.randint(1, max_val)
            num1 = num2 * answer

        # Create problem string and calculate answer
        problem = f"{num1} {operator} {num2}"
        if problem_type == "addition":
            answer = num1 + num2
        elif problem_type == "subtraction":
            answer = num1 - num2
        elif problem_type == "multiplication":
            answer = num1 * num2
        elif problem_type == "division":
            answer = num1 // num2

        return problem, str(answer)

    def generate_math_problems(
        self, age: int, count: Optional[int] = None
    ) -> Tuple[List[str], List[str]]:
        """Generate age-appropriate math problems.

        Args:
            age: Age of student.
            count: Optional number of problems to generate.
                If None, generates based on age and progress.

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

        # Determine number of problems if not specified
        if count is None:
            base_count = 10 + (age - 6) * 2  # More problems for older students
            count = base_count + month  # More problems later in year

        # Generate problems
        problems = []
        answers = []

        while len(problems) < count:
            # Select random problem type
            problem_type = random.choice(list(problem_types.keys()))
            range_tuple = problem_types[problem_type]

            # Generate problem
            try:
                problem, answer = self._generate_problem(
                    problem_type, range_tuple, month
                )
                problems.append(problem)
                answers.append(answer)
            except ValueError as e:
                logger.warning(f"Failed to generate problem: {e}")
                continue

        return problems, answers
