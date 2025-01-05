from io import BytesIO

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader


class MarkerUtils:
    PDF_MARKERS = [
        (10, 10),  # Bottom-left
        (10, 770),  # Top-left
        (590, 10),  # Bottom-right
        (590, 770),  # Top-right
    ]
    REQUIRED_MARKER_IDS = [0, 1, 2, 3]  # IDs for the alignment markers

    @staticmethod
    def map_pdf_to_image_space(
        pdf_rois, image_markers, image_dimensions, visualize=True
    ):
        """
        Map ROIs from PDF coordinate space to image space using alignment markers and visualize.

        Args:
            pdf_rois (list of tuples): ROIs in PDF coordinate space [(x1, y1, x2, y2), ...].
            image_markers (list of tuples): ArUco marker positions in image space [(x, y), ...].
            image_dimensions (tuple): Dimensions of the image as (width, height).
            visualize (bool): Whether to visualize the transformation.

        Returns:
            list of tuples: Validated and transformed ROIs in image space.
        """
        # Ensure PDF_MARKERS and image_markers have the same length
        if len(MarkerUtils.PDF_MARKERS) != len(image_markers):
            raise ValueError(
                "Mismatch between number of PDF markers and image markers."
            )

        # Compute the transformation matrix using alignment markers
        pdf_points = np.array(MarkerUtils.PDF_MARKERS, dtype=np.float32)
        image_points = np.array(image_markers, dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(pdf_points, image_points)

        # Transform the ROIs
        image_width, image_height = image_dimensions
        transformed_rois = []

        for roi in pdf_rois:
            top_left = np.array([[[roi[0], roi[1]]]], dtype=np.float32)
            bottom_right = np.array([[[roi[2], roi[3]]]], dtype=np.float32)

            transformed_top_left = cv2.perspectiveTransform(top_left, matrix)[0][0]
            transformed_bottom_right = cv2.perspectiveTransform(bottom_right, matrix)[
                0
            ][0]

            x1 = max(0, min(int(round(transformed_top_left[0])), image_width))
            y1 = max(0, min(int(round(transformed_top_left[1])), image_height))
            x2 = max(0, min(int(round(transformed_bottom_right[0])), image_width))
            y2 = max(0, min(int(round(transformed_bottom_right[1])), image_height))

            if x2 > x1 and y2 > y1:
                transformed_rois.append((x1, y1, x2, y2))
            else:
                print(
                    f"Invalid transformed ROI: {(x1, y1, x2, y2)} from original ROI {roi}"
                )
                # raise ValueError(f"Invalid ROI after transformation: {roi}")

        if visualize:
            MarkerUtils.visualize_rois(image_dimensions, pdf_rois, transformed_rois)

        return transformed_rois

    @staticmethod
    def visualize_rois(image_dimensions, pdf_rois, transformed_rois):
        """
        Visualize the ROIs in PDF space and transformed image space.

        Args:
            image_dimensions (tuple): Dimensions of the image as (width, height).
            pdf_rois (list of tuples): ROIs in PDF coordinate space.
            transformed_rois (list of tuples): Transformed ROIs in image space.
        """
        pdf_canvas = Image.new(
            "RGB", (800, 800), "white"
        )  # Assume PDF space is 800x800
        draw_pdf = ImageDraw.Draw(pdf_canvas)

        # Draw PDF ROIs
        for roi in pdf_rois:
            draw_pdf.rectangle(roi, outline="blue", width=2)

        # Plot PDF ROIs
        plt.figure(figsize=(10, 10))
        plt.title("PDF ROIs")
        plt.imshow(pdf_canvas)
        plt.show()

        # Draw transformed ROIs on the scanned image
        scanned_image = Image.new("RGB", image_dimensions, "white")
        draw_image = ImageDraw.Draw(scanned_image)

        for roi in transformed_rois:
            draw_image.rectangle(roi, outline="red", width=2)

        # Plot Transformed ROIs
        plt.figure(figsize=(10, 10))
        plt.title("Transformed Image ROIs")
        plt.imshow(scanned_image)
        plt.show()

    @staticmethod
    def detect_alignment_markers(image_path):
        """Detect ArUco markers in the scanned image."""
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

        # Map detected marker IDs to their centers
        markers = {}
        for corner, marker_id in zip(corners, ids.flatten()):
            center_x = int(corner[0][:, 0].mean())
            center_y = int(corner[0][:, 1].mean())
            markers[marker_id] = (center_x, center_y)

        # Ensure all required markers are detected
        for marker_id in MarkerUtils.REQUIRED_MARKER_IDS:
            if marker_id not in markers:
                raise ValueError(f"Marker ID {marker_id} not found in the image.")

        return [markers[marker_id] for marker_id in MarkerUtils.REQUIRED_MARKER_IDS]

    @staticmethod
    def draw_alignment_markers(pdf, marker_size=100):
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
                width=marker_size / 10,
                height=marker_size / 10,
            )
