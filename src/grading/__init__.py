"""Grading module for automatic worksheet grading via image upload."""

from .grader import Grader, GradingResult
from .ocr_service import OCRService
from .answer_parser import AnswerParser
from .image_alignment import (
    calculate_html_grid_rois,
    transform_rois_to_image_coords,
    crop_image_regions,
    image_to_base64,
    base64_to_image,
)
from .image_preprocessing import WorksheetAligner, AlignmentMetadata

__all__ = [
    "Grader",
    "GradingResult",
    "OCRService",
    "AnswerParser",
    "calculate_html_grid_rois",
    "transform_rois_to_image_coords",
    "crop_image_regions",
    "image_to_base64",
    "base64_to_image",
    "WorksheetAligner",
    "AlignmentMetadata",
]
