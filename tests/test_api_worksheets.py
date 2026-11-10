"""Tests for the device API: list children and print a new worksheet."""

import pytest

from src.database.models import Child
from src.device_tokens import issue_token
from tests.conftest import OWNER, bearer


@pytest.fixture
def token(owner, repository):
    return issue_token("Pi")


@pytest.fixture
def owner_child(repository, owner):
    child = Child(parent_email=OWNER, name="Ada", age=8, grade=3)
    repository.create_child(child)
    return child


@pytest.fixture
def other_child(repository, auth_manager):
    auth_manager.get_or_create_user("other@example.com", "Other")
    child = Child(parent_email="other@example.com", name="Eve", age=9, grade=4)
    repository.create_child(child)
    return child


def test_list_children_returns_owner_children_only(
    client, token, owner_child, other_child
):
    response = client.get("/api/children", headers=bearer(token))

    assert response.status_code == 200
    assert response.get_json() == {
        "children": [{"id": owner_child.id, "name": "Ada", "age": 8, "grade": 3}]
    }


def test_list_children_requires_auth_401(client, db):
    assert client.get("/api/children").status_code == 401


def test_new_worksheet_returns_html_with_serial(client, token, owner_child):
    response = client.post(
        f"/api/children/{owner_child.id}/worksheets", headers=bearer(token)
    )

    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == {"worksheet_id", "serial", "html"}
    assert body["serial"].startswith("WS-")
    assert f"Serial: {body['serial']}" in body["html"]
    assert "Answer Key" not in body["html"]


def test_new_worksheet_fills_in_child_name(client, token, owner_child):
    response = client.post(
        f"/api/children/{owner_child.id}/worksheets", headers=bearer(token)
    )

    html = response.get_json()["html"]
    assert 'Name: <span class="underline">Ada</span>' in html


def test_new_worksheet_escapes_child_name(client, token, repository, owner):
    child = Child(parent_email=OWNER, name="<b>Bo</b>", age=8, grade=3)
    repository.create_child(child)

    response = client.post(
        f"/api/children/{child.id}/worksheets", headers=bearer(token)
    )

    html = response.get_json()["html"]
    assert "&lt;b&gt;Bo&lt;/b&gt;" in html
    assert "<b>Bo</b>" not in html


def test_new_worksheet_is_persisted_for_child(client, token, owner_child, repository):
    body = client.post(
        f"/api/children/{owner_child.id}/worksheets", headers=bearer(token)
    ).get_json()

    saved = repository.get_child_worksheets(owner_child.id)
    assert [w.id for w in saved] == [body["worksheet_id"]]
    assert saved[0].serial_number == body["serial"]
    assert len(saved[0].problems) == 30


def test_new_worksheet_unknown_child_404(client, token):
    response = client.post("/api/children/nope/worksheets", headers=bearer(token))

    assert response.status_code == 404
    assert response.get_json() == {"error": "not found"}


def test_new_worksheet_other_parents_child_404(client, token, other_child, repository):
    response = client.post(
        f"/api/children/{other_child.id}/worksheets", headers=bearer(token)
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "not found"}
    assert repository.get_child_worksheets(other_child.id) == []


def test_new_worksheet_requires_auth_401(client, owner_child):
    assert client.post(f"/api/children/{owner_child.id}/worksheets").status_code == 401


def test_new_worksheet_get_not_allowed_405(client, token, owner_child):
    response = client.get(
        f"/api/children/{owner_child.id}/worksheets", headers=bearer(token)
    )
    assert response.status_code == 405
