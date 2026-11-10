"""Tests for shared worksheet generation and printable rendering."""

import json

from src.worksheet_service import generate_for_child, render_printable

PROBLEM_COUNT = 30


def test_generate_for_child_persists_30_problems_with_answers(repository, test_child):
    ws = generate_for_child(test_child)

    saved = repository.get_worksheet(ws.id)
    problems = saved.problems
    if isinstance(problems, str):
        problems = json.loads(problems)
    assert saved is not None and saved.child_id == test_child.id
    assert len(problems) == PROBLEM_COUNT
    assert saved.correct_answers


def test_render_printable_has_serial_and_no_answer_key(app, repository, test_child):
    ws = generate_for_child(test_child)

    with app.test_request_context():
        html = render_printable(ws, test_child)

    assert f"Serial: {ws.serial_number}" in html
    assert "Answer Key" not in html
    assert "MathTutor Worksheet" in html


def test_generate_route_renders_worksheet_without_serial(
    client, repository, test_child, test_session
):
    client.set_cookie("session_token", test_session.token)
    response = client.get(f"/worksheets/generate?child_id={test_child.id}")

    assert response.status_code == 200
    assert b"Serial:" not in response.data
