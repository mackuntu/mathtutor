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


@dataclass
class LayoutConfig:
    """Configuration for worksheet layout."""

    columns: List[str]
    column_limits: List[int]
    x_positions: Dict[str, int]
    y_start: int = 680
    row_spacing: int = 40
    word_problem_spacing: int = 80  # Extra space for word problems
    answer_box_dimensions: Tuple[int, int, int, int] = (0, -10, 80, 20)


class TemplateManager:
    """Manages worksheet templates and layouts."""

    # Default layout configurations
    LAYOUT_CONFIGS = {
        LayoutChoice.TWO_COLUMN: LayoutConfig(
            columns=["column_1", "column_2"],
            column_limits=[15, 15],
            x_positions={
                "column_1_problem": 50,
                "column_1_answer": 180,
                "column_2_problem": 350,
                "column_2_answer": 480,
            },
        ),
        LayoutChoice.ONE_COLUMN: LayoutConfig(
            columns=["column_1"],
            column_limits=[30],
            x_positions={
                "column_1_problem": 50,
                "column_1_answer": 480,
            },
        ),
    }

    @staticmethod
    def choose_layout(problems: List[str]) -> LayoutChoice:
        """Choose the best layout based on problem lengths.

        Args:
            problems: List of problem strings.

        Returns:
            The most appropriate layout choice.
        """
        # Count word problems
        word_problems = sum(1 for p in problems if len(p) > 30 or "?" in p)

        # Use one column if there are too many word problems
        if word_problems > len(problems) * 0.3:  # More than 30% are word problems
            return LayoutChoice.ONE_COLUMN
        return LayoutChoice.TWO_COLUMN

    def calculate_layout(
        self,
        num_problems: int,
        problems: List[str],
        layout_choice: Optional[LayoutChoice] = None,
    ) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int, int, int]]]:
        """Calculate positions and ROIs for problems based on layout choice.

        Args:
            num_problems: Number of problems to layout
            problems: List of problem strings
            layout_choice: Optional layout choice. If None, automatically chosen.

        Returns:
            Tuple of (positions, rois) where:
            - positions is a list of (x_problem, y, x_answer) tuples
            - rois is a list of (x1, y1, x2, y2) tuples for answer boxes
        """
        if layout_choice is None:
            layout_choice = self.choose_layout(problems)

        config = self.LAYOUT_CONFIGS[layout_choice]
        positions = []
        rois = []

        # Initialize y-positions for each column
        y_positions = {col: config.y_start for col in config.columns}

        # Calculate positions column by column
        for i in range(num_problems):
            # Determine which column to use
            col_idx = i % len(config.columns)
            column = config.columns[col_idx]

            # Get x-positions for this column
            x_problem = config.x_positions[f"{column}_problem"]
            x_answer = config.x_positions[f"{column}_answer"]

            # Get current y-position for this column
            y = y_positions[column]

            # Add position
            positions.append((x_problem, y, x_answer))

            # Calculate ROI
            x1, y1_offset, x2, y2_offset = config.answer_box_dimensions
            rois.append(
                (
                    x_answer + x1,
                    y + y1_offset,
                    x_answer + x2,
                    y + y2_offset,
                )
            )

            # Update y-position for next problem in this column
            y_positions[column] -= config.row_spacing

        return positions, rois
