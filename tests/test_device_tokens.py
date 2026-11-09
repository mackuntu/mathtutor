"""Tests for revocable device tokens and the /api bearer auth."""

import hashlib
import re

import pytest

from src.database.db import get_conn
from src.device_tokens import issue_token

OWNER = "owner@example.com"


@pytest.fixture(autouse=True)
def owner_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_EMAILS", OWNER)


@pytest.fixture
def owner(auth_manager):
    return auth_manager.get_or_create_user(OWNER, "Owner")


@pytest.fixture
def logged_in(client, auth_manager, owner):
    client.set_cookie("session_token", auth_manager.create_session(owner.email))
    return client


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_issued_token_authorizes_api_ping_and_updates_last_used(
    client, repository, app
):
    raw = issue_token("Pi")
    assert raw.startswith("mt_")
    assert repository.list_device_tokens()[0]["last_used_at"] is None

    response = client.get("/api/ping", headers=bearer(raw))

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}
    assert repository.list_device_tokens()[0]["last_used_at"] is not None


def test_revoked_token_401(client, repository):
    raw = issue_token("Pi")
    token_id = repository.list_device_tokens()[0]["id"]
    repository.revoke_device_token(token_id, 123)

    response = client.get("/api/ping", headers=bearer(raw))

    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized"}


def test_wrong_token_401(client, repository):
    issue_token("Pi")
    response = client.get("/api/ping", headers=bearer("mt_nope"))
    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized"}


@pytest.mark.parametrize("scheme", ["", "bearer ", "Token ", "Bearer  "])
def test_token_without_bearer_prefix_401(client, repository, scheme):
    raw = issue_token("Pi")
    response = client.get("/api/ping", headers={"Authorization": f"{scheme}{raw}"})
    assert response.status_code == 401


def test_invalid_bearer_does_not_fall_back_to_session(logged_in):
    response = logged_in.get("/api/ping", headers=bearer("mt_nope"))
    assert response.status_code == 401


def test_no_credentials_401(client, db):
    assert client.get("/api/ping").status_code == 401


def test_session_cookie_authorizes_api_ping(logged_in):
    assert logged_in.get("/api/ping").status_code == 200


def test_valid_token_without_owner_configured_401(client, repository, monkeypatch):
    raw = issue_token("Pi")
    monkeypatch.setenv("ALLOWED_EMAILS", "")
    assert client.get("/api/ping", headers=bearer(raw)).status_code == 401


def test_token_creates_owner_user_row(client, repository):
    raw = issue_token("Pi")
    client.get("/api/ping", headers=bearer(raw))
    assert repository.get_user_by_email(OWNER) is not None


def test_bearer_token_does_not_authorize_browser_route(client, repository):
    raw = issue_token("Pi")
    response = client.get("/children/", headers=bearer(raw))
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_raw_token_never_stored(repository):
    raw = issue_token("Pi")
    stored = get_conn().execute("SELECT * FROM device_tokens").fetchall()
    assert len(stored) == 1
    assert raw not in "".join(str(v) for v in stored[0].values())
    assert stored[0]["token_hash"] == hashlib.sha256(raw.encode()).hexdigest()


def test_settings_page_requires_login(client, db):
    assert client.get("/settings/devices").status_code == 302
    assert client.post("/settings/devices", data={"name": "x"}).status_code == 302
    assert client.post("/settings/devices/abc/revoke").status_code == 302


def test_create_shows_token_once_then_list_hides_it(logged_in, repository):
    response = logged_in.post("/settings/devices", data={"name": "Kitchen Pi"})
    assert response.status_code == 200
    raw = re.search(r"mt_[A-Za-z0-9_-]+", response.get_data(as_text=True)).group(0)
    assert logged_in.get("/api/ping", headers=bearer(raw)).status_code == 200

    listing = logged_in.get("/settings/devices").get_data(as_text=True)
    assert "Kitchen Pi" in listing
    assert raw not in listing


@pytest.mark.parametrize("name", ["", "   ", "x" * 51])
def test_create_rejects_bad_name(logged_in, repository, name):
    response = logged_in.post("/settings/devices", data={"name": name})
    assert response.status_code == 400
    assert repository.list_device_tokens() == []


def test_revoke_via_settings_blocks_token(logged_in, repository):
    raw = issue_token("Pi")
    token_id = repository.list_device_tokens()[0]["id"]

    assert logged_in.post(f"/settings/devices/{token_id}/revoke").status_code == 302
    assert logged_in.post(f"/settings/devices/{token_id}/revoke").status_code == 302
    assert logged_in.get("/api/ping", headers=bearer(raw)).status_code == 401


def test_revoke_unknown_id_404(logged_in):
    assert logged_in.post("/settings/devices/nope/revoke").status_code == 404


def test_revoke_requires_post(logged_in):
    assert logged_in.get("/settings/devices/abc/revoke").status_code == 405


def test_list_returns_newest_first_without_hashes(repository):
    repository.create_device_token("a", "A", "h1", 1)
    repository.create_device_token("b", "B", "h2", 2)
    listed = repository.list_device_tokens()
    assert [t["id"] for t in listed] == ["b", "a"]
    assert all("token_hash" not in t for t in listed)
