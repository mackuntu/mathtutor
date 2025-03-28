"""Production configuration settings for the application."""

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
    "facebook": {
        "client_id": os.getenv("FACEBOOK_CLIENT_ID", ""),
        "client_secret": os.getenv("FACEBOOK_CLIENT_SECRET", ""),
        "authorize_url": "https://www.facebook.com/v12.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v12.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email,picture",
        "scope": "email public_profile",
    },
    "x": {
        "client_id": os.getenv("X_CLIENT_ID", ""),
        "client_secret": os.getenv("X_CLIENT_SECRET", ""),
        "authorize_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "userinfo_url": "https://api.twitter.com/2/users/me",
        "scope": "users.read tweet.read",
    },
}

# DynamoDB configuration - in production, we use the default endpoint
DYNAMODB_ENDPOINT = None  # Use default AWS endpoint
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Flask configuration
FLASK_ENV = "production"
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# OAuth redirect URI - use the production URL
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")
