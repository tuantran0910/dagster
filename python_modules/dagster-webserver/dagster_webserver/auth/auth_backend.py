"""Authentication backends for different OAuth providers."""

import secrets
import time
from abc import ABC, abstractmethod
from typing import Dict, Any
from urllib.parse import urlencode
import requests
from datetime import datetime

from .models import User, UserRole


class AuthBackend(ABC):
    """Base class for authentication backends."""

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Get the authorization URL to redirect users to."""
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token."""
        pass

    @abstractmethod
    def create_user_from_info(
        self, user_info: Dict[str, Any], default_role: UserRole
    ) -> User:
        """Create a User object from the provider's user info."""
        pass


class GitHubOAuthBackend(AuthBackend):
    """GitHub OAuth authentication backend."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Get GitHub OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",
            "state": state,
            "response_type": "code",
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange GitHub authorization code for access token."""
        token_url = "https://github.com/login/oauth/access_token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Accept": "application/json"}

        response = requests.post(token_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()

        token_data = response.json()
        if "error" in token_data:
            raise ValueError(
                f"OAuth error: {token_data.get('error_description', 'Unknown error')}"
            )

        return token_data

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get GitHub user information."""
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Get user info
        user_response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=30
        )
        user_response.raise_for_status()
        user_data = user_response.json()

        # Get user emails
        email_response = requests.get(
            "https://api.github.com/user/emails", headers=headers, timeout=30
        )
        email_response.raise_for_status()
        emails = email_response.json()

        # Find primary email
        primary_email = None
        for email in emails:
            if email.get("primary", False):
                primary_email = email["email"]
                break

        if not primary_email and emails:
            primary_email = emails[0]["email"]

        user_data["email"] = primary_email
        return user_data

    def create_user_from_info(
        self, user_info: Dict[str, Any], default_role: UserRole
    ) -> User:
        """Create User from GitHub user info."""
        return User(
            username=user_info["login"],
            email=user_info["email"],
            full_name=user_info.get("name"),
            role=default_role,
            provider="github",
            provider_id=str(user_info["id"]),
            avatar_url=user_info.get("avatar_url"),
            created_at=datetime.now(),
            last_login=datetime.now(),
        )


class AuthState:
    """Manages OAuth state for security."""

    def __init__(self):
        self._states: Dict[str, float] = {}  # state -> timestamp
        self._state_timeout = 600  # 10 minutes

    def generate_state(self) -> str:
        """Generate a secure random state."""
        state = secrets.token_urlsafe(32)
        self._states[state] = time.time()
        return state

    def validate_state(self, state: str) -> bool:
        """Validate and consume a state."""
        if state not in self._states:
            return False

        timestamp = self._states.pop(state)

        # Check if state hasn't expired
        if time.time() - timestamp > self._state_timeout:
            return False

        return True

    def cleanup_expired_states(self):
        """Remove expired states."""
        current_time = time.time()
        expired_states = [
            state
            for state, timestamp in self._states.items()
            if current_time - timestamp > self._state_timeout
        ]
        for state in expired_states:
            del self._states[state]
