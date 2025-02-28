"""Tests for worksheet functionality."""

from src.database.models import Worksheet


def test_create_worksheet(repository, test_child_dynamodb, cleanup_children):
    """Test creating a new worksheet."""
    worksheet = Worksheet(
        child_id=test_child_dynamodb.id,
        problems=[
            {"type": "addition", "a": 5, "b": 3, "answer": 8},
            {"type": "subtraction", "a": 10, "b": 4, "answer": 6},
        ],
    )
    repository.create_worksheet(worksheet)

    # Verify worksheet was created
    saved_worksheet = repository.get_worksheet(worksheet.id)
    assert saved_worksheet is not None
    assert len(saved_worksheet.problems) == 2
    assert saved_worksheet.problems[0]["type"] == "addition"
    assert saved_worksheet.problems[1]["type"] == "subtraction"


def test_get_child_worksheets(repository, test_child_dynamodb):
    """Test retrieving all worksheets for a child."""
    # Create two worksheets
    worksheet1 = Worksheet(
        child_id=test_child_dynamodb.id,
        problems=[{"type": "addition", "a": 1, "b": 1, "answer": 2}],
    )
    worksheet2 = Worksheet(
        child_id=test_child_dynamodb.id,
        problems=[{"type": "multiplication", "a": 2, "b": 3, "answer": 6}],
    )
    repository.create_worksheet(worksheet1)
    repository.create_worksheet(worksheet2)

    # Get worksheets for child
    worksheets = repository.get_child_worksheets(test_child_dynamodb.id)
    assert len(worksheets) == 2
    assert any(w.problems[0]["type"] == "addition" for w in worksheets)
    assert any(w.problems[0]["type"] == "multiplication" for w in worksheets)


def test_update_worksheet(repository, test_worksheet_dynamodb):
    """Test updating a worksheet."""
    # Add answers and mark as completed
    test_worksheet_dynamodb.answers = [8, 6]
    test_worksheet_dynamodb.completed = True
    repository.update_worksheet(test_worksheet_dynamodb)

    # Verify changes
    updated_worksheet = repository.get_worksheet(test_worksheet_dynamodb.id)
    assert updated_worksheet.answers == [8, 6]
    assert updated_worksheet.completed is True


def test_delete_worksheet(repository, test_worksheet_dynamodb, cleanup_children):
    """Test deleting a worksheet."""
    # Delete worksheet
    repository.delete_worksheet(test_worksheet_dynamodb.id)

    # Verify worksheet was deleted
    deleted_worksheet = repository.get_worksheet(test_worksheet_dynamodb.id)
    assert deleted_worksheet is None


def test_worksheet_without_answers(repository, test_child_dynamodb):
    """Test creating a worksheet without answers."""
    worksheet = Worksheet(
        child_id=test_child_dynamodb.id,
        problems=[
            {"type": "addition", "a": 5, "b": 3},
            {"type": "subtraction", "a": 10, "b": 4},
        ],
    )
    repository.create_worksheet(worksheet)

    # Verify worksheet was created without answers
    saved_worksheet = repository.get_worksheet(worksheet.id)
    assert saved_worksheet is not None
    assert saved_worksheet.answers is None
    assert saved_worksheet.completed is False


def test_get_nonexistent_worksheet(repository):
    """Test retrieving a worksheet that doesn't exist."""
    nonexistent_worksheet = repository.get_worksheet("nonexistent-id")
    assert nonexistent_worksheet is None
