"""MathTutor application package."""

import os

from dotenv import load_dotenv
from flask import Flask

from .auth import AuthManager
from .database import get_repository
from .web import init_app as init_web_routes

# Load environment variables
load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

    # Enable debug mode and development environment
    app.debug = os.getenv("FLASK_ENV") == "development"
    app.env = os.getenv("FLASK_ENV", "development")

    # Initialize components
    auth_manager = AuthManager()
    repository = get_repository()

    # Initialize web routes
    init_web_routes(app)

    return app


__all__ = ["create_app"]
