from PIL import Image
from pyzbar.pyzbar import decode
import pytesseract
from db_handler import DatabaseHandler
import sqlite3


class AnswerGrader:
    GRADE_SCALE = {
        "A": 90,
        "B": 80,
        "C": 70,
        "D": 60,
        "F": 0,
    }

    @staticmethod
    def extract_qr_code(image_path):
        """Extract and decode QR code from an image."""
        image = Image.open(image_path)
        decoded_data = decode(image)
        if decoded_data:
            qr_data = decoded_data[0].data.decode("utf-8")
            return eval(qr_data)  # Assuming QR code contains a dictionary
        raise ValueError("QR Code not found in image.")

    @staticmethod
    def fetch_answer_key(worksheet_id, version):
        """Fetch correct answers from the database using DatabaseHandler."""
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()
        c.execute(
            "SELECT answers FROM worksheets WHERE id = ? AND version = ?",
            (worksheet_id, version),
        )
        result = c.fetchone()
        conn.close()
        if result:
            return result[0].split(
                ","
            )  # Convert answers from a stored string to a list
        else:
            raise ValueError("Worksheet not found in database.")

    @staticmethod
    def parse_student_answers(image_path):
        """Extract handwritten student answers from the image."""
        image = Image.open(image_path)

        # Define regions of interest (ROIs) for each answer
        # Example coordinates must be calibrated based on worksheet layout
        rois = [
            (100, 200, 400, 250),  # Example ROI for first answer
            # Add more ROIs for each question
        ]

        student_answers = []
        for roi in rois:
            cropped_image = image.crop(roi)
            answer = pytesseract.image_to_string(
                cropped_image, config="--psm 7"
            ).strip()
            student_answers.append(answer)

        return student_answers

    @staticmethod
    def grade_answers(student_answers, correct_answers):
        """Compare student answers with correct answers and calculate grade."""
        total_questions = len(correct_answers)
        total_correct = sum(
            1
            for student, correct in zip(student_answers, correct_answers)
            if student == correct
        )
        percentage = (total_correct / total_questions) * 100

        # Determine letter grade
        for grade, cutoff in AnswerGrader.GRADE_SCALE.items():
            if percentage >= cutoff:
                return total_correct, total_questions, grade

    @staticmethod
    def grade_worksheet(image_path):
        """Main grading function."""
        # Extract QR Code
        qr_data = AnswerGrader.extract_qr_code(image_path)
        worksheet_id, version = qr_data["worksheet_id"], qr_data["version"]

        # Fetch the answer key
        correct_answers = AnswerGrader.fetch_answer_key(worksheet_id, version)

        # Parse student answers
        student_answers = AnswerGrader.parse_student_answers(image_path)

        # Grade answers
        total_correct, total_questions, grade = AnswerGrader.grade_answers(
            student_answers, correct_answers
        )

        return {
            "total_correct": total_correct,
            "total_questions": total_questions,
            "grade": grade,
        }


if __name__ == "__main__":
    AnswerGrader.grade_worksheet(
        "/Users/martinqian/Downloads/math_worksheet_2024-12-30_filled.png"
    )
