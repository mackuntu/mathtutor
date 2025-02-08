import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from src.db_handler import DatabaseHandler


@pytest.fixture(autouse=True)
def setup_test_db():
    """Fixture to set up and tear down a test database."""
    # Create a temporary directory for the test database
    test_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(test_dir, "worksheets.db")

    # Patch the database path
    with patch("src.db_handler.DatabaseHandler.initialize_database") as mock_init:
        mock_init.return_value = None
        yield

    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    os.rmdir(test_dir)


def test_database_initialization():
    """Test database initialization and table creation."""
    DatabaseHandler.initialize_database()

    # Connect to the database and check if tables exist
    conn = sqlite3.connect("data/worksheets.db")
    cursor = conn.cursor()

    # Check worksheets table
    cursor.execute(
        """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='worksheets'
    """
    )
    assert cursor.fetchone() is not None

    # Check roi_templates table
    cursor.execute(
        """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='roi_templates'
    """
    )
    assert cursor.fetchone() is not None

    conn.close()


def test_worksheet_operations():
    """Test saving and retrieving worksheets."""
    worksheet_id = "test_123"
    version = "1.0"
    problems = ["2 + 2", "3 - 1"]
    answers = ["4", "2"]
    template_id = "template_123"

    # Save worksheet
    DatabaseHandler.save_worksheet(
        worksheet_id, version, problems, answers, template_id
    )

    # Retrieve worksheet
    worksheet = DatabaseHandler.fetch_worksheet(worksheet_id, version)

    assert worksheet.worksheet_id == worksheet_id
    assert worksheet.version == version
    assert list(worksheet.problems) == problems
    assert list(worksheet.answers) == answers
    assert worksheet.template_id == template_id


def test_roi_template_operations():
    """Test saving and retrieving ROI templates."""
    roi_hash = "template_123"
    rois = [(100, 100, 200, 200), (300, 300, 400, 400)]

    # Save template
    DatabaseHandler.save_roi_template(roi_hash, rois)

    # Retrieve template
    retrieved_rois = DatabaseHandler.fetch_roi_template(roi_hash)

    assert len(retrieved_rois) == len(rois)
    for original, retrieved in zip(rois, retrieved_rois):
        assert original == retrieved


def test_error_handling():
    """Test error handling for non-existent data."""
    with pytest.raises(ValueError):
        DatabaseHandler.fetch_worksheet("nonexistent", "1.0")

    with pytest.raises(ValueError):
        DatabaseHandler.fetch_roi_template("nonexistent")
