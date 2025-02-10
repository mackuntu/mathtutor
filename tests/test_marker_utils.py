"""Test marker detection and ROI mapping utilities."""

import logging
from typing import List, Tuple

import numpy as np
import pytest

from src.utils.marker_utils import MarkerUtils


@pytest.fixture
def setup_data():
    """Create test data for marker detection."""
    # Sample ROIs in PDF space
    rois = [
        (400, 500, 500, 540),  # Normal ROI
        (400, 460, 500, 500),
        (400, 420, 500, 460),
        (400, 380, 500, 420),
    ]

    # Sample marker positions in image space
    image_markers = [
        (100, 100),  # Top-left
        (100, 900),  # Bottom-left
        (900, 100),  # Top-right
        (900, 900),  # Bottom-right
    ]

    # Image dimensions
    image_dimensions = (1000, 1000)

    return rois, image_markers, image_dimensions


def test_marker_detection(setup_data):
    """Test basic marker detection functionality."""
    rois, image_markers, image_dimensions = setup_data

    # Transform ROIs to image space
    transformed_rois = MarkerUtils.map_pdf_to_image_space(
        rois, image_markers, image_dimensions
    )

    # Check that we got the expected number of ROIs
    assert len(transformed_rois) == len(rois)

    # Check that all ROIs are within image bounds
    for roi in transformed_rois:
        x1, y1, x2, y2 = roi
        assert 0 <= x1 < image_dimensions[0]
        assert 0 <= y1 < image_dimensions[1]
        assert 0 <= x2 < image_dimensions[0]
        assert 0 <= y2 < image_dimensions[1]
        assert x1 < x2  # Width is positive
        assert y1 < y2  # Height is positive


def test_marker_ordering(setup_data):
    """Test that markers are correctly ordered."""
    rois, image_markers, image_dimensions = setup_data

    # Shuffle markers but maintain the correct order according to MarkerUtils.REQUIRED_MARKER_IDS
    ordered_markers = [
        image_markers[0],  # Bottom-left
        image_markers[1],  # Top-left
        image_markers[2],  # Bottom-right
        image_markers[3],  # Top-right
    ]

    # Transform ROIs with ordered markers
    transformed_rois = MarkerUtils.map_pdf_to_image_space(
        rois, ordered_markers, image_dimensions
    )

    # Should get valid results
    assert len(transformed_rois) == len(rois)
    for roi in transformed_rois:
        x1, y1, x2, y2 = roi
        assert x1 < x2
        assert y1 < y2


def test_invalid_marker_count():
    """Test handling of invalid marker counts."""
    rois = [(0, 0, 100, 100)]
    image_markers = [(0, 0), (100, 100)]  # Only 2 markers
    image_dimensions = (1000, 1000)

    with pytest.raises(
        ValueError, match="Mismatch between number of PDF markers and image markers"
    ):
        MarkerUtils.map_pdf_to_image_space(rois, image_markers, image_dimensions)


def test_warning_for_invalid_rois(setup_data, caplog):
    """Test warnings for invalid ROIs (e.g., Y1 > Y2)."""
    caplog.set_level(logging.WARNING)

    # Create an invalid ROI where y1 > y2
    invalid_rois = [(400, 500, 500, 400)]  # y1=500, y2=400
    _, image_markers, image_dimensions = setup_data

    # Transform ROIs with invalid dimensions
    transformed_rois = MarkerUtils.map_pdf_to_image_space(
        invalid_rois, image_markers, image_dimensions
    )

    # Should get no ROIs back since they're invalid
    assert len(transformed_rois) == 0
    # Should have logged a warning
    assert any("Invalid ROI dimensions" in record.message for record in caplog.records)


def test_perspective_transform():
    """Test that perspective transform is working correctly."""
    # Create a simple square in PDF space
    rois = [(0, 0, 100, 100)]

    # Create markers that will skew the square
    image_markers = [
        (100, 100),  # Top-left
        (100, 1000),  # Bottom-left
        (1000, 50),  # Top-right
        (1000, 950),  # Bottom-right
    ]

    image_dimensions = (1100, 1100)

    transformed_rois = MarkerUtils.map_pdf_to_image_space(
        rois, image_markers, image_dimensions
    )

    # The transformed ROI should be a quadrilateral
    x1, y1, x2, y2 = transformed_rois[0]
    assert x1 != x2  # Width should be preserved
    assert y1 != y2  # Height should be preserved
    assert 0 <= x1 < image_dimensions[0]
    assert 0 <= y1 < image_dimensions[1]
