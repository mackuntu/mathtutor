"""Strategies for generating multiplication and division problems."""

import random
from typing import Tuple

from src.problem_strategy import ProblemStrategy, adjust_range_by_difficulty
from src.problem_types import OPERATORS


class MultiplicationStrategy(ProblemStrategy):
    """Strategy for generating multiplication problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate a multiplication problem with age-appropriate complexity.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        # Generate numbers based on age-specific complexity rules with sliding windows
        if age <= 6:
            # Ages 5-6: Single digits only, but sliding window based on difficulty
            if difficulty < 0.3:
                base_min, base_max = 1, 3
                range_size = 2
            elif difficulty < 0.7:
                base_min, base_max = 2, 5
                range_size = 3
            else:
                base_min, base_max = 3, 6
                range_size = 3

            num1 = random.randint(base_min, base_max)
            num2 = random.randint(base_min, min(base_max + range_size, 9))

        elif age == 7:
            # Age 7: Introduce 10s and simple patterns with sliding window
            if difficulty < 0.3:
                # Easier: small numbers with occasional 10s
                num1 = random.choice([random.randint(2, 5), 10])
                num2 = random.randint(2, 6)
            elif difficulty < 0.7:
                # Medium: more 10s and 20s
                num1 = random.choice([10, 20, random.randint(4, 7)])
                num2 = random.randint(4, 8)
            else:
                # Harder: more 10s and 20s with larger multipliers
                num1 = random.choice([10, 20, random.randint(5, 9)])
                num2 = random.randint(5, 10)

        elif age == 8:
            # Age 8: Multiples of 5 and 10 with sliding window
            if difficulty < 0.3:
                # Easy: small single digits
                num1 = random.randint(3, 6)
                num2 = random.randint(3, 7)
            elif difficulty < 0.7:
                # Medium: multiples of 5 with sliding window
                base_min, base_max = 4, 6
                num1 = random.choice([5, 10, random.randint(base_min, base_max)])
                num2 = random.randint(base_min, min(base_max + 3, 9))
            else:
                # Hard: multiples of 5 and 10 with higher base
                base_min, base_max = 5, 8
                num1 = random.choice(
                    [5, 10, 15, 20, random.randint(base_min, base_max)]
                )
                num2 = random.randint(base_min, min(base_max + 4, 9))

        elif age == 9:
            # Age 9: Double-digit × single digit with sliding window
            if difficulty < 0.3:
                # Easier: small single digits
                num1 = random.randint(2, 5)
                num2 = random.randint(2, 6)
            elif difficulty < 0.7:
                # Medium: double-digit × single digit with sliding window
                base_min, base_max = 4, 7
                num1 = random.randint(12 + base_min, 18 + base_max)
                num2 = random.randint(base_min, min(base_max + 3, 9))
            else:
                # Harder: larger double-digit × single digit
                base_min, base_max = 5, 9
                num1 = random.randint(18 + base_min, 28 + base_max)
                num2 = random.randint(base_min, min(base_max + 2, 9))

        elif age == 10:
            # Age 10: Double-digit × double-digit with sliding window
            if difficulty < 0.3:
                # Easier: single × double with sliding window
                base_min, base_max = 3, 5
                num1 = random.randint(base_min, min(base_max + 2, 7))
                num2 = random.randint(12 + base_min, 18 + base_max)
            elif difficulty < 0.7:
                # Medium: double × double, avoid "easy" numbers with sliding window
                base_min, base_max = 4, 7
                num1 = random.randint(14 + base_min, 22 + base_max)
                num2 = random.randint(14 + base_min, 22 + base_max)
                # Avoid "easy" combinations like 12×10, 15×10, etc.
                while (num1 % 10 == 0 and num2 <= 15) or (
                    num2 % 10 == 0 and num1 <= 15
                ):
                    num1 = random.randint(14 + base_min, 22 + base_max)
                    num2 = random.randint(14 + base_min, 22 + base_max)
            else:
                # Harder: larger double-digit × double-digit with sliding window
                base_min, base_max = 5, 9
                num1 = random.randint(18 + base_min, 28 + base_max)
                num2 = random.randint(18 + base_min, 28 + base_max)

        elif age == 11:
            # Age 11: Larger numbers with sliding window, focus on "hard" combinations
            if difficulty < 0.3:
                # Easier: double × double with sliding window
                base_min, base_max = 3, 6
                num1 = random.randint(15 + base_min, 23 + base_max)
                num2 = random.randint(15 + base_min, 23 + base_max)
            elif difficulty < 0.7:
                # Medium: larger numbers, avoid "easy" patterns with sliding window
                base_min, base_max = 5, 9
                num1 = random.randint(23 + base_min, 33 + base_max)
                num2 = random.randint(23 + base_min, 33 + base_max)
                # Avoid multiples of 10
                while num1 % 10 == 0 or num2 % 10 == 0:
                    num1 = random.randint(23 + base_min, 33 + base_max)
                    num2 = random.randint(23 + base_min, 33 + base_max)
            else:
                # Harder: complex multi-digit with sliding window
                base_min, base_max = 6, 12
                num1 = random.randint(28 + base_min, 38 + base_max)
                num2 = random.randint(28 + base_min, 38 + base_max)

        else:  # age >= 12
            # Age 12+: Complex multi-digit with sliding window and strategic number choices
            if difficulty < 0.3:
                # Easier: double × double with sliding window
                base_min, base_max = 4, 7
                num1 = random.randint(18 + base_min, 28 + base_max)
                num2 = random.randint(18 + base_min, 28 + base_max)
            elif difficulty < 0.7:
                # Medium: larger numbers, avoid "easy" patterns with sliding window
                base_min, base_max = 6, 12
                num1 = random.randint(28 + base_min, 38 + base_max)
                num2 = random.randint(28 + base_min, 38 + base_max)
                # Avoid multiples of 5 and 10
                while (num1 % 5 == 0 and num1 % 10 == 0) or (
                    num2 % 5 == 0 and num2 % 10 == 0
                ):
                    num1 = random.randint(28 + base_min, 38 + base_max)
                    num2 = random.randint(28 + base_min, 38 + base_max)
            else:
                # Harder: complex multi-digit with "hard" numbers and sliding window
                base_min, base_max = 10, 18
                num1 = random.randint(40 + base_min, 50 + base_max)
                num2 = random.randint(40 + base_min, 50 + base_max)
                # Prefer "hard" numbers (primes, numbers ending in 3, 7, 9)
                hard_numbers = [37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
                if random.random() < 0.5:  # 50% chance of using "hard" numbers
                    num1 = random.choice(hard_numbers)
                    num2 = random.randint(40 + base_min, 50 + base_max)

        operator = OPERATORS["multiplication"]
        problem = f"{num1} {operator} {num2}"
        answer = num1 * num2

        return problem, str(answer)


class DivisionStrategy(ProblemStrategy):
    """Strategy for generating division problems."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[str, str]:
        """Generate a division problem with age-appropriate complexity.

        Args:
            min_val: Minimum value for the range
            max_val: Maximum value for the range
            difficulty: Difficulty level from 0.0 to 1.0
            age: Student age for context-appropriate scaling

        Returns:
            Tuple of (problem, answer)
        """
        # Generate division problems based on age-specific complexity rules with sliding windows
        if age <= 6:
            # Ages 5-6: Simple division facts with sliding window
            if difficulty < 0.3:
                divisor = random.choice([2, 3])
                answer = random.randint(1, 4)
            elif difficulty < 0.7:
                divisor = random.choice([2, 3, 4])
                answer = random.randint(2, 6)
            else:
                divisor = random.choice([2, 3, 4, 5])
                answer = random.randint(3, 8)
            dividend = answer * divisor

        elif age == 7:
            # Age 7: Introduce ÷6, ÷7, ÷8, ÷9, ÷10 with sliding window
            if difficulty < 0.3:
                # Easier: simple divisors with sliding window
                divisor = random.choice([2, 3, 4])
                answer = random.randint(1, 5)
            elif difficulty < 0.7:
                # Medium: more divisors with sliding window
                divisor = random.choice([4, 5, 6])
                answer = random.randint(2, 6)
            else:
                # Harder: more divisors with higher base
                divisor = random.choice([6, 7, 8, 9])
                answer = random.randint(3, 8)
            dividend = answer * divisor

        elif age == 8:
            # Age 8: Division with remainders, but simple divisors with sliding window
            if difficulty < 0.3:
                # Easier: whole number division with sliding window
                divisor = random.choice([2, 3, 4, 5])
                answer = random.randint(1, 6)
                dividend = answer * divisor
            elif difficulty < 0.7:
                # Medium: introduce remainders occasionally with sliding window
                divisor = random.choice([3, 4, 5, 6])
                answer = random.randint(2, 8)
                if random.random() < 0.3:  # 30% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor
            else:
                # Harder: more remainders with sliding window
                divisor = random.choice([4, 5, 6, 7, 8])
                answer = random.randint(3, 10)
                if random.random() < 0.6:  # 60% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor

        elif age == 9:
            # Age 9: Larger dividends, but still simple divisors with sliding window
            if difficulty < 0.3:
                # Easier: simple division with sliding window
                divisor = random.choice([2, 3, 4, 5])
                answer = random.randint(2, 8)
                dividend = answer * divisor
            elif difficulty < 0.7:
                # Medium: larger dividends, some remainders with sliding window
                divisor = random.choice([4, 5, 6, 7, 8])
                answer = random.randint(3, 12)
                if random.random() < 0.4:  # 40% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor
            else:
                # Harder: more complex division with sliding window
                divisor = random.choice([5, 6, 7, 8, 9, 10])
                answer = random.randint(4, 15)
                if random.random() < 0.5:  # 50% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor

        elif age == 10:
            # Age 10: More complex divisors with sliding window, avoid "easy" combinations
            if difficulty < 0.3:
                # Easier: simple divisors with sliding window
                divisor = random.choice([3, 4, 5, 6, 7])
                answer = random.randint(2, 10)
                dividend = answer * divisor
            elif difficulty < 0.7:
                # Medium: avoid "easy" divisors, more remainders with sliding window
                divisor = random.choice([7, 8, 9, 11, 12])
                answer = random.randint(3, 15)
                if random.random() < 0.5:  # 50% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor
            else:
                # Harder: complex divisors, more remainders with sliding window
                divisor = random.choice([11, 13, 14, 15, 16, 17])
                answer = random.randint(4, 20)
                if random.random() < 0.7:  # 70% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor

        elif age == 11:
            # Age 11: Complex divisors with sliding window, strategic number choices
            if difficulty < 0.3:
                # Easier: medium complexity with sliding window
                divisor = random.choice([8, 9, 10, 11, 12])
                answer = random.randint(3, 15)
                dividend = answer * divisor
            elif difficulty < 0.7:
                # Medium: avoid "easy" patterns with sliding window
                divisor = random.choice([13, 14, 15, 16, 17, 18])
                answer = random.randint(4, 20)
                if random.random() < 0.6:  # 60% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor
            else:
                # Harder: complex divisors, strategic remainders with sliding window
                divisor = random.choice([17, 19, 21, 23, 24, 25])
                answer = random.randint(5, 25)
                if random.random() < 0.8:  # 80% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor

        else:  # age >= 12
            # Age 12+: Most complex division with sliding window and strategic number choices
            if difficulty < 0.3:
                # Easier: medium complexity with sliding window
                divisor = random.choice([15, 16, 17, 18, 19])
                answer = random.randint(4, 20)
                dividend = answer * divisor
            elif difficulty < 0.7:
                # Medium: avoid "easy" patterns, more remainders with sliding window
                divisor = random.choice([19, 21, 23, 24, 25, 26, 27])
                answer = random.randint(5, 30)
                if random.random() < 0.7:  # 70% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor
            else:
                # Harder: most complex division with "hard" divisors and sliding window
                hard_divisors = [23, 27, 29, 31, 33, 34, 37, 38, 39]
                divisor = random.choice(hard_divisors)
                answer = random.randint(6, 35)
                if random.random() < 0.85:  # 85% chance of remainder
                    remainder = random.randint(1, divisor - 1)
                    dividend = answer * divisor + remainder
                    operator = OPERATORS["division"]
                    problem = f"{dividend} {operator} {divisor}"
                    return problem, f"{answer} R{remainder}"
                else:
                    dividend = answer * divisor

        operator = OPERATORS["division"]
        problem = f"{dividend} {operator} {divisor}"

        return problem, str(answer)
