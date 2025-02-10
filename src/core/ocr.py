"""Module for OCR functionality optimized for handwritten digits."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

logger = logging.getLogger(__name__)


class DigitRecognizer(nn.Module):
    """CNN model for digit recognition."""

    def __init__(self):
        super().__init__()
        # First convolutional block with residual connection
        self.conv1a = nn.Sequential(
            nn.Conv2d(1, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
        )
        self.conv1b = nn.Sequential(
            nn.Conv2d(64, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
        )
        self.pool1 = nn.MaxPool2d(2, 2)

        # Second convolutional block with residual connection
        self.conv2a = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )
        self.conv2b = nn.Sequential(
            nn.Conv2d(128, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )
        self.pool2 = nn.MaxPool2d(2, 2)

        # Third convolutional block with residual connection
        self.conv3a = nn.Sequential(
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
        )
        self.conv3b = nn.Sequential(
            nn.Conv2d(256, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
        )
        self.pool3 = nn.MaxPool2d(2, 2)

        # Fully connected layers
        self.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256 * 4 * 4, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 10),
        )

    def forward(self, x):
        # First block with residual
        identity = self.conv1a(x)
        x = self.conv1b(identity)
        x = x + identity
        x = self.pool1(x)

        # Second block with residual
        identity = self.conv2a(x)
        x = self.conv2b(identity)
        x = x + identity
        x = self.pool2(x)

        # Third block with residual
        identity = self.conv3a(x)
        x = self.conv3b(identity)
        x = x + identity
        x = self.pool3(x)

        x = x.view(-1, 256 * 4 * 4)
        x = self.fc(x)
        return x


@dataclass
class OCRConfig:
    """Configuration for OCR engine."""

    model_path: str = "data/models/digit_recognizer.pt"  # Path to save/load model
    min_confidence: float = 0.8  # Minimum confidence threshold (0-1)
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    image_size: int = 32  # Input size for the model
    threshold: int = 128  # Base threshold for binarization
    num_epochs: int = 30  # Increased number of epochs
    batch_size: int = 128  # Batch size for training
    learning_rate: float = 0.001  # Learning rate for training
    warmup_epochs: int = 3  # Number of epochs for learning rate warmup


class OCRResult:
    """Represents the result of OCR processing."""

    def __init__(
        self, text: Optional[str], confidence: float, error: Optional[str] = None
    ):
        self.text = text
        self.confidence = confidence
        self.error = error
        self.success = error is None and text is not None

    def __bool__(self) -> bool:
        return self.success


class OCREngine:
    """Handles OCR optimized for handwritten digits."""

    def __init__(self, config: Optional[OCRConfig] = None):
        """Initialize OCR engine with specified configuration."""
        self.config = config or OCRConfig()
        self._initialize_model()

    def _initialize_model(self):
        """Initialize digit recognition model."""
        try:
            self.model = DigitRecognizer()

            # Load pre-trained weights if they exist
            if os.path.exists(self.config.model_path):
                self.model.load_state_dict(torch.load(self.config.model_path))
                logger.info(f"Loaded model from {self.config.model_path}")
            else:
                # Train on MNIST if no pre-trained weights
                self._train_on_mnist()
                logger.info("Trained new model on MNIST")

            self.model.to(self.config.device)
            self.model.eval()

        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise

    def _train_on_mnist(self):
        """Train the model on MNIST dataset."""
        from torchvision import datasets, transforms

        # Enhanced data augmentation
        train_transform = transforms.Compose(
            [
                transforms.Resize((32, 32)),
                transforms.RandomRotation(15),  # Increased rotation
                transforms.RandomAffine(
                    degrees=0,
                    translate=(0.15, 0.15),  # Increased translation
                    scale=(0.8, 1.2),  # Increased scale variation
                    shear=(-15, 15),  # Added shear
                ),
                transforms.RandomPerspective(
                    distortion_scale=0.2, p=0.5
                ),  # Added perspective
                transforms.ToTensor(),
                transforms.RandomErasing(p=0.1),  # Added random erasing
            ]
        )

        test_transform = transforms.Compose(
            [
                transforms.Resize((32, 32)),
                transforms.ToTensor(),
            ]
        )

        train_dataset = datasets.MNIST(
            "data", train=True, download=True, transform=train_transform
        )
        test_dataset = datasets.MNIST(
            "data", train=False, download=True, transform=test_transform
        )

        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=self.config.batch_size, shuffle=True
        )
        test_loader = torch.utils.data.DataLoader(
            test_dataset, batch_size=self.config.batch_size, shuffle=False
        )

        # Train model
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=0.01,
            betas=(0.9, 0.999),
        )

        # Learning rate scheduler with warmup
        def get_lr_multiplier(epoch):
            if epoch < self.config.warmup_epochs:
                return (epoch + 1) / self.config.warmup_epochs
            return 1.0

        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=3, verbose=True
        )

        # Cross entropy with label smoothing
        criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

        best_accuracy = 0.0
        self.model.train()

        for epoch in range(self.config.num_epochs):
            # Set learning rate with warmup
            lr_multiplier = get_lr_multiplier(epoch)
            for param_group in optimizer.param_groups:
                param_group["lr"] = self.config.learning_rate * lr_multiplier

            # Training phase
            self.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0

            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(self.config.device), target.to(
                    self.config.device
                )
                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

                optimizer.step()

                train_loss += loss.item()
                _, predicted = output.max(1)
                train_total += target.size(0)
                train_correct += predicted.eq(target).sum().item()

                if batch_idx % 100 == 0:
                    accuracy = 100.0 * train_correct / train_total
                    avg_loss = train_loss / (batch_idx + 1)
                    logger.info(
                        f"Epoch {epoch}: [{batch_idx}/{len(train_loader)}] "
                        f"Loss: {avg_loss:.4f} Accuracy: {accuracy:.2f}%"
                    )

            # Evaluation phase
            self.model.eval()
            test_loss = 0
            test_correct = 0
            test_total = 0

            with torch.no_grad():
                for data, target in test_loader:
                    data, target = data.to(self.config.device), target.to(
                        self.config.device
                    )
                    output = self.model(data)
                    loss = criterion(output, target)
                    test_loss += loss.item()
                    _, predicted = output.max(1)
                    test_total += target.size(0)
                    test_correct += predicted.eq(target).sum().item()

            test_accuracy = 100.0 * test_correct / test_total
            avg_test_loss = test_loss / len(test_loader)
            logger.info(
                f"Epoch {epoch}: Test Loss: {avg_test_loss:.4f} "
                f"Test Accuracy: {test_accuracy:.2f}%"
            )

            # Save best model
            if test_accuracy > best_accuracy:
                best_accuracy = test_accuracy
                os.makedirs(os.path.dirname(self.config.model_path), exist_ok=True)
                torch.save(self.model.state_dict(), self.config.model_path)
                logger.info(f"Saved best model with accuracy: {test_accuracy:.2f}%")

            # Update learning rate
            scheduler.step(test_accuracy)

        self.model.eval()

    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for digit recognition.

        Args:
            image: Input image.

        Returns:
            Preprocessed image tensor.
        """
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Convert to numpy array
        img_array = np.array(image)

        # Normalize pixel values
        img_array = img_array.astype(np.float32) / 255.0

        # Apply contrast stretching
        p2, p98 = np.percentile(img_array, (2, 98))
        img_array = np.clip((img_array - p2) / (p98 - p2), 0, 1)

        # Convert back to uint8
        img_array = (img_array * 255).astype(np.uint8)

        # Apply Gaussian blur to reduce noise
        img_array = cv2.GaussianBlur(img_array, (3, 3), 0)

        # Apply Otsu's thresholding
        _, binary = cv2.threshold(
            img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Apply morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)  # Remove noise
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)  # Fill small holes

        # Resize to model input size
        binary = cv2.resize(binary, (self.config.image_size, self.config.image_size))

        # Convert to tensor and normalize
        tensor = torch.from_numpy(binary).float() / 255.0
        tensor = tensor.unsqueeze(0).unsqueeze(0)  # Add batch and channel dimensions

        return tensor

    def read_text(
        self,
        image: Union[str, Path, Image.Image],
        confidence_threshold: Optional[float] = None,
    ) -> OCRResult:
        """Extract text from an image using digit recognition.

        Args:
            image: Input image.
            confidence_threshold: Optional confidence threshold override.

        Returns:
            OCRResult containing the recognized digit and confidence.
        """
        try:
            # Load image
            if isinstance(image, (str, Path)):
                try:
                    image = Image.open(image)
                except Exception as e:
                    return OCRResult(None, 0.0, str(e))

            # Preprocess image
            tensor = self._preprocess_image(image)
            tensor = tensor.to(self.config.device)

            # Get model prediction
            with torch.no_grad():
                output = self.model(tensor)
                probabilities = F.softmax(output, dim=1)
                confidence, predicted = torch.max(probabilities, 1)
                confidence = confidence.item()
                digit = predicted.item()

            # Check confidence threshold
            threshold = (
                confidence_threshold
                if confidence_threshold is not None
                else self.config.min_confidence
            )
            if confidence < threshold:
                return OCRResult(None, confidence, "Confidence below threshold")

            return OCRResult(str(digit), confidence)

        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return OCRResult(None, 0.0, str(e))

    def read_multiple(
        self,
        images: List[Union[str, Path, Image.Image]],
        confidence_threshold: Optional[float] = None,
    ) -> List[OCRResult]:
        """Extract text from multiple images."""
        return [self.read_text(image, confidence_threshold) for image in images]
