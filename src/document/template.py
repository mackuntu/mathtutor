"""Module for managing worksheet templates and layouts."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LayoutChoice(Enum):
    """Available worksheet layout options."""

    TWO_COLUMN = "2_column"
    ONE_COLUMN = "1_column"
    MIXED = "mixed"


@dataclass
class LayoutConfig:
    """Configuration for worksheet layout."""

    columns: List[str]
    column_limits: List[int]
    x_positions: Dict[str, int]
    y_start: int = 680
    row_spacing: int = 40
    answer_box_dimensions: Tuple[int, int, int, int] = (0, 20, 100, -20)


class TemplateManager:
    """Manages worksheet templates and layouts."""

    # Default layout configurations
    LAYOUT_CONFIGS = {
        LayoutChoice.TWO_COLUMN: LayoutConfig(
            columns=["column_1", "column_2"],
            column_limits=[15, 15],
            x_positions={
                "column_1_problem": 50,
                "column_1_answer": 150,
                "column_2_problem": 300,
                "column_2_answer": 400,
            },
        ),
        LayoutChoice.ONE_COLUMN: LayoutConfig(
            columns=["column_1"],
            column_limits=[30],
            x_positions={
                "column_1_problem": 50,
                "column_1_answer": 150,
            },
        ),
        LayoutChoice.MIXED: LayoutConfig(
            columns=["column_1", "column_2"],
            column_limits=[20, 10],
            x_positions={
                "column_1_problem": 50,
                "column_1_answer": 150,
                "column_2_problem": 300,
                "column_2_answer": 400,
            },
        ),
    }

    def calculate_layout(
        self,
        num_problems: int,
        layout_choice: LayoutChoice = LayoutChoice.TWO_COLUMN,
    ) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int, int, int]]]:
        """Calculate positions and ROIs for problems based on layout choice.

        Args:
            num_problems: Number of problems to layout.
            layout_choice: Desired layout configuration.

        Returns:
            Tuple of (positions, ROIs) where:
                positions is a list of (x_problem, y, x_answer) tuples
                ROIs is a list of (x1, y1, x2, y2) tuples

        Raises:
            ValueError: If layout cannot accommodate number of problems.
        """
        config = self.LAYOUT_CONFIGS[layout_choice]
        total_capacity = sum(config.column_limits)

        if num_problems > total_capacity:
            raise ValueError(
                f"Layout {layout_choice.value} cannot fit {num_problems} problems "
                f"(maximum {total_capacity})"
            )

        positions = []
        rois = []
        y_positions = {col: config.y_start for col in config.columns}
        problem_index = 0

        for col_index, column in enumerate(config.columns):
            x_problem = config.x_positions[f"{column}_problem"]
            x_answer = config.x_positions[f"{column}_answer"]
            limit = config.column_limits[col_index]

            for _ in range(limit):
                if problem_index >= num_problems:
                    break

                y_position = y_positions[column]

                # Add problem and ROI positions
                positions.append((x_problem, y_position, x_answer))
                x1, y1_offset, x2, y2_offset = config.answer_box_dimensions
                rois.append(
                    (
                        x_answer + x1,
                        y_position + y1_offset,
                        x_answer + x2,
                        y_position + y2_offset,
                    )
                )

                # Update y_position
                y_positions[column] -= config.row_spacing
                problem_index += 1

        return positions, rois
