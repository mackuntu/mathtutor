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
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# OAuth redirect URI
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", "http://localhost:8080/auth/oauth/callback"
)
