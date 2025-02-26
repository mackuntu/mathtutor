"""Tests for child registration functionality."""

import re
from datetime import date, datetime, timedelta, timezone

import pytest

from src.child_registration import ChildManager
from src.database.models import Child
from src.exceptions import ValidationError


@pytest.fixture(scope="function")
def child_manager(repository):
    """Create a child manager instance."""
    return ChildManager(repository)


def test_create_child(repository, test_user):
    """Test creating a new child."""
    child = Child(
        parent_email=test_user.email,
        name="Test Child",
        age=7,
        grade=2,
        preferred_color="#FF5733",
    )
    repository.create_child(child)

    # Verify child was created
    saved_child = repository.get_child_by_id(child.id)
    assert saved_child is not None
    assert saved_child.name == "Test Child"
    assert saved_child.age == 7
    assert saved_child.grade == 2
    assert saved_child.preferred_color == "#FF5733"


def test_get_children_by_parent(repository, test_user):
    """Test retrieving all children for a parent."""
    # Create two children
    child1 = Child(
        parent_email=test_user.email,
        name="Child One",
        age=7,
        grade=2,
        preferred_color="#FF5733",
    )
    child2 = Child(
        parent_email=test_user.email,
        name="Child Two",
        age=9,
        grade=4,
        preferred_color="#33FF57",
    )
    repository.create_child(child1)
    repository.create_child(child2)

    # Get children for parent
    children = repository.get_children_by_parent(test_user.email)
    assert len(children) == 2
    assert any(c.name == "Child One" for c in children)
    assert any(c.name == "Child Two" for c in children)


def test_update_child(repository, test_child_dynamodb):
    """Test updating a child."""
    # Update child information
    test_child_dynamodb.name = "Updated Name"
    test_child_dynamodb.grade = 4
    repository.update_child(test_child_dynamodb)

    # Verify changes
    updated_child = repository.get_child_by_id(test_child_dynamodb.id)
    assert updated_child.name == "Updated Name"
    assert updated_child.grade == 4


def test_delete_child(repository, test_child_dynamodb):
    """Test deleting a child."""
    # Delete child
    repository.delete_child(test_child_dynamodb.id)

    # Verify child was deleted
    deleted_child = repository.get_child_by_id(test_child_dynamodb.id)
    assert deleted_child is None


def test_invalid_grade_age_combination(repository, test_user):
    """Test validation of grade and age combination."""
    # Try to create a child with invalid grade/age combination
    child = Child(
        parent_email=test_user.email,
        name="Invalid Child",
        age=5,
        grade=8,  # Too high for age
        preferred_color="#FF5733",
    )
    with pytest.raises(ValueError, match="Invalid grade/age combination"):
        child.validate()
        repository.create_child(child)


def test_get_nonexistent_child(repository):
    """Test retrieving a child that doesn't exist."""
    nonexistent_child = repository.get_child_by_id("nonexistent-id")
    assert nonexistent_child is None


def test_register_child(child_manager, test_user):
    """Test registering a new child."""
    child_data = {
        "name": "New Child",
        "age": 8,
        "grade": 3,
        "preferred_color": "#FF5733",
    }
    child = child_manager.register_child(test_user.email, child_data)
    assert child is not None
    assert child.name == "New Child"
    assert child.grade == 3


def test_get_child(child_manager, test_user, test_child_dynamodb):
    """Test getting a child by ID."""
    child = child_manager.get_child(test_child_dynamodb.id)
    assert child is not None
    assert child.name == test_child_dynamodb.name
    assert child.grade == test_child_dynamodb.grade


def test_get_children(child_manager, test_user, test_child_dynamodb):
    """Test getting all children for a parent."""
    # Create another child
    child2 = Child(
        parent_email=test_user.email,
        name="Child Two",
        age=9,
        grade=4,
        preferred_color="#33FF57",
    )
    child_manager.repository.create_child(child2)

    # Get all children
    children = child_manager.get_children(test_user.email)
    assert len(children) == 2
    assert any(c.name == test_child_dynamodb.name for c in children)
    assert any(c.name == "Child Two" for c in children)


def test_validate_child_data(child_manager):
    """Test validation of child registration data."""
    # Test valid data
    valid_data = {
        "name": "Test Child",
        "age": 8,
        "grade": 3,
        "preferred_color": "#FF5733",
    }
    assert child_manager.validate_child_data(valid_data) is True

    # Test invalid data
    invalid_data = {
        "name": "",  # Empty name
        "age": 4,  # Too young
        "grade": 12,  # Too high for age
        "preferred_color": "invalid-color",
    }
    with pytest.raises(ValueError):
        child_manager.validate_child_data(invalid_data)
