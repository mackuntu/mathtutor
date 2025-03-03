"""Routes package for the MathTutor application."""

from flask import Flask

from . import admin, auth, children, pages, subscription, worksheets


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application.

    Args:
        app: The Flask application instance.
    """
    app.register_blueprint(auth.bp)
    app.register_blueprint(children.bp)
    app.register_blueprint(pages.bp)
    app.register_blueprint(worksheets.bp)
    app.register_blueprint(subscription.bp)
    app.register_blueprint(admin.bp)
