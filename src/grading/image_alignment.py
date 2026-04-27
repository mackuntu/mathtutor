"""Image alignment utilities for transforming PDF coordinates to image coordinates."""

import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


# Empirically measured layout constants for HTML worksheet
# Based on test image: worksheet 7c81b248, image 4284x5712
# Measurements taken from actual worksheet photos with handwritten answers
HTML_LAYOUT = {
    # Page margins
    "margin_x_ratio": 0.05,  # 5% margin on each side
    "printable_width_ratio": 0.90,  # 90% of page width

    # Grid structure
    "columns": 5,

    # Fixed row positions (empirically determined from 8-row worksheet)
    # Row 1 answers at ~16.5%, Row 8 answers at ~85.5%
    # These are the Y-positions where answer boxes START
    "row_y_positions": [0.165],  # Row 1 at 16.5%, others calculated from spacing

    # Row spacing: (85.5% - 16.5%) / 7 rows = ~9.86%
    "row_spacing": 0.099,  # ~9.9% between row starts

    # Answer box dimensions within each cell
    "box_width_ratio": 0.126,  # ~12.6% of page width (70% of column)
    "box_height_ratio": 0.035,  # 3.5% of page height (captures handwritten numbers)
}


def calculate_html_grid_rois(
    num_problems: int,
    page_width_px: Optional[int] = None,
    page_height_px: Optional[int] = None,
) -> List[Tuple[float, float, float, float]]:
    """
    Calculate answer box ROIs using fixed position model.

    The HTML worksheet uses fixed CSS spacing (rem units) and only occupies
    the top ~35% of the page. This function uses empirically measured
    positions rather than assuming the grid expands to fill the page.

    Args:
        num_problems: Number of problems on the worksheet
        page_width_px: Optional page width in pixels (for direct pixel coords)
        page_height_px: Optional page height in pixels (for direct pixel coords)

    Returns:
        List of (x1, y1, x2, y2) tuples in normalized coordinates (0-1)
        or pixel coordinates if page dimensions provided
    """
    layout = HTML_LAYOUT
    columns = layout["columns"]
    rows = (num_problems + columns - 1) // columns

    # Column center positions
    col_width = layout["printable_width_ratio"] / columns
    col_centers = [
        layout["margin_x_ratio"] + col_width * (i + 0.5)
        for i in range(columns)
    ]

    # Row Y positions (use fixed positions, extend if needed)
    row_y_starts = list(layout["row_y_positions"])
    while len(row_y_starts) < rows:
        row_y_starts.append(
            row_y_starts[-1] + layout["row_spacing"]
        )

    # Build ROIs
    box_half_width = layout["box_width_ratio"] / 2
    box_height = layout["box_height_ratio"]

    rois = []
    for i in range(num_problems):
        col = i % columns
        row = i // columns

        x_center = col_centers[col]
        y_start = row_y_starts[row]

        x1 = x_center - box_half_width
        y1 = y_start
        x2 = x_center + box_half_width
        y2 = y_start + box_height

        rois.append((x1, y1, x2, y2))

    # Convert to pixels if dimensions provided
    if page_width_px is not None and page_height_px is not None:
        rois = [
            (
                int(x1 * page_width_px),
                int(y1 * page_height_px),
                int(x2 * page_width_px),
                int(y2 * page_height_px),
            )
            for x1, y1, x2, y2 in rois
        ]

    return rois


def transform_rois_to_image_coords(
    rois: List[Tuple[int, int, int, int]],
    pdf_dimensions: Tuple[int, int],
    image_dimensions: Tuple[int, int],
    padding_percent: float = 0.15,
) -> List[Tuple[int, int, int, int]]:
    """
    Transform PDF ROIs to image coordinates.

    PDF coordinate system:
    - Origin: bottom-left
    - Y increases upward
    - Units: points (1/72 inch)

    Image coordinate system:
    - Origin: top-left
    - Y increases downward
    - Units: pixels

    Args:
        rois: List of (x1, y1, x2, y2) tuples in PDF coordinates
        pdf_dimensions: (width, height) of PDF in points
        image_dimensions: (width, height) of image in pixels
        padding_percent: Percentage of box size to add as padding (default 15%)

    Returns:
        List of (x1, y1, x2, y2) tuples in image coordinates
    """
    pdf_width, pdf_height = pdf_dimensions
    img_width, img_height = image_dimensions

    # Calculate scale factors
    scale_x = img_width / pdf_width
    scale_y = img_height / pdf_height

    logger.debug(
        f"Transforming ROIs: PDF {pdf_dimensions} -> Image {image_dimensions}, "
        f"scale_x={scale_x:.3f}, scale_y={scale_y:.3f}"
    )

    transformed_rois = []
    for roi in rois:
        x1_pdf, y1_pdf, x2_pdf, y2_pdf = roi

        # Transform X coordinates (simple scaling)
        x1_img = int(x1_pdf * scale_x)
        x2_img = int(x2_pdf * scale_x)

        # Transform Y coordinates (flip and scale)
        # PDF Y increases upward, image Y increases downward
        # y_image = image_height - (y_pdf * scale_y)
        y1_img = int(img_height - (y2_pdf * scale_y))  # y2_pdf is higher in PDF
        y2_img = int(img_height - (y1_pdf * scale_y))  # y1_pdf is lower in PDF

        # Ensure correct ordering (y1 < y2 for image coordinates)
        if y1_img > y2_img:
            y1_img, y2_img = y2_img, y1_img

        # Add padding for tolerance
        width = x2_img - x1_img
        height = y2_img - y1_img
        pad_x = int(width * padding_percent)
        pad_y = int(height * padding_percent)

        x1_img = max(0, x1_img - pad_x)
        y1_img = max(0, y1_img - pad_y)
        x2_img = min(img_width, x2_img + pad_x)
        y2_img = min(img_height, y2_img + pad_y)

        transformed_rois.append((x1_img, y1_img, x2_img, y2_img))
        logger.debug(
            f"ROI transformed: PDF ({x1_pdf}, {y1_pdf}, {x2_pdf}, {y2_pdf}) -> "
            f"Image ({x1_img}, {y1_img}, {x2_img}, {y2_img})"
        )

    return transformed_rois


def crop_image_regions(
    image,
    regions: List[Tuple[int, int, int, int]],
) -> List:
    """
    Crop multiple regions from an image.

    Args:
        image: PIL Image object
        regions: List of (x1, y1, x2, y2) tuples in image coordinates

    Returns:
        List of cropped PIL Image objects
    """
    crops = []
    for region in regions:
        x1, y1, x2, y2 = region
        # Ensure valid crop region
        x1 = max(0, min(x1, image.width - 1))
        y1 = max(0, min(y1, image.height - 1))
        x2 = max(x1 + 1, min(x2, image.width))
        y2 = max(y1 + 1, min(y2, image.height))

        cropped = image.crop((x1, y1, x2, y2))
        crops.append(cropped)

    return crops


def image_to_base64(image, format: str = "PNG") -> str:
    """
    Convert a PIL Image to base64-encoded string.

    Args:
        image: PIL Image object
        format: Image format (default: PNG)

    Returns:
        Base64-encoded string
    """
    import base64
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def base64_to_image(base64_string: str):
    """
    Convert a base64-encoded string back to a PIL Image.

    Args:
        base64_string: Base64-encoded image string

    Returns:
        PIL Image object
    """
    import base64
    from io import BytesIO
    from PIL import Image

    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data))
