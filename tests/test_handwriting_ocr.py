"""Tests for handwriting simulation and OCR functionality."""

import os
import re
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from src.core.handwriting import HandwritingSimulator
from src.core.ocr import OCRConfig, OCREngine, OCRResult
from src.utils.mnist_loader import MNISTLoader


@pytest.fixture
def handwriting():
    """Fixture to create HandwritingSimulator instance."""
    return HandwritingSimulator()


@pytest.fixture
def ocr():
    """Fixture to create OCREngine instance with optimized config."""
    config = OCRConfig(
        model_path="data/models/digit_recognizer.pt",
        min_confidence=0.3,  # Lower threshold for testing since we're using softmax probabilities
        image_size=32,  # Standard size for digit recognition
    )
    return OCREngine(config)


@pytest.fixture
def mnist_loader():
    """Fixture to create MNISTLoader instance."""
    return MNISTLoader()


def normalize_text(text: str) -> str:
    """Normalize text by removing punctuation and extra whitespace."""
    if text is None:
        return ""
    # Remove punctuation and whitespace
    text = re.sub(r"[^\w\s]", "", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text.strip()


def test_write_and_read_single_answer(handwriting, ocr):
    """Test writing a single answer and reading it back with OCR."""
    # Write a simple answer
    answer = "42"
    roi = (0, 0, 100, 50)  # Simple ROI for testing
    answer_image = handwriting.write_answer(answer, roi)

    # Read it back with OCR
    result = ocr.read_text(answer_image)
    assert isinstance(result, OCRResult)
    assert normalize_text(result.text) == answer
    assert result.confidence > -20  # Basic confidence check


def test_write_and_read_multiple_answers(handwriting, ocr):
    """Test writing multiple answers and reading them back with OCR."""
    # Test data
    answers = ["1", "2", "3", "4"]
    rois = [
        (0, 0, 100, 50),
        (0, 50, 100, 100),
        (0, 100, 100, 150),
        (0, 150, 100, 200),
    ]

    # Generate answer images
    answer_images = handwriting.write_multiple_answers(answers, rois)

    # Read them back
    results = ocr.read_multiple(answer_images)

    # Check results
    for result, expected_answer in zip(results, answers):
        assert isinstance(result, OCRResult)
        assert normalize_text(result.text) == expected_answer
        assert result.confidence > -20


def test_handwriting_variations(handwriting, ocr):
    """Test that handwriting variations still produce readable results."""
    answer = "7"
    roi = (0, 0, 100, 50)

    # Generate multiple versions of the same answer
    results = []
    for _ in range(5):
        answer_image = handwriting.write_answer(answer, roi)
        result = ocr.read_text(answer_image)
        assert isinstance(result, OCRResult)
        results.append(result)

    # Check that all variations are readable
    for result in results:
        assert normalize_text(result.text) == answer
        assert result.confidence > -20


def test_incorrect_answer_simulation(handwriting, ocr):
    """Test that simulated incorrect answers are detected."""
    answer = "10"
    roi = (0, 0, 100, 50)

    # Generate an intentionally incorrect answer
    answer_image = handwriting.write_answer(answer, roi, is_correct=False)
    result = ocr.read_text(answer_image)

    # The OCR result should be different from the original answer
    assert isinstance(result, OCRResult)
    assert result.text.strip() != answer


def test_handwriting_size_adaptation(handwriting, ocr):
    """Test that handwriting adapts to different ROI sizes."""
    answer = "123"

    # Test different ROI sizes
    roi_sizes = [
        (0, 0, 50, 25),  # Small
        (0, 0, 100, 50),  # Medium
        (0, 0, 200, 100),  # Large
    ]

    for roi in roi_sizes:
        answer_image = handwriting.write_answer(answer, roi)

        # Verify image dimensions match ROI with some tolerance
        width = roi[2] - roi[0]
        height = roi[3] - roi[1]
        assert abs(answer_image.size[0] - width) <= width * 0.1  # 10% tolerance
        assert abs(answer_image.size[1] - height) <= height * 0.1


def test_font_loading_and_fallback(handwriting, ocr):
    """Test font loading behavior and fallback."""
    # Test with invalid font path
    simulator = HandwritingSimulator(font_paths=["nonexistent.ttf"])

    # Should raise error when no fonts are available
    with pytest.raises(ValueError, match="No fonts available"):
        simulator.write_answer("test", (0, 0, 100, 50))


def test_perfect_score_single_digits(mnist_loader, ocr):
    """Test recognition of all single digits with perfect writing."""
    # Test each digit from 0-9
    debug_dir = Path("debug_images")
    debug_dir.mkdir(exist_ok=True)

    for digit in range(10):
        # Get MNIST sample for the digit
        digit_str = str(digit)
        digit_image = mnist_loader.get_digit_sample(digit)

        # Save debug image
        digit_image.save(debug_dir / f"digit_{digit}.png")

        # Test OCR
        result = ocr.read_text(digit_image)

        # Print debug info
        print(f"\nTesting digit {digit}:")
        print(f"OCR Result: {result.text}")
        print(f"Confidence: {result.confidence}")
        if result.error:
            print(f"Error: {result.error}")

        # Assertions
        assert result.success, f"Failed to recognize digit {digit}"
        assert result.text == digit_str, f"Expected {digit_str}, got {result.text}"
        assert (
            result.confidence > -10.0
        ), f"Low confidence for digit {digit}: {result.confidence}"
        assert result.error is None, f"Error recognizing digit {digit}: {result.error}"


def test_perfect_score_different_sizes(handwriting, ocr):
    """Test recognition with different ROI sizes."""
    digit = "7"  # Use a digit with distinctive features
    roi_sizes = [
        (0, 0, 50, 50),  # Small
        (0, 0, 100, 100),  # Medium
        (0, 0, 200, 200),  # Large
    ]

    for roi in roi_sizes:
        answer_image = handwriting.write_answer(digit, roi)
        result = ocr.read_text(answer_image)

        assert result.success, f"Failed with ROI size {roi}"
        assert result.text == digit, f"Wrong recognition for ROI size {roi}"
        assert result.confidence > -5.0, f"Low confidence for ROI size {roi}"


def test_perfect_score_multiple_digits(handwriting, ocr):
    """Test recognition of multiple digits in sequence."""
    digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    rois = [(0, i * 60, 100, (i + 1) * 60) for i in range(len(digits))]

    # Generate all digit images
    answer_images = handwriting.write_multiple_answers(digits, rois)

    # Test batch recognition
    results = ocr.read_multiple(answer_images)

    # Verify each result
    for digit, result in zip(digits, results):
        assert result.success, f"Failed to recognize digit {digit}"
        assert result.text == digit, f"Expected {digit}, got {result.text}"
        assert result.confidence > -5.0, f"Low confidence for digit {digit}"


def test_perfect_score_all_fonts(handwriting, ocr):
    """Test recognition with all available fonts."""
    digit = "4"  # Use a digit with complex features
    roi = (0, 0, 100, 100)

    for font_path in HandwritingSimulator.DEFAULT_FONTS:
        # Create simulator with specific font
        simulator = HandwritingSimulator(font_paths=[font_path])

        # Generate digit image
        answer_image = simulator.write_answer(digit, roi)

        # Test recognition
        result = ocr.read_text(answer_image)

        font_name = Path(font_path).stem
        assert result.success, f"Failed with font {font_name}"
        assert result.text == digit, f"Wrong recognition with font {font_name}"
        assert result.confidence > -5.0, f"Low confidence with font {font_name}"


def test_perfect_score_image_formats(handwriting, ocr):
    """Test recognition with different image formats and modes."""
    digit = "5"
    roi = (0, 0, 100, 100)

    # Generate base image
    answer_image = handwriting.write_answer(digit, roi)

    # Test different image modes
    modes = ["L", "RGB", "RGBA"]
    for mode in modes:
        converted_image = answer_image.convert(mode)
        result = ocr.read_text(converted_image)

        assert result.success, f"Failed with image mode {mode}"
        assert result.text == digit, f"Wrong recognition with image mode {mode}"

    # Test saving and loading in different formats
    formats = ["PNG", "JPEG", "BMP"]
    for fmt in formats:
        # Save and load image
        with tempfile.NamedTemporaryFile(suffix=f".{fmt.lower()}", delete=False) as tmp:
            answer_image.save(tmp.name, format=fmt)
            loaded_image = Image.open(tmp.name)
            result = ocr.read_text(loaded_image)

            assert result.success, f"Failed with format {fmt}"
            assert result.text == digit, f"Wrong recognition with format {fmt}"

            # Cleanup
            os.unlink(tmp.name)


def test_perfect_score_confidence_levels(handwriting, ocr):
    """Test different confidence thresholds."""
    digit = "6"
    roi = (0, 0, 100, 100)
    answer_image = handwriting.write_answer(digit, roi)

    # Test with different confidence thresholds
    thresholds = [-10.0, -5.0, -2.0, 0.0]
    for threshold in thresholds:
        result = ocr.read_text(answer_image, confidence_threshold=threshold)

        if threshold <= -5.0:  # Should succeed for reasonable thresholds
            assert result.success, f"Failed with threshold {threshold}"
            assert result.text == digit
        else:  # Should fail for very strict thresholds
            assert not result.success
            assert result.error == "Confidence below threshold"


def test_perfect_score_error_cases(handwriting, ocr):
    """Test error handling in perfect score scenarios."""
    digit = "8"
    roi = (0, 0, 100, 100)

    # Test with invalid image path
    result = ocr.read_text("nonexistent.png")
    assert not result.success
    assert result.error is not None

    # Test with empty image
    empty_image = Image.new("RGB", (100, 100), color="white")
    result = ocr.read_text(empty_image)
    assert not result.success

    # Test with very small image
    tiny_image = handwriting.write_answer(digit, (0, 0, 10, 10))
    result = ocr.read_text(tiny_image)
    assert (
        not result.success or result.confidence < -5.0
    )  # Should fail or have low confidence
