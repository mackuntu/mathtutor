"""Detect answer-region ROIs by finding the printed `addition-line` borders.

For each problem in `src/templates/problem_grid.html`, the print includes a
horizontal line (the `.addition-line` div's border-bottom) directly above the
answer space. Detecting those lines anchors ROIs to the printed grid rather
than relying on absolute pixel positions, which makes the algorithm robust to
slight rotation, perspective, and paper offset within the photo frame.

Pipeline:
1. Adaptive threshold isolates printed dark structures.
2. Horizontal morphology keeps long horizontal segments (addition-lines, but
   also some title underlines and stray noise).
3. Width filter (4-10% of image width) selects only structures matching the
   3.9rem `.problem-content` width — drops grid-wide separators and short
   underlines.
4. Y-clustering groups segments into row candidates.
5. Per-column linear fit `X(y) = a*y + b` from rows with all 5 lines tolerates
   any residual perspective.
6. Missing lines (handwriting obscuring the print) are interpolated from the
   per-column fit at the row's median Y.
7. Uniform-size ROIs centered on (predicted_x, line_y).

All thresholds are ratios of image dimensions, so the algorithm scales with
input resolution.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class DetectorConfig:
    """Tunable parameters. Defaults work for `problem_grid.html` (5 columns)."""
    expected_columns: int = 5
    # Horizontal-erosion kernel as fraction of image width
    kernel_length_ratio: float = 0.028
    # Y-cluster gap threshold as fraction of image height
    cluster_gap_ratio: float = 0.025
    # Width filter for line candidates (fractions of image width)
    min_line_width_ratio: float = 0.04
    max_line_width_ratio: float = 0.10
    max_line_thickness_px: int = 25
    line_aspect_ratio: float = 5.0  # w/h must exceed this
    # Drop clusters whose top edge is in this fraction of image (title area)
    top_margin_ratio: float = 0.10
    # ROI dimensions
    roi_width_padding_ratio: float = 0.20  # extra padding on each side of detected line width
    roi_above_ratio: float = 0.08          # fraction of row spacing above line
    roi_below_ratio: float = 0.58          # fraction of row spacing below line
    # Adaptive threshold (cv2 specific)
    adaptive_block_size: int = 31
    adaptive_C: int = 15
    # Fallback contract: minimum complete rows needed for column template
    min_complete_rows_for_template: int = 3


@dataclass
class DetectionMetadata:
    """Diagnostic info about the ROI detection run."""
    rows_detected: int = 0
    lines_per_row: List[int] = field(default_factory=list)
    interpolated_count: int = 0
    column_slopes: List[float] = field(default_factory=list)  # X(y) drift per column
    fallback_reason: Optional[str] = None  # set when caller should use fixed-% fallback


def _binarize(image: Image.Image, cfg: DetectorConfig) -> np.ndarray:
    gray = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,
        cfg.adaptive_block_size, cfg.adaptive_C,
    )


def _detect_horizontal_segments(binary: np.ndarray, image_w: int, cfg: DetectorConfig) -> np.ndarray:
    """Erode then dilate with a horizontal kernel to keep only horizontal structures."""
    kernel_len = max(20, int(image_w * cfg.kernel_length_ratio))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    horiz = cv2.erode(binary, kernel, iterations=1)
    horiz = cv2.dilate(horiz, kernel, iterations=1)
    return horiz


def _filter_line_candidates(
    horiz_mask: np.ndarray, image_w: int, cfg: DetectorConfig
) -> List[Tuple[int, int, int, int]]:
    contours, _ = cv2.findContours(horiz_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_w = int(image_w * cfg.min_line_width_ratio)
    max_w = int(image_w * cfg.max_line_width_ratio)
    out = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if (
            min_w <= w <= max_w
            and h <= cfg.max_line_thickness_px
            and w > h * cfg.line_aspect_ratio
        ):
            out.append((x, y, w, h))
    out.sort(key=lambda l: l[1])
    return out


def _cluster_rows(
    candidates: List[Tuple[int, int, int, int]],
    image_h: int,
    cfg: DetectorConfig,
) -> List[List[Tuple[int, int, int, int]]]:
    """Y-cluster candidates by gap. Drop clusters in the top margin or with
    fewer than 4 lines (rules out title underlines, footers)."""
    if not candidates:
        return []
    clusters = []
    current = [candidates[0]]
    gap = int(image_h * cfg.cluster_gap_ratio)
    for c in candidates[1:]:
        if c[1] - current[-1][1] < gap:
            current.append(c)
        else:
            clusters.append(current)
            current = [c]
    clusters.append(current)

    real = []
    for cl in clusters:
        if len(cl) < cfg.expected_columns - 1:
            continue
        if min(l[1] for l in cl) < image_h * cfg.top_margin_ratio:
            continue
        real.append(cl)
    return real


def _fit_columns(
    rows: List[List[Tuple[int, int, int, int]]],
    cfg: DetectorConfig,
) -> Tuple[List[Tuple[float, float]], List[float]]:
    """Per-column linear fit X(y) = a*y + b from rows with all 5 lines.

    Returns (fits, all_widths) where fits[col] = (a, b).
    Raises ValueError if not enough complete rows.
    """
    complete = [r for r in rows if len(r) == cfg.expected_columns]
    if len(complete) < cfg.min_complete_rows_for_template:
        raise ValueError(
            f"Need >= {cfg.min_complete_rows_for_template} complete rows for "
            f"column template; got {len(complete)}"
        )

    col_x = [[] for _ in range(cfg.expected_columns)]
    col_y = [[] for _ in range(cfg.expected_columns)]
    widths = []
    for cl in complete:
        for i, (x, y, w, h) in enumerate(sorted(cl, key=lambda l: l[0])):
            col_x[i].append(x + w / 2)
            col_y[i].append(y + h / 2)
            widths.append(w)

    fits = []
    for c in range(cfg.expected_columns):
        a, b = np.polyfit(col_y[c], col_x[c], 1)
        fits.append((float(a), float(b)))
    return fits, widths


def _predict_x(fit: Tuple[float, float], y: float) -> float:
    a, b = fit
    return a * y + b


def _build_rois(
    rows: List[List[Tuple[int, int, int, int]]],
    fits: List[Tuple[float, float]],
    line_width: int,
    row_spacing: int,
    image_w: int,
    image_h: int,
    cfg: DetectorConfig,
) -> Tuple[List[Tuple[int, int, int, int]], List[bool]]:
    roi_w = line_width + 2 * int(line_width * cfg.roi_width_padding_ratio)
    roi_above = int(row_spacing * cfg.roi_above_ratio)
    roi_below = int(row_spacing * cfg.roi_below_ratio)

    rois: List[Tuple[int, int, int, int]] = []
    interpolated: List[bool] = []
    for row in rows:
        sorted_lines = sorted(row, key=lambda l: l[0])
        median_y = float(np.median([l[1] + l[3] / 2 for l in sorted_lines]))

        # Match each detected line to nearest column by X-fit prediction
        matched: List[Optional[Tuple[float, float]]] = [None] * cfg.expected_columns
        for line in sorted_lines:
            x_c = line[0] + line[2] / 2
            y_c = line[1] + line[3] / 2
            best = min(
                range(cfg.expected_columns),
                key=lambda c: abs(_predict_x(fits[c], y_c) - x_c),
            )
            if matched[best] is None:
                matched[best] = (x_c, y_c)

        for col in range(cfg.expected_columns):
            if matched[col] is not None:
                x_c, y_c = matched[col]
                interp = False
            else:
                x_c, y_c = _predict_x(fits[col], median_y), median_y
                interp = True
            x1 = max(0, int(x_c - roi_w / 2))
            x2 = min(image_w, int(x_c + roi_w / 2))
            y1 = max(0, int(y_c - roi_above))
            y2 = min(image_h, int(y_c + roi_below))
            rois.append((x1, y1, x2, y2))
            interpolated.append(interp)
    return rois, interpolated


def detect_rois(
    image: Image.Image,
    num_problems: int,
    config: Optional[DetectorConfig] = None,
) -> Tuple[List[Tuple[int, int, int, int]], DetectionMetadata]:
    """Detect ROIs for handwritten answers.

    Args:
        image: PIL Image (post-rectification recommended for best results).
        num_problems: Expected number of problems on the worksheet.
        config: Override default tuning.

    Returns:
        (rois, metadata). When the algorithm cannot run reliably, `rois` is an
        empty list and `metadata.fallback_reason` is set; the caller is
        expected to fall back to a coordinate-based ROI computation.
    """
    cfg = config or DetectorConfig()
    expected_rows = (num_problems + cfg.expected_columns - 1) // cfg.expected_columns
    W, H = image.size

    binary = _binarize(image, cfg)
    horiz_mask = _detect_horizontal_segments(binary, W, cfg)
    candidates = _filter_line_candidates(horiz_mask, W, cfg)
    rows = _cluster_rows(candidates, H, cfg)

    if len(rows) < expected_rows:
        return [], DetectionMetadata(
            rows_detected=len(rows),
            lines_per_row=[len(r) for r in rows],
            fallback_reason=f"Detected {len(rows)} rows, expected {expected_rows}",
        )

    rows = rows[:expected_rows]

    try:
        fits, widths = _fit_columns(rows, cfg)
    except ValueError as e:
        return [], DetectionMetadata(
            rows_detected=len(rows),
            lines_per_row=[len(r) for r in rows],
            fallback_reason=str(e),
        )

    line_width = int(np.percentile(widths, 90))
    spacings = np.diff([np.median([l[1] + l[3] / 2 for l in cl]) for cl in rows])
    if len(spacings) == 0:
        return [], DetectionMetadata(
            rows_detected=len(rows),
            lines_per_row=[len(r) for r in rows],
            fallback_reason="Cannot compute row spacing (only one row)",
        )
    row_spacing = int(np.median(spacings))

    rois, interp = _build_rois(rows, fits, line_width, row_spacing, W, H, cfg)

    return rois, DetectionMetadata(
        rows_detected=len(rows),
        lines_per_row=[len(r) for r in rows],
        interpolated_count=sum(interp),
        column_slopes=[a for a, _ in fits],
    )
