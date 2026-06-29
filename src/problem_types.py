"""Problem type definitions and difficulty weights for math problems."""

from typing import Dict, Tuple

# Base problem types by age group (ranges are now used for basic bounds, complexity is handled in strategies)
PROBLEM_TYPES = {
    5: {  # Kindergarten
        "addition": (1, 30),  # Numbers up to 30
        "subtraction": (1, 30),  # Numbers up to 30
    },
    6: {  # First grade
        "addition": (1, 30),  # Numbers up to 30
        "subtraction": (1, 30),  # Numbers up to 30
    },
    7: {  # Second grade (lighter version of the grade-3 topic set)
        "addition": (1, 100),
        "subtraction": (1, 100),
        "multiplication": (1, 12),  # Basic multiplication facts
        "place_value": (1, 999),
        "rounding": (1, 100),
        "order_of_operations": (1, 12),
        "roman_numerals": (1, 100),
        "measurement": (1, 100),
        "money": (1, 100),
        "time": (1, 100),
        "geometry": (1, 100),
        "data_graphing": (1, 10),
        "fractions": (1, 8),
    },
    8: {  # Third grade (full k5 grade-3 topic set)
        "addition": (1, 9999),  # 3-4 digit with regrouping
        "subtraction": (1, 9999),  # borrow across zeros
        "multiplication": (1, 12),  # tables to 12, 2-digit×1-digit, ×10/×100
        "division": (1, 12),  # facts to 12, remainders, ÷10/÷100
        "fractions": (1, 8),
        "place_value": (1, 9999),
        "rounding": (1, 999),
        "order_of_operations": (1, 12),
        "roman_numerals": (1, 100),
        "measurement": (1, 100),
        "money": (1, 100),
        "time": (1, 100),
        "geometry": (1, 100),
        "data_graphing": (1, 10),
    },
    9: {  # Fourth grade
        "addition": (1, 1000),
        "subtraction": (1, 1000),
        "multiplication": (1, 35),  # Double-digit × single digit
        "division": (1, 15),  # Division with remainders
        "fractions": (1, 10),
    },
    10: {  # Fifth grade
        "addition": (1, 10000),
        "subtraction": (1, 10000),
        "multiplication": (1, 35),  # Double-digit × double-digit
        "division": (1, 25),  # Complex divisors
        "fractions": (1, 20),
    },
    11: {  # Sixth grade
        "addition": (1, 100000),
        "subtraction": (1, 100000),
        "multiplication": (1, 50),  # Larger multi-digit
        "division": (1, 35),  # Strategic divisors
        "fractions": (1, 50),
    },
    12: {  # Seventh grade
        "addition": (1, 1000000),
        "subtraction": (1, 1000000),
        "multiplication": (1, 75),  # Complex multi-digit
        "division": (1, 50),  # Hard divisors
        "fractions": (1, 100),
    },
}

# Problem type weights by difficulty (0.0 to 1.0)
DIFFICULTY_WEIGHTS = {
    5: {  # Kindergarten
        0.0: {"addition": 0.8, "subtraction": 0.2},  # Easier: mostly addition
        0.5: {
            "addition": 0.6,
            "subtraction": 0.4,
        },  # Medium: more addition than subtraction
        1.0: {"addition": 0.5, "subtraction": 0.5},  # Harder: equal mix
    },
    6: {  # First grade
        0.0: {"addition": 0.7, "subtraction": 0.3},  # Easier: more addition
        0.5: {"addition": 0.5, "subtraction": 0.5},  # Medium: balanced
        1.0: {"addition": 0.3, "subtraction": 0.7},  # Harder: more subtraction
    },
    7: {  # Second grade (lighter version of the grade-3 mix)
        0.0: {
            "addition": 0.22,
            "subtraction": 0.18,
            "multiplication": 0.08,
            "place_value": 0.08,
            "rounding": 0.07,
            "order_of_operations": 0.03,
            "roman_numerals": 0.03,
            "measurement": 0.06,
            "money": 0.06,
            "time": 0.06,
            "geometry": 0.05,
            "data_graphing": 0.05,
            "fractions": 0.03,
        },
        0.5: {
            "addition": 0.18,
            "subtraction": 0.16,
            "multiplication": 0.12,
            "place_value": 0.07,
            "rounding": 0.06,
            "order_of_operations": 0.04,
            "roman_numerals": 0.04,
            "measurement": 0.06,
            "money": 0.06,
            "time": 0.06,
            "geometry": 0.05,
            "data_graphing": 0.05,
            "fractions": 0.05,
        },
        1.0: {
            "addition": 0.14,
            "subtraction": 0.13,
            "multiplication": 0.16,
            "place_value": 0.06,
            "rounding": 0.06,
            "order_of_operations": 0.05,
            "roman_numerals": 0.05,
            "measurement": 0.06,
            "money": 0.06,
            "time": 0.05,
            "geometry": 0.06,
            "data_graphing": 0.05,
            "fractions": 0.07,
        },
    },
    8: {  # Third grade (full topic set)
        0.0: {
            "addition": 0.14,
            "subtraction": 0.12,
            "multiplication": 0.12,
            "division": 0.08,
            "place_value": 0.08,
            "rounding": 0.08,
            "order_of_operations": 0.04,
            "roman_numerals": 0.03,
            "measurement": 0.06,
            "money": 0.06,
            "time": 0.06,
            "geometry": 0.05,
            "data_graphing": 0.05,
            "fractions": 0.03,
        },
        0.5: {
            "addition": 0.10,
            "subtraction": 0.09,
            "multiplication": 0.12,
            "division": 0.10,
            "place_value": 0.07,
            "rounding": 0.06,
            "order_of_operations": 0.05,
            "roman_numerals": 0.04,
            "measurement": 0.06,
            "money": 0.06,
            "time": 0.06,
            "geometry": 0.05,
            "data_graphing": 0.04,
            "fractions": 0.05,
        },
        1.0: {
            "addition": 0.07,
            "subtraction": 0.07,
            "multiplication": 0.12,
            "division": 0.12,
            "place_value": 0.06,
            "rounding": 0.05,
            "order_of_operations": 0.07,
            "roman_numerals": 0.05,
            "measurement": 0.06,
            "money": 0.06,
            "time": 0.05,
            "geometry": 0.06,
            "data_graphing": 0.05,
            "fractions": 0.07,
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
    10: {  # Fifth grade
        0.0: {
            "addition": 0.2,
            "subtraction": 0.2,
            "multiplication": 0.3,
            "division": 0.2,
            "fractions": 0.1,
        },
        0.5: {
            "addition": 0.15,
            "subtraction": 0.15,
            "multiplication": 0.25,
            "division": 0.25,
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
    11: {  # Sixth grade
        0.0: {
            "addition": 0.15,
            "subtraction": 0.15,
            "multiplication": 0.3,
            "division": 0.25,
            "fractions": 0.15,
        },
        0.5: {
            "addition": 0.1,
            "subtraction": 0.1,
            "multiplication": 0.25,
            "division": 0.3,
            "fractions": 0.25,
        },
        1.0: {
            "addition": 0.05,
            "subtraction": 0.05,
            "multiplication": 0.2,
            "division": 0.35,
            "fractions": 0.35,
        },
    },
    12: {  # Seventh grade
        0.0: {
            "addition": 0.1,
            "subtraction": 0.1,
            "multiplication": 0.3,
            "division": 0.3,
            "fractions": 0.2,
        },
        0.5: {
            "addition": 0.05,
            "subtraction": 0.05,
            "multiplication": 0.25,
            "division": 0.35,
            "fractions": 0.3,
        },
        1.0: {
            "addition": 0.02,
            "subtraction": 0.03,
            "multiplication": 0.2,
            "division": 0.4,
            "fractions": 0.35,
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


def get_problem_types_for_age(age: int) -> Dict[str, Tuple[int, int]]:
    """Get problem types for a specific age.

    Args:
        age: Student age

    Returns:
        Dictionary of problem types and their ranges

    Raises:
        ValueError: If age is not supported
    """
    if age not in PROBLEM_TYPES:
        raise ValueError(
            f"Age {age} not supported. Supported ages: {list(PROBLEM_TYPES.keys())}"
        )
    return PROBLEM_TYPES[age]


def get_difficulty_weights(age: int, difficulty: float) -> Dict[str, float]:
    """Get problem type weights based on difficulty.

    Args:
        age: Student age
        difficulty: Difficulty level from 0.0 to 1.0

    Returns:
        Dictionary of problem types and their weights

    Raises:
        ValueError: If age is not supported
    """
    if age not in DIFFICULTY_WEIGHTS:
        raise ValueError(
            f"Age {age} not supported. Supported ages: {list(DIFFICULTY_WEIGHTS.keys())}"
        )

    weights = DIFFICULTY_WEIGHTS[age]

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
