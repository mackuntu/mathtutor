import logging
from io import BytesIO

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)


class MarkerUtils:
    """Utility class for handling alignment markers."""

    # Marker positions in points (72 DPI)
    MARKER_SIZE = 20  # Size of each marker in points
    MARGIN = 40  # Margin from page edges in points

    REQUIRED_MARKER_IDS = [0, 1, 2, 3]  # IDs for the four corner markers

    @staticmethod
    def create_corner_pattern(size=20):
        """Create a unique corner pattern with nested squares and diagonal lines."""
        # Create a white image with padding to avoid edge artifacts
        padded_size = size + 4
        pattern = Image.new("L", (padded_size, padded_size), 255)
        draw = ImageDraw.Draw(pattern)

        # Calculate actual pattern size within padding
        pattern_size = size
        offset = 2  # Padding offset

        # Draw outer square
        margin = 2
        draw.rectangle(
            [
                offset + margin,
                offset + margin,
                offset + pattern_size - margin - 1,
                offset + pattern_size - margin - 1,
            ],
            outline=0,
            width=2,
        )

        # Draw inner filled square
        inner_size = pattern_size // 3
        inner_offset = offset + (pattern_size - inner_size) // 2
        draw.rectangle(
            [
                inner_offset,
                inner_offset,
                inner_offset + inner_size - 1,
                inner_offset + inner_size - 1,
            ],
            fill=0,
        )

        # Draw diagonal lines from corners to inner square
        # Top-left to inner square
        draw.line(
            [(offset + margin, offset + margin), (inner_offset, inner_offset)],
            fill=0,
            width=2,
        )
        # Top-right to inner square
        draw.line(
            [
                (offset + pattern_size - margin - 1, offset + margin),
                (inner_offset + inner_size - 1, inner_offset),
            ],
            fill=0,
            width=2,
        )
        # Bottom-left to inner square
        draw.line(
            [
                (offset + margin, offset + pattern_size - margin - 1),
                (inner_offset, inner_offset + inner_size - 1),
            ],
            fill=0,
            width=2,
        )
        # Bottom-right to inner square
        draw.line(
            [
                (
                    offset + pattern_size - margin - 1,
                    offset + pattern_size - margin - 1,
                ),
                (inner_offset + inner_size - 1, inner_offset + inner_size - 1),
            ],
            fill=0,
            width=2,
        )

        # Convert to numpy array and crop to remove padding
        pattern_np = np.array(pattern)
        pattern_np = pattern_np[2:-2, 2:-2]  # Remove padding
        return pattern_np

    @staticmethod
    def draw_alignment_markers(pdf, width: float, height: float) -> None:
        """Draw ArUco markers in the corners of the page.

        Args:
            pdf: ReportLab canvas to draw on.
            width: Page width in points.
            height: Page height in points.
        """
        # Create ArUco dictionary
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        # Generate markers for each corner
        marker_positions = [
            (MarkerUtils.MARGIN, MarkerUtils.MARGIN),  # Bottom-left
            (MarkerUtils.MARGIN, height - MarkerUtils.MARGIN),  # Top-left
            (width - MarkerUtils.MARGIN, MarkerUtils.MARGIN),  # Bottom-right
            (width - MarkerUtils.MARGIN, height - MarkerUtils.MARGIN),  # Top-right
        ]

        for marker_id, (x, y) in enumerate(marker_positions):
            # Generate marker image
            marker_img = cv2.aruco.generateImageMarker(
                aruco_dict, marker_id, MarkerUtils.MARKER_SIZE
            )

            # Convert to PIL Image
            marker_pil = Image.fromarray(marker_img)

            # Convert to bytes for ReportLab
            marker_stream = BytesIO()
            marker_pil.save(marker_stream, format="PNG")
            marker_stream.seek(0)

            # Create ImageReader object
            marker_reader = ImageReader(marker_stream)

            # Draw the marker at the specified position
            # Note: ReportLab coordinates are from bottom-left
            pdf.drawImage(
                marker_reader,
                x - MarkerUtils.MARKER_SIZE / 2,
                y - MarkerUtils.MARKER_SIZE / 2,
                width=MarkerUtils.MARKER_SIZE,
                height=MarkerUtils.MARKER_SIZE,
            )

    @staticmethod
    def detect_alignment_markers(image_path):
        """Detect ArUco markers in the image and ensure all required markers are present."""
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Create ArUco dictionary
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()

        # Detect markers
        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
        corners, ids, rejected = detector.detectMarkers(gray)

        # Save debug image
        debug_img = cv2.cvtColor(gray.copy(), cv2.COLOR_GRAY2BGR)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(debug_img, corners, ids)
        cv2.imwrite("debug_template_match.png", debug_img)

        if ids is None:
            raise ValueError("No markers detected")

        # Convert ids to list for easier handling
        ids = ids.flatten().tolist()

        # Check if all required markers are present
        if not all(marker_id in ids for marker_id in MarkerUtils.REQUIRED_MARKER_IDS):
            raise ValueError("Not all alignment markers detected")

        # Extract corners in the correct order
        marker_points = []
        for required_id in MarkerUtils.REQUIRED_MARKER_IDS:
            idx = ids.index(required_id)
            # Get center point of the marker
            corner = corners[idx][0]
            center_x = int(np.mean(corner[:, 0]))
            center_y = int(np.mean(corner[:, 1]))
            marker_points.append((center_x, center_y))

        return marker_points  # Return points in image space (300 DPI)

    @staticmethod
    def map_pdf_to_image_space(
        pdf_rois, image_markers, image_dimensions, visualize=False
    ):
        """Map ROIs from PDF coordinate space to image space using corner patterns."""
        if len(MarkerUtils.PDF_MARKERS) != len(image_markers):
            raise ValueError(
                "Mismatch between number of PDF markers and image markers."
            )

        image_width, image_height = image_dimensions

        # Convert PDF ROIs from 72 DPI to 300 DPI
        scaled_pdf_rois = []
        for roi in pdf_rois:
            x1, y1, x2, y2 = roi
            # Check for invalid ROI dimensions
            if x1 >= x2 or y1 >= y2:
                logging.warning(f"Invalid ROI dimensions: {roi}")
                continue
            scaled_pdf_rois.append(
                (x1 * 300 / 72, y1 * 300 / 72, x2 * 300 / 72, y2 * 300 / 72)
            )

        # If no valid ROIs, return empty list
        if not scaled_pdf_rois:
            return []

        # Ensure markers are numpy arrays
        pdf_points = MarkerUtils.PDF_MARKERS  # Already in 300 DPI
        image_points = np.array(image_markers, dtype=np.float32)  # Already in 300 DPI

        if not MarkerUtils.is_valid_quadrilateral(
            pdf_points
        ) or not MarkerUtils.is_valid_quadrilateral(image_points):
            raise ValueError(
                "Points are collinear or insufficient for a valid perspective transformation."
            )

        # Compute transformation matrix
        try:
            matrix = cv2.getPerspectiveTransform(pdf_points, image_points)
            # Transform ROIs
            transformed_rois = []
            for roi in scaled_pdf_rois:  # Use scaled ROIs
                roi_points = np.array(
                    [[[roi[0], roi[1]], [roi[2], roi[3]]]], dtype=np.float32
                )
                transformed_points = cv2.perspectiveTransform(roi_points, matrix)

                # Clip and convert to integers
                clipped_points = np.clip(
                    transformed_points[0], [0, 0], [image_width, image_height]
                ).astype(int)
                x1, y1 = clipped_points[0]
                x2, y2 = clipped_points[1]

                if x2 > x1 and y2 > y1:
                    transformed_rois.append((x1, y1, x2, y2))
                else:
                    logging.warning(
                        f"Invalid transformed ROI dimensions: ({x1}, {y1}, {x2}, {y2})"
                    )

            if visualize:
                MarkerUtils.visualize_rois(image_dimensions, pdf_rois, transformed_rois)

            return transformed_rois

        except cv2.error as e:
            raise ValueError(f"Error computing perspective transform: {e}")

    @staticmethod
    def is_valid_quadrilateral(points):
        """Ensure the points form a valid quadrilateral."""
        if len(points) != 4:
            return False

        # Calculate vectors between points
        vec1 = points[1] - points[0]
        vec2 = points[2] - points[1]
        vec3 = points[3] - points[2]
        vec4 = points[0] - points[3]

        # Ensure determinant is not zero (not collinear)
        det1 = np.cross(vec1, vec2)
        det2 = np.cross(vec2, vec3)
        det3 = np.cross(vec3, vec4)
        det4 = np.cross(vec4, vec1)

        return not (
            np.isclose(det1, 0)
            or np.isclose(det2, 0)
            or np.isclose(det3, 0)
            or np.isclose(det4, 0)
        )

    @staticmethod
    def visualize_rois(image_dimensions, pdf_rois, transformed_rois):
        """Visualize the ROIs in PDF space and transformed image space."""
        pdf_canvas_width = 600
        pdf_canvas_height = 800
        pdf_height = 800  # Letter size PDF height in points

        # Create canvas for PDF space
        pdf_canvas = Image.new("RGB", (pdf_canvas_width, pdf_canvas_height), "white")
        draw_pdf = ImageDraw.Draw(pdf_canvas)

        # Draw PDF ROIs (with Y-axis reversed for visualization clarity)
        for i, roi in enumerate(pdf_rois):
            x1, y1, x2, y2 = roi
            y1_vis = pdf_height - y1  # Reverse Y-axis for visualization
            y2_vis = pdf_height - y2
            draw_pdf.rectangle((x1, y1_vis, x2, y2_vis), outline="blue", width=2)
            draw_pdf.text((x1, y1_vis), f"PDF-{i + 1}", fill="blue")

            # Annotate corners
            corners = [(x1, y1_vis), (x2, y1_vis), (x2, y2_vis), (x1, y2_vis)]
            for idx, (cx, cy) in enumerate(corners):
                draw_pdf.text((cx, cy), f"{idx + 1}", fill="blue")

        # Plot PDF ROIs
        plt.figure(figsize=(10, 10))
        plt.title("PDF Coordinate Space ROIs")
        plt.imshow(pdf_canvas)
        plt.axis("on")
        plt.show()

        # Create canvas for Image space
        image_width, image_height = image_dimensions
        scanned_image = Image.new("RGB", (image_width, image_height), "white")
        draw_image = ImageDraw.Draw(scanned_image)

        # Draw Transformed ROIs
        for i, roi in enumerate(transformed_rois):
            x1, y1, x2, y2 = roi
            draw_image.rectangle((x1, y1, x2, y2), outline="red", width=2)
            draw_image.text((x1, y1), f"IMG-{i + 1}", fill="red")

            # Annotate corners
            corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            for idx, (cx, cy) in enumerate(corners):
                draw_image.text((cx, cy), f"{idx + 1}", fill="red")

        # Plot Transformed ROIs
        plt.figure(figsize=(10, 10))
        plt.title("Image Coordinate Space ROIs")
        plt.imshow(scanned_image)
        plt.axis("on")
        plt.show()
