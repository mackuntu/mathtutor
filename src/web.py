"""Web routes for the MathTutor application."""

import datetime
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

    # Add context processor for template variables
    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.datetime.now().year}

    # Add custom filters
    @app.template_filter("timestamp_to_date")
    def timestamp_to_date(timestamp):
        """Convert a timestamp to a formatted date string."""
        if not timestamp:
            return ""
        return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("Web routes initialized")


if __name__ == "__main__":
    from . import create_app

    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
