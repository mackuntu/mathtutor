"""Configuration settings for the application."""

import os
from typing import Dict, TypedDict


class OAuthConfig(TypedDict):
    """OAuth provider configuration."""

    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: str


# Social login configuration
OAUTH_PROVIDERS: Dict[str, OAuthConfig] = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
    },
}

# Flask configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")

# OAuth redirect URI
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", "http://localhost:8080/auth/oauth/callback"
)


def _parse_emails(raw: str) -> tuple[str, ...]:
    return tuple(e.strip().lower() for e in raw.split(",") if e.strip())


def owner_email() -> str | None:
    """First ALLOWED_EMAILS entry (the owner identity), read at call time."""
    emails = _parse_emails(os.environ.get("ALLOWED_EMAILS", ""))
    return emails[0] if emails else None


def allowed_emails() -> frozenset[str]:
    """Emails permitted to log in, read at call time. Empty means nobody."""
    return frozenset(_parse_emails(os.environ.get("ALLOWED_EMAILS", "")))


ALLOWED_EMAILS: frozenset[str] = allowed_emails()
OWNER_EMAIL: str | None = owner_email()
