"""DynamoDB models for the MathTutor application."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class DynamoDBModel:
    """Base class for DynamoDB models."""

    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique ID for a new record."""
        return str(uuid.uuid4())

    @staticmethod
    def utc_now() -> int:
        """Get current UTC timestamp in seconds."""
        return int(datetime.now(timezone.utc).timestamp())

    @staticmethod
    def to_dynamodb_item(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Convert a Python dictionary to DynamoDB item format."""
        item = {}
        for key, value in data.items():
            if value is None:
                continue

            if isinstance(value, str):
                item[key] = {"S": value}
            elif isinstance(value, bool):
                item[key] = {"BOOL": value}
            elif isinstance(value, (int, float)):
                item[key] = {"N": str(value)}
            elif isinstance(value, list):
                if all(isinstance(x, str) for x in value):
                    item[key] = {"SS": value}
                else:
                    item[key] = {"L": [{"S": str(x)} for x in value]}
            elif isinstance(value, dict):
                item[key] = {"M": DynamoDBModel.to_dynamodb_item(value)}
        return item

    @staticmethod
    def from_dynamodb_item(
        item: Optional[Dict[str, Dict[str, Any]]]
    ) -> Optional[Dict[str, Any]]:
        """Convert a DynamoDB item to a Python dictionary."""
        if not item:
            return None

        data = {}
        for key, value in item.items():
            type_key = list(value.keys())[0]
            if type_key == "S":
                data[key] = value["S"]
            elif type_key == "N":
                data[key] = float(value["N"])
            elif type_key == "BOOL":
                data[key] = value["BOOL"]
            elif type_key == "SS":
                data[key] = value["SS"]
            elif type_key == "L":
                data[key] = [x["S"] for x in value["L"]]
            elif type_key == "M":
                data[key] = DynamoDBModel.from_dynamodb_item(value["M"])
        return data


class User(DynamoDBModel):
    """User model for DynamoDB."""

    def __init__(self, email: str, name: str, picture: Optional[str] = None):
        self.email = email
        self.name = name
        self.picture = picture
        self.created_at = self.utc_now()
        self.updated_at = self.created_at

    def to_item(self) -> Dict[str, Dict[str, Any]]:
        """Convert user to DynamoDB item format."""
        data = {
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.picture:
            data["picture"] = self.picture
        return self.to_dynamodb_item(data)

    @classmethod
    def from_item(cls, item: Optional[Dict[str, Dict[str, Any]]]) -> Optional["User"]:
        """Create User instance from DynamoDB item."""
        if not item:
            return None
        data = cls.from_dynamodb_item(item)
        if not data:
            return None
        user = cls(email=data["email"], name=data["name"], picture=data.get("picture"))
        user.created_at = int(data["created_at"])
        user.updated_at = int(data["updated_at"])
        return user


class Child(DynamoDBModel):
    """Child model for DynamoDB."""

    def __init__(
        self,
        parent_email: str,
        name: str,
        age: int,
        grade: int,
        preferred_color: Optional[str] = None,
    ):
        self.id = self.generate_id()
        self.parent_email = parent_email
        self.name = name
        self.age = age
        self.grade = grade
        self.preferred_color = preferred_color
        self.created_at = self.utc_now()
        self.updated_at = self.created_at
        self._birthday = None  # Store the actual birthday when set

    @property
    def birthday(self):
        """Get the birthday based on stored value or calculate from age."""
        if self._birthday:
            return self._birthday

        # Calculate an approximate birthday based on the age
        # This is a workaround for the template that expects a birthday
        today = datetime.now(timezone.utc)
        # Use January 1st instead of today's date to avoid always showing today's date
        return datetime(today.year - self.age, 1, 1, tzinfo=timezone.utc)

    @birthday.setter
    def birthday(self, value):
        """Set age based on birthday and store the actual birthday."""
        if not isinstance(value, datetime):
            raise ValueError("Birthday must be a datetime object")

        # Store the actual birthday
        self._birthday = value

        # Calculate age from birthday
        today = datetime.now(timezone.utc)
        self.age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )

    def validate(self) -> None:
        """Validate child data."""
        if self.grade < 1 or self.grade > 12:
            raise ValueError("Grade must be between 1 and 12")
        if self.age < 5 or self.age > 18:
            raise ValueError("Age must be between 5 and 18")
        expected_age_range = range(self.grade + 4, self.grade + 7)
        if self.age not in expected_age_range:
            msg = "Invalid grade/age combination. "
            msg += f"For grade {self.grade}, age should be between "
            msg += f"{min(expected_age_range)} and {max(expected_age_range)}"
            raise ValueError(msg)

    def to_item(self) -> Dict[str, Dict[str, Any]]:
        """Convert child to DynamoDB item format."""
        data = {
            "id": self.id,
            "parent_email": self.parent_email,
            "name": self.name,
            "age": self.age,
            "grade": self.grade,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.preferred_color:
            data["preferred_color"] = self.preferred_color
        if self._birthday:
            data["birthday"] = self._birthday.isoformat()
        return self.to_dynamodb_item(data)

    @classmethod
    def from_item(cls, item: Optional[Dict[str, Dict[str, Any]]]) -> Optional["Child"]:
        """Create Child instance from DynamoDB item."""
        if not item:
            return None
        data = cls.from_dynamodb_item(item)
        if not data:
            return None
        child = cls(
            parent_email=data["parent_email"],
            name=data["name"],
            age=int(data["age"]),
            grade=int(data["grade"]),
            preferred_color=data.get("preferred_color"),
        )
        child.id = data["id"]
        child.created_at = int(data["created_at"])
        child.updated_at = int(data["updated_at"])
        if "birthday" in data:
            child._birthday = datetime.fromisoformat(data["birthday"])
        return child


class Session(DynamoDBModel):
    """Session model for DynamoDB."""

    def __init__(self, token: str, user_email: str, expires_at: int):
        self.token = token
        self.user_email = user_email
        self.expires_at = expires_at
        self.created_at = self.utc_now()

    def to_item(self) -> Dict[str, Dict[str, Any]]:
        """Convert session to DynamoDB item format."""
        data = {
            "token": self.token,
            "user_email": self.user_email,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
        }
        return self.to_dynamodb_item(data)

    @classmethod
    def from_item(
        cls, item: Optional[Dict[str, Dict[str, Any]]]
    ) -> Optional["Session"]:
        """Create Session instance from DynamoDB item."""
        if not item:
            return None
        data = cls.from_dynamodb_item(item)
        if not data:
            return None
        session = cls(
            token=data["token"],
            user_email=data["user_email"],
            expires_at=int(data["expires_at"]),
        )
        session.created_at = int(data["created_at"])
        return session


class Worksheet(DynamoDBModel):
    """Worksheet model."""

    def __init__(
        self,
        child_id: str,
        problems: List[Dict[str, Any]],
        answers: Optional[List[float]] = None,
        completed: bool = False,
        incorrect_problems: Optional[List[int]] = None,
    ):
        """Initialize a worksheet."""
        self.id = self.generate_id()
        self.child_id = child_id
        self.problems = problems
        self.answers = answers
        self.completed = completed
        self.incorrect_problems = incorrect_problems
        self.created_at = self.utc_now()
        self.updated_at = self.created_at

    def to_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item."""
        item = {
            "id": self.id,
            "child_id": self.child_id,
            "problems": json.dumps(self.problems),
            "completed": self.completed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.answers is not None:
            item["answers"] = json.dumps(self.answers)
        if self.incorrect_problems is not None:
            item["incorrect_problems"] = json.dumps(self.incorrect_problems)
        return item

    @classmethod
    def from_item(cls, item: Optional[Dict[str, Any]]) -> Optional["Worksheet"]:
        """Create from DynamoDB item."""
        if not item:
            return None

        problems = json.loads(item["problems"])
        answers = json.loads(item["answers"]) if "answers" in item else None
        incorrect_problems = (
            json.loads(item["incorrect_problems"])
            if "incorrect_problems" in item
            else None
        )

        worksheet = cls(
            child_id=item["child_id"],
            problems=problems,
            answers=answers,
            completed=item["completed"],
            incorrect_problems=incorrect_problems,
        )
        worksheet.id = item["id"]
        worksheet.created_at = int(float(item["created_at"]))
        worksheet.updated_at = int(float(item["updated_at"]))
        return worksheet
