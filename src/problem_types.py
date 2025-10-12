"""Problem type definitions and difficulty weights for math problems."""

from typing import Dict, Tuple

# Base problem types by age group (ranges are now used for basic bounds, complexity is handled in strategies)
PROBLEM_TYPES = {
    5: {  # Kindergarten
        "addition": (1, 20),  # Numbers up to 20
        "subtraction": (1, 20),  # Numbers up to 20
    },
    6: {  # First grade
        "addition": (1, 20),  # Numbers up to 20
        "subtraction": (1, 20),  # Numbers up to 20
    },
    7: {  # Second grade
        "addition": (1, 50),
        "subtraction": (1, 50),
        "multiplication": (1, 10),  # Basic multiplication facts
    },
    8: {  # Third grade
        "addition": (1, 100),
        "subtraction": (1, 100),
        "multiplication": (1, 25),  # Multiples of 5 and 10
        "division": (1, 10),  # Simple division facts
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
