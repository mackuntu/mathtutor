"""Answer parser for normalizing and comparing OCR-extracted answers."""

import logging
import re
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


class AnswerParser:
    """
    Parses OCR text into normalized answer formats and compares answers.

    Handles formats:
    - Integers: 42, -5
    - Decimals: 0.33, 3.14159
    - Remainders: 5 R2, 5r2, 5 r 2
    - Fractions: 1/2, 3/4
    """

    # Common OCR misreadings for digits
    OCR_CORRECTIONS = {
        "O": "0",
        "o": "0",
        "l": "1",
        "I": "1",
        "|": "1",
        "S": "5",
        "s": "5",
        "B": "8",
        "g": "9",
        "q": "9",
        "Z": "2",
        "z": "2",
    }

    def parse(self, text: Optional[str]) -> Optional[Union[int, float, str]]:
        """
        Parse OCR text into a normalized answer value.

        Args:
            text: Raw OCR text

        Returns:
            Parsed value (int, float, or string for special formats) or None
        """
        if not text:
            return None

        # Clean and correct OCR errors
        cleaned = self._apply_ocr_corrections(text.strip())

        # Try different parsing strategies
        parsers = [
            self._parse_integer,
            self._parse_decimal,
            self._parse_remainder,
            self._parse_fraction,
        ]

        for parser in parsers:
            result = parser(cleaned)
            if result is not None:
                logger.debug(f"Parsed '{text}' -> {result} (type: {type(result).__name__})")
                return result

        logger.warning(f"Could not parse answer: '{text}'")
        return None

    def compare(self, student_answer: Any, correct_answer: Any, tolerance: float = 0.001) -> bool:
        """
        Compare a student answer with the correct answer.

        Args:
            student_answer: Parsed student answer
            correct_answer: Correct answer value
            tolerance: Tolerance for floating point comparison

        Returns:
            True if answers match, False otherwise
        """
        if student_answer is None or correct_answer is None:
            return False

        # Parse both answers if they're strings
        if isinstance(student_answer, str):
            student_answer = self.parse(student_answer)
        if isinstance(correct_answer, str):
            correct_answer = self.parse(correct_answer)

        if student_answer is None:
            return False

        # Handle numeric comparison with tolerance
        if isinstance(student_answer, (int, float)) and isinstance(correct_answer, (int, float)):
            return abs(float(student_answer) - float(correct_answer)) <= tolerance

        # Handle string comparison (for remainders, fractions)
        if isinstance(student_answer, str) and isinstance(correct_answer, str):
            return self._normalize_string_answer(student_answer) == self._normalize_string_answer(correct_answer)

        # Handle mixed type comparison
        # Try converting both to float
        try:
            student_float = self._to_float(student_answer)
            correct_float = self._to_float(correct_answer)
            if student_float is not None and correct_float is not None:
                return abs(student_float - correct_float) <= tolerance
        except (ValueError, TypeError):
            pass

        return str(student_answer).strip() == str(correct_answer).strip()

    def _apply_ocr_corrections(self, text: str) -> str:
        """Apply common OCR error corrections."""
        result = []
        for char in text:
            result.append(self.OCR_CORRECTIONS.get(char, char))
        return "".join(result)

    def _parse_integer(self, text: str) -> Optional[int]:
        """Parse as integer."""
        # Remove spaces
        text = text.replace(" ", "")

        # Check for integer pattern
        if re.match(r"^-?\d+$", text):
            try:
                return int(text)
            except ValueError:
                return None
        return None

    def _parse_decimal(self, text: str) -> Optional[float]:
        """Parse as decimal number."""
        # Remove spaces
        text = text.replace(" ", "")

        # Check for decimal pattern
        if re.match(r"^-?\d+\.\d+$", text):
            try:
                return float(text)
            except ValueError:
                return None
        return None

    def _parse_remainder(self, text: str) -> Optional[str]:
        """
        Parse as division with remainder (e.g., "5 R2", "5r2").

        Returns normalized format "Q R R" where Q is quotient and R is remainder.
        """
        # Pattern: quotient R remainder (with optional spaces)
        pattern = r"^(\d+)\s*[Rr]\s*(\d+)$"
        match = re.match(pattern, text)

        if match:
            quotient = match.group(1)
            remainder = match.group(2)
            return f"{quotient} R {remainder}"

        return None

    def _parse_fraction(self, text: str) -> Optional[str]:
        """
        Parse as fraction (e.g., "1/2", "3/4").

        Returns normalized format "N/D" where N is numerator and D is denominator.
        """
        # Remove spaces
        text = text.replace(" ", "")

        # Pattern: numerator/denominator
        pattern = r"^(-?\d+)/(\d+)$"
        match = re.match(pattern, text)

        if match:
            numerator = match.group(1)
            denominator = match.group(2)
            return f"{numerator}/{denominator}"

        return None

    def _normalize_string_answer(self, answer: str) -> str:
        """Normalize a string answer for comparison."""
        # Remove all whitespace
        answer = re.sub(r"\s+", "", answer)
        # Convert to lowercase
        answer = answer.lower()
        return answer

    def _to_float(self, value: Any) -> Optional[float]:
        """Convert a value to float if possible."""
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # Handle fraction
            if "/" in value:
                parts = value.split("/")
                if len(parts) == 2:
                    try:
                        return float(parts[0]) / float(parts[1])
                    except (ValueError, ZeroDivisionError):
                        return None

            # Try direct conversion
            try:
                return float(value)
            except ValueError:
                return None

        return None
