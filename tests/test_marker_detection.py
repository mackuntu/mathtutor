"""Test marker detection and alignment."""

import os
from pathlib import Path

import cv2
import numpy as np
import pytest
from pdf2image import convert_from_path
from PIL import Image, ImageDraw

from src.document.template import LayoutChoice, TemplateManager
from src.utils.marker_utils import MarkerUtils


def test_marker_detection_and_roi_alignment():
    """Test marker detection and ROI alignment on a generated worksheet."""
    # Get the latest generated worksheet
    worksheet_dir = Path("data/worksheets")
    worksheet_files = sorted(worksheet_dir.glob("math_worksheet_*.pdf"))
    if not worksheet_files:
        pytest.skip("No worksheet files found")
    latest_worksheet = worksheet_files[-1]

    # Convert PDF to image
    images = convert_from_path(latest_worksheet)
    worksheet_image = images[0]
    image_width, image_height = worksheet_image.size

    # Save as JPG for testing
    test_image_path = "data/test_worksheet.jpg"
    worksheet_image.save(test_image_path)

    try:
        # Detect markers
        marker_points = MarkerUtils.detect_alignment_markers(test_image_path)
        assert len(marker_points) == 4, f"Expected 4 markers, got {len(marker_points)}"

        # Generate ROIs for a typical worksheet
        template_manager = TemplateManager()
        _, rois = template_manager.calculate_layout(30, LayoutChoice.TWO_COLUMN)

        # Transform ROIs to image space
        transformed_rois = MarkerUtils.map_pdf_to_image_space(
            rois, marker_points, (image_width, image_height)
        )

        # Draw detected markers and ROIs for visualization
        image = cv2.imread(test_image_path)

        # Draw markers
        for i, (x, y) in enumerate(marker_points):
            # Draw a circle at each marker center
            cv2.circle(image, (x, y), 10, (0, 255, 0), 2)
            # Add marker ID
            cv2.putText(
                image,
                str(i),
                (x + 15, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

        # Draw ROIs
        for i, roi in enumerate(transformed_rois):
            x1, y1, x2, y2 = roi
            # Draw ROI rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            # Add ROI number
            cv2.putText(
                image,
                str(i + 1),
                (x1 - 30, y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
            )

            # Verify ROI dimensions are reasonable
            width = x2 - x1
            height = y2 - y1
            assert width > 0, f"ROI {i} has invalid width: {width}"
            assert height > 0, f"ROI {i} has invalid height: {height}"
            assert x1 >= 0 and x2 <= image_width, f"ROI {i} x-coordinates out of bounds"
            assert (
                y1 >= 0 and y2 <= image_height
            ), f"ROI {i} y-coordinates out of bounds"

        # Save debug image
        cv2.imwrite("data/detected_markers_and_rois.jpg", image)

        print("Marker positions:")
        for i, (x, y) in enumerate(marker_points):
            print(f"Marker {i}: ({x}, {y})")

        print("\nROI positions:")
        for i, (x1, y1, x2, y2) in enumerate(transformed_rois):
            print(f"ROI {i + 1}: ({x1}, {y1}) -> ({x2}, {y2})")

    finally:
        # Cleanup
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
