"""Grading module for automatic worksheet grading via image upload."""

from .grader import Grader, GradingResult
from .ocr_service import OCRService
from .answer_parser import AnswerParser

__all__ = ["Grader", "GradingResult", "OCRService", "AnswerParser"]
