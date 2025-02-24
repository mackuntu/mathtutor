"""Web interface for math worksheet generation."""

import asyncio
import base64
import logging
import os
import time
from datetime import datetime
from functools import partial
from io import BytesIO

import pyppeteer
from flask import Flask, Response, jsonify, render_template, request, send_file, url_for
from werkzeug.utils import safe_join, secure_filename

from src.document.template import LayoutChoice
from src.generator import ProblemGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MathTutorApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.browser_manager = None

    def init_browser(self):
        """Initialize browser manager if not already initialized."""
        if self.browser_manager is None:
            logger.info("Initializing browser manager...")
            self.browser_manager = BrowserManager()
            self.browser_manager.run_async(self.browser_manager.init_browser())
            logger.info("Browser manager initialized")


class BrowserManager:
    def __init__(self):
        self.browser = None
        self.loop = None
        self.page = None

    async def init_browser(self):
        """Initialize browser if not already running."""
        if not self.browser:
            self.browser = await pyppeteer.launch(
                handleSIGINT=False,
                handleSIGTERM=False,
                handleSIGHUP=False,
                headless=True,
                args=["--no-sandbox", "--disable-gpu"],
            )
            self.page = await self.browser.newPage()
            # Set page size to US Letter
            await self.page.setViewport({"width": 816, "height": 1056})

    async def create_pdf(self, html_content: str) -> bytes:
        """Create PDF using existing page."""
        if not self.browser or not self.page:
            await self.init_browser()

        # Load HTML content
        await self.page.setContent(html_content)
        # Wait for any fonts/resources to load
        await self.page.waitFor(100)

        # Generate PDF
        pdf_data = await self.page.pdf(
            {
                "format": "Letter",
                "margin": {
                    "top": "0.4in",
                    "right": "0.4in",
                    "bottom": "0.4in",
                    "left": "0.4in",
                },
                "printBackground": True,
            }
        )

        return pdf_data

    def get_new_event_loop(self):
        """Get a new event loop for async operations."""
        if not self.loop or self.loop.is_closed():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        return self.loop

    def run_async(self, coro):
        """Run coroutine in the event loop."""
        loop = self.get_new_event_loop()
        return loop.run_until_complete(coro)

    async def cleanup(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        self.page = None
        self.browser = None


# Create Flask app with browser management
app = MathTutorApp(__name__)

# Configure absolute paths
app.config["BASE_DIR"] = os.path.abspath(os.path.dirname(__file__))

# Initialize components
generator = ProblemGenerator()


@app.route("/")
def index():
    """Render the main page."""
    app.init_browser()  # Initialize browser on first request
    return render_template(
        "index.html",
        ages=list(range(6, 10)),  # Ages 6-9
        default_age=6,
        default_difficulty=generator.get_school_year_progress(),
    )


@app.route("/generate", methods=["POST"])
def generate_worksheet():
    """Generate a worksheet or answer key PDF for printing."""
    try:
        start_time = time.time()

        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )
        pdf_type = request.form.get("type", "worksheet")

        # Generate problems
        prob_start = time.time()
        problems, answers = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )
        prob_time = time.time() - prob_start
        logger.info(f"Problem generation took: {prob_time:.2f} seconds")

        # Generate HTML
        html_start = time.time()
        is_answer_key = pdf_type == "answer_key"
        html_content = render_template(
            "worksheet.html",
            problems=[{"text": p} for p in problems],
            answers=answers if is_answer_key else None,
            is_answer_key=is_answer_key,
            is_preview=False,
        )
        html_time = time.time() - html_start
        logger.info(f"HTML generation took: {html_time:.2f} seconds")

        # Generate PDF
        pdf_start = time.time()
        pdf = app.browser_manager.run_async(
            app.browser_manager.create_pdf(html_content)
        )
        pdf_time = time.time() - pdf_start
        logger.info(f"PDF generation took: {pdf_time:.2f} seconds")

        # Create response
        response = Response(pdf, mimetype="application/pdf")
        filename = "answer_key.pdf" if is_answer_key else "worksheet.pdf"
        response.headers["Content-Disposition"] = f'inline; filename="{filename}"'

        total_time = time.time() - start_time
        logger.info(f"Total request took: {total_time:.2f} seconds")

        return response

    except Exception as e:
        logger.error(f"Error generating worksheet: {str(e)}")
        if app.browser_manager:
            app.browser_manager.run_async(app.browser_manager.cleanup())
            app.browser_manager = None
        return {"error": str(e)}, 500


@app.route("/preview", methods=["POST"])
def preview_problems():
    """Generate a preview of problems based on current settings."""
    try:
        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )

        # Generate problems but only use first 5 for preview
        problems, _ = generator.generate_math_problems(age, count, difficulty)
        preview_problems = [{"text": p} for p in problems[:5]]

        # Generate preview HTML
        preview_html = render_template(
            "problem_grid.html", problems=preview_problems, is_preview=True
        )

        return jsonify({"success": True, "html": preview_html})

    except Exception as e:
        return jsonify({"error": str(e), "success": False})


@app.route("/generate_both", methods=["POST"])
def generate_both():
    """Generate both worksheet and answer key PDFs."""
    try:
        start_time = time.time()

        # Get form data
        age = int(request.form["age"])
        count = int(request.form.get("count", 30))
        difficulty = float(
            request.form.get("difficulty", generator.get_school_year_progress())
        )

        # Generate problems (only once for both PDFs)
        prob_start = time.time()
        problems, answers = generator.generate_math_problems(
            age=age,
            count=count,
            difficulty=difficulty,
        )
        prob_time = time.time() - prob_start
        logger.info(f"Problem generation took: {prob_time:.2f} seconds")

        problem_list = [{"text": p} for p in problems]

        # Generate worksheet HTML
        html_start = time.time()
        worksheet_html = render_template(
            "worksheet.html",
            problems=problem_list,
            answers=None,
            is_answer_key=False,
            is_preview=False,
        )

        # Generate answer key HTML
        answer_key_html = render_template(
            "worksheet.html",
            problems=problem_list,
            answers=answers,
            is_answer_key=True,
            is_preview=False,
        )
        html_time = time.time() - html_start
        logger.info(f"HTML generation took: {html_time:.2f} seconds")

        # Generate both PDFs
        pdf_start = time.time()
        worksheet_pdf = app.browser_manager.run_async(
            app.browser_manager.create_pdf(worksheet_html)
        )
        answer_key_pdf = app.browser_manager.run_async(
            app.browser_manager.create_pdf(answer_key_html)
        )
        pdf_time = time.time() - pdf_start
        logger.info(f"PDF generation took: {pdf_time:.2f} seconds")

        # Return both PDFs
        response = jsonify(
            {
                "worksheet": base64.b64encode(worksheet_pdf).decode("utf-8"),
                "answer_key": base64.b64encode(answer_key_pdf).decode("utf-8"),
            }
        )

        total_time = time.time() - start_time
        logger.info(f"Total request took: {total_time:.2f} seconds")

        return response

    except Exception as e:
        logger.error(f"Error generating PDFs: {str(e)}")
        if app.browser_manager:
            app.browser_manager.run_async(app.browser_manager.cleanup())
            app.browser_manager = None
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
