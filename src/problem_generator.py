"""Main problem generator module."""

import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Type

from src.problem_generators.basic_operations import (
    AdditionStrategy,
    SubtractionStrategy,
)
from src.problem_generators.fractions import FractionStrategy
from src.problem_generators.multiplication import (
    DivisionStrategy,
    MultiplicationStrategy,
)
from src.problem_strategy import ProblemStrategy
from src.problem_types import get_difficulty_weights, get_problem_types_for_age

logger = logging.getLogger(__name__)


class ProblemGenerator:
    """Generates age-appropriate math problems."""

    # Map of problem types to strategy classes
    STRATEGY_MAP: Dict[str, Type[ProblemStrategy]] = {
        "addition": AdditionStrategy,
        "subtraction": SubtractionStrategy,
        "multiplication": MultiplicationStrategy,
        "division": DivisionStrategy,
        "fractions": FractionStrategy,
    }

    def __init__(self, seed: Optional[int] = None):
        """Initialize problem generator."""
        if seed is not None:
            random.seed(seed)

        # Initialize strategy instances
        self.strategies: Dict[str, ProblemStrategy] = {
            problem_type: strategy_class()
            for problem_type, strategy_class in self.STRATEGY_MAP.items()
        }

    def get_school_year_progress(self) -> float:
        """Calculate current progress in school year (0.0 to 1.0)."""
        current_month = datetime.now().month
        if current_month >= 8:  # August to December
            month_in_year = current_month - 7
        else:  # January to July
            month_in_year = current_month + 5
        return month_in_year / 10.0

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
        if difficulty is None:
            difficulty = self.get_school_year_progress()
        elif not 0.0 <= difficulty <= 1.0:
            raise ValueError("Difficulty must be between 0.0 and 1.0")

        # Get available problem types and their weights based on difficulty
        problem_weights = get_difficulty_weights(age, difficulty)
        problem_types = get_problem_types_for_age(age)

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
                # Get the appropriate strategy for this problem type
                strategy = self.strategies[problem_type]

                # Generate the problem using the strategy
                problem, answer = strategy.generate(
                    range_tuple[0], range_tuple[1], difficulty, age
                )

                # Only add if we haven't seen this problem before
                if problem not in used_problems:
                    problems.append(problem)
                    answers.append(answer)
                    used_problems.add(problem)
            except ValueError as e:
                logger.warning(f"Failed to generate problem: {e}")
                continue
            except KeyError as e:
                logger.warning(f"Strategy not found for problem type: {problem_type}")
                continue

        if len(problems) < count:
            logger.warning(
                f"Could only generate {len(problems)} unique problems out of {count} requested"
            )

        return problems, answers
