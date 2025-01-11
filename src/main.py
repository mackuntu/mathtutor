import uuid
from datetime import datetime

from src.db_handler import DatabaseHandler
from src.problem_generator import ProblemGenerator
from src.renderer import WorksheetRenderer


def main():
    # Initialize the database
    DatabaseHandler.initialize_database()

    # Step 1: Generate math problems and answers
    age = 6
    school_year_month = ProblemGenerator.get_school_year_month()
    print(f"Automatically calculated school year month: {school_year_month}")

    problems, answers = ProblemGenerator.generate_math_problems(age)

    # Step 2: Prepare metadata and file names
    today = datetime.now().strftime("%Y-%m-%d")
    worksheet_id = str(uuid.uuid4())
    version = "v1"
    worksheet_filename = f"data/worksheets/math_worksheet_{today}.pdf"
    answer_key_filename = f"data/answer_keys/math_answer_key_{today}.pdf"
    qr_code_stream = WorksheetRenderer.create_qr_code(worksheet_id, version)

    # Step 3: Render worksheet and answer key, and retrieve template ID
    template_id = WorksheetRenderer.create_math_worksheet(
        worksheet_filename, problems, qr_code_stream
    )
    print(
        f"Generated worksheet: {worksheet_filename}, worksheet_id: {worksheet_id}, template_id: {template_id}"
    )

    WorksheetRenderer.create_answer_key(
        answer_key_filename, problems, answers, qr_code_stream
    )
    print(
        f"Generated answer key: {answer_key_filename}, worksheet_id: {worksheet_id}, version: {version}"
    )

    # Step 4: Save metadata and problems to the database
    DatabaseHandler.save_worksheet(
        worksheet_id=worksheet_id,
        version=version,
        problems=problems,
        answers=answers,
        template_id=template_id,
    )
    print("Saved worksheet and answers to the database.")


if __name__ == "__main__":
    main()
