import logging
from io import BytesIO

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader


class MarkerUtils:
    PDF_MARKERS = np.array(
        [
            (15, 15),  # Bottom-left
            (15, 765),  # Top-left
            (585, 15),  # Bottom-right
            (585, 765),  # Top-right
        ],
        dtype=np.float32,
    )
    REQUIRED_MARKER_IDS = [0, 1, 2, 3]  # IDs for the alignment markers

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
    def map_pdf_to_image_space(
        pdf_rois, image_markers, image_dimensions, visualize=False
    ):
        """
        Map ROIs from PDF coordinate space to image space using alignment markers.

        Args:
            pdf_rois (list of tuples): ROIs in PDF coordinate space [(x1, y1, x2, y2), ...].
            image_markers (list of tuples): ArUco marker positions in image space [(x, y), ...].
            image_dimensions (tuple): Dimensions of the image as (width, height).
            visualize (bool): Whether to visualize the transformation.

        Returns:
            list of tuples: Validated and transformed ROIs in image space.
        """
        if len(MarkerUtils.PDF_MARKERS) != len(image_markers):
            raise ValueError(
                "Mismatch between number of PDF markers and image markers."
            )

        image_width, image_height = image_dimensions

        # Ensure MarkerUtils.PDF_MARKERS is a numpy array
        pdf_points = MarkerUtils.PDF_MARKERS
        logging.warning(f"PDF Points: {pdf_points}")

        # pdf_points[:, 1] = pdf_height - pdf_points[:, 1]
        image_points = np.array(image_markers, dtype=np.float32)
        logging.warning(f"Image Points: {image_points}")

        if not MarkerUtils.is_valid_quadrilateral(
            pdf_points
        ) or not MarkerUtils.is_valid_quadrilateral(image_points):
            raise ValueError(
                "Points are collinear or insufficient for a valid perspective transformation."
            )

        # Compute transformation matrix
        try:
            matrix = cv2.getPerspectiveTransform(pdf_points, image_points)
            logging.warning(f"Transformation Matrix: {matrix}")
            # Validate the matrix by transforming pdf_points and comparing to image_points
            transformed_pdf_points = cv2.perspectiveTransform(
                np.array([pdf_points], dtype=np.float32), matrix
            )
            for i, (transformed, expected) in enumerate(
                zip(transformed_pdf_points[0], image_points)
            ):
                if not np.allclose(transformed, expected, atol=1e-2):
                    logging.error(
                        f"Matrix validation failed for point {i}: {transformed} != {expected}"
                    )
                    raise ValueError(
                        "Transformation matrix does not map points correctly."
                    )
        except cv2.error as e:
            raise ValueError(f"Error computing perspective transform: {e}")

        # Transform ROIs
        transformed_rois = []
        for roi in pdf_rois:
            # Modify ROI transformation to avoid manual reversal:
            roi_points = np.array(
                [[[roi[0], roi[1]], [roi[2], roi[3]]]], dtype=np.float32
            )

            try:
                transformed_points = cv2.perspectiveTransform(roi_points, matrix)
            except cv2.error as e:
                logging.error(f"Failed to transform ROI {roi}: {e}")
                continue

            # Vectorized clipping and conversion
            clipped_points = np.clip(
                transformed_points[0], [0, 0], [image_width, image_height]
            ).astype(int)
            x1, y1 = clipped_points[0]
            x2, y2 = clipped_points[1]

            # Validate and append ROIs
            if x2 > x1 and y2 > y1:
                transformed_rois.append((x1, y1, x2, y2))
            else:
                logging.warning(
                    f"Invalid transformed ROI: {(x1, y1, x2, y2)} from original ROI {roi}"
                )

        if visualize:
            MarkerUtils.visualize_rois(image_dimensions, pdf_rois, transformed_rois)

        return transformed_rois

    @staticmethod
    def visualize_rois(image_dimensions, pdf_rois, transformed_rois):
        """
        Visualize the ROIs in PDF space and transformed image space, with corner annotations.

        Args:
            image_dimensions (tuple): Dimensions of the image as (width, height).
            pdf_rois (list of tuples): ROIs in PDF coordinate space.
            transformed_rois (list of tuples): Transformed ROIs in image space.
        """
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

    @staticmethod
    def detect_alignment_markers(image_path):
        """Detect ArUco markers in the scanned image and align to the PDF reference corner."""
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Load predefined dictionary
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

        # Detect markers
        corners, ids, _ = detector.detectMarkers(gray)

        if ids is None or len(ids) < 4:
            raise ValueError("Not all alignment markers detected.")

        # Map detected marker IDs to their top-left corners
        markers = {}
        for corner, marker_id in zip(corners, ids.flatten()):
            # Use the bottom-left corner (consistent with PDF drawing)
            bottom_left_corner = corner[0][3]  # Bottom-left corner of the marker
            bottom_left_x = int(bottom_left_corner[0])
            bottom_left_y = int(bottom_left_corner[1])
            markers[marker_id] = (bottom_left_x, bottom_left_y)

        # Ensure all required markers are detected
        for marker_id in MarkerUtils.REQUIRED_MARKER_IDS:
            if marker_id not in markers:
                raise ValueError(f"Marker ID {marker_id} not found in the image.")

        return [markers[marker_id] for marker_id in MarkerUtils.REQUIRED_MARKER_IDS]

    @staticmethod
    def draw_alignment_markers(pdf, marker_size=10):
        """Draw ArUco alignment markers on the PDF."""
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        for (x, y), marker_id in zip(
            MarkerUtils.PDF_MARKERS, MarkerUtils.REQUIRED_MARKER_IDS
        ):
            marker_image = cv2.aruco.generateImageMarker(
                aruco_dict, marker_id, marker_size
            )
            _, buffer = cv2.imencode(".png", marker_image)
            marker_image_stream = BytesIO(buffer.tobytes())
            marker_image_reader = ImageReader(marker_image_stream)
            pdf.drawImage(
                marker_image_reader,
                x,
                y,
                width=marker_size,
                height=marker_size,
            )
