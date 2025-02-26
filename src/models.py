"""Database models for the MathTutor application."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import List, Optional


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

    @classmethod
    def create(cls, child_id: str, problems: str) -> "Worksheet":
        """Create a new worksheet."""
        now = utc_now()
        return cls(
            id=generate_id(),
            child_id=child_id,
            problems=problems,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        """Convert to DynamoDB item."""
        return {
            "id": self.id,
            "child_id": self.child_id,
            "problems": self.problems,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Worksheet":
        """Create from DynamoDB item."""
        return cls(
            id=data["id"],
            child_id=data["child_id"],
            problems=data["problems"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
