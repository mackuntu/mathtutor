"""Module for generating math problems."""

import logging
import random
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Union

import qrcode

logger = logging.getLogger(__name__)


class ProblemGenerator:
    """Generates age-appropriate math problems."""

    # Base problem types by age group (will be adjusted by difficulty)
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

    # Problem type weights by difficulty (0.0 to 1.0)
    DIFFICULTY_WEIGHTS = {
        6: {  # First grade
            0.0: {"addition": 0.7, "subtraction": 0.3},  # Easier: more addition
            0.5: {"addition": 0.5, "subtraction": 0.5},  # Medium: balanced
            1.0: {"addition": 0.3, "subtraction": 0.7},  # Harder: more subtraction
        },
        7: {  # Second grade
            0.0: {"addition": 0.5, "subtraction": 0.4, "multiplication": 0.1},
            0.5: {"addition": 0.3, "subtraction": 0.4, "multiplication": 0.3},
            1.0: {"addition": 0.2, "subtraction": 0.3, "multiplication": 0.5},
        },
        8: {
            0.0: {
                "addition": 0.4,
                "subtraction": 0.3,
                "multiplication": 0.2,
                "division": 0.1,
            },
            0.5: {
                "addition": 0.25,
                "subtraction": 0.25,
                "multiplication": 0.25,
                "division": 0.25,
            },
            1.0: {
                "addition": 0.1,
                "subtraction": 0.2,
                "multiplication": 0.3,
                "division": 0.4,
            },
        },
        9: {
            0.0: {
                "addition": 0.3,
                "subtraction": 0.3,
                "multiplication": 0.2,
                "division": 0.15,
                "fractions": 0.05,
            },
            0.5: {
                "addition": 0.2,
                "subtraction": 0.2,
                "multiplication": 0.2,
                "division": 0.2,
                "fractions": 0.2,
            },
            1.0: {
                "addition": 0.1,
                "subtraction": 0.1,
                "multiplication": 0.2,
                "division": 0.3,
                "fractions": 0.3,
            },
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

    def get_school_year_progress(self) -> float:
        """Calculate current progress in school year (0.0 to 1.0)."""
        current_month = datetime.now().month
        if current_month >= 8:  # August to December
            month_in_year = current_month - 7
        else:  # January to July
            month_in_year = current_month + 5
        return month_in_year / 10.0

    def _adjust_range_by_difficulty(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[int, int]:
        """Adjust number range based on difficulty level.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (adjusted_min, adjusted_max)
        """
        range_size = max_val - min_val

        # Scale ranges more aggressively with difficulty
        if difficulty > 0.5:  # For higher difficulties, extend the maximum
            extension_factor = 1.0 + (difficulty - 0.5) * 2  # Up to 2x extension
            adjusted_max = min(
                max_val * extension_factor,  # Extend range
                self.PROBLEM_TYPES[
                    min(age + 1, 9)
                ].get(  # But don't exceed next age level
                    list(self.PROBLEM_TYPES[min(age + 1, 9)].keys())[0]
                )[
                    1
                ],
            )
        else:
            adjusted_max = max_val

        # Adjust minimum value to make problems harder
        if difficulty > 0.7:  # For very high difficulties, raise the minimum
            adjusted_min = min_val + int(range_size * 0.3)  # Start from 30% of range
        else:
            adjusted_min = min_val

        return int(adjusted_min), int(adjusted_max)

    def _get_problem_types(self, age: int, difficulty: float) -> Dict[str, float]:
        """Get problem type weights based on difficulty.

        Args:
            age: Student age
            difficulty: Difficulty level from 0.0 to 1.0

        Returns:
            Dictionary of problem types and their weights
        """
        weights = self.DIFFICULTY_WEIGHTS[age]

        # Interpolate between difficulty levels
        if difficulty <= 0.0:
            return weights[0.0]
        elif difficulty >= 1.0:
            return weights[1.0]
        elif difficulty <= 0.5:
            # Interpolate between 0.0 and 0.5
            factor = difficulty / 0.5
            return {
                k: weights[0.0][k] + (weights[0.5][k] - weights[0.0][k]) * factor
                for k in weights[0.0]
            }
        else:
            # Interpolate between 0.5 and 1.0
            factor = (difficulty - 0.5) / 0.5
            return {
                k: weights[0.5][k] + (weights[1.0][k] - weights[0.5][k]) * factor
                for k in weights[0.5]
            }

    def _generate_problem(
        self,
        problem_type: str,
        range_tuple: Tuple[int, int],
        difficulty: float,
        age: int,
    ) -> Tuple[str, str]:
        """Generate a single problem of specified type.

        Args:
            problem_type: Type of problem to generate
            range_tuple: Base range for numbers (min, max)
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling
        """
        min_val, max_val = self._adjust_range_by_difficulty(
            *range_tuple, difficulty, age
        )

        if problem_type in ["addition", "subtraction"]:
            # Generate both numbers in the full range
            num1 = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)

            # For subtraction, ensure first number is larger
            if problem_type == "subtraction":
                num1, num2 = max(num1, num2), min(num1, num2)

            # Add word problems for higher difficulties
            if difficulty > 0.6 and random.random() < difficulty - 0.6:
                if problem_type == "addition":
                    templates = [
                        f"You have {num1} apples and get {num2} more.\nHow many apples do you have?",
                        f"There are {num1} red and {num2} blue balls.\nHow many balls in total?",
                    ]
                else:  # subtraction
                    templates = [
                        f"You have {num1} candies and give {num2} away.\nHow many remain?",
                        f"There are {num1} students. {num2} leave.\nHow many stay?",
                    ]
                problem = random.choice(templates)
            else:
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

            # Add word problems for higher difficulties
            if difficulty > 0.6 and random.random() < difficulty - 0.6:
                templates = [
                    f"You have {num1} boxes with {num2} toys each.\nHow many toys total?",
                    f"{num1} rows of chairs, {num2} chairs per row.\nHow many chairs total?",
                ]
                problem = random.choice(templates)
            else:
                operator = self.OPERATORS[problem_type]
                problem = f"{num1} {operator} {num2}"

            return problem, str(num1 * num2)

        elif problem_type == "division":
            # Generate division problems with whole number answers
            answer = random.randint(min_val, max_val)
            num2 = random.randint(min_val, max_val)
            num1 = answer * num2

            # Add word problems for higher difficulties
            if difficulty > 0.6 and random.random() < difficulty - 0.6:
                templates = [
                    f"Share {num1} candies among {num2} friends.\nHow many each?",
                    f"Split {num1} students into {num2} equal teams.\nHow many per team?",
                ]
                problem = random.choice(templates)
            else:
                operator = self.OPERATORS[problem_type]
                problem = f"{num1} {operator} {num2}"

            return problem, str(answer)

        elif problem_type == "fractions":
            denominator = random.randint(2, max_val)
            numerator = random.randint(1, denominator)

            # Add word problems for higher difficulties
            if difficulty > 0.6 and random.random() < difficulty - 0.6:
                templates = [
                    f"What is {numerator}/{denominator} written as a decimal?",
                    f"If you eat {numerator}/{denominator} of a pizza, what fraction of the pizza did you eat?",
                ]
                problem = random.choice(templates)
            else:
                problem = f"{numerator}/{denominator}"

            return problem, str(round(numerator / denominator, 3))

        raise ValueError(f"Invalid problem type: {problem_type}")

    def generate_math_problems(
        self, age: int, count: Optional[int] = 30, difficulty: Optional[float] = None
    ) -> Tuple[List[str], List[str]]:
        """Generate age-appropriate math problems.

        Args:
            age: Age of student.
            count: Number of problems to generate (default 30).
            difficulty: Optional difficulty level from 0.0 to 1.0.
                      If None, uses current school year progress.

        Returns:
            Tuple of (problems, answers) lists.

        Raises:
            ValueError: If age group is not supported or difficulty is invalid.
        """
        if age not in self.PROBLEM_TYPES:
            raise ValueError(
                f"Age {age} not supported. Supported ages: {list(self.PROBLEM_TYPES.keys())}"
            )

        if difficulty is None:
            difficulty = self.get_school_year_progress()
        elif not 0.0 <= difficulty <= 1.0:
            raise ValueError("Difficulty must be between 0.0 and 1.0")

        # Get available problem types and their weights based on difficulty
        problem_weights = self._get_problem_types(age, difficulty)
        problem_types = self.PROBLEM_TYPES[age]

        # Generate problems with weighted distribution
        problems = []
        answers = []
        used_problems = set()  # Keep track of problems we've already generated

        attempts = 0
        max_attempts = count * 10  # Allow some retries to find unique problems

        while len(problems) < count and attempts < max_attempts:
            attempts += 1

            # Choose problem type based on weights
            problem_type = random.choices(
                list(problem_weights.keys()),
                weights=list(problem_weights.values()),
                k=1,
            )[0]
            range_tuple = problem_types[problem_type]

            try:
                problem, answer = self._generate_problem(
                    problem_type, range_tuple, difficulty, age
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

    def create_qr_code(self, worksheet_id: str) -> BytesIO:
        """Generate a QR code for worksheet identification.

        Args:
            worksheet_id: Unique identifier for worksheet.

        Returns:
            BytesIO containing QR code image.
        """
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
        )
        qr.add_data(worksheet_id)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        byte_stream = BytesIO()
        qr_image.save(byte_stream, format="PNG")
        byte_stream.seek(0)

        return byte_stream
