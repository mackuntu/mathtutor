"""Main application module for math worksheet generation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from src.document.renderer import DocumentRenderer
from src.document.template import LayoutChoice
from src.problem_generator import ProblemGenerator

logger = logging.getLogger(__name__)


class MathTutor:
    """Main application class for math worksheet generation."""

    def __init__(self, output_dir: str = "data"):
        """Initialize MathTutor application.

        Args:
            output_dir: Directory for storing generated files.
        """
        self.output_dir = Path(output_dir)

        # Create output directories
        self.worksheets_dir = self.output_dir / "worksheets"
        self.answer_keys_dir = self.output_dir / "answer_keys"

        for directory in [self.worksheets_dir, self.answer_keys_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.generator = ProblemGenerator()
        self.renderer = DocumentRenderer()

    def generate_worksheet(
        self,
        age: int,
        count: Optional[int] = 30,
        layout: LayoutChoice = LayoutChoice.TWO_COLUMN,
        difficulty: Optional[float] = None,
    ) -> Tuple[str, str]:
        """Generate a new worksheet and answer key.

        Args:
            age: Age of student.
            count: Number of problems (defaults to 30).
            layout: Desired layout configuration.
            difficulty: Optional difficulty level from 0.0 to 1.0.
                      If None, uses current school year progress.

        Returns:
            Tuple of (worksheet_path, answer_key_path).

        Raises:
            ValueError: If age is not supported or difficulty is invalid.
        """
        # Generate problems
        problems, answers = self.generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )

        # Generate unique ID and paths
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        worksheet_id = f"math_worksheet_{timestamp}"

        worksheet_path = self.worksheets_dir / f"{worksheet_id}.pdf"
        answer_key_path = self.answer_keys_dir / f"{worksheet_id}_key.pdf"

        # Create worksheet and answer key
        self.renderer.create_worksheet(
            str(worksheet_path), problems, worksheet_id, layout
        )
        self.renderer.create_answer_key(
            str(answer_key_path), problems, answers, worksheet_id, layout
        )

        return str(worksheet_path), str(answer_key_path)


if __name__ == "__main__":
    # Example usage
    tutor = MathTutor()
    worksheet_path, answer_key_path = tutor.generate_worksheet(age=6)
    print(f"Generated worksheet: {worksheet_path}")
    print(f"Generated answer key: {answer_key_path}")
