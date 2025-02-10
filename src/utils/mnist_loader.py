"""Module for loading MNIST dataset for testing."""

import gzip
import os
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image


class MNISTLoader:
    """Helper class to load MNIST images for testing."""

    def __init__(self, mnist_dir: str = "data/MNIST/raw"):
        """Initialize MNIST loader.

        Args:
            mnist_dir: Directory containing MNIST dataset files.
        """
        self.mnist_dir = Path(mnist_dir)
        self._test_images = None
        self._test_labels = None

    def _load_mnist_file(self, filename: str) -> np.ndarray:
        """Load a MNIST file.

        Args:
            filename: Name of the file to load.

        Returns:
            Numpy array containing the data.
        """
        path = self.mnist_dir / filename
        with gzip.open(str(path), "rb") as f:
            data = np.frombuffer(
                f.read(), np.uint8, offset=16 if "images" in filename else 8
            )
            if "images" in filename:
                return data.reshape(-1, 28, 28)
            return data

    def load_test_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load MNIST test dataset.

        Returns:
            Tuple of (images, labels) arrays.
        """
        if self._test_images is None:
            self._test_images = self._load_mnist_file("t10k-images-idx3-ubyte.gz")
            self._test_labels = self._load_mnist_file("t10k-labels-idx1-ubyte.gz")
        return self._test_images, self._test_labels

    def _preprocess_mnist_image(self, img_array: np.ndarray) -> Image.Image:
        """Preprocess MNIST image for better OCR.

        Args:
            img_array: Raw MNIST image array.

        Returns:
            Preprocessed PIL Image.
        """
        # Convert to float32 and normalize
        img = img_array.astype(np.float32) / 255.0

        # Apply contrast stretching
        p2, p98 = np.percentile(img, (2, 98))
        img = np.clip((img - p2) / (p98 - p2), 0, 1)

        # Convert back to uint8
        img = (img * 255).astype(np.uint8)

        # Apply Gaussian blur to smooth edges
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # Apply Otsu's thresholding
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Add padding and resize to make it more like handwritten text
        target_size = (128, 128)  # Larger size for better detail
        padded = np.full(target_size, 255, dtype=np.uint8)

        # Calculate scaling to maintain aspect ratio
        scale = min(
            (target_size[0] - 40) / binary.shape[1],  # Leave 20px padding on each side
            (target_size[1] - 40) / binary.shape[0],  # Leave 20px padding on top/bottom
        )
        new_size = (int(binary.shape[1] * scale), int(binary.shape[0] * scale))

        # Resize the image
        resized = cv2.resize(binary, new_size, interpolation=cv2.INTER_LANCZOS4)

        # Calculate position to center the image
        x_offset = (target_size[0] - new_size[0]) // 2
        y_offset = (target_size[1] - new_size[1]) // 2

        # Paste the resized image onto the padded background
        padded[y_offset : y_offset + new_size[1], x_offset : x_offset + new_size[0]] = (
            resized
        )

        # Apply morphological operations to thicken the digits
        kernel = np.ones((2, 2), np.uint8)
        padded = cv2.dilate(padded, kernel, iterations=1)

        # Add random rotation (-5 to 5 degrees)
        angle = np.random.uniform(-5, 5)
        matrix = cv2.getRotationMatrix2D(
            (target_size[0] // 2, target_size[1] // 2), angle, 1.0
        )
        padded = cv2.warpAffine(padded, matrix, target_size)

        # Add slight perspective distortion
        if np.random.random() < 0.5:
            src_pts = np.float32(
                [
                    [0, 0],
                    [target_size[0], 0],
                    [0, target_size[1]],
                    [target_size[0], target_size[1]],
                ]
            )
            dst_pts = np.float32(
                [
                    [np.random.uniform(0, 10), np.random.uniform(0, 10)],
                    [
                        target_size[0] - np.random.uniform(0, 10),
                        np.random.uniform(0, 10),
                    ],
                    [
                        np.random.uniform(0, 10),
                        target_size[1] - np.random.uniform(0, 10),
                    ],
                    [
                        target_size[0] - np.random.uniform(0, 10),
                        target_size[1] - np.random.uniform(0, 10),
                    ],
                ]
            )
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            padded = cv2.warpPerspective(padded, matrix, target_size)

        # Convert to PIL Image
        return Image.fromarray(padded)

    def get_digit_samples(self, digit: int, num_samples: int = 1) -> List[Image.Image]:
        """Get sample images for a specific digit.

        Args:
            digit: The digit to get samples for (0-9).
            num_samples: Number of samples to return.

        Returns:
            List of PIL Images containing the digit.

        Raises:
            ValueError: If digit is not in range 0-9.
        """
        if not 0 <= digit <= 9:
            raise ValueError("Digit must be between 0 and 9")

        # Load test data if not already loaded
        images, labels = self.load_test_data()

        # Find indices for the requested digit
        digit_indices = np.where(labels == digit)[0]
        if len(digit_indices) == 0:
            raise ValueError(f"No samples found for digit {digit}")

        # Select random samples
        selected_indices = np.random.choice(
            digit_indices, size=min(num_samples, len(digit_indices)), replace=False
        )

        # Convert to PIL Images with preprocessing
        samples = []
        for idx in selected_indices:
            img = self._preprocess_mnist_image(images[idx])
            samples.append(img)

        return samples

    def get_digit_sample(self, digit: int) -> Image.Image:
        """Get a single sample image for a digit.

        Args:
            digit: The digit to get a sample for (0-9).

        Returns:
            PIL Image containing the digit.
        """
        return self.get_digit_samples(digit, num_samples=1)[0]
