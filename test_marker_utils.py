import logging
import unittest

import numpy as np

from marker_utils import MarkerUtils


class TestMarkerUtils(unittest.TestCase):

    def setUp(self):
        # Set up sample data for tests
        self.pdf_rois = [
            (400, 500, 500, 540),
            (400, 460, 500, 500),
            (400, 420, 500, 460),
            (400, 380, 500, 420),
        ]
        self.image_markers = [
            (100, 100),  # Bottom-left
            (100, 900),  # Top-left
            (900, 100),  # Bottom-right
            (900, 900),  # Top-right
        ]
        self.image_dimensions = (1000, 1000)

    def test_map_pdf_to_image_space_y_axis_reversal(self):
        # Ensure transformed ROIs correctly map and eliminate Y-axis reversal bug
        transformed_rois = MarkerUtils.map_pdf_to_image_space(
            self.pdf_rois, self.image_markers, self.image_dimensions
        )

        # Validate the number of transformed ROIs
        self.assertEqual(len(transformed_rois), len(self.pdf_rois))

        # Validate Y-axis values in transformed ROIs
        for original, transformed in zip(self.pdf_rois, transformed_rois):
            x1, y1, x2, y2 = transformed
            self.assertTrue(y1 <= y2, f"Y-axis reversed in ROI: {transformed}")
            self.assertTrue(x1 <= x2, f"X-axis reversed in ROI: {transformed}")

        print("Transformed ROIs:")
        for roi in transformed_rois:
            print(roi)

    def test_invalid_image_markers(self):
        # Test with invalid image markers (e.g., collinear or insufficient points)
        invalid_markers = [(100, 100), (100, 200)]  # Only 2 points
        with self.assertRaises(ValueError):
            MarkerUtils.map_pdf_to_image_space(
                self.pdf_rois, invalid_markers, self.image_dimensions
            )

    def test_collinear_image_markers(self):
        # Test with collinear image markers
        collinear_markers = [(100, 100), (200, 200), (300, 300), (400, 400)]
        with self.assertRaises(ValueError):
            MarkerUtils.map_pdf_to_image_space(
                self.pdf_rois, collinear_markers, self.image_dimensions
            )

    def test_y_axis_reversal_correction(self):
        transformed_rois = MarkerUtils.map_pdf_to_image_space(
            self.pdf_rois, self.image_markers, self.image_dimensions
        )

        for roi in transformed_rois:
            x1, y1, x2, y2 = roi
            self.assertTrue(y1 <= y2, f"Y-coordinates reversed in ROI: {roi}")
            self.assertTrue(x1 <= x2, f"X-coordinates reversed in ROI: {roi}")

    def test_warning_for_invalid_rois(self):
        # Test warnings for invalid ROIs (e.g., Y1 > Y2)
        invalid_rois = [(400, 300, 500, 200)]  # Invalid because y1 > y2
        with self.assertLogs(level="WARNING") as log:
            transformed_rois = MarkerUtils.map_pdf_to_image_space(
                invalid_rois, self.image_markers, self.image_dimensions
            )
            self.assertIn("Invalid transformed ROI", log.output[0])
            self.assertEqual(len(transformed_rois), 0)


if __name__ == "__main__":
    unittest.main()
