"""Authentication manager for the MathTutor application."""

import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union
from urllib.parse import urlencode

import requests
from flask import session
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .config import OAUTH_PROVIDERS, OAUTH_REDIRECT_URI
from .database import get_repository
from .database.models import Session, User

# Configure logging
logger = logging.getLogger(__name__)


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

        # Add provider-specific parameters
        if provider == "x":
            params["code_challenge"] = self._generate_code_challenge()
            params["code_challenge_method"] = "S256"

        return f"{config['authorize_url']}?{urlencode(params)}"

    def verify_oauth_token(
        self, provider: str, token: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Verify OAuth token and get user info."""
        if provider not in OAUTH_PROVIDERS:
            return False, None

        config = OAUTH_PROVIDERS[provider]

        try:
            if provider == "google":
                return self._verify_google_token(token)
            elif provider == "facebook":
                return self._verify_facebook_token(token)
            elif provider == "x":
                return self._verify_x_token(token)

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
            return True, {
                "email": userinfo["email"],
                "name": userinfo["name"],
                "picture": userinfo.get("picture"),
            }
        except Exception as e:
            logger.error(f"Error verifying Google token: {str(e)}")
            return False, None

    def _verify_facebook_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify Facebook OAuth token."""
        try:
            response = requests.get(
                OAUTH_PROVIDERS["facebook"]["userinfo_url"],
                params={"access_token": token},
            )
            response.raise_for_status()
            data = response.json()
            return True, {
                "email": data["email"],
                "name": data["name"],
                "picture": data.get("picture", {}).get("data", {}).get("url"),
            }
        except Exception as e:
            logger.error(f"Error verifying Facebook token: {str(e)}")
            return False, None

    def _verify_x_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify X (Twitter) OAuth token."""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
            }
            response = requests.get(
                OAUTH_PROVIDERS["x"]["userinfo_url"], headers=headers
            )
            response.raise_for_status()
            data = response.json()
            return True, {
                "email": data["data"]["email"],
                "name": data["data"]["name"],
                "picture": data["data"].get("profile_image_url"),
            }
        except Exception as e:
            logger.error(f"Error verifying X token: {str(e)}")
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

            # Add provider-specific parameters
            if provider == "x":
                data["code_verifier"] = self._get_code_verifier()

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
        """Get or create a user."""
        user = self.repository.get_user_by_email(email)
        if not user:
            user = User(email=email, name=name, picture=picture)
            self.repository.create_user(user)
        return user

    def create_session(self, user_email: str) -> str:
        """Create a new session."""
        token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + (7 * 24 * 60 * 60)  # 7 days
        session = Session(token=token, user_email=user_email, expires_at=expires_at)
        self.repository.create_session(session)
        return token

    def validate_session(self, token: Optional[str]) -> Optional[User]:
        """Validate a session token."""
        if not token:
            return None

        session = self.repository.get_session(token)
        if not session or session.expires_at < int(time.time()):
            return None

        return self.repository.get_user_by_email(session.user_email)

    def logout(self, token: str) -> None:
        """Log out a user by deleting their session."""
        self.repository.delete_session(token)

    def _generate_code_challenge(self) -> str:
        """Generate a code challenge for PKCE."""
        verifier = secrets.token_urlsafe(32)
        session["code_verifier"] = verifier
        # In a real implementation, you would hash the verifier
        return verifier

    def _get_code_verifier(self) -> str:
        """Get the code verifier from the session."""
        return session.pop("code_verifier", "")
