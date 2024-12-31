from problem_generator import ProblemGenerator
from renderer import WorksheetRenderer
from datetime import datetime
from db_handler import DatabaseHandler
import uuid


def main():
    # age = int(input("Enter the age of the student: "))
    age = 6
    school_year_month = ProblemGenerator.get_school_year_month()

    print(f"Automatically calculated school year month: {school_year_month}")
    problems, answers = ProblemGenerator.generate_math_problems(age)

    today = datetime.now().strftime("%Y-%m-%d")
    worksheet_id = str(uuid.uuid4())
    version = "v1"
    worksheet_filename = f"math_worksheet_{today}.pdf"
    answer_key_filename = f"math_answer_key_{today}.pdf"
    qr_code_stream = WorksheetRenderer.create_qr_code(worksheet_id, version)

    WorksheetRenderer.create_math_worksheet(
        worksheet_filename, problems, worksheet_id, version, qr_code_stream
    )
    print(
        f"Generated worksheet: {worksheet_filename}, worksheet_id: {worksheet_id}, version: {version}"
    )
    WorksheetRenderer.create_answer_key(
        answer_key_filename, problems, answers, worksheet_id, version, qr_code_stream
    )
    print(
        f"Generated answer key: {answer_key_filename}, worksheet_id: {worksheet_id}, version: {version}"
    )
    DatabaseHandler.save_to_database(worksheet_id, problems, answers, version)
    print(f"Saved to database..")


if __name__ == "__main__":
    main()
