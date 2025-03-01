"""Web routes for the MathTutor application."""

import logging

from flask import Blueprint, Flask

from .routes import register_blueprints

# Configure logging
logger = logging.getLogger(__name__)

# Create a legacy blueprint for backward compatibility
bp = Blueprint("web", __name__, url_prefix="")


def init_app(app: Flask) -> None:
    """Initialize the web routes for the application.

    Args:
        app: The Flask application instance.
    """
    # Register all blueprints
    register_blueprints(app)

    # Register the legacy blueprint
    app.register_blueprint(bp)

    logger.info("Web routes initialized")


if __name__ == "__main__":
    from . import create_app

    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
