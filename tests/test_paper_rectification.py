"""End-to-end tests for paper rectification + ROI detection on a real photo.

The calibration image is `IMG_7360.jpeg` — a phone photo of a 40-problem
worksheet with a hand occluding the bottom-left paper edge. Tests skip when
the image isn't available locally (e.g. CI without the asset).
"""

import os

import pytest
from PIL import Image

from src.grading.paper_rectifier import rectify_paper, RectificationMetadata
from src.grading.roi_detector import detect_rois, DetectorConfig


TEST_IMAGE_PATH = "/Users/martinqian/Downloads/IMG_7360.jpeg"
NUM_PROBLEMS = 40


@pytest.fixture(scope="module")
def test_image():
    if not os.path.exists(TEST_IMAGE_PATH):
        pytest.skip(f"Test image not found at {TEST_IMAGE_PATH}")
    return Image.open(TEST_IMAGE_PATH)


@pytest.fixture(scope="module")
def rectified(test_image):
    rect_img, meta = rectify_paper(test_image)
    if rect_img is None:
        pytest.fail(f"Rectification failed: {meta.skip_reason}")
    return rect_img, meta


class TestRectification:
    def test_returns_image_and_metadata(self, rectified):
        rect_img, meta = rectified
        assert rect_img is not None
        assert isinstance(meta, RectificationMetadata)
        assert meta.success is True

    def test_output_has_letter_aspect(self, rectified):
        rect_img, _ = rectified
        w, h = rect_img.size
        aspect = h / w
        assert abs(aspect - 11 / 8.5) < 0.01

    def test_observed_aspect_close_to_letter(self, rectified):
        _, meta = rectified
        # Detected paper aspect should be near 11/8.5 = 1.294 once geometry is
        # consistent. Allow some tolerance for skewed photos.
        assert abs(meta.paper_aspect_observed - 11 / 8.5) < 0.20

    def test_corners_in_TL_TR_BR_BL_order(self, rectified):
        _, meta = rectified
        tl, tr, br, bl = meta.corners
        assert tl[0] < tr[0]   # top-left X less than top-right X
        assert tl[1] < bl[1]   # top-left Y less than bottom-left Y
        assert tr[1] < br[1]
        assert bl[0] < br[0]

    def test_three_visible_edges_detected(self, rectified):
        _, meta = rectified
        for side in ("top", "bot", "right"):
            assert meta.edges_detected[side] >= 1


class TestROIDetectionOnRectified:
    def test_detects_all_40_rois(self, rectified):
        rect_img, _ = rectified
        rois, meta = detect_rois(rect_img, NUM_PROBLEMS)
        assert meta.fallback_reason is None
        assert len(rois) == NUM_PROBLEMS

    def test_detects_8_rows_of_5(self, rectified):
        rect_img, _ = rectified
        _, meta = detect_rois(rect_img, NUM_PROBLEMS)
        assert meta.rows_detected == 8
        assert meta.lines_per_row == [5] * 8

    def test_zero_or_low_interpolation(self, rectified):
        rect_img, _ = rectified
        _, meta = detect_rois(rect_img, NUM_PROBLEMS)
        # On a clean rectified image, no lines should need interpolation.
        # Allow up to 2 in case of handwriting overlap.
        assert meta.interpolated_count <= 2

    def test_rois_are_uniform_size(self, rectified):
        rect_img, _ = rectified
        rois, _ = detect_rois(rect_img, NUM_PROBLEMS)
        widths = {r[2] - r[0] for r in rois}
        heights = {r[3] - r[1] for r in rois}
        assert len(widths) == 1, f"ROI widths vary: {widths}"
        assert len(heights) == 1, f"ROI heights vary: {heights}"

    def test_rois_span_paper_width(self, rectified):
        rect_img, _ = rectified
        rois, _ = detect_rois(rect_img, NUM_PROBLEMS)
        W, _ = rect_img.size
        # First-column and last-column ROI centers should span most of paper width
        col_xs = sorted({(r[0] + r[2]) // 2 for r in rois})
        assert col_xs[0] < W * 0.20
        assert col_xs[-1] > W * 0.80

    def test_rows_evenly_spaced(self, rectified):
        rect_img, _ = rectified
        rois, _ = detect_rois(rect_img, NUM_PROBLEMS)
        # Y centers within a row vary by a few pixels (residual rotation);
        # cluster into rows by 50px tolerance.
        y_centers = sorted((r[1] + r[3]) // 2 for r in rois)
        rows_y = []
        for y in y_centers:
            if rows_y and y - rows_y[-1] < 50:
                continue
            rows_y.append(y)
        assert len(rows_y) == 8
        import numpy as np
        spacings = np.diff(rows_y)
        cv = np.std(spacings) / np.mean(spacings)
        assert cv < 0.05, f"Row spacing not uniform (cv={cv:.3f}, spacings={spacings})"


class TestFallbackContract:
    def test_garbage_image_triggers_fallback(self):
        """An unrelated image should not silently produce wrong ROIs."""
        # Solid white image — no lines to detect
        img = Image.new("RGB", (1700, 2200), color="white")
        rois, meta = detect_rois(img, NUM_PROBLEMS)
        assert rois == []
        assert meta.fallback_reason is not None
