from datetime import datetime
from problem_templates import ProblemTemplates
import random


class ProblemGenerator:
    @staticmethod
    def get_school_year_month():
        current_month = datetime.now().month
        if current_month >= 8:  # August to December
            school_year_month = current_month - 7
        else:  # January to May
            school_year_month = current_month + 5
        return school_year_month

    @staticmethod
    def generate_math_problems(age):
        """
        Generate a problem sheet for 6-year-olds, focusing on simple arithmetic and geometry.
        """
        school_year_month = ProblemGenerator.get_school_year_month()
        progression_factor = school_year_month / 10

        # Generate problems
        arithmetic_problems = ProblemTemplates.generate_arithmetic(
            1, progression_factor, count=30
        )
        # geometry_problems = ProblemTemplates.generate_geometry(geometry_level, count=10)

        # Combine problems into a single sheet
        # problems = arithmetic_problems + geometry_problems
        problems = arithmetic_problems
        random.shuffle(problems)

        questions = [p[0] for p in problems]
        answers = [p[1] for p in problems]

        return questions, answers
