"""Authentication manager for the MathTutor application."""

import logging
import os
import secrets
import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

import requests

from .config import OAUTH_PROVIDERS, OAUTH_REDIRECT_URI, allowed_emails
from .database import get_repository
from .database.models import Session, User

# Configure logging
logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _email_permitted(email: str) -> bool:
    """Whether a session for ``email`` may still be used.

    The allowlist is enforced on Vercel (where an empty list admits nobody) and
    wherever ALLOWED_EMAILS is set, so removing an email takes effect at once.
    Local dev without an allowlist keeps working for /auth/test-auth.
    """
    allowed = allowed_emails()
    if not allowed and not os.environ.get("VERCEL"):
        return True
    return email.strip().lower() in allowed


class AuthManager:
    """Authentication manager."""

    def __init__(self):
        """Initialize the auth manager."""
        self.repository = get_repository()

    def get_oauth_url(self, provider: str, state: str) -> str:
        """Get OAuth URL for the specified provider."""
        if provider not in OAUTH_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        config = OAUTH_PROVIDERS[provider]
        params = {
            "client_id": config["client_id"],
            "redirect_uri": OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": config["scope"],
            "state": state,
        }

        return f"{config['authorize_url']}?{urlencode(params)}"

    def verify_oauth_token(
        self, provider: str, token: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Verify OAuth token and get user info."""
        if provider not in OAUTH_PROVIDERS:
            return False, None

        try:
            if provider == "google":
                return self._verify_google_token(token)

            return False, None
        except Exception as e:
            logger.error(f"Error verifying {provider} token: {str(e)}")
            return False, None

    def _verify_google_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify Google OAuth token."""
        try:
            response = requests.get(
                OAUTH_PROVIDERS["google"]["userinfo_url"],
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            userinfo = response.json()
            email = userinfo["email"]
            return True, {
                "email": email,
                "name": userinfo.get("name") or email,
                "picture": userinfo.get("picture"),
                "email_verified": userinfo.get("email_verified"),
            }
        except Exception as e:
            logger.error(f"Error verifying Google token: {str(e)}")
            return False, None

    def exchange_code_for_token(self, provider: str, code: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        if provider not in OAUTH_PROVIDERS:
            return None

        config = OAUTH_PROVIDERS[provider]
        try:
            data = {
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "code": code,
                "redirect_uri": OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            }

            response = requests.post(config["token_url"], data=data)
            response.raise_for_status()
            return response.json().get("access_token") or response.json().get(
                "id_token"
            )
        except Exception as e:
            logger.error(f"Error exchanging code for {provider} token: {str(e)}")
            return None

    def get_or_create_user(
        self, email: str, name: str, picture: Optional[str] = None
    ) -> User:
        """Get or create a user atomically (safe against concurrent first logins).

        A row whose name is still its email (created by a device-token request
        before the owner ever logged in) takes the real profile name/picture.
        """
        self.repository.create_user_if_absent(
            User(email=email, name=name, picture=picture)
        )
        user = self.repository.get_user_by_email(email)
        if user.name != user.email or name == email:
            return user
        profiled = User(email=email, name=name, picture=picture)
        profiled.created_at = user.created_at
        self.repository.update_user(profiled)
        return profiled

    def create_session(self, user_email: str) -> str:
        """Create a new session."""
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        self.repository.delete_expired_sessions(now)
        expires_at = now + SESSION_TTL_SECONDS
        session = Session(token=token, user_email=user_email, expires_at=expires_at)
        self.repository.create_session(session)
        return token

    def validate_session(self, token: Optional[str]) -> Optional[User]:
        """Validate a session token."""
        if not token:
            return None

        session = self.repository.get_session(token)
        if not session:
            return None

        if session.expires_at < int(time.time()) or not _email_permitted(
            session.user_email
        ):
            self.repository.delete_session(token)
            return None

        return self.repository.get_user_by_email(session.user_email)

    def logout(self, token: str) -> None:
        """Log out a user by deleting their session."""
        self.repository.delete_session(token)
