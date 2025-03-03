"""MathTutor application package."""

import os

from dotenv import load_dotenv
from flask import Flask

from . import config
from .auth import AuthManager
from .database import get_repository, init_db
from .web import init_app as init_web_routes

# Load environment variables
load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Set environment
    flask_env = os.getenv("FLASK_ENV", "development")
    app.env = flask_env

    # Load appropriate configuration
    if flask_env == "production":
        app.secret_key = os.getenv("FLASK_SECRET_KEY")
        app.debug = False
        # In production, we don't need to load .env file as environment variables
        # are set by the deployment platform
    else:
        app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
        app.debug = flask_env == "development"

    # Load configuration variables from config.py
    for key in dir(config):
        if key.isupper():
            app.config[key] = getattr(config, key)

    # Initialize components
    auth_manager = AuthManager()
    repository = get_repository()

    # Initialize database
    init_db(app)

    # Initialize web routes
    init_web_routes(app)

    return app


__all__ = ["create_app"]
