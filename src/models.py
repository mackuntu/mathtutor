"""Database models for the MathTutor application."""

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


@dataclass
class User:
    """User model."""

    id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, email: str, name: str) -> "User":
        """Create a new user."""
        now = utc_now()
        return cls(
            id=generate_id(), email=email, name=name, created_at=now, updated_at=now
        )

    def to_dict(self) -> dict:
        """Convert to DynamoDB item."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create from DynamoDB item."""
        return cls(
            id=data["id"],
            email=data["email"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class Child:
    """Child model."""

    id: str
    parent_id: str
    name: str
    birthday: datetime
    grade: int
    preferred_color: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        parent_id: str,
        name: str,
        birthday: datetime,
        grade: int,
        preferred_color: str,
    ) -> "Child":
        """Create a new child."""
        now = utc_now()
        return cls(
            id=generate_id(),
            parent_id=parent_id,
            name=name,
            birthday=birthday,
            grade=grade,
            preferred_color=preferred_color,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        """Convert to DynamoDB item."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "name": self.name,
            "birthday": self.birthday.isoformat(),
            "grade": self.grade,
            "preferred_color": self.preferred_color,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Child":
        """Create from DynamoDB item."""
        return cls(
            id=data["id"],
            parent_id=data["parent_id"],
            name=data["name"],
            birthday=datetime.fromisoformat(data["birthday"]),
            grade=data["grade"],
            preferred_color=data["preferred_color"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class Worksheet:
    """Worksheet model."""

    id: str
    child_id: str
    problems: str
    created_at: datetime
    updated_at: datetime
    serial_number: Optional[str] = None
    incorrect_problems: Optional[List[int]] = None
    answers: Optional[List[str]] = None

    @property
    def problem_count(self) -> int:
        """Get the number of problems in the worksheet."""
        try:
            return len(json.loads(self.problems))
        except (json.JSONDecodeError, TypeError):
            return 0

    @classmethod
    def create(
        cls, child_id: str, problems: str, answers: Optional[List[str]] = None
    ) -> "Worksheet":
        """Create a new worksheet."""
        now = utc_now()
        # Generate a unique human-readable serial number based on timestamp and random suffix
        serial_number = f"{now.strftime('%Y%m%d-%H%M%S')}-{generate_id()[:4]}"
        return cls(
            id=generate_id(),
            child_id=child_id,
            problems=problems,
            created_at=now,
            updated_at=now,
            serial_number=serial_number,
            incorrect_problems=None,
            answers=answers,
        )

    def to_dict(self) -> dict:
        """Convert to DynamoDB item."""
        data = {
            "id": self.id,
            "child_id": self.child_id,
            "problems": self.problems,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.serial_number:
            data["serial_number"] = self.serial_number
        if self.incorrect_problems:
            data["incorrect_problems"] = json.dumps(self.incorrect_problems)
        if self.answers:
            data["answers"] = json.dumps(self.answers)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Worksheet":
        """Create a Worksheet instance from a dictionary."""
        incorrect_problems = None
        if data.get("incorrect_problems"):
            try:
                incorrect_problems = json.loads(data["incorrect_problems"])
            except (json.JSONDecodeError, TypeError):
                incorrect_problems = []

        answers = None
        if data.get("answers"):
            try:
                answers = json.loads(data["answers"])
            except (json.JSONDecodeError, TypeError):
                answers = []

        # Parse datetime strings if they are strings
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not created_at:
            created_at = utc_now()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif not updated_at:
            updated_at = utc_now()

        return cls(
            id=data.get("id"),
            child_id=data["child_id"],
            problems=data["problems"],
            created_at=created_at,
            updated_at=updated_at,
            serial_number=data.get("serial_number"),
            incorrect_problems=incorrect_problems,
            answers=answers,
        )
