"""Grader module that orchestrates the grading pipeline."""

import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional

from PIL import Image

from .ocr_service import OCRService
from .answer_parser import AnswerParser

logger = logging.getLogger(__name__)


@dataclass
class ProblemResult:
    """Result for a single problem."""

    problem_index: int
    problem_text: str
    correct_answer: Any
    student_answer: Optional[str]
    parsed_student_answer: Any
    is_correct: bool


@dataclass
class GradingResult:
    """Complete grading result for a worksheet."""

    worksheet_id: Optional[str] = None
    total_problems: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    unanswered_count: int = 0
    score_percentage: float = 0.0
    problem_results: List[ProblemResult] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def incorrect_indices(self) -> List[int]:
        """Get indices of incorrect problems."""
        return [r.problem_index for r in self.problem_results if not r.is_correct and r.student_answer is not None]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "worksheet_id": self.worksheet_id,
            "total_problems": self.total_problems,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "unanswered_count": self.unanswered_count,
            "score_percentage": round(self.score_percentage, 1),
            "problem_results": [
                {
                    "problem_index": r.problem_index,
                    "problem_text": r.problem_text,
                    "correct_answer": r.correct_answer,
                    "student_answer": r.student_answer,
                    "parsed_student_answer": r.parsed_student_answer,
                    "is_correct": r.is_correct,
                }
                for r in self.problem_results
            ],
            "incorrect_indices": self.incorrect_indices,
            "error": self.error,
        }


class Grader:
    """
    Orchestrates the worksheet grading pipeline.

    Pipeline:
    1. Extract answers using OCR
    2. Parse and normalize answers
    3. Compare with correct answers
    4. Return grading results
    """

    def __init__(self):
        """Initialize grader with required services."""
        self.ocr_service = OCRService()
        self.answer_parser = AnswerParser()

    def grade_worksheet_image(
        self,
        image: Image.Image,
        problems: List[str],
        correct_answers: List[Any],
        worksheet_id: Optional[str] = None,
    ) -> GradingResult:
        """
        Grade a worksheet from an uploaded image.

        Args:
            image: PIL Image of the completed worksheet
            problems: List of problem text strings
            correct_answers: List of correct answers
            worksheet_id: Optional worksheet ID

        Returns:
            GradingResult with detailed grading information
        """
        result = GradingResult()

        try:
            result.worksheet_id = worksheet_id
            result.total_problems = len(problems)

            # Extract answers from the image using OCR
            logger.info(f"Extracting {len(problems)} answers from image")
            extracted_answers = self.ocr_service.extract_answers_from_worksheet(
                image, num_problems=len(problems)
            )

            # Grade each problem
            correct_count = 0
            incorrect_count = 0
            unanswered_count = 0

            for i, (problem, correct_answer) in enumerate(zip(problems, correct_answers)):
                student_answer = extracted_answers[i] if i < len(extracted_answers) else None

                # Parse the student answer
                parsed_answer = self.answer_parser.parse(student_answer) if student_answer else None

                # Compare answers
                if student_answer is None or student_answer.strip() == "":
                    is_correct = False
                    unanswered_count += 1
                elif self.answer_parser.compare(parsed_answer, correct_answer):
                    is_correct = True
                    correct_count += 1
                else:
                    is_correct = False
                    incorrect_count += 1

                problem_result = ProblemResult(
                    problem_index=i,
                    problem_text=problem,
                    correct_answer=correct_answer,
                    student_answer=student_answer,
                    parsed_student_answer=parsed_answer,
                    is_correct=is_correct,
                )
                result.problem_results.append(problem_result)

            result.correct_count = correct_count
            result.incorrect_count = incorrect_count
            result.unanswered_count = unanswered_count

            # Calculate score (counting only answered problems)
            answered_count = result.total_problems - unanswered_count
            if answered_count > 0:
                result.score_percentage = (correct_count / answered_count) * 100
            else:
                result.score_percentage = 0.0

            logger.info(
                f"Grading complete: {correct_count}/{result.total_problems} correct "
                f"({result.score_percentage:.1f}%)"
            )

        except Exception as e:
            logger.error(f"Error during grading: {str(e)}")
            result.error = str(e)

        return result

    def grade_with_manual_answers(
        self,
        student_answers: List[Optional[str]],
        problems: List[str],
        correct_answers: List[Any],
        worksheet_id: Optional[str] = None,
    ) -> GradingResult:
        """
        Grade a worksheet with manually provided answers (for OCR correction).

        Args:
            student_answers: List of student answers (strings)
            problems: List of problem text strings
            correct_answers: List of correct answers
            worksheet_id: Optional worksheet ID

        Returns:
            GradingResult with detailed grading information
        """
        result = GradingResult()
        result.worksheet_id = worksheet_id
        result.total_problems = len(problems)

        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0

        for i, (problem, correct_answer) in enumerate(zip(problems, correct_answers)):
            student_answer = student_answers[i] if i < len(student_answers) else None

            # Parse the student answer
            parsed_answer = self.answer_parser.parse(student_answer) if student_answer else None

            # Compare answers
            if student_answer is None or (isinstance(student_answer, str) and student_answer.strip() == ""):
                is_correct = False
                unanswered_count += 1
            elif self.answer_parser.compare(parsed_answer, correct_answer):
                is_correct = True
                correct_count += 1
            else:
                is_correct = False
                incorrect_count += 1

            problem_result = ProblemResult(
                problem_index=i,
                problem_text=problem,
                correct_answer=correct_answer,
                student_answer=student_answer,
                parsed_student_answer=parsed_answer,
                is_correct=is_correct,
            )
            result.problem_results.append(problem_result)

        result.correct_count = correct_count
        result.incorrect_count = incorrect_count
        result.unanswered_count = unanswered_count

        # Calculate score
        answered_count = result.total_problems - unanswered_count
        if answered_count > 0:
            result.score_percentage = (correct_count / answered_count) * 100
        else:
            result.score_percentage = 0.0

        return result
