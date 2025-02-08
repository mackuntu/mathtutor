from enum import Enum


class LayoutChoice(Enum):
    TWO_COLUMN = "2_column"
    ONE_COLUMN = "1_column"
    MIXED = "mixed"


LAYOUT_CONFIGS = {
    "2_column": {
        "columns": ["column_1", "column_2"],
        "column_limits": [15, 15],
    },
    "1_column": {
        "columns": ["column_1"],
        "column_limits": [30],
    },
    "mixed": {
        "columns": ["column_1", "column_2"],
        "column_limits": [20, 10],
    },
}

X_POSITIONS = {
    "column_1_problem": 50,
    "column_1_answer": 150,
    "column_2_problem": 300,
    "column_2_answer": 400,
}

Y_START = 680
ROW_SPACING = 40

# Dimensions of the answer bounding box: (x1_offset, y1_offset, x2_offset, y2_offset)
ANSWER_BOX_DIMENSIONS = (0, 20, 100, -20)
