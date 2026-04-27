"""Detect paper boundary in worksheet photo and warp to canonical letter-aspect plane.

Rationale: photographing a printed worksheet introduces rotation, perspective
(trapezoidal foreshortening), and offset within the photo frame. The grading
pipeline needs answer regions at known coordinates; rectifying first makes the
later ROI detection a fixed-coordinate sampling problem instead of a
distortion-correction problem.

Strategy:
- Saturation/value mask isolates white paper from colored background.
- Hough line transform on the mask boundary gives candidate paper edges.
- Top, bottom, right edges are usually visible. Left edge often occluded
  (hand holding the paper). Derive left edge geometrically from the right
  edge length and known letter aspect ratio (8.5/11).
- Perspective warp to a canonical letter-shaped canvas.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# Letter paper aspect (8.5 × 11 inches)
LETTER_ASPECT = 8.5 / 11.0

# Default rectified canvas. Width chosen so 1px ≈ 0.005in — adequate for OCR.
DEFAULT_OUTPUT_WIDTH = 1700
DEFAULT_OUTPUT_HEIGHT = int(DEFAULT_OUTPUT_WIDTH * 11 / 8.5)  # 2200


@dataclass
class RectificationMetadata:
    """Diagnostic info about the rectification step."""
    success: bool
    skip_reason: Optional[str] = None
    corners: Optional[Tuple[Tuple[float, float], ...]] = None  # TL, TR, BR, BL
    paper_aspect_observed: Optional[float] = None  # right_edge_len / paper_width
    edges_detected: Optional[dict] = None  # {top: int, bot: int, right: int}


def _build_paper_mask(image: np.ndarray) -> np.ndarray:
    """White paper has low saturation and high value. Mask out colored background."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    s, v = hsv[:, :, 1], hsv[:, :, 2]
    mask = ((s < 60) & (v > 100)).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (60, 60))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def _segment_angle_deg(seg: Tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = seg
    a = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
    if a > 90:
        a -= 180
    if a < -90:
        a += 180
    return a


def _segment_length(seg: Tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = seg
    return float(np.hypot(x2 - x1, y2 - y1))


def _fit_line(segs: List[Tuple[int, int, int, int]]) -> Tuple[float, float, float, float]:
    """L2-fit a single line through all endpoints. Returns (vx, vy, x0, y0)."""
    pts = []
    for s in segs:
        pts.append([s[0], s[1]])
        pts.append([s[2], s[3]])
    arr = np.array(pts, dtype=np.float32)
    return tuple(cv2.fitLine(arr, cv2.DIST_L2, 0, 0.01, 0.01).flatten())


def _intersect_lines(L1, L2) -> Optional[Tuple[float, float]]:
    """Intersect two parametric lines (vx, vy, x0, y0). None if parallel."""
    vx1, vy1, x1, y1 = L1
    vx2, vy2, x2, y2 = L2
    A = np.array([[vx1, -vx2], [vy1, -vy2]])
    b = np.array([x2 - x1, y2 - y1])
    if abs(np.linalg.det(A)) < 1e-6:
        return None
    t = np.linalg.solve(A, b)
    return (float(x1 + t[0] * vx1), float(y1 + t[0] * vy1))


def _bucket_segments_by_side(
    lines: np.ndarray, image_w: int, image_h: int
) -> Tuple[List, List, List]:
    """Classify Hough segments as top/bottom/right by orientation and position.

    Left edge is intentionally not bucketed — it is unreliable when a hand
    occludes paper edge, and is derived geometrically from the other three.
    """
    top_segs, bot_segs, right_segs = [], [], []
    for line in lines:
        seg = tuple(int(v) for v in line[0])
        angle = _segment_angle_deg(seg)
        cy = (seg[1] + seg[3]) / 2
        cx = (seg[0] + seg[2]) / 2

        if abs(angle) < 25:  # near horizontal
            if cy < image_h * 0.50:
                top_segs.append(seg)
            else:
                bot_segs.append(seg)
        elif abs(abs(angle) - 90) < 25 and cx > image_w * 0.50:
            right_segs.append(seg)

    return top_segs, bot_segs, right_segs


def _filter_near(
    segs: List[Tuple[int, int, int, int]],
    ref_seg: Tuple[int, int, int, int],
    axis: int,
    tol: int = 200,
) -> List:
    """Drop segments whose midpoint is far from ref_seg's midpoint along given axis."""
    if axis == 0:
        ref = (ref_seg[0] + ref_seg[2]) / 2
        return [s for s in segs if abs((s[0] + s[2]) / 2 - ref) < tol]
    ref = (ref_seg[1] + ref_seg[3]) / 2
    return [s for s in segs if abs((s[1] + s[3]) / 2 - ref) < tol]


def _detect_paper_corners(
    image: np.ndarray,
) -> Tuple[Optional[np.ndarray], RectificationMetadata]:
    """Detect 4 paper corners. Returns (corners_array, metadata).

    corners_array is a (4, 2) float32 array in TL/TR/BR/BL order, or None on
    failure.
    """
    H, W = image.shape[:2]
    paper_mask = _build_paper_mask(image)
    edges = cv2.Canny(paper_mask, 50, 150)

    min_len = int(min(W, H) * 0.05)
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi / 360,
        threshold=50, minLineLength=min_len, maxLineGap=500,
    )
    if lines is None or len(lines) == 0:
        return None, RectificationMetadata(
            success=False, skip_reason="No Hough lines on paper boundary"
        )

    top_segs, bot_segs, right_segs = _bucket_segments_by_side(lines, W, H)
    if not (top_segs and bot_segs and right_segs):
        return None, RectificationMetadata(
            success=False,
            skip_reason=(
                f"Missing edges (top:{len(top_segs)}, bot:{len(bot_segs)}, "
                f"right:{len(right_segs)})"
            ),
            edges_detected={"top": len(top_segs), "bot": len(bot_segs), "right": len(right_segs)},
        )

    # Pick longest segment as the side's reference, then keep nearby segments only
    top_ref = max(top_segs, key=_segment_length)
    bot_ref = max(bot_segs, key=_segment_length)
    right_ref = max(right_segs, key=_segment_length)

    top_clean = _filter_near(top_segs, top_ref, axis=1)
    bot_clean = _filter_near(bot_segs, bot_ref, axis=1)
    right_clean = _filter_near(right_segs, right_ref, axis=0)

    top_line = _fit_line(top_clean)
    bot_line = _fit_line(bot_clean)
    right_line = _fit_line(right_clean)

    tr = _intersect_lines(top_line, right_line)
    br = _intersect_lines(bot_line, right_line)
    if tr is None or br is None:
        return None, RectificationMetadata(
            success=False, skip_reason="Could not intersect right edge with top/bottom"
        )

    # Derive TL and BL geometrically: walk back along top/bottom edge by paper width.
    # Paper width in image ≈ right-edge length × LETTER_ASPECT (8.5/11).
    right_len = float(np.hypot(br[0] - tr[0], br[1] - tr[1]))
    paper_width_px = right_len * LETTER_ASPECT

    # Top edge unit vector pointing TR → TL (away from right side)
    vx_top, vy_top, _, _ = top_line
    if vx_top > 0:
        vx_top, vy_top = -vx_top, -vy_top
    tl = (tr[0] + vx_top * paper_width_px, tr[1] + vy_top * paper_width_px)

    vx_bot, vy_bot, _, _ = bot_line
    if vx_bot > 0:
        vx_bot, vy_bot = -vx_bot, -vy_bot
    bl = (br[0] + vx_bot * paper_width_px, br[1] + vy_bot * paper_width_px)

    corners = np.array([tl, tr, br, bl], dtype=np.float32)
    return corners, RectificationMetadata(
        success=True,
        corners=tuple(tuple(c) for c in corners),
        paper_aspect_observed=right_len / paper_width_px,
        edges_detected={
            "top": len(top_clean), "bot": len(bot_clean), "right": len(right_clean)
        },
    )


def rectify_paper(
    image: Image.Image,
    output_width: int = DEFAULT_OUTPUT_WIDTH,
    output_height: int = DEFAULT_OUTPUT_HEIGHT,
) -> Tuple[Optional[Image.Image], RectificationMetadata]:
    """Detect paper, warp to letter-aspect canvas.

    Args:
        image: PIL Image of photographed worksheet.
        output_width / output_height: dimensions of rectified canvas.

    Returns:
        (rectified_image, metadata). rectified_image is None when paper
        boundary couldn't be detected; caller should fall back to working in
        the original image coordinate frame.
    """
    arr = np.array(image.convert("RGB"))
    corners, meta = _detect_paper_corners(arr)
    if corners is None:
        logger.info(f"Paper rectification skipped: {meta.skip_reason}")
        return None, meta

    dst = np.array(
        [
            [0, 0],
            [output_width - 1, 0],
            [output_width - 1, output_height - 1],
            [0, output_height - 1],
        ],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(corners, dst)
    rectified = cv2.warpPerspective(arr, M, (output_width, output_height))
    return Image.fromarray(rectified), meta
