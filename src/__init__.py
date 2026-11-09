"""MathTutor application package."""

import os

from dotenv import load_dotenv
from flask import Flask

from . import config
from .database import init_db
from .web import init_app as init_web_routes

# Load environment variables
load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    on_vercel = bool(os.getenv("VERCEL"))
    if on_vercel:
        for var in ("FLASK_SECRET_KEY", "DATABASE_URL"):
            if not os.getenv(var):
                raise RuntimeError(f"{var} must be set when running on Vercel")

    flask_env = os.getenv("FLASK_ENV", "development")
    app.env = flask_env
    is_production = on_vercel or flask_env == "production"

    if is_production:
        app.secret_key = os.getenv("FLASK_SECRET_KEY")
        app.debug = False
    else:
        app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
        app.debug = flask_env == "development"

    # Load configuration variables from config.py
    for key in dir(config):
        if key.isupper():
            app.config[key] = getattr(config, key)

    # Initialize database
    init_db(app)

    # Initialize web routes
    init_web_routes(app)

    return app


__all__ = ["create_app"]
