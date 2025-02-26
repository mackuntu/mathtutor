from datetime import datetime
from typing import Dict, List, Optional

from src.database.models import Child
from src.database.repository import DynamoDBRepository, get_repository


class ChildManager:
    def __init__(self, repository: Optional[DynamoDBRepository] = None):
        """Initialize ChildManager with an optional repository."""
        self.repository = repository or get_repository()

    def register_child(self, parent_email: str, child_data: Dict) -> Child:
        """Register a new child."""
        self.validate_child_data(child_data)
        child = Child(
            parent_email=parent_email,
            name=child_data["name"],
            age=child_data["age"],
            grade=child_data["grade"],
            preferred_color=child_data["preferred_color"],
        )
        child.validate()
        self.repository.create_child(child)
        return child

    def get_child(self, child_id: str) -> Optional[Child]:
        """Get a child by ID."""
        return self.repository.get_child_by_id(child_id)

    def get_children(self, parent_email: str) -> List[Child]:
        """Get all children for a parent."""
        return self.repository.get_children_by_parent(parent_email)

    def validate_child_data(self, child_data: Dict) -> bool:
        """Validate child registration data."""
        required_fields = ["name", "age", "grade", "preferred_color"]
        for field in required_fields:
            if field not in child_data:
                raise ValueError(f"Missing required field: {field}")
            if not child_data[field]:
                raise ValueError(f"Field cannot be empty: {field}")

        if not isinstance(child_data["age"], int):
            raise ValueError("Age must be an integer")
        if not isinstance(child_data["grade"], int):
            raise ValueError("Grade must be an integer")
        if not isinstance(child_data["name"], str):
            raise ValueError("Name must be a string")
        if not isinstance(child_data["preferred_color"], str):
            raise ValueError("Preferred color must be a string")

        # Create a temporary child to validate grade/age combination
        temp_child = Child(
            parent_email="temp@example.com",
            name=child_data["name"],
            age=child_data["age"],
            grade=child_data["grade"],
            preferred_color=child_data["preferred_color"],
        )
        temp_child.validate()
        return True

    def update_child(self, child: Child) -> Child:
        self._validate_grade_age(child.grade, child.age)
        return self.repository.update_child(child)

    def delete_child(self, child_id: str) -> None:
        self.repository.delete_child(child_id)

    def _validate_grade_age(self, grade: int, age: int) -> None:
        if grade < 1 or grade > 12:
            raise ValueError("Grade must be between 1 and 12")
        if age < 5 or age > 18:
            raise ValueError("Age must be between 5 and 18")
        expected_age_range = range(grade + 4, grade + 7)
        if age not in expected_age_range:
            msg = "Invalid grade/age combination. "
            msg += f"For grade {grade}, age should be between "
            msg += f"{min(expected_age_range)} and {max(expected_age_range)}"
            raise ValueError(msg)
