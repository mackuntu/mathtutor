"""Tests for the page routes."""

from src.database.models import Worksheet


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


def test_submit_worksheet_stores_answers_as_jsonb_list(
    client, auth_manager, repository, test_user, test_child
):
    """Submitted answers persist as a JSON list and the view page renders them."""
    worksheet = Worksheet(
        child_id=test_child.id,
        problems=[{"text": "1 + 1", "answer": 2}, {"text": "2 + 3", "answer": 5}],
    )
    repository.create_worksheet(worksheet)
    client.set_cookie("session_token", auth_manager.create_session(test_user.email))

    response = client.post(
        f"/worksheets/{worksheet.id}/submit", data={"answer_0": "2", "answer_1": "4"}
    )

    assert response.status_code == 302
    saved = repository.get_worksheet(worksheet.id)
    assert saved.answers == [2.0, 4.0]
    assert saved.incorrect_problems == [1]
    assert client.get(f"/worksheets/{worksheet.id}").status_code == 200


BIRTHDAY = "2018-03-15"


def _expected_school_year_age():
    from datetime import datetime

    from src.database.models import calculate_age_at_end_of_school_year

    return calculate_age_at_end_of_school_year(datetime(2018, 3, 15))


def test_register_child_persists_birthday_and_school_year_age(
    client, auth_manager, repository, test_user
):
    """Registering stores the birthday and the end-of-school-year age."""
    client.set_cookie("session_token", auth_manager.create_session(test_user.email))

    response = client.post(
        "/children/",
        data={"name": "Kid", "birthday": BIRTHDAY, "grade_level": "3"},
    )

    assert response.status_code == 302
    (saved,) = repository.get_children_by_parent(test_user.email)
    assert saved.birthday.strftime("%Y-%m-%d") == BIRTHDAY
    assert saved.birthday.tzinfo is not None
    assert saved.age == _expected_school_year_age()


def test_edit_child_keeps_school_year_age_and_shows_stored_birthday(
    client, auth_manager, repository, test_user
):
    """Editing with the same birthday leaves the age unchanged."""
    client.set_cookie("session_token", auth_manager.create_session(test_user.email))
    client.post(
        "/children/", data={"name": "Kid", "birthday": BIRTHDAY, "grade_level": "3"}
    )
    (child,) = repository.get_children_by_parent(test_user.email)

    client.post(
        f"/children/{child.id}/edit",
        data={"name": "Kid", "birthday": BIRTHDAY, "grade_level": "3"},
    )

    saved = repository.get_child_by_id(child.id)
    assert saved.age == _expected_school_year_age()
    html = client.get(f"/children/{child.id}/edit").get_data(as_text=True)
    assert f'value="{BIRTHDAY}"' in html


def test_edit_form_leaves_birthday_blank_when_unknown(
    client, auth_manager, test_user, test_child
):
    """A child without a stored birthday gets an empty field, not a made-up date."""
    client.set_cookie("session_token", auth_manager.create_session(test_user.email))

    html = client.get(f"/children/{test_child.id}/edit").get_data(as_text=True)

    assert 'name="birthday"' in html
    assert "-01-01" not in html


def test_school_year_age_uses_june_30_of_current_school_year():
    """Before June the school year ends this year; from June on, next year."""
    from datetime import date, datetime

    from src.database.models import calculate_age_at_end_of_school_year

    born = datetime(2018, 3, 15)
    assert calculate_age_at_end_of_school_year(born, today=date(2026, 5, 31)) == 8
    assert calculate_age_at_end_of_school_year(born, today=date(2026, 11, 9)) == 9
    late = datetime(2018, 7, 1)
    assert calculate_age_at_end_of_school_year(late, today=date(2026, 11, 9)) == 8
