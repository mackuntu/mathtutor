"""Module for grading worksheets using OCR."""

import logging
import random
from datetime import datetime
from typing import List, Optional, Tuple

from PIL import Image

from .handwriting import HandwritingSimulator
from .ocr import OCRConfig, OCREngine, OCRResult
from .worksheet import Problem, Worksheet

logger = logging.getLogger(__name__)


class GradingService:
    """Service for grading worksheets using OCR."""

    GRADE_SCALE = {
        0.9: "A",  # 90% and above
        0.8: "B",  # 80-89%
        0.7: "C",  # 70-79%
        0.6: "D",  # 60-69%
        # Below 60% is F
    }

    def __init__(
        self,
        ocr_engine: Optional[OCREngine] = None,
        ocr_config: Optional[OCRConfig] = None,
    ):
        """Initialize the grading service.

        Args:
            ocr_engine: Optional OCR engine to use. If None, creates a new one.
            ocr_config: Optional configuration for creating a new OCR engine.
        """
        self.ocr = ocr_engine or OCREngine(config=ocr_config)

    def _normalize_answer(self, answer: str) -> str:
        """Normalize an answer string for comparison.

        Args:
            answer: Raw answer string.

        Returns:
            Normalized answer string.
        """
        if not answer:
            return ""

        # Remove whitespace and convert to lowercase
        answer = answer.strip().lower()

        # Remove trailing decimal point
        if answer.endswith("."):
            answer = answer[:-1]

        # Remove leading zeros
        if "." in answer:
            integer, decimal = answer.split(".")
            if integer:
                integer = str(int(integer))
            answer = f"{integer}.{decimal}" if integer else f"0.{decimal}"
        else:
            try:
                answer = str(int(answer))
            except ValueError:
                pass

        return answer

    def _answers_match(self, expected: str, actual: str) -> bool:
        """Check if two answers match after normalization.

        Args:
            expected: Expected answer string.
            actual: Actual answer string.

        Returns:
            True if answers match after normalization.
        """
        return self._normalize_answer(expected) == self._normalize_answer(actual)

    def grade_answers(
        self,
        correct_answers: List[str],
        student_answers: List[OCRResult],
    ) -> Tuple[int, int]:
        """Grade a list of answers.

        Args:
            correct_answers: List of correct answers.
            student_answers: List of OCR results with student answers.

        Returns:
            Tuple of (total correct, total questions).
        """
        total_correct = 0
        total_questions = len(correct_answers)

        for correct, result in zip(correct_answers, student_answers):
            if result and result.text and self._answers_match(correct, result.text):
                total_correct += 1
            elif not result:
                logger.warning(f"OCR failed for answer: {result.error}")

        return total_correct, total_questions

    def grade_worksheet(
        self, worksheet: Worksheet, answer_images: List[Image.Image]
    ) -> None:
        """Grade a worksheet using OCR on the provided answer images.

        Args:
            worksheet: Worksheet to grade.
            answer_images: List of answer images to grade. Can be a single image containing all answers
                          or individual images for each answer.

        Raises:
            ValueError: If no images are provided.
        """
        if not answer_images:
            raise ValueError("No answer images provided")

        # If a single image is provided, extract ROIs from it
        if len(answer_images) == 1:
            full_image = answer_images[0]
            roi_images = []
            for problem in worksheet.problems:
                if not problem.roi:
                    raise ValueError(f"Problem {problem.question} has no ROI defined")
                x1, y1, x2, y2 = problem.roi
                roi_image = full_image.crop((x1, y1, x2, y2))
                roi_images.append(roi_image)
            answer_images = roi_images
        elif len(answer_images) != len(worksheet.problems):
            raise ValueError(
                f"Number of images ({len(answer_images)}) doesn't match "
                f"number of problems ({len(worksheet.problems)})"
            )

        # Process each answer
        total_correct = 0
        for problem, image in zip(worksheet.problems, answer_images):
            result = self.ocr.read_text(image)
            if result and result.text:
                student_answer = self._normalize_answer(result.text)
                correct_answer = self._normalize_answer(problem.answer)
                problem.student_answer = student_answer
                problem.confidence = result.confidence
                if student_answer == correct_answer:
                    total_correct += 1

        # Calculate grade
        total_questions = len(worksheet.problems)
        if total_questions > 0:
            score = total_correct / total_questions
            worksheet.grade = next(
                (
                    grade
                    for threshold, grade in sorted(
                        self.GRADE_SCALE.items(), reverse=True
                    )
                    if score >= threshold
                ),
                "F",
            )
        else:
            worksheet.grade = "F"

        worksheet.total_correct = total_correct
        worksheet.total_questions = total_questions
        worksheet.graded_at = datetime.now()

    def simulate_student_answers(
        self,
        worksheet: Worksheet,
        accuracy: float = 1.0,
        simulator: Optional[HandwritingSimulator] = None,
    ) -> List[Image.Image]:
        """Simulate student answers for a worksheet.

        Args:
            worksheet: Worksheet to simulate answers for.
            accuracy: Probability of writing correct answer (0.0 to 1.0).
            simulator: Optional handwriting simulator to use.

        Returns:
            List of simulated answer images.

        Raises:
            ValueError: If accuracy is not between 0 and 1.
        """
        if not 0 <= accuracy <= 1:
            raise ValueError("Accuracy must be between 0 and 1")

        simulator = simulator or HandwritingSimulator()
        images = []

        for problem in worksheet.problems:
            if not problem.roi:
                raise ValueError(f"Problem {problem.question} has no ROI defined")

            if accuracy >= 1.0 or random.random() < accuracy:
                answer = problem.answer
            else:
                # Generate an incorrect answer
                try:
                    correct = int(problem.answer)
                    answer = str(correct + random.choice([-1, 1]))
                except ValueError:
                    answer = problem.answer + "?"

            image = simulator.write_answer(answer, problem.roi)
            images.append(image)

        return images
