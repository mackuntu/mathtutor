"""Tests for the page routes."""


def test_index_generate_button_is_enabled(client, auth_manager, test_user, test_child):
    """The Generate button must render without the disabled attribute."""
    token = auth_manager.create_session(test_user.email)
    client.set_cookie("session_token", token)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    start = html.index('id="generateBtn"')
    tag = html[html.rindex("<button", 0, start) : html.index(">", start)]
    assert "disabled" not in tag


def test_past_worksheets_shows_serial_and_date(
    client, auth_manager, repository, test_user, test_worksheet
):
    """Graded worksheets list renders serial and created date from Postgres."""
    test_worksheet.completed = True
    repository.update_worksheet(test_worksheet)
    client.set_cookie("session_token", auth_manager.create_session(test_user.email))

    response = client.get(f"/worksheets/past/{test_worksheet.child_id}")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert test_worksheet.serial in html
    assert test_worksheet.created_date.strftime("%Y-%m-%d") in html


def test_edit_child_persists_birthday(
    client, auth_manager, repository, test_user, test_child
):
    """Editing a child stores the birthday in the DATE column."""
    client.set_cookie("session_token", auth_manager.create_session(test_user.email))

    response = client.post(
        f"/children/{test_child.id}/edit",
        data={"name": "Kid", "birthday": "2017-04-02", "grade_level": "3"},
    )

    assert response.status_code == 302
    saved = repository.get_child_by_id(test_child.id)
    assert saved.birthday.strftime("%Y-%m-%d") == "2017-04-02"
    edit_page = client.get(f"/children/{test_child.id}/edit")
    assert 'value="2017-04-02"' in edit_page.get_data(as_text=True)
