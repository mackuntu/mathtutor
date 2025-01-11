import random
from datetime import datetime

from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

NUM_PROBLEMS = 30

# Map decorations to image paths
SPACE_DECORATIONS = [
    "assets/rocket.png",
    "assets/moon.png",
    "assets/star.png",
    "assets/shining_star.png",
    "assets/planet.png",
    "assets/galaxy.png",
]


def generate_math_problems():
    """
    Generate 30 math problems with answers, covering addition, subtraction, and multiplication.
    """
    problems = []
    answers = []

    for i in range(NUM_PROBLEMS):
        if i < 3:  # Simple addition and subtraction
            a, b = random.randint(1, 20), random.randint(1, 20)
            operation = random.choice(["+", "-"])
        elif i < 6:  # Higher addition and subtraction
            a, b = random.randint(10, 50), random.randint(10, 50)
            operation = random.choice(["+", "-"])
        else:  # Multiplication
            a, b = random.randint(1, 10), random.randint(1, 10)
            operation = "x"

        if operation == "+":
            answer = a + b
        elif operation == "-":
            answer = a - b
        else:  # Multiplication
            answer = a * b

        problems.append(f"{a} {operation} {b} = _______")
        answers.append(answer)

    return problems, answers


def create_math_worksheet(filename, problems):
    """
    Generate a PDF worksheet with the given math problems.
    """
    pdf = canvas.Canvas(filename, pagesize=portrait(letter))
    pdf.setFont("Helvetica", 18)

    # Title and Header
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.drawString(200, 750, "Math Worksheet - Space Edition")
    pdf.drawString(50, 720, f"Name: _______________    Date: {current_datetime}")

    # Add Problems
    y = 680
    x_left = 50
    x_right = 300
    decoration_index = 0
    for i, problem in enumerate(problems):
        decoration_path = SPACE_DECORATIONS[decoration_index]
        decoration_index = (decoration_index + 1) % len(SPACE_DECORATIONS)
        decoration = ImageReader(decoration_path)

        if i % 2 == 0:  # Left column
            pdf.drawImage(decoration, x_left - 25, y - 3, width=18, height=18)
            pdf.drawString(x_left, y, f"{i + 1}. {problem}")
        else:  # Right column
            pdf.drawImage(decoration, x_right - 25, y - 3, width=18, height=18)
            pdf.drawString(x_right, y, f"{i + 1}. {problem}")
            y -= 40

    pdf.save()


def create_answer_key(filename, problems, answers):
    """
    Generate a PDF answer key for the given math problems.
    """
    pdf = canvas.Canvas(filename, pagesize=portrait(letter))
    pdf.setFont("Helvetica", 18)

    # Title
    pdf.drawString(200, 750, "Math Worksheet Answer Key")

    # Add Answers
    y = 680
    x_left = 50
    x_right = 300
    for i, (problem, answer) in enumerate(zip(problems, answers)):
        if i % 2 == 0:  # Left column
            pdf.drawString(
                x_left, y, f"{i + 1}. {problem.replace('= _______', f'= {answer}')}"
            )
        else:  # Right column
            pdf.drawString(
                x_right, y, f"{i + 1}. {problem.replace('= _______', f'= {answer}')}"
            )
            y -= 40

    pdf.save()


def main():
    # Generate problems and answers
    problems, answers = generate_math_problems()

    # File paths
    today = datetime.now().strftime("%Y-%m-%d")
    worksheet_filename = f"math_worksheet_{today}.pdf"
    answer_key_filename = f"math_answer_key_{today}.pdf"

    # Create worksheet and answer key
    create_math_worksheet(worksheet_filename, problems)
    create_answer_key(answer_key_filename, problems, answers)

    print(f"Generated worksheet: {worksheet_filename}")
    print(f"Generated answer key: {answer_key_filename}")


if __name__ == "__main__":
    main()
