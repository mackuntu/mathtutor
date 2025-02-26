"""Tests for document rendering functionality."""

import os
import tempfile
from io import BytesIO

import pytest
from reportlab.lib.pagesizes import letter

from src.document.renderer import DocumentRenderer
from src.document.template import LayoutChoice, TemplateManager


@pytest.fixture
def renderer():
    """Create a DocumentRenderer instance for testing."""
    return DocumentRenderer()


@pytest.fixture
def sample_problems():
    """Create sample problems for testing."""
    return [
        "2 + 2",
        "3 - 1",
        "4 × 2",
        "Which number is greater: 12 or 15?",
        "Solve the equation: x + 5 = 10",
        "If you have 3 apples and get 2 more, how many do you have?",
    ]


def test_layout_calculation(renderer, sample_problems):
    """Test layout calculation for different problem types."""
    # Test two-column layout (short problems)
    positions, rois = renderer.template_manager.calculate_layout(
        len(sample_problems[:3]), sample_problems[:3], LayoutChoice.TWO_COLUMN
    )

    assert len(positions) == 3
    assert len(rois) == 3

    # Check positions are within page bounds
    page_width, page_height = letter
    for x_prob, y, x_ans in positions:
        assert 0 <= x_prob <= page_width
        assert 0 <= y <= page_height
        assert 0 <= x_ans <= page_width

    # Test one-column layout (long problems)
    positions, rois = renderer.template_manager.calculate_layout(
        len(sample_problems[3:]), sample_problems[3:], LayoutChoice.ONE_COLUMN
    )

    assert len(positions) == 3
    assert len(rois) == 3

    # Verify one-column layout has wider spacing
    x_positions = [x_ans for _, _, x_ans in positions]
    assert all(x >= 400 for x in x_positions)


def test_worksheet_creation(renderer, sample_problems):
    """Test worksheet PDF creation with different layouts."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        # Create worksheet with two-column layout
        renderer.create_worksheet(
            tmp_file.name,
            sample_problems[:3],
            "test_123",
            LayoutChoice.TWO_COLUMN,
        )

        # Verify file exists and has content
        assert os.path.exists(tmp_file.name)
        assert os.path.getsize(tmp_file.name) > 0

        # Clean up
        os.unlink(tmp_file.name)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        # Create worksheet with one-column layout
        renderer.create_worksheet(
            tmp_file.name,
            sample_problems[3:],
            "test_123",
            LayoutChoice.ONE_COLUMN,
        )

        # Verify file exists and has content
        assert os.path.exists(tmp_file.name)
        assert os.path.getsize(tmp_file.name) > 0

        # Clean up
        os.unlink(tmp_file.name)


def test_automatic_layout_selection(renderer, sample_problems):
    """Test automatic layout selection based on problem lengths."""
    # Short problems should use two-column layout
    layout = renderer.template_manager.choose_layout(sample_problems[:3])
    assert layout == LayoutChoice.TWO_COLUMN

    # Long problems should use one-column layout
    layout = renderer.template_manager.choose_layout(sample_problems[3:])
    assert layout == LayoutChoice.ONE_COLUMN

    # Mixed problems should use one-column layout to accommodate the longer problems
    mixed_problems = [
        "2 + 2",  # short
        "Which number is greater: 12 or 15?",  # medium
        "4 × 2",  # short
        "If you have 3 apples and get 2 more, how many do you have?",  # long
    ]
    layout = renderer.template_manager.choose_layout(mixed_problems)
    assert (
        layout == LayoutChoice.ONE_COLUMN
    )  # Use one column when there are any long problems
