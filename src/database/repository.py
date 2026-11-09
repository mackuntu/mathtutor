"""Postgres-backed repository for all MathTutor persistence."""

from typing import List, Optional

from psycopg.types.json import Jsonb

from .db import get_conn
from .models import Child, Session, User, Worksheet


def _one(query: str, params: tuple) -> Optional[dict]:
    """Run a parameterized query and return its first row, if any."""
    return get_conn().execute(query, params).fetchone()


def _all(query: str, params: tuple) -> List[dict]:
    """Run a parameterized query and return every row."""
    return get_conn().execute(query, params).fetchall()


def _jsonb_or_none(value):
    """Wrap a value for a JSONB column, keeping SQL NULL for None."""
    return None if value is None else Jsonb(value)


class PostgresRepository:
    """Stateless repository; each call uses the app-context connection."""

    # User operations
    def get_user_by_email(self, email: str) -> Optional[User]:
        row = _one("SELECT * FROM users WHERE email = %s", (email,))
        return User.from_row(row) if row else None

    def create_user(self, user: User) -> None:
        get_conn().execute(
            "INSERT INTO users (email, name, picture, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user.email, user.name, user.picture, user.created_at, user.updated_at),
        )

    def update_user(self, user: User) -> None:
        user.updated_at = user.utc_now()
        get_conn().execute(
            "UPDATE users SET name = %s, picture = %s, updated_at = %s "
            "WHERE email = %s",
            (user.name, user.picture, user.updated_at, user.email),
        )

    # Child operations
    def get_child_by_id(self, child_id: str) -> Optional[Child]:
        row = _one("SELECT * FROM children WHERE id = %s", (child_id,))
        return Child.from_row(row) if row else None

    def get_children_by_parent(self, parent_email: str) -> List[Child]:
        rows = _all(
            "SELECT * FROM children WHERE parent_email = %s ORDER BY name, id",
            (parent_email,),
        )
        return [Child.from_row(row) for row in rows]

    def create_child(self, child: Child) -> None:
        get_conn().execute(
            "INSERT INTO children (id, parent_email, name, age, grade, "
            "preferred_color, birthday, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                child.id,
                child.parent_email,
                child.name,
                child.age,
                child.grade,
                child.preferred_color,
                child.stored_birthday,
                child.created_at,
                child.updated_at,
            ),
        )

    def update_child(self, child: Child) -> None:
        child.updated_at = child.utc_now()
        get_conn().execute(
            "UPDATE children SET name = %s, age = %s, grade = %s, "
            "preferred_color = %s, birthday = %s, updated_at = %s WHERE id = %s",
            (
                child.name,
                child.age,
                child.grade,
                child.preferred_color,
                child.stored_birthday,
                child.updated_at,
                child.id,
            ),
        )

    def delete_child(self, child_id: str) -> None:
        """Delete a child; its worksheets go with it via ON DELETE CASCADE."""
        get_conn().execute("DELETE FROM children WHERE id = %s", (child_id,))

    # Session operations
    def get_session(self, token: str) -> Optional[Session]:
        row = _one("SELECT * FROM sessions WHERE token = %s", (token,))
        return Session.from_row(row) if row else None

    def create_session(self, session: Session) -> None:
        get_conn().execute(
            "INSERT INTO sessions (token, user_email, expires_at) VALUES (%s, %s, %s)",
            (session.token, session.user_email, session.expires_at),
        )

    def delete_session(self, token: str) -> None:
        get_conn().execute("DELETE FROM sessions WHERE token = %s", (token,))

    def delete_expired_sessions(self, now: int) -> int:
        """Delete sessions that expired before ``now``; return how many."""
        cursor = get_conn().execute(
            "DELETE FROM sessions WHERE expires_at < %s", (now,)
        )
        return cursor.rowcount

    # Worksheet operations
    def get_worksheet(self, worksheet_id: str) -> Optional[Worksheet]:
        row = _one(
            "SELECT * FROM worksheets WHERE id = %s",
            (worksheet_id,),
        )
        return Worksheet.from_row(row) if row else None

    def get_child_worksheets(self, child_id: str) -> List[Worksheet]:
        """All worksheets for a child, newest first."""
        rows = _all(
            "SELECT * FROM worksheets WHERE child_id = %s "
            "ORDER BY created_at DESC, id",
            (child_id,),
        )
        return [Worksheet.from_row(row) for row in rows]

    def get_worksheets_by_serial(self, serial: str) -> List[Worksheet]:
        rows = _all(
            "SELECT * FROM worksheets WHERE serial = %s "
            "ORDER BY created_at DESC, id",
            (serial,),
        )
        return [Worksheet.from_row(row) for row in rows]

    def create_worksheet(self, worksheet: Worksheet) -> None:
        get_conn().execute(
            "INSERT INTO worksheets (id, child_id, serial, problems, answers, "
            "completed, incorrect_problems, correct_answers, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                worksheet.id,
                worksheet.child_id,
                worksheet.serial,
                Jsonb(worksheet.problems),
                _jsonb_or_none(worksheet.answers),
                worksheet.completed,
                Jsonb(worksheet.incorrect_problems),
                _jsonb_or_none(worksheet.correct_answers),
                worksheet.created_at,
                worksheet.updated_at,
            ),
        )

    def update_worksheet(self, worksheet: Worksheet) -> None:
        worksheet.updated_at = worksheet.utc_now()
        get_conn().execute(
            "UPDATE worksheets SET problems = %s, answers = %s, completed = %s, "
            "incorrect_problems = %s, correct_answers = %s, updated_at = %s "
            "WHERE id = %s",
            (
                Jsonb(worksheet.problems),
                _jsonb_or_none(worksheet.answers),
                worksheet.completed,
                Jsonb(worksheet.incorrect_problems),
                _jsonb_or_none(worksheet.correct_answers),
                worksheet.updated_at,
                worksheet.id,
            ),
        )

    def delete_worksheet(self, worksheet_id: str) -> None:
        get_conn().execute("DELETE FROM worksheets WHERE id = %s", (worksheet_id,))

    # Device token operations
    def create_device_token(
        self, id: str, name: str, token_hash: str, created_at: int
    ) -> None:
        get_conn().execute(
            "INSERT INTO device_tokens (id, name, token_hash, created_at) "
            "VALUES (%s, %s, %s, %s)",
            (id, name, token_hash, created_at),
        )

    def list_device_tokens(self) -> List[dict]:
        """All tokens, newest first; the hash is never returned."""
        return _all(
            "SELECT id, name, created_at, last_used_at, revoked_at "
            "FROM device_tokens ORDER BY created_at DESC, id DESC",
            (),
        )

    def get_active_device_token_by_hash(self, token_hash: str) -> Optional[dict]:
        return _one(
            "SELECT * FROM device_tokens "
            "WHERE token_hash = %s AND revoked_at IS NULL",
            (token_hash,),
        )

    def touch_device_token(self, id: str, now: int) -> None:
        get_conn().execute(
            "UPDATE device_tokens SET last_used_at = %s WHERE id = %s", (now, id)
        )

    def revoke_device_token(self, id: str, now: int) -> bool:
        """Revoke a token (idempotent); return False if the id is unknown."""
        cursor = get_conn().execute(
            "UPDATE device_tokens SET revoked_at = COALESCE(revoked_at, %s) "
            "WHERE id = %s",
            (now, id),
        )
        return cursor.rowcount > 0
