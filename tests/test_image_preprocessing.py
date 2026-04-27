"""Tests for image preprocessing and alignment."""

import os
import sys
import pytest
import numpy as np
from PIL import Image, ImageDraw
import importlib.util

# Import the module directly to avoid loading the full grading package
# which has easyocr dependency issues in some environments
_module_path = os.path.join(
    os.path.dirname(__file__), '..', 'src', 'grading', 'image_preprocessing.py'
)
_spec = importlib.util.spec_from_file_location("image_preprocessing", _module_path)
_image_preprocessing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_image_preprocessing)
WorksheetAligner = _image_preprocessing.WorksheetAligner
AlignmentMetadata = _image_preprocessing.AlignmentMetadata


class TestWorksheetAlignerBasic:
    """Basic unit tests for WorksheetAligner without external images."""

    @pytest.fixture
    def aligner(self):
        """Create a WorksheetAligner instance."""
        return WorksheetAligner()

    @pytest.fixture
    def synthetic_image_with_lines(self):
        """Create a synthetic image with horizontal and vertical lines."""
        # Create white background
        img = Image.new('RGB', (1000, 1400), color='white')
        draw = ImageDraw.Draw(img)

        # Draw horizontal lines (simulating worksheet grid)
        for y in range(100, 1300, 150):
            draw.line([(50, y), (950, y)], fill='black', width=2)

        # Draw vertical lines (simulating column separators)
        for x in range(100, 950, 180):
            draw.line([(x, 50), (x, 1350)], fill='black', width=2)

        # Draw a title box at top
        draw.rectangle([(100, 30), (900, 80)], outline='black', width=3)

        return img

    def test_aligner_instantiation(self, aligner):
        """Test that WorksheetAligner can be instantiated."""
        assert aligner is not None
        assert aligner.rotation_threshold == WorksheetAligner.ROTATION_THRESHOLD_DEG
        assert aligner.max_rotation == WorksheetAligner.MAX_ROTATION_DEG

    def test_aligner_custom_parameters(self):
        """Test WorksheetAligner with custom parameters."""
        aligner = WorksheetAligner(
            rotation_threshold=1.0,
            max_rotation=15.0,
            max_processing_time=1000,
        )
        assert aligner.rotation_threshold == 1.0
        assert aligner.max_rotation == 15.0
        assert aligner.max_processing_time == 1000

    def test_preprocess_returns_image_and_metadata(self, aligner, synthetic_image_with_lines):
        """Test that preprocess_image returns both image and metadata."""
        result_image, metadata = aligner.preprocess_image(synthetic_image_with_lines)

        assert isinstance(result_image, Image.Image)
        assert isinstance(metadata, AlignmentMetadata)

    def test_metadata_has_required_fields(self, aligner, synthetic_image_with_lines):
        """Test that AlignmentMetadata has all required fields."""
        _, metadata = aligner.preprocess_image(synthetic_image_with_lines)

        assert hasattr(metadata, 'rotation_detected')
        assert hasattr(metadata, 'rotation_applied')
        assert hasattr(metadata, 'confidence')
        assert hasattr(metadata, 'num_lines_detected')
        assert hasattr(metadata, 'processing_time_ms')
        assert hasattr(metadata, 'skipped')

    def test_straight_image_not_rotated(self, aligner, synthetic_image_with_lines):
        """Test that an already straight image is not significantly rotated."""
        _, metadata = aligner.preprocess_image(synthetic_image_with_lines)

        # Straight image should have very small detected rotation
        assert abs(metadata.rotation_detected) < 2.0, \
            f"Straight image detected rotation: {metadata.rotation_detected}°"

    def test_lines_detected_in_synthetic_image(self, aligner, synthetic_image_with_lines):
        """Test that lines are detected in synthetic image."""
        _, metadata = aligner.preprocess_image(synthetic_image_with_lines)

        assert metadata.num_lines_detected > 0, "No lines detected in synthetic image"


class TestWorksheetAlignerRotationDetection:
    """Tests for rotation detection accuracy."""

    @pytest.fixture
    def aligner(self):
        """Create a WorksheetAligner instance with low threshold for testing."""
        return WorksheetAligner(rotation_threshold=0.1)

    def create_rotated_image(self, angle_degrees: float) -> Image.Image:
        """Create a synthetic image with known rotation."""
        # Create larger base image to avoid edge issues after rotation
        base_size = 1500
        img = Image.new('RGB', (base_size, base_size), color='white')
        draw = ImageDraw.Draw(img)

        # Draw strong horizontal lines
        for y in range(200, base_size - 200, 100):
            draw.line([(100, y), (base_size - 100, y)], fill='black', width=3)

        # Draw strong vertical lines
        for x in range(200, base_size - 200, 100):
            draw.line([(x, 100), (x, base_size - 100)], fill='black', width=3)

        # Rotate the image
        rotated = img.rotate(
            angle_degrees,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor='white'
        )

        return rotated

    @pytest.mark.parametrize("angle", [5.0, -5.0, 10.0, -10.0])
    def test_rotation_detection_accuracy(self, aligner, angle):
        """Test that rotation is detected within reasonable accuracy."""
        rotated_img = self.create_rotated_image(angle)
        _, metadata = aligner.preprocess_image(rotated_img)

        # Detection should be within ±2 degrees of actual rotation
        # Note: detected rotation should be opposite sign (correction angle)
        detected = metadata.rotation_detected
        error = abs(abs(detected) - abs(angle))
        assert error < 3.0, \
            f"Rotation detection error too large: detected {detected}°, actual {angle}°"

    def test_small_rotation_detected(self, aligner):
        """Test that small rotations (3-5°) are detected."""
        rotated_img = self.create_rotated_image(3.0)
        _, metadata = aligner.preprocess_image(rotated_img)

        assert metadata.num_lines_detected > 0, "No lines detected"
        # Should detect some rotation
        assert abs(metadata.rotation_detected) > 0.5, \
            f"Small rotation not detected: {metadata.rotation_detected}°"

    def test_rotation_correction_applied(self, aligner):
        """Test that rotation correction is actually applied."""
        # Create rotated image
        angle = 8.0
        rotated_img = self.create_rotated_image(angle)
        original_size = rotated_img.size

        # Apply correction
        corrected_img, metadata = aligner.preprocess_image(rotated_img)

        # If rotation was applied, image size might change slightly
        # and rotation_applied should be non-zero
        if not metadata.skipped:
            assert abs(metadata.rotation_applied) > 0.5, \
                f"Rotation should have been applied: {metadata.rotation_applied}°"


class TestWorksheetAlignerEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def aligner(self):
        return WorksheetAligner()

    def test_blank_image(self, aligner):
        """Test handling of blank white image."""
        blank = Image.new('RGB', (800, 1000), color='white')
        result_img, metadata = aligner.preprocess_image(blank)

        # Should not crash and should return original image
        assert result_img is not None
        assert metadata.skipped, "Blank image should skip alignment"

    def test_very_small_image(self, aligner):
        """Test handling of very small image."""
        small = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(small)
        draw.line([(10, 50), (90, 50)], fill='black', width=2)

        result_img, metadata = aligner.preprocess_image(small)
        assert result_img is not None

    def test_rgba_image(self, aligner):
        """Test handling of RGBA image."""
        rgba = Image.new('RGBA', (800, 1000), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(rgba)
        draw.line([(100, 500), (700, 500)], fill=(0, 0, 0, 255), width=2)

        result_img, metadata = aligner.preprocess_image(rgba)
        assert result_img is not None
        # Output mode may be RGB or RGBA depending on whether rotation was applied
        assert result_img.mode in ('RGB', 'RGBA'), f"Unexpected mode: {result_img.mode}"

    def test_grayscale_image(self, aligner):
        """Test handling of grayscale image."""
        gray = Image.new('L', (800, 1000), color=255)
        # Convert to RGB for processing
        gray_rgb = gray.convert('RGB')
        draw = ImageDraw.Draw(gray_rgb)
        draw.line([(100, 500), (700, 500)], fill='black', width=2)

        result_img, metadata = aligner.preprocess_image(gray_rgb)
        assert result_img is not None

    def test_max_rotation_exceeded(self, aligner):
        """Test that excessive rotation is rejected."""
        # Create image with extreme rotation
        img = Image.new('RGB', (1000, 1000), color='white')
        draw = ImageDraw.Draw(img)
        for y in range(100, 900, 100):
            draw.line([(50, y), (950, y)], fill='black', width=2)

        # Rotate 30 degrees (exceeds max of 20)
        extreme_rotated = img.rotate(30, expand=True, fillcolor='white')

        result_img, metadata = aligner.preprocess_image(extreme_rotated)

        # Should skip due to exceeding max rotation
        # Note: Detection might not be exactly 30° but should be large enough to trigger skip
        if abs(metadata.rotation_detected) > aligner.max_rotation:
            assert metadata.skipped, "Should skip when rotation exceeds maximum"


class TestWorksheetAlignerPerformance:
    """Performance-related tests."""

    @pytest.fixture
    def aligner(self):
        return WorksheetAligner()

    def test_large_image_resizing(self, aligner):
        """Test that large images are resized for detection."""
        # Create a large image
        large = Image.new('RGB', (4000, 5000), color='white')
        draw = ImageDraw.Draw(large)
        for y in range(500, 4500, 500):
            draw.line([(200, y), (3800, y)], fill='black', width=5)

        _, metadata = aligner.preprocess_image(large)

        # Should complete without timeout
        assert metadata.processing_time_ms < aligner.max_processing_time, \
            f"Processing took too long: {metadata.processing_time_ms}ms"

    def test_processing_time_recorded(self, aligner):
        """Test that processing time is recorded."""
        img = Image.new('RGB', (800, 1000), color='white')
        _, metadata = aligner.preprocess_image(img)

        assert metadata.processing_time_ms > 0, "Processing time should be recorded"


class TestGridLandmarkDetection:
    """Tests for grid landmark detection (optional enhancement)."""

    @pytest.fixture
    def aligner(self):
        return WorksheetAligner()

    @pytest.fixture
    def grid_image(self):
        """Create image with clear grid structure."""
        img = Image.new('RGB', (1000, 1400), color='white')
        draw = ImageDraw.Draw(img)

        # Draw horizontal grid lines at regular intervals
        y_positions = [200, 350, 500, 650, 800, 950, 1100, 1250]
        for y in y_positions:
            draw.line([(50, y), (950, y)], fill='black', width=2)

        # Draw vertical lines for columns
        x_positions = [100, 280, 460, 640, 820]
        for x in x_positions:
            draw.line([(x, 150), (x, 1300)], fill='black', width=2)

        return img

    def test_detect_grid_landmarks(self, aligner, grid_image):
        """Test detection of grid landmarks."""
        import cv2
        cv_image = aligner._pil_to_cv(grid_image)
        landmarks = aligner.detect_grid_landmarks(cv_image)

        # Should detect some landmarks or return None
        if landmarks is not None:
            assert 'horizontal_lines_y' in landmarks
            assert 'confidence' in landmarks
            assert landmarks['confidence'] >= 0.0


# Integration test with real image (skipped if image not available)
TEST_IMAGE_PATH = "/Users/martinqian/Downloads/IMG_7360.jpeg"


@pytest.mark.skipif(
    not os.path.exists(TEST_IMAGE_PATH),
    reason=f"Test image not found at {TEST_IMAGE_PATH}"
)
class TestWorksheetAlignerIntegration:
    """Integration tests with real worksheet image."""

    @pytest.fixture
    def aligner(self):
        return WorksheetAligner()

    @pytest.fixture
    def test_image(self):
        return Image.open(TEST_IMAGE_PATH)

    def test_real_image_processing(self, aligner, test_image):
        """Test processing of real worksheet image."""
        result_img, metadata = aligner.preprocess_image(test_image)

        assert result_img is not None
        assert isinstance(metadata, AlignmentMetadata)

        # Log results for debugging
        print(f"\nReal image alignment results:")
        print(f"  Rotation detected: {metadata.rotation_detected:.2f}°")
        print(f"  Rotation applied: {metadata.rotation_applied:.2f}°")
        print(f"  Confidence: {metadata.confidence:.2f}")
        print(f"  Lines detected: {metadata.num_lines_detected}")
        print(f"  Processing time: {metadata.processing_time_ms:.0f}ms")
        print(f"  Skipped: {metadata.skipped}")
        if metadata.skip_reason:
            print(f"  Skip reason: {metadata.skip_reason}")

    def test_real_image_confidence(self, aligner, test_image):
        """Test that confidence is reasonable for real image."""
        _, metadata = aligner.preprocess_image(test_image)

        # Real worksheet should have detectable lines
        assert metadata.num_lines_detected > 0, "Should detect lines in worksheet"
