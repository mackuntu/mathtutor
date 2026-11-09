"""Tests for PostgresRepository against a real Postgres test database."""

import time
from datetime import datetime

import pytest

from src.database.models import Child, Session, User, Worksheet
from tests.conftest import assert_test_database


def _child(parent_email, name="Kid"):
    return Child(parent_email=parent_email, name=name, age=8, grade=3)


def test_user_roundtrip(repository):
    user = User(email="a@example.com", name="Ann", picture="https://x/p.png")
    repository.create_user(user)

    saved = repository.get_user_by_email("a@example.com")

    assert saved.name == "Ann"
    assert saved.picture == "https://x/p.png"
    assert saved.created_at == user.created_at


def test_get_missing_user_returns_none(repository):
    assert repository.get_user_by_email("nobody@example.com") is None


def test_update_user_persists_changes(repository, test_user):
    test_user.name = "Renamed"
    repository.update_user(test_user)

    assert repository.get_user_by_email(test_user.email).name == "Renamed"


def test_children_by_parent_only_returns_that_parents_children(repository):
    for email in ("p1@example.com", "p2@example.com"):
        repository.create_user(User(email=email, name=email))
    repository.create_child(_child("p1@example.com", "Zed"))
    repository.create_child(_child("p1@example.com", "Amy"))
    repository.create_child(_child("p2@example.com", "Other"))

    children = repository.get_children_by_parent("p1@example.com")

    assert [c.name for c in children] == ["Amy", "Zed"]


def test_child_birthday_roundtrip(repository, test_user):
    child = _child(test_user.email)
    child.birthday = datetime(2016, 3, 14)
    repository.create_child(child)

    saved = repository.get_child_by_id(child.id)

    assert saved.birthday.strftime("%Y-%m-%d") == "2016-03-14"


def test_child_without_birthday_stores_null(repository, test_user):
    child = _child(test_user.email)
    repository.create_child(child)

    assert repository.get_child_by_id(child.id)._birthday is None


def test_worksheet_roundtrip_preserves_jsonb(repository, test_child):
    problems = [{"text": "3 x 4", "type": "mult"}, {"text": "clock", "h": 3}]
    worksheet = Worksheet(
        child_id=test_child.id, problems=problems, correct_answers=["12", "3:05"]
    )
    repository.create_worksheet(worksheet)

    saved = repository.get_worksheet(worksheet.id)

    assert saved.problems == problems
    assert saved.correct_answers == ["12", "3:05"]
    assert saved.serial == "WS-" + worksheet.id[:8]
    assert saved.serial_number == saved.serial
    assert saved.answers is None
    assert saved.completed is False


def test_get_worksheets_by_serial(repository, test_child):
    worksheet = Worksheet(child_id=test_child.id, problems=[{"text": "1 + 1"}])
    other = Worksheet(child_id=test_child.id, problems=[{"text": "2 + 2"}])
    repository.create_worksheet(worksheet)
    repository.create_worksheet(other)

    found = repository.get_worksheets_by_serial(worksheet.serial)

    assert [w.id for w in found] == [worksheet.id]


def test_child_worksheets_newest_first(repository, test_child):
    old = Worksheet(child_id=test_child.id, problems=[{"text": "old"}])
    new = Worksheet(child_id=test_child.id, problems=[{"text": "new"}])
    old.created_at = new.created_at - 100
    repository.create_worksheet(old)
    repository.create_worksheet(new)

    worksheets = repository.get_child_worksheets(test_child.id)

    assert [w.id for w in worksheets] == [new.id, old.id]


def test_update_worksheet_persists_grades(repository, test_worksheet):
    test_worksheet.completed = True
    test_worksheet.incorrect_problems = [2, 5]
    repository.update_worksheet(test_worksheet)

    saved = repository.get_worksheet(test_worksheet.id)

    assert saved.completed is True
    assert saved.incorrect_problems == [2, 5]


def test_delete_worksheet(repository, test_worksheet):
    repository.delete_worksheet(test_worksheet.id)

    assert repository.get_worksheet(test_worksheet.id) is None


def test_delete_child_cascades_worksheets(repository, test_worksheet, test_child):
    repository.delete_child(test_child.id)

    assert repository.get_child_by_id(test_child.id) is None
    assert repository.get_worksheet(test_worksheet.id) is None


def test_delete_expired_sessions_removes_only_expired(repository, test_user):
    now = int(time.time())
    repository.create_session(Session("old", test_user.email, now - 1))
    repository.create_session(Session("live", test_user.email, now + 60))

    deleted = repository.delete_expired_sessions(now)

    assert deleted == 1
    assert repository.get_session("old") is None
    assert repository.get_session("live") is not None


def test_create_session_purges_expired_sessions(auth_manager, repository, test_user):
    repository.create_session(Session("stale", test_user.email, int(time.time()) - 1))

    auth_manager.create_session(test_user.email)

    assert repository.get_session("stale") is None


def test_expired_session_cookie_redirects_to_login(client, repository, test_user):
    repository.create_session(Session("expired", test_user.email, int(time.time()) - 1))
    client.set_cookie("session_token", "expired")

    response = client.get("/children/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
    assert repository.get_session("expired") is None


def test_db_guard_refuses_non_test_database():
    with pytest.raises(RuntimeError, match="must end with '_test'"):
        assert_test_database("postgresql://u:p@localhost:5432/mathtutor")
