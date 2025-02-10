"""Module for worksheet data structures and operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class Problem:
    """Represents a single math problem."""

    question: str
    answer: str
    roi: Optional[Tuple[int, int, int, int]] = None
    student_answer: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class Worksheet:
    """Represents a complete math worksheet."""

    id: str
    version: str = "1.0"
    problems: List[Problem] = None
    template_id: Optional[str] = None
    created_at: datetime = None
    graded_at: Optional[datetime] = None
    grade: Optional[str] = None
    total_correct: Optional[int] = None
    total_questions: Optional[int] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.problems is None:
            self.problems = []
        if self.created_at is None:
            self.created_at = datetime.now()

    def add_problem(
        self,
        question: str,
        answer: str,
        roi: Optional[Tuple[int, int, int, int]] = None,
    ) -> None:
        """Add a problem to the worksheet."""
        self.problems.append(Problem(question=question, answer=answer, roi=roi))

    def set_student_answer(self, index: int, answer: str, confidence: float) -> None:
        """Set a student's answer for a specific problem."""
        if 0 <= index < len(self.problems):
            self.problems[index].student_answer = answer
            self.problems[index].confidence = confidence

    def get_correct_answers(self) -> List[str]:
        """Get list of correct answers."""
        return [problem.answer for problem in self.problems]

    def get_student_answers(self) -> List[Optional[str]]:
        """Get list of student answers."""
        return [problem.student_answer for problem in self.problems]

    def get_rois(self) -> List[Optional[Tuple[int, int, int, int]]]:
        """Get list of ROIs."""
        return [problem.roi for problem in self.problems]

    def set_grade(self, grade: str, total_correct: int) -> None:
        """Set the grade and mark as graded."""
        self.grade = grade
        self.total_correct = total_correct
        self.total_questions = len(self.problems)
        self.graded_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert worksheet to dictionary for storage."""
        return {
            "id": self.id,
            "version": self.version,
            "problems": [
                {
                    "question": p.question,
                    "answer": p.answer,
                    "roi": p.roi,
                    "student_answer": p.student_answer,
                    "confidence": p.confidence,
                }
                for p in self.problems
            ],
            "template_id": self.template_id,
            "created_at": self.created_at.isoformat(),
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "grade": self.grade,
            "total_correct": self.total_correct,
            "total_questions": self.total_questions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Worksheet":
        """Create worksheet from dictionary."""
        problems = [Problem(**p) for p in data.get("problems", [])]
        return cls(
            id=data["id"],
            version=data.get("version", "1.0"),
            problems=problems,
            template_id=data.get("template_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            graded_at=(
                datetime.fromisoformat(data["graded_at"])
                if data.get("graded_at")
                else None
            ),
            grade=data.get("grade"),
            total_correct=data.get("total_correct"),
            total_questions=data.get("total_questions"),
        )
