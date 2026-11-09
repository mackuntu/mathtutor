"""Tests for the page routes."""

import pytest

from src import create_app


@pytest.fixture
def client(dynamodb):
    """Flask test client backed by the mocked DynamoDB tables."""
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_index_generate_button_is_enabled(
    client, auth_manager, test_user, test_child_dynamodb
):
    """The Generate button must render without the disabled attribute."""
    token = auth_manager.create_session(test_user.email)
    client.set_cookie("session_token", token)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    start = html.index('id="generateBtn"')
    tag = html[html.rindex("<button", 0, start) : html.index(">", start)]
    assert "disabled" not in tag
