"""Authentication middleware for Dagster webserver."""

from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse, JSONResponse
from starlette.types import ASGIApp

from .models import User
from .session_manager import SessionManager
from .user_store import UserStore


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for all requests."""

    def __init__(
        self,
        app: ASGIApp,
        session_manager: SessionManager,
        user_store: UserStore,
        login_url: str = "/auth/login",
        public_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.session_manager = session_manager
        self.user_store = user_store
        self.login_url = login_url

        # Default public paths that don't require authentication
        self.public_paths = public_paths or [
            "/auth/login",
            "/auth/callback",
            "/auth/logout",
            "/server_info",
            "/dagit_info",
            "/favicon.ico",
            "/favicon.png",
            "/favicon.svg",
            "/robots.txt",
        ]

        # Static file patterns that should be public
        self.public_patterns = [
            "/static/",
            "/vendor/",
            "/.css",
            "/.js",
            "/.png",
            "/.jpg",
            "/.jpeg",
            "/.gif",
            "/.svg",
            "/.ico",
            "/.woff",
            "/.woff2",
            "/.ttf",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process authentication for each request."""

        # Check if this is a public path
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Get user from session
        user = self._get_authenticated_user(request)

        # Add user to request state
        request.state.user = user

        # If user is not authenticated, handle based on request type
        if not user:
            return await self._handle_unauthenticated_request(request)

        # User is authenticated, proceed with request
        response = await call_next(request)

        # Cleanup expired sessions periodically
        self.session_manager.cleanup_expired_sessions()

        return response

    def _is_public_path(self, path: str) -> bool:
        """Check if the path is public and doesn't require authentication."""
        # Check exact matches
        if path in self.public_paths:
            return True

        # Check patterns
        for pattern in self.public_patterns:
            if pattern in path:
                return True

        return False

    def _get_authenticated_user(self, request: Request) -> Optional[User]:
        """Get authenticated user from request."""
        # Try to get session ID from cookie
        session_id = request.cookies.get("dagster_session_id")
        if not session_id:
            return None

        # Get user from session
        user = self.session_manager.get_user_from_session(session_id)
        if not user:
            return None

        # Verify user still exists and is active
        stored_user = self.user_store.get_user(user.username)
        if not stored_user or not stored_user.is_active:
            # Invalidate session if user no longer exists or is inactive
            self.session_manager.invalidate_session(session_id)
            return None

        return stored_user

    async def _handle_unauthenticated_request(self, request: Request) -> Response:
        """Handle unauthenticated requests."""
        # For API/GraphQL requests, return 401
        if (
            request.url.path.startswith("/graphql")
            or request.url.path.startswith("/api/")
            or "application/json" in request.headers.get("accept", "")
        ):
            return JSONResponse(
                {"error": "Authentication required", "login_url": self.login_url},
                status_code=401,
            )

        # For web requests, redirect to login
        return RedirectResponse(url=self.login_url, status_code=302)


def get_current_user(request: Request) -> Optional[User]:
    """Helper function to get current user from request."""
    return getattr(request.state, "user", None)
