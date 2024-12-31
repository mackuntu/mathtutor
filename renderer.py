from reportlab.lib.pagesizes import letter, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import qrcode
from io import BytesIO


class WorksheetRenderer:
    SPACE_DECORATIONS = [
        "assets/rocket.png",
        "assets/moon.png",
        "assets/star.png",
        "assets/shining_star.png",
        "assets/planet.png",
        "assets/galaxy.png"
    ]

    @staticmethod
    def create_qr_code(worksheet_id, version):
        """
        Generate a QR code for the worksheet ID and version.
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data({"worksheet_id": worksheet_id, "version": version})
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        byte_stream = BytesIO()
        qr_image.save(byte_stream, format="PNG")
        byte_stream.seek(0)
        return byte_stream

    @staticmethod
    def create_math_worksheet(filename, problems, worksheet_id, version, qr_code_stream):
        pdf = canvas.Canvas(filename, pagesize=portrait(letter))
        pdf.setFont("Helvetica", 18)

        # Render worksheet header
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.drawString(200, 750, "Math Worksheet")
        pdf.drawString(50, 720, f"Name: _______________    Date: {current_datetime}")
        pdf.drawImage(ImageReader(qr_code_stream), 550, 700, width=40, height=40)

        y_positions = {"left": 680, "right": 680}
        x_positions = {"left": 50, "right": 300}
        columns = {"left": problems[:len(problems) // 2], "right": problems[len(problems) // 2:]}

        decoration_index = 0

        def draw_problem(pdf, column, y, x, problem, index):
            nonlocal decoration_index
            decoration_path = WorksheetRenderer.SPACE_DECORATIONS[decoration_index]
            decoration_index = (decoration_index + 1) % len(WorksheetRenderer.SPACE_DECORATIONS)
            decoration = ImageReader(decoration_path)

            pdf.drawImage(decoration, x - 30, y - 3, width=18, height=18)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x, y, f"{index}.")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(x + 20, y, problem)

        for column, problems_list in columns.items():
            for i, problem in enumerate(problems_list):
                y = y_positions[column]
                x = x_positions[column]
                index = i + 1 if column == "left" else i + 1 + len(columns["left"])

                draw_problem(pdf, column, y, x, problem, index)

                y_positions[column] -= 40

                if y_positions[column] < 50:
                    pdf.showPage()
                    y_positions[column] = 750

        pdf.save()

    @staticmethod
    def create_answer_key(filename, problems, answers, worksheet_id, version, qr_code_stream):
        """
        Create a PDF answer key for the given math problems.
        """
        pdf = canvas.Canvas(filename, pagesize=portrait(letter))
        pdf.setFont("Helvetica", 18)

        # Title and QR code
        pdf.drawString(200, 750, "Math Worksheet Answer Key")
        pdf.drawString(50, 720, f"Worksheet ID: {worksheet_id}")
        pdf.drawImage(ImageReader(qr_code_stream), 550, 700, width=40, height=40)

        y_positions = {"left": 680, "right": 680}
        x_positions = {"left": 50, "right": 300}
        columns = {"left": list(zip(problems[:len(problems) // 2], answers[:len(problems) // 2])),
                   "right": list(zip(problems[len(problems) // 2:], answers[len(problems) // 2:]))}

        def draw_answer(pdf, column, y, x, problem, answer, index):
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x, y, f"{index}.")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(x + 20, y, problem.replace("= _______", f"= {answer}"))

        for column, problem_answer_list in columns.items():
            for i, (problem, answer) in enumerate(problem_answer_list):
                y = y_positions[column]
                x = x_positions[column]
                index = i + 1 if column == "left" else i + 1 + len(columns["left"])

                draw_answer(pdf, column, y, x, problem, answer, index)

                y_positions[column] -= 40

                if y_positions[column] < 50:
                    pdf.showPage()
                    y_positions[column] = 750

        pdf.save()
