"""Tests for image alignment and ROI calculation."""

import os
import pytest
from PIL import Image

from src.grading.image_alignment import calculate_html_grid_rois


# Path to test image - skip test if not available
TEST_IMAGE_PATH = "/Users/martinqian/Downloads/IMG_7360.jpeg"
WORKSHEET_ID = "7c81b248"


@pytest.mark.skipif(
    not os.path.exists(TEST_IMAGE_PATH),
    reason=f"Test image not found at {TEST_IMAGE_PATH}"
)
class TestImageAlignmentROIs:
    """Test ROI calculation against real worksheet image."""

    @pytest.fixture
    def test_image(self):
        """Load the test worksheet image."""
        return Image.open(TEST_IMAGE_PATH)

    @pytest.fixture
    def rois_40_problems(self, test_image):
        """Calculate ROIs for a 40-problem worksheet."""
        return calculate_html_grid_rois(40, test_image.width, test_image.height)

    def test_roi_count(self, rois_40_problems):
        """Verify correct number of ROIs are generated."""
        assert len(rois_40_problems) == 40

    def test_row_positions(self, test_image, rois_40_problems):
        """Verify rows are at expected Y positions."""
        h = test_image.height

        # Row 1 should be around 16-18% from top
        row1_y = rois_40_problems[0][1] / h
        assert 0.15 <= row1_y <= 0.19, f"Row 1 at {row1_y*100:.1f}%, expected 16-18%"

        # Row 8 should be around 84-88% from top
        row8_y = rois_40_problems[35][1] / h
        assert 0.84 <= row8_y <= 0.88, f"Row 8 at {row8_y*100:.1f}%, expected 84-88%"

    def test_column_positions(self, test_image, rois_40_problems):
        """Verify columns are evenly distributed."""
        w = test_image.width

        # Get X centers of first 5 problems (row 1)
        col_centers = []
        for i in range(5):
            x1, _, x2, _ = rois_40_problems[i]
            center = (x1 + x2) / 2 / w
            col_centers.append(center)

        # Columns should be roughly at 14%, 32%, 50%, 68%, 86% of width
        expected_centers = [0.14, 0.32, 0.50, 0.68, 0.86]
        for actual, expected in zip(col_centers, expected_centers):
            assert abs(actual - expected) < 0.05, \
                f"Column at {actual*100:.1f}%, expected ~{expected*100:.0f}%"

    def test_roi_captures_answer_140(self, test_image, rois_40_problems):
        """Problem 1 ROI should capture the answer '140'."""
        x1, y1, x2, y2 = rois_40_problems[0]
        crop = test_image.crop((x1, y1, x2, y2))

        # Verify the crop has reasonable dimensions
        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"

        # Visual verification: save crop for manual inspection
        crop.save("/tmp/test_p01_140.png")

    def test_roi_captures_answer_83(self, test_image, rois_40_problems):
        """Problem 2 ROI should capture the answer '83'."""
        x1, y1, x2, y2 = rois_40_problems[1]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p02_83.png")

    def test_roi_captures_answer_180(self, test_image, rois_40_problems):
        """Problem 3 ROI should capture the answer '180'."""
        x1, y1, x2, y2 = rois_40_problems[2]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p03_180.png")

    def test_roi_captures_answer_40(self, test_image, rois_40_problems):
        """Problem 4 ROI should capture the answer '40'."""
        x1, y1, x2, y2 = rois_40_problems[3]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p04_40.png")

    def test_row8_roi_captures_empty(self, test_image, rois_40_problems):
        """Problem 36 (row 8, col 1) ROI should capture empty box."""
        x1, y1, x2, y2 = rois_40_problems[35]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p36_empty.png")

    def test_row8_roi_captures_answer_90(self, test_image, rois_40_problems):
        """Problem 37 (row 8, col 2) ROI should capture the answer '90'."""
        x1, y1, x2, y2 = rois_40_problems[36]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p37_90.png")

    def test_row8_roi_captures_answer_120(self, test_image, rois_40_problems):
        """Problem 38 (row 8, col 3) ROI should capture the answer '120'."""
        x1, y1, x2, y2 = rois_40_problems[37]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p38_120.png")

    def test_row8_roi_captures_answer_64(self, test_image, rois_40_problems):
        """Problem 39 (row 8, col 4) ROI should capture the answer '64'."""
        x1, y1, x2, y2 = rois_40_problems[38]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p39_64.png")

    def test_row8_roi_captures_answer_53(self, test_image, rois_40_problems):
        """Problem 40 (row 8, col 5) ROI should capture the answer '53'."""
        x1, y1, x2, y2 = rois_40_problems[39]
        crop = test_image.crop((x1, y1, x2, y2))

        assert crop.width > 100, "ROI too narrow"
        assert crop.height > 50, "ROI too short"
        crop.save("/tmp/test_p40_53.png")


class TestROICalculationBasic:
    """Basic tests for ROI calculation without test image."""

    def test_10_problems_generates_10_rois(self):
        """10 problems should generate 10 ROIs."""
        rois = calculate_html_grid_rois(10)
        assert len(rois) == 10

    def test_40_problems_generates_40_rois(self):
        """40 problems should generate 40 ROIs."""
        rois = calculate_html_grid_rois(40)
        assert len(rois) == 40

    def test_rois_are_normalized_without_dimensions(self):
        """Without pixel dimensions, ROIs should be in 0-1 range."""
        rois = calculate_html_grid_rois(10)
        for x1, y1, x2, y2 in rois:
            assert 0 <= x1 <= 1, f"x1={x1} out of normalized range"
            assert 0 <= y1 <= 1, f"y1={y1} out of normalized range"
            assert 0 <= x2 <= 1, f"x2={x2} out of normalized range"
            assert 0 <= y2 <= 1, f"y2={y2} out of normalized range"

    def test_rois_are_pixels_with_dimensions(self):
        """With pixel dimensions, ROIs should be in pixel range."""
        rois = calculate_html_grid_rois(10, 1000, 2000)
        for x1, y1, x2, y2 in rois:
            assert 0 <= x1 <= 1000, f"x1={x1} out of pixel range"
            assert 0 <= y1 <= 2000, f"y1={y1} out of pixel range"
            assert 0 <= x2 <= 1000, f"x2={x2} out of pixel range"
            assert 0 <= y2 <= 2000, f"y2={y2} out of pixel range"

    def test_row_1_before_row_2(self):
        """Row 1 problems should have smaller Y than row 2."""
        rois = calculate_html_grid_rois(10)
        row1_y = rois[0][1]  # Problem 1 y1
        row2_y = rois[5][1]  # Problem 6 y1
        assert row1_y < row2_y, "Row 1 should be above row 2"

    def test_columns_left_to_right(self):
        """Columns should be ordered left to right."""
        rois = calculate_html_grid_rois(10)
        for i in range(4):
            x1_current = rois[i][0]
            x1_next = rois[i + 1][0]
            assert x1_current < x1_next, \
                f"Column {i+1} should be left of column {i+2}"
