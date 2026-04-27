"""Image preprocessing module for worksheet alignment and rotation correction."""

import logging
import time
from dataclasses import dataclass
from typing import Tuple, Optional, List

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class AlignmentMetadata:
    """Metadata from the alignment process."""
    rotation_detected: float  # Degrees
    rotation_applied: float  # Degrees (may differ if capped)
    confidence: float  # 0.0 to 1.0
    num_lines_detected: int
    processing_time_ms: float
    skipped: bool  # True if alignment was skipped
    skip_reason: Optional[str] = None


class WorksheetAligner:
    """
    Detects rotation from line analysis and applies correction.

    Uses Hough Line Transform to detect horizontal and vertical lines
    in the worksheet (title box, problem separator lines, grid) and
    calculates the rotation angle needed to correct the image.
    """

    ROTATION_THRESHOLD_DEG = 0.5   # Skip rotation if angle < this
    MAX_ROTATION_DEG = 20.0        # Reject if detected rotation exceeds this
    MAX_PROCESSING_TIME_MS = 2000  # Skip if processing takes too long
    DETECTION_IMAGE_MAX_DIM = 1500 # Resize for faster detection

    # Hough Line parameters
    HOUGH_THRESHOLD = 100
    MIN_LINE_LENGTH = 100
    MAX_LINE_GAP = 10

    def __init__(
        self,
        rotation_threshold: float = ROTATION_THRESHOLD_DEG,
        max_rotation: float = MAX_ROTATION_DEG,
        max_processing_time: float = MAX_PROCESSING_TIME_MS,
    ):
        self.rotation_threshold = rotation_threshold
        self.max_rotation = max_rotation
        self.max_processing_time = max_processing_time

    def preprocess_image(self, image: Image.Image) -> Tuple[Image.Image, AlignmentMetadata]:
        """
        Main entry point: detect rotation and apply correction.

        Args:
            image: PIL Image to process

        Returns:
            Tuple of (aligned_image, alignment_metadata)
        """
        start_time = time.time()

        # Convert PIL Image to OpenCV format
        cv_image = self._pil_to_cv(image)
        original_height, original_width = cv_image.shape[:2]

        # Resize for faster detection (we'll apply correction to full resolution)
        detection_image, scale_factor = self._resize_for_detection(cv_image)

        # Detect rotation angle
        rotation_angle, confidence, num_lines = self._detect_rotation(detection_image)

        processing_time_ms = (time.time() - start_time) * 1000

        # Check if we should skip rotation
        skip_reason = None
        skipped = False
        rotation_applied = 0.0

        if processing_time_ms > self.max_processing_time:
            skip_reason = f"Processing time {processing_time_ms:.0f}ms exceeds limit"
            skipped = True
        elif abs(rotation_angle) < self.rotation_threshold:
            skip_reason = f"Rotation {rotation_angle:.2f}° below threshold"
            skipped = True
        elif abs(rotation_angle) > self.max_rotation:
            skip_reason = f"Rotation {rotation_angle:.2f}° exceeds maximum"
            skipped = True
        elif confidence < 0.3:
            skip_reason = f"Low confidence {confidence:.2f}"
            skipped = True

        if skipped:
            logger.info(f"Skipping alignment: {skip_reason}")
            metadata = AlignmentMetadata(
                rotation_detected=rotation_angle,
                rotation_applied=0.0,
                confidence=confidence,
                num_lines_detected=num_lines,
                processing_time_ms=processing_time_ms,
                skipped=True,
                skip_reason=skip_reason,
            )
            return image, metadata

        # Apply rotation to full resolution image
        rotated_cv = self._rotate_image(cv_image, rotation_angle)
        rotation_applied = rotation_angle

        # Convert back to PIL
        aligned_image = self._cv_to_pil(rotated_cv)

        total_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Alignment complete: rotation={rotation_angle:.2f}°, "
            f"confidence={confidence:.2f}, time={total_time_ms:.0f}ms"
        )

        metadata = AlignmentMetadata(
            rotation_detected=rotation_angle,
            rotation_applied=rotation_applied,
            confidence=confidence,
            num_lines_detected=num_lines,
            processing_time_ms=total_time_ms,
            skipped=False,
        )

        return aligned_image, metadata

    def _detect_rotation(self, cv_image: np.ndarray) -> Tuple[float, float, int]:
        """
        Use Hough Line Transform to find dominant line angles.

        Args:
            cv_image: OpenCV image (BGR or grayscale)

        Returns:
            Tuple of (rotation_angle, confidence, num_lines)
        """
        # Convert to grayscale if needed
        if len(cv_image.shape) == 3:
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv_image

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

        # Detect lines using Probabilistic Hough Transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.HOUGH_THRESHOLD,
            minLineLength=self.MIN_LINE_LENGTH,
            maxLineGap=self.MAX_LINE_GAP,
        )

        if lines is None or len(lines) == 0:
            logger.warning("No lines detected in image")
            return 0.0, 0.0, 0

        # Calculate angles of all detected lines
        horizontal_angles = []
        vertical_angles = []

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Calculate angle from horizontal (-90 to 90 degrees)
            if x2 - x1 == 0:  # Vertical line
                angle = 90.0
            else:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

            # Classify as horizontal or vertical based on angle
            if abs(angle) < 45:
                # Near-horizontal line
                horizontal_angles.append(angle)
            elif abs(angle) > 45:
                # Near-vertical line - convert to deviation from vertical
                if angle > 0:
                    vertical_angles.append(angle - 90)
                else:
                    vertical_angles.append(angle + 90)

        num_lines = len(horizontal_angles) + len(vertical_angles)

        # Prefer horizontal lines (more common in worksheets: title box, separators)
        if len(horizontal_angles) >= 3:
            angles = horizontal_angles
        elif len(vertical_angles) >= 3:
            angles = vertical_angles
        elif len(horizontal_angles) > 0:
            angles = horizontal_angles
        elif len(vertical_angles) > 0:
            angles = vertical_angles
        else:
            return 0.0, 0.0, num_lines

        # Use median angle to be robust against outliers
        median_angle = np.median(angles)

        # Calculate confidence based on standard deviation
        # Lower std_dev = higher confidence
        std_dev = np.std(angles)
        confidence = max(0.0, min(1.0, 1.0 - (std_dev / 10.0)))

        # Boost confidence if we have many lines
        if len(angles) > 10:
            confidence = min(1.0, confidence + 0.1)

        logger.debug(
            f"Line detection: {len(horizontal_angles)} horizontal, "
            f"{len(vertical_angles)} vertical, median_angle={median_angle:.2f}°, "
            f"std_dev={std_dev:.2f}, confidence={confidence:.2f}"
        )

        return median_angle, confidence, num_lines

    def _rotate_image(self, cv_image: np.ndarray, angle: float) -> np.ndarray:
        """
        Apply rotation correction using cv2.warpAffine.

        Args:
            cv_image: OpenCV image
            angle: Rotation angle in degrees (counter-clockwise positive)

        Returns:
            Rotated image
        """
        height, width = cv_image.shape[:2]
        center = (width / 2, height / 2)

        # Get rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new bounding box size to avoid cropping
        cos = abs(rotation_matrix[0, 0])
        sin = abs(rotation_matrix[0, 1])
        new_width = int(height * sin + width * cos)
        new_height = int(height * cos + width * sin)

        # Adjust the rotation matrix to account for translation
        rotation_matrix[0, 2] += (new_width - width) / 2
        rotation_matrix[1, 2] += (new_height - height) / 2

        # Apply rotation with white background
        rotated = cv2.warpAffine(
            cv_image,
            rotation_matrix,
            (new_width, new_height),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255),  # White background
        )

        return rotated

    def _resize_for_detection(
        self, cv_image: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """
        Resize image for faster line detection.

        Args:
            cv_image: OpenCV image

        Returns:
            Tuple of (resized_image, scale_factor)
        """
        height, width = cv_image.shape[:2]
        max_dim = max(height, width)

        if max_dim <= self.DETECTION_IMAGE_MAX_DIM:
            return cv_image, 1.0

        scale = self.DETECTION_IMAGE_MAX_DIM / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = cv2.resize(cv_image, (new_width, new_height), interpolation=cv2.INTER_AREA)

        return resized, scale

    def _pil_to_cv(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV BGR format."""
        # Handle different image modes
        if pil_image.mode == 'RGBA':
            # Convert RGBA to RGB first
            pil_image = pil_image.convert('RGB')
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Convert to numpy array (RGB)
        rgb_array = np.array(pil_image)

        # Convert RGB to BGR
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)

        return bgr_array

    def _cv_to_pil(self, cv_image: np.ndarray) -> Image.Image:
        """Convert OpenCV BGR image to PIL Image."""
        # Convert BGR to RGB
        rgb_array = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        return Image.fromarray(rgb_array)

    def detect_grid_landmarks(self, cv_image: np.ndarray) -> Optional[dict]:
        """
        Attempt to detect grid landmarks for adaptive ROI calculation.

        This is an optional enhancement that tries to find:
        - Title box boundaries
        - Grid column separators
        - Row boundaries

        Args:
            cv_image: OpenCV image (BGR)

        Returns:
            Dictionary with landmark positions and confidence, or None if detection fails
        """
        # Convert to grayscale
        if len(cv_image.shape) == 3:
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv_image

        height, width = gray.shape[:2]

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Detect lines
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=80,
            minLineLength=width * 0.1,  # At least 10% of image width
            maxLineGap=20,
        )

        if lines is None or len(lines) < 5:
            return None

        # Separate horizontal and vertical lines
        horizontal_lines = []
        vertical_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))

            if angle < 10:  # Near horizontal
                horizontal_lines.append((x1, y1, x2, y2))
            elif angle > 80:  # Near vertical
                vertical_lines.append((x1, y1, x2, y2))

        if len(horizontal_lines) < 2:
            return None

        # Find distinct horizontal line Y positions (potential row boundaries)
        y_positions = []
        for x1, y1, x2, y2 in horizontal_lines:
            y_avg = (y1 + y2) / 2
            y_positions.append(y_avg)

        # Cluster Y positions to find distinct rows
        y_positions = sorted(y_positions)
        clustered_y = self._cluster_positions(y_positions, threshold=height * 0.02)

        if len(clustered_y) < 2:
            return None

        # Calculate confidence based on regularity of spacing
        if len(clustered_y) >= 3:
            spacings = [clustered_y[i+1] - clustered_y[i] for i in range(len(clustered_y) - 1)]
            avg_spacing = np.mean(spacings)
            spacing_std = np.std(spacings)
            confidence = max(0.0, min(1.0, 1.0 - (spacing_std / avg_spacing)))
        else:
            confidence = 0.3

        return {
            "horizontal_lines_y": clustered_y,
            "vertical_lines_x": self._cluster_positions(
                [(x1 + x2) / 2 for x1, y1, x2, y2 in vertical_lines],
                threshold=width * 0.02
            ) if vertical_lines else [],
            "confidence": confidence,
            "image_size": (width, height),
        }

    def _cluster_positions(
        self, positions: List[float], threshold: float
    ) -> List[float]:
        """Cluster nearby positions and return cluster centers."""
        if not positions:
            return []

        positions = sorted(positions)
        clusters = [[positions[0]]]

        for pos in positions[1:]:
            if pos - clusters[-1][-1] < threshold:
                clusters[-1].append(pos)
            else:
                clusters.append([pos])

        # Return cluster centers
        return [np.mean(cluster) for cluster in clusters]
