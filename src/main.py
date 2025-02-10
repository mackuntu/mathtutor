"""Main application module for math worksheet generation and grading."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

from core.grading import GradingService
from core.handwriting import HandwritingSimulator
from core.ocr import OCRConfig, OCREngine
from core.worksheet import Worksheet
from document.renderer import DocumentRenderer
from document.template import LayoutChoice
from grading.generator import ProblemGenerator
from storage.db import DatabaseConnection

logger = logging.getLogger(__name__)


class MathTutor:
    """Main application class for math worksheet management."""

    def __init__(
        self,
        output_dir: str = "data",
        ocr_config: Optional[OCRConfig] = None,
        db: Optional[DatabaseConnection] = None,
    ):
        """Initialize MathTutor application.

        Args:
            output_dir: Directory for storing generated files.
            ocr_config: Optional OCR configuration.
            db: Optional database connection.
        """
        self.output_dir = Path(output_dir)
        self.db = db or DatabaseConnection()

        # Create output directories
        self.worksheets_dir = self.output_dir / "worksheets"
        self.answer_keys_dir = self.output_dir / "answer_keys"
        self.filled_dir = self.output_dir / "filled_worksheets"

        for directory in [self.worksheets_dir, self.answer_keys_dir, self.filled_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.generator = ProblemGenerator()
        self.renderer = DocumentRenderer()
        self.grading_service = GradingService(ocr_config=ocr_config)
        self.simulator = HandwritingSimulator()

    def generate_worksheet(
        self,
        age: int,
        count: Optional[int] = None,
        layout: LayoutChoice = LayoutChoice.TWO_COLUMN,
    ) -> Tuple[str, str]:
        """Generate a new worksheet and answer key.

        Args:
            age: Age of student.
            count: Optional number of problems.
            layout: Desired layout configuration.

        Returns:
            Tuple of (worksheet_path, answer_key_path).

        Raises:
            ValueError: If age is not supported.
        """
        # Generate problems
        problems, answers = self.generator.generate_math_problems(age, count)

        # Generate unique ID and paths
        timestamp = datetime.now().strftime("%Y-%m-%d")
        worksheet_id = f"math_worksheet_{timestamp}"

        worksheet_path = self.worksheets_dir / f"{worksheet_id}.pdf"
        answer_key_path = self.answer_keys_dir / f"{worksheet_id}_key.pdf"

        # Create worksheet and answer key
        template_id = self.renderer.create_worksheet(
            str(worksheet_path), problems, worksheet_id, layout
        )
        self.renderer.create_answer_key(
            str(answer_key_path), problems, answers, worksheet_id, layout
        )

        # Create and save worksheet object
        worksheet = Worksheet(
            id=worksheet_id,
            version="1.0",
            template_id=template_id,
        )
        for problem, answer in zip(problems, answers):
            worksheet.add_problem(question=problem, answer=answer)

        # Save to database
        self.db.save_worksheet(
            worksheet_id=worksheet.id,
            version=worksheet.version,
            data=worksheet.to_dict(),
            template_id=template_id,
        )

        return str(worksheet_path), str(answer_key_path)

    def grade_worksheet(
        self, image_path: str, worksheet_id: Optional[str] = None
    ) -> Worksheet:
        """Grade a filled worksheet.

        Args:
            image_path: Path to scanned worksheet image.
            worksheet_id: Optional worksheet ID. If None, extracts from QR code.

        Returns:
            Graded worksheet object.

        Raises:
            ValueError: If worksheet not found or image invalid.
        """
        # Load worksheet data
        if worksheet_id is None:
            # Extract from QR code
            pass  # TODO: Implement QR code reading

        worksheet_data = self.db.fetch_worksheet(worksheet_id, "1.0")
        if not worksheet_data:
            raise ValueError(f"Worksheet {worksheet_id} not found")

        worksheet = Worksheet.from_dict(worksheet_data)

        # Grade the worksheet
        image = Image.open(image_path)
        self.grading_service.grade_worksheet(worksheet, [image])

        # Save graded worksheet
        self.db.save_worksheet(
            worksheet_id=worksheet.id,
            version=worksheet.version,
            data=worksheet.to_dict(),
            template_id=worksheet.template_id,
            grade=worksheet.grade,
            total_correct=worksheet.total_correct,
            total_questions=worksheet.total_questions,
        )

        return worksheet

    def simulate_student(
        self,
        worksheet_id: str,
        accuracy: float = 1.0,
        output_path: Optional[str] = None,
    ) -> str:
        """Simulate a student filling out a worksheet.

        Args:
            worksheet_id: ID of worksheet to simulate.
            accuracy: Probability of correct answers (0.0 to 1.0).
            output_path: Optional path for output image.

        Returns:
            Path to simulated worksheet image.

        Raises:
            ValueError: If worksheet not found.
        """
        # Load worksheet
        worksheet_data = self.db.fetch_worksheet(worksheet_id, "1.0")
        if not worksheet_data:
            raise ValueError(f"Worksheet {worksheet_id} not found")

        worksheet = Worksheet.from_dict(worksheet_data)

        # Generate simulated answers
        answer_images = self.grading_service.simulate_student_answers(
            worksheet, accuracy, self.simulator
        )

        # Create output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(
                self.filled_dir / f"{worksheet_id}_{timestamp}_filled.jpg"
            )

        # Combine images into final worksheet
        # TODO: Implement image composition

        return output_path
