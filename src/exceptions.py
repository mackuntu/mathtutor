"""Custom exceptions for the application."""


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""

    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""

    pass


class WorksheetError(Exception):
    """Raised when worksheet operations fail."""

    pass
