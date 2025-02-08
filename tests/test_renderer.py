import os
import tempfile
from io import BytesIO

import numpy as np
import pytest
from PIL import Image
from reportlab.lib.pagesizes import letter

from src.renderer import WorksheetRenderer
from src.utils.layout_utils import LayoutChoice


@pytest.fixture
def sample_problems():
    """Fixture to create sample problems for testing."""
    return [
        {"question": "2 + 2", "answer": 4, "type": "addition", "difficulty": 1},
        {"question": "10 - 3", "answer": 7, "type": "subtraction", "difficulty": 1},
    ]


@pytest.fixture
def qr_code_stream():
    """Fixture to create a sample QR code stream."""
    return WorksheetRenderer.create_qr_code("test_123", "1.0")


def test_qr_code_generation():
    """Test QR code generation."""
    qr_stream = WorksheetRenderer.create_qr_code("test_123", "1.0")
    assert isinstance(qr_stream, BytesIO)

    # Verify the QR code can be opened as an image
    img = Image.open(qr_stream)
    assert img.size[0] > 0 and img.size[1] > 0


def test_layout_calculation():
    """Test layout calculation for problems."""
    problems = ["2 + 2", "3 - 1", "4 × 2"]
    positions, rois = WorksheetRenderer.calculate_layout(
        problems, LayoutChoice.TWO_COLUMN
    )

    assert len(positions) == len(problems)
    assert len(rois) == len(problems)

    # Check that positions are within page bounds
    page_width, page_height = letter
    for x_prob, y, x_ans in positions:
        assert 0 <= x_prob <= page_width
        assert 0 <= y <= page_height
        assert 0 <= x_ans <= page_width


def test_worksheet_creation(sample_problems, qr_code_stream):
    """Test worksheet PDF creation."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        template_id = WorksheetRenderer.create_math_worksheet(
            tmp_file.name, [p["question"] for p in sample_problems], qr_code_stream
        )

        # Verify the file exists and has content
        assert os.path.exists(tmp_file.name)
        assert os.path.getsize(tmp_file.name) > 0
        assert isinstance(template_id, str)

        # Clean up
        os.unlink(tmp_file.name)


def test_answer_key_creation(sample_problems, qr_code_stream):
    """Test answer key PDF creation."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        WorksheetRenderer.create_answer_key(
            tmp_file.name,
            [p["question"] for p in sample_problems],
            [p["answer"] for p in sample_problems],
            qr_code_stream,
        )

        # Verify the file exists and has content
        assert os.path.exists(tmp_file.name)
        assert os.path.getsize(tmp_file.name) > 0

        # Clean up
        os.unlink(tmp_file.name)


def test_text_rendering(sample_problems):
    """Test text rendering functionality."""
    from io import BytesIO

    from reportlab.pdfgen import canvas

    # Create a PDF in memory
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    # Calculate layout
    problems = [p["question"] for p in sample_problems]
    answers = [p["answer"] for p in sample_problems]
    positions, rois = WorksheetRenderer.calculate_layout(
        problems, LayoutChoice.TWO_COLUMN
    )

    # Test rendering without answers
    WorksheetRenderer.render_text(pdf, positions, rois, problems)

    # Test rendering with answers
    WorksheetRenderer.render_text(
        pdf, positions, rois, problems, answers, render_answers=True
    )

    pdf.save()

    # Verify PDF was created
    assert len(buffer.getvalue()) > 0
