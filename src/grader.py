import sqlite3

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from data.worksheet_pb2 import Worksheet
from db_handler import DatabaseHandler
from utils.marker_utils import MarkerUtils


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
        """Extract QR code data from the image."""
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Try to detect QR code
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(gray)

        if not data:
            raise ValueError("No QR code found in image")

        # Return the worksheet ID directly
        return data

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
    def parse_student_answers(image_path, rois, model_dir="src/model/trained_model"):
        # Load model and processor from the saved directory
        processor = TrOCRProcessor.from_pretrained(model_dir)
        model = VisionEncoderDecoderModel.from_pretrained(model_dir)

        # Set the model to evaluation mode
        model.eval()
        print(f"Trained model and processor loaded from {model_dir}")
        """Extract handwritten student answers from the image with ROI visualization."""
        image = Image.open(image_path)
        student_answers = []
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=24)

        for roi in rois:
            x1, y1, x2, y2 = roi
            cropped_image = image.crop(roi)
            # Preprocess image
            pixel_values = processor(
                images=cropped_image, return_tensors="pt"
            ).pixel_values

            # Generate text
            generated_ids = model.generate(pixel_values)
            answer = processor.batch_decode(generated_ids, skip_special_tokens=True)[
                0
            ].strip()
            student_answers.append(answer)

            # Visualize ROI on the image
            draw.rectangle([x1, y1, x2, y2], outline="blue", width=2)
            draw.text((x1, y1 + 20), f"{answer}", fill="blue", font=font)

        # Show the annotated image for debugging
        image.show()

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
    def annotate_image(
        image,
        transformed_rois,
        student_answers,
        correct_answers,
        total_correct,
        total_questions,
        grade,
    ):
        """
        Annotate the image with parsed answers, correctness, and grade tally.

        Args:
            image (PIL.Image): The image to annotate.
            transformed_rois (list): List of transformed ROIs in image space.
            student_answers (list): List of student answers.
            correct_answers (list): List of correct answers.
            total_correct (int): Total number of correct answers.
            total_questions (int): Total number of questions.
            grade (str): The grade based on the score.

        Returns:
            str: Path to the annotated image.
        """
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=24)

        # Add the tally and grade at the top
        tally_text = f"{total_correct} / {total_questions} correct, Grade: {grade}"
        draw.text((20, 20), tally_text, fill="red", font=font)

        # Annotate each ROI with the student's answer and correctness
        for roi, student_answer, correct_answer in zip(
            transformed_rois, student_answers, correct_answers
        ):
            x1, y1, x2, y2 = roi
            correctness = "X" if student_answer != correct_answer else ""
            annotation = f"{correctness} Answered: {student_answer}"
            if student_answer != correct_answer:
                annotation += f" Correct: {correct_answer}"

            draw.text(
                (x1 + 200, (y2 + y1) / 2), annotation, fill="red", font=font
            )  # Offset to the right of ROI

        # Save the annotated image
        annotated_image_path = image.filename.replace(".jpg", "_graded.jpg")
        image.save(annotated_image_path)
        image.show()
        return annotated_image_path

    @staticmethod
    def grade_worksheet(image_path):
        """Grade a filled worksheet image."""
        # Extract worksheet ID from QR code
        worksheet_id = AnswerGrader.extract_qr_code(image_path)

        # Fetch worksheet data from database
        worksheet = DatabaseHandler.fetch_worksheet(worksheet_id, "1.0")
        if not worksheet:
            raise ValueError(f"Worksheet {worksheet_id} not found in database")

        # Get ROI template
        rois = DatabaseHandler.fetch_roi_template(worksheet.template_id)
        if not rois:
            raise ValueError(f"ROI template {worksheet.template_id} not found")

        # Detect alignment markers
        try:
            image_markers = MarkerUtils.detect_alignment_markers(image_path)
        except Exception as e:
            print(f"Debug: Failed to detect markers: {str(e)}")
            raise

        # Get image dimensions
        image = cv2.imread(image_path)
        image_height, image_width = image.shape[:2]

        # Transform ROIs from PDF to image space
        transformed_rois = MarkerUtils.map_pdf_to_image_space(
            rois, image_markers, (image_width, image_height), visualize=True
        )

        # Extract student answers from ROIs
        student_answers = AnswerGrader.parse_student_answers(
            image_path, transformed_rois
        )

        # Grade the answers
        total_correct, total_questions, grade = AnswerGrader.grade_answers(
            student_answers, worksheet.answers
        )

        return {
            "worksheet_id": worksheet_id,
            "total_correct": total_correct,
            "total_questions": total_questions,
            "grade": grade,
            "student_answers": student_answers,
            "correct_answers": worksheet.answers,
        }


if __name__ == "__main__":
    result = AnswerGrader.grade_worksheet(
        "data/filled_worksheets/math_worksheet_2025-01-11_filled.jpg"
    )
    print(result)
