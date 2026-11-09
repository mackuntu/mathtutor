"""MathTutor application package."""

import os

from dotenv import load_dotenv

# Load .env before importing modules that read the environment at import time.
# Real environment variables (e.g. Vercel's) win over .env values.
load_dotenv(override=False)

import logging  # noqa: E402

from flask import Flask  # noqa: E402

from . import config  # noqa: E402
from .database import db as db_module  # noqa: E402
from .database import init_db  # noqa: E402
from .web import init_app as init_web_routes  # noqa: E402


def create_app():
    """Create and configure the Flask application."""
    # No-op when the root logger already has handlers (e.g. under pytest).
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)

    on_vercel = bool(os.getenv("VERCEL"))
    if on_vercel:
        if not os.getenv("FLASK_SECRET_KEY"):
            raise RuntimeError("FLASK_SECRET_KEY must be set when running on Vercel")
        if not db_module.database_url():
            raise RuntimeError("DATABASE_URL must be set when running on Vercel")

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
