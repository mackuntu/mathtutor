"""Problem type definitions and difficulty weights for math problems."""

from typing import Dict, Tuple

# Base problem types by age group (will be adjusted by difficulty)
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
