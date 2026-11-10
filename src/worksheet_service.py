"""Worksheet generation and printable rendering shared by web and device API."""

import json

from flask import render_template

from .database import PostgresRepository
from .database.models import Child, Worksheet
from .problem_generator import ProblemGenerator

PROBLEMS_PER_WORKSHEET = 30


def generate_for_child(child: Child) -> Worksheet:
    """Generate, persist and return a new worksheet (with answers) for a child."""
    generator = ProblemGenerator()
    problems, answers = generator.generate_math_problems(
        age=child.age,
        count=PROBLEMS_PER_WORKSHEET,
        difficulty=generator.get_school_year_progress(),
    )
    worksheet = Worksheet.create(child_id=child.id, problems=json.dumps(problems))
    worksheet.correct_answers = answers  # Stored for grading
    PostgresRepository().create_worksheet(worksheet)
    return worksheet


def render_printable(worksheet: Worksheet, child: Child) -> str:
    """Render a worksheet as printable HTML (with serial, without answer key)."""
    problems = worksheet.problems
    if isinstance(problems, str):
        problems = json.loads(problems)
    # Older worksheets stored bare strings; wrap them for the template.
    problem_list = [
        p if isinstance(p, dict) else {"text": p, "kind": "operands"} for p in problems
    ]
    return render_template(
        "worksheet.html",
        user=None,
        child=child,
        problems=problem_list,
        answers=None,
        worksheet_id=worksheet.id,
        serial_number=worksheet.serial_number,
        is_answer_key=False,
    )
