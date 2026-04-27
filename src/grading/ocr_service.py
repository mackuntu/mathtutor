"""OCR service for extracting handwritten answers from worksheet images."""

import logging
from typing import List, Optional, Tuple, Union

import easyocr
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class OCRService:
    """
    OCR service using EasyOCR for extracting handwritten text from images.

    EasyOCR is a local OCR solution that doesn't require cloud API keys.
    Note: First use will download ~200MB model files.
    """

    _reader: Optional[easyocr.Reader] = None

    def __init__(self, languages: List[str] = None):
        """
        Initialize OCR service.

        Args:
            languages: List of language codes (default: ['en'])
        """
        self.languages = languages or ["en"]

    @property
    def reader(self) -> easyocr.Reader:
        """Lazy-load the EasyOCR reader to avoid loading models until needed."""
        if OCRService._reader is None:
            logger.info("Initializing EasyOCR reader (this may take a moment on first use)...")
            OCRService._reader = easyocr.Reader(self.languages, gpu=False)
            logger.info("EasyOCR reader initialized")
        return OCRService._reader

    def extract_text_from_image(self, image: Image.Image) -> List[Tuple[str, float]]:
        """
        Extract all text from an image.

        Args:
            image: PIL Image object

        Returns:
            List of (text, confidence) tuples
        """
        try:
            # Convert PIL Image to numpy array
            image_array = np.array(image)

            # Run OCR
            results = self.reader.readtext(image_array)

            # Extract text and confidence from results
            # Result format: [(bbox, text, confidence), ...]
            extracted = []
            for bbox, text, confidence in results:
                extracted.append((text.strip(), confidence))
                logger.debug(f"OCR found: '{text}' (confidence: {confidence:.2f})")

            return extracted

        except Exception as e:
            logger.error(f"Error during OCR: {str(e)}")
            return []

    def extract_text_from_region(
        self, image: Image.Image, region: Tuple[int, int, int, int]
    ) -> Optional[str]:
        """
        Extract text from a specific region of an image.

        Args:
            image: PIL Image object
            region: Tuple of (left, top, right, bottom) coordinates

        Returns:
            Extracted text or None if extraction failed
        """
        try:
            # Crop the region
            cropped = image.crop(region)

            # Extract text
            results = self.extract_text_from_image(cropped)

            if results:
                # Return the highest confidence result
                results.sort(key=lambda x: x[1], reverse=True)
                return results[0][0]

            return None

        except Exception as e:
            logger.error(f"Error extracting text from region: {str(e)}")
            return None

    def extract_answers_from_worksheet(
        self,
        image: Image.Image,
        num_problems: int,
        answer_regions: List[Tuple[int, int, int, int]] = None,
        return_crops: bool = False,
    ) -> Union[List[Optional[str]], Tuple[List[Optional[str]], List[Image.Image]]]:
        """
        Extract answers from a worksheet image.

        If answer_regions is provided, extracts from those specific regions.
        Otherwise, performs full-image OCR and attempts to identify answer patterns.

        Args:
            image: PIL Image object of the worksheet
            num_problems: Expected number of problems/answers
            answer_regions: Optional list of (left, top, right, bottom) tuples for answer locations
            return_crops: If True, also return the cropped images for each answer region

        Returns:
            If return_crops is False: List of extracted answer strings
            If return_crops is True: Tuple of (answers list, cropped images list)
        """
        cropped_images = []

        if answer_regions:
            # Extract from specific regions
            answers = []
            for region in answer_regions:
                # Crop the region
                x1, y1, x2, y2 = region
                # Ensure valid crop region
                x1 = max(0, min(x1, image.width - 1))
                y1 = max(0, min(y1, image.height - 1))
                x2 = max(x1 + 1, min(x2, image.width))
                y2 = max(y1 + 1, min(y2, image.height))

                cropped = image.crop((x1, y1, x2, y2))
                if return_crops:
                    cropped_images.append(cropped)

                # Extract text from the cropped region
                text = self._extract_text_from_crop(cropped)
                answers.append(text)

            if return_crops:
                return answers, cropped_images
            return answers

        # Full image extraction - get all text
        all_text = self.extract_text_from_image(image)

        # Filter for likely numeric answers (digits, decimals, fractions)
        answer_candidates = []
        for text, confidence in all_text:
            # Clean the text
            cleaned = self._clean_answer_text(text)
            if cleaned and confidence > 0.3:  # Minimum confidence threshold
                answer_candidates.append(cleaned)

        logger.info(f"Found {len(answer_candidates)} answer candidates for {num_problems} problems")

        # If we have roughly the right number of candidates, return them
        # Otherwise return what we have with None padding
        answers = answer_candidates[:num_problems]
        while len(answers) < num_problems:
            answers.append(None)

        if return_crops:
            # No specific regions, so no crops to return
            return answers, [None] * num_problems
        return answers

    def _extract_text_from_crop(self, cropped: Image.Image) -> Optional[str]:
        """
        Extract text from a cropped image region.

        Args:
            cropped: PIL Image object (already cropped)

        Returns:
            Extracted text or None if extraction failed
        """
        try:
            results = self.extract_text_from_image(cropped)

            if results:
                # Find the best result (highest confidence, cleaned)
                best_text = None
                best_confidence = 0.0

                for text, confidence in results:
                    cleaned = self._clean_answer_text(text)
                    if cleaned and confidence > best_confidence:
                        best_text = cleaned
                        best_confidence = confidence

                return best_text

            return None

        except Exception as e:
            logger.error(f"Error extracting text from crop: {str(e)}")
            return None

    def _clean_answer_text(self, text: str) -> Optional[str]:
        """
        Clean OCR text to extract answer value.

        Args:
            text: Raw OCR text

        Returns:
            Cleaned answer text or None if not a valid answer
        """
        if not text:
            return None

        text = text.strip()

        # Remove common OCR artifacts
        text = text.replace("=", "").strip()
        text = text.replace(":", "").strip()

        # Check if it looks like a numeric answer
        # Allow digits, decimal point, minus sign, R for remainder
        valid_chars = set("0123456789.-/Rr ")
        if all(c in valid_chars for c in text):
            return text

        return None
