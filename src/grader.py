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
        """Main grading function with annotation."""
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

        # Annotate the image
        annotated_image_path = AnswerGrader.annotate_image(
            image,
            transformed_rois,
            student_answers,
            correct_answers,
            total_correct,
            total_questions,
            grade,
        )

        return {
            "total_correct": total_correct,
            "total_questions": total_questions,
            "grade": grade,
            "annotated_image_path": annotated_image_path,
        }


if __name__ == "__main__":
    result = AnswerGrader.grade_worksheet(
        "data/filled_worksheets/math_worksheet_2025-01-11_filled.jpg"
    )
    print(result)
