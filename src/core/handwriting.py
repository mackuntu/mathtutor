"""Module for simulating handwritten text using various fonts and styles."""

import logging
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class HandwritingSimulator:
    """Simulates handwritten text using fonts."""

    DEFAULT_FONTS = [
        "data/fonts/Childrens-Handwriting.ttf",
        "data/fonts/KidsHandwriting.ttf",
        "data/fonts/MessyHandwriting.ttf",
    ]

    def __init__(self, font_paths: Optional[List[str]] = None):
        """Initialize the handwriting simulator.

        Args:
            font_paths: List of paths to font files. If None, uses default fonts.
                       If provided paths fail to load, falls back to default fonts.

        Raises:
            ValueError: If no fonts could be loaded, even after fallback.
        """
        self.fonts = []
        self._font_cache = {}
        provided_paths = font_paths or self.DEFAULT_FONTS

        # Try loading provided fonts
        for path in provided_paths:
            try:
                font = ImageFont.truetype(path, size=36)
                self.fonts.append(font)
                logger.info(f"Successfully loaded font: {path}")
            except (OSError, IOError) as e:
                logger.warning(f"Could not load font: {path} - {str(e)}")

        # If no fonts loaded and custom paths were provided, try default fonts
        if not self.fonts and font_paths is not None:
            logger.warning("No custom fonts loaded, falling back to default fonts")
            for path in self.DEFAULT_FONTS:
                try:
                    font = ImageFont.truetype(path, size=36)
                    self.fonts.append(font)
                    logger.info(f"Successfully loaded default font: {path}")
                except (OSError, IOError) as e:
                    logger.warning(f"Could not load default font: {path} - {str(e)}")

        # If still no fonts, try system fonts
        if not self.fonts:
            logger.warning("No fonts loaded, trying system fonts")
            try:
                # Try to load a basic system font
                font = ImageFont.load_default()
                self.fonts.append(font)
                logger.info("Successfully loaded system default font")
            except Exception as e:
                logger.error(f"Could not load any fonts: {str(e)}")
                raise ValueError("No fonts available")

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font with the specified size, using cache if available.

        Args:
            size: Font size in points.

        Returns:
            Font object at the specified size.
        """
        if size not in self._font_cache:
            # Try each font in order until one works
            for font in self.fonts:
                try:
                    if hasattr(font, "path"):  # TrueType font
                        self._font_cache[size] = ImageFont.truetype(
                            font.path, size=size
                        )
                    else:  # Default font
                        self._font_cache[size] = font
                    break
                except (OSError, IOError) as e:
                    logger.warning(f"Failed to resize font to {size}: {str(e)}")
                    continue
            else:
                # If no font works, use the first font at its current size
                self._font_cache[size] = self.fonts[0]
                logger.warning(
                    f"Failed to resize any font to {size}, using original size"
                )

        return self._font_cache[size]

    def _calculate_font_size(
        self,
        text: str,
        target_width: int,
        target_height: int,
        font_path: str,
        start_size: int = 32,
    ) -> int:
        """Calculate the appropriate font size to fit text in target dimensions.

        Args:
            text: Text to render.
            target_width: Target width in pixels.
            target_height: Target height in pixels.
            font_path: Path to the font file.
            start_size: Initial font size to try.

        Returns:
            Font size that fits the text in the target dimensions.
        """
        size = start_size
        font = self._get_font(size)
        bbox = font.getbbox(text)

        # Scale up or down based on the larger dimension
        if bbox:
            width_ratio = target_width / bbox[2]
            height_ratio = target_height / bbox[3]
            ratio = min(width_ratio, height_ratio) * 0.8  # Leave some padding
            size = int(size * ratio)

        # Ensure minimum size
        return max(12, size)

    def write_answer(
        self, text: str, roi: Tuple[int, int, int, int], is_correct: bool = True
    ) -> Image.Image:
        """Write text in a clear, simple style optimized for OCR.

        Args:
            text: Text to write.
            roi: Region of interest (x1, y1, x2, y2).
            is_correct: Whether to write the correct answer or simulate a mistake.

        Returns:
            PIL Image containing the text.
        """
        if not is_correct:
            # Simulate a mistake by modifying the answer
            try:
                num = int(text)
                offset = random.choice([-2, -1, 1, 2])
                text = str(num + offset)
            except ValueError:
                text = text + "?"

        # Create image with white background
        width = roi[2] - roi[0]
        height = roi[3] - roi[1]
        image = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Make the font size 70% of the height for better visibility
        font_size = int(height * 0.7)
        font = self._get_font(font_size)

        # Calculate text size and position
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center text perfectly
        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # Draw text with solid black color and increased thickness
        # Draw multiple times with small offsets for thickness
        offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for offset_x, offset_y in offsets:
            draw.text((x + offset_x, y + offset_y), text, font=font, fill=(0, 0, 0))

        return image

    def write_multiple_answers(
        self, texts: List[str], rois: List[Tuple[int, int, int, int]]
    ) -> List[Image.Image]:
        """Write multiple answers.

        Args:
            texts: List of texts to write.
            rois: List of ROIs (x1, y1, x2, y2).

        Returns:
            List of PIL Images containing handwritten text.

        Raises:
            ValueError: If lengths of texts and rois don't match.
        """
        if len(texts) != len(rois):
            raise ValueError("Number of texts must match number of ROIs")

        return [self.write_answer(text, roi) for text, roi in zip(texts, rois)]
