import sqlite3

import cv2
import numpy as np
import pytesseract
from PIL import Image

from db_handler import DatabaseHandler
from marker_utils import MarkerUtils
from worksheet_pb2 import Worksheet


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
        """Extract and decode QR code from an image using OpenCV."""
        image = cv2.imread(image_path)
        qr_code_detector = cv2.QRCodeDetector()

        # Detect and decode the QR code
        data, _, _ = qr_code_detector.detectAndDecode(image)

        if data:
            return eval(data)  # Assuming QR code contains a dictionary
        else:
            raise ValueError("QR Code not found in image.")

    @staticmethod
    def fetch_answer_key(worksheet_id, version):
        """Fetch correct answers from the database using DatabaseHandler."""
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()
        c.execute(
            "SELECT data FROM worksheets WHERE id = ? AND version = ?",
            (worksheet_id, version),
        )
        result = c.fetchone()
        conn.close()

        if result:
            serialized_data = result[0]
            worksheet = Worksheet()
            worksheet.ParseFromString(serialized_data)
            return worksheet.answers
        else:
            raise ValueError("Worksheet not found in database.")

    @staticmethod
    def parse_student_answers(image_path, rois):
        """Extract handwritten student answers from the image."""
        image = Image.open(image_path)
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

        # Fetch worksheet metadata
        worksheet_metadata = DatabaseHandler.fetch_worksheet(worksheet_id, version)
        template_id = worksheet_metadata.template_id
        correct_answers = worksheet_metadata.answers

        # Fetch ROIs and alignment markers
        rois = DatabaseHandler.fetch_roi_template(template_id)
        image_markers = MarkerUtils.detect_alignment_markers(image_path)

        # Get image dimensions
        image = Image.open(image_path)
        image_width, image_height = image.size

        # Map ROIs to image space
        transformed_rois = MarkerUtils.map_pdf_to_image_space(
            rois, image_markers, (image_width, image_height)
        )

        # Parse student answers
        student_answers = AnswerGrader.parse_student_answers(
            image_path, transformed_rois
        )

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
    result = AnswerGrader.grade_worksheet("math_worksheet_2025-01-05.jpg")
    print(result)
