"""Data models for the MathTutor application, mapped to Postgres rows."""

import json
import uuid
from datetime import date, datetime, timezone
from typing import Optional


SCHOOL_YEAR_END_MONTH = 6
SCHOOL_YEAR_END_DAY = 30


def calculate_age_at_end_of_school_year(
    birthday_date: datetime, today: Optional[date] = None
) -> int:
    """Age a child will be at the end of the current school year (June 30th).

    Before June the school year ends this calendar year; from June on it ends
    next year. Using a fixed reference date keeps age stable all school year.
    """
    today = today or datetime.now(timezone.utc).date()
    end_year = today.year if today.month < SCHOOL_YEAR_END_MONTH else today.year + 1
    end = (SCHOOL_YEAR_END_MONTH, SCHOOL_YEAR_END_DAY)
    return (
        end_year
        - birthday_date.year
        - (end < (birthday_date.month, birthday_date.day))
    )


class Model:
    """Base class for persisted models."""

    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique ID for a new record."""
        return str(uuid.uuid4())

    @staticmethod
    def utc_now() -> int:
        """Get current UTC timestamp in seconds."""
        return int(datetime.now(timezone.utc).timestamp())


class User(Model):
    """A signed-in parent."""

    def __init__(self, email: str, name: str, picture: Optional[str] = None):
        self.email = email
        self.name = name
        self.picture = picture
        self.created_at = self.utc_now()
        self.updated_at = self.created_at

    @classmethod
    def from_row(cls, row: dict) -> "User":
        """Build a User from a ``users`` row."""
        user = cls(email=row["email"], name=row["name"], picture=row["picture"])
        user.created_at = row["created_at"]
        user.updated_at = row["updated_at"]
        return user


class Child(Model):
    """A child belonging to a parent user."""

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
        self._birthday: Optional[datetime] = None  # Stored birthday, if known

    @property
    def birthday(self) -> Optional[datetime]:
        """The stored birthday (UTC-aware), or None when unknown."""
        return self._birthday

    @birthday.setter
    def birthday(self, value: datetime) -> None:
        """Store the birthday and derive age at the end of the school year."""
        if not isinstance(value, datetime):
            raise ValueError("Birthday must be a datetime object")
        self._birthday = (
            value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        )
        self.age = calculate_age_at_end_of_school_year(self._birthday)

    @property
    def stored_birthday(self) -> Optional[date]:
        """The birthday as a ``DATE`` column value (None when not set)."""
        return self._birthday.date() if self._birthday else None

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

    @classmethod
    def from_row(cls, row: dict) -> "Child":
        """Build a Child from a ``children`` row."""
        child = cls(
            parent_email=row["parent_email"],
            name=row["name"],
            age=row["age"],
            grade=row["grade"],
            preferred_color=row["preferred_color"],
        )
        child.id = row["id"]
        child.created_at = row["created_at"]
        child.updated_at = row["updated_at"]
        birthday = row["birthday"]
        if birthday is not None:
            # Set directly: the setter would recompute (and overwrite) age.
            child._birthday = datetime(
                birthday.year, birthday.month, birthday.day, tzinfo=timezone.utc
            )
        return child


class Session(Model):
    """A login session keyed by an opaque token."""

    def __init__(self, token: str, user_email: str, expires_at: int):
        self.token = token
        self.user_email = user_email
        self.expires_at = expires_at

    @classmethod
    def from_row(cls, row: dict) -> "Session":
        """Build a Session from a ``sessions`` row."""
        return cls(
            token=row["token"],
            user_email=row["user_email"],
            expires_at=row["expires_at"],
        )


class Worksheet(Model):
    """A generated worksheet and its grading state."""

    def __init__(
        self,
        child_id: str,
        problems: list = None,
        answers: list = None,
        completed: bool = False,
        incorrect_problems: list = None,
        correct_answers: list = None,
    ):
        """Initialize a worksheet."""
        self.id = self.generate_id()
        self.serial = f"WS-{self.id[:8]}"
        self.child_id = child_id
        self.problems = problems or []
        self.answers = answers
        self.completed = completed
        self.incorrect_problems = incorrect_problems or []
        self.correct_answers = correct_answers  # Store correct answers at creation time
        self.created_at = self.utc_now()
        self.updated_at = self.created_at

    @property
    def serial_number(self) -> str:
        """Return the printed serial number for the worksheet."""
        return self.serial

    @property
    def created_date(self) -> datetime:
        """``created_at`` (epoch seconds) as a UTC datetime, for display."""
        return datetime.fromtimestamp(self.created_at, tz=timezone.utc)

    @property
    def problem_count(self) -> int:
        """Return the number of problems in the worksheet."""
        return len(self.problems) if self.problems else 0

    @property
    def score(self) -> float:
        """Calculate the score as a percentage."""
        if not self.completed or not self.problems:
            return 0.0
        correct = len(self.problems) - len(self.incorrect_problems)
        return (correct / len(self.problems)) * 100

    @classmethod
    def create(cls, child_id: str, problems: str) -> "Worksheet":
        """Create a new worksheet."""
        # Convert problems from string to list if needed
        if isinstance(problems, str):
            problems = json.loads(problems)
        return cls(child_id=child_id, problems=problems)

    @classmethod
    def from_row(cls, row: dict) -> "Worksheet":
        """Build a Worksheet from a ``worksheets`` row."""
        worksheet = cls(
            child_id=row["child_id"],
            problems=row["problems"],
            answers=row["answers"],
            completed=row["completed"],
            incorrect_problems=row["incorrect_problems"],
            correct_answers=row["correct_answers"],
        )
        worksheet.id = row["id"]
        worksheet.serial = row["serial"]
        worksheet.created_at = row["created_at"]
        worksheet.updated_at = row["updated_at"]
        return worksheet
