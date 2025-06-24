"""Authentication routes for login, logout, and OAuth handling."""

from starlette.requests import Request
from starlette.responses import Response, RedirectResponse, JSONResponse, HTMLResponse
from starlette.routing import Route

from .auth_backend import AuthBackend, AuthState
from .session_manager import SessionManager
from .user_store import UserStore
from .models import UserRole
from .middleware import get_current_user


class AuthRoutes:
    """Handles authentication-related routes."""

    def __init__(
        self,
        auth_backend: AuthBackend,
        session_manager: SessionManager,
        user_store: UserStore,
        default_role: UserRole = UserRole.VIEWER,
        base_url: str = "",
    ):
        self.auth_backend = auth_backend
        self.session_manager = session_manager
        self.user_store = user_store
        self.default_role = default_role
        self.base_url = base_url
        self.auth_state = AuthState()

    def get_routes(self) -> list[Route]:
        """Get all authentication routes."""
        return [
            Route("/auth/login", self.login_page, methods=["GET"]),
            Route("/auth/callback", self.oauth_callback, methods=["GET"]),
            Route("/auth/logout", self.logout, methods=["GET", "POST"]),
            Route("/auth/user", self.get_current_user_info, methods=["GET"]),
            Route("/auth/status", self.auth_status, methods=["GET"]),
        ]

    async def login_page(self, request: Request) -> Response:
        """Display the login page."""
        # Check if user is already authenticated
        user = get_current_user(request)
        if user:
            # Redirect to home if already authenticated
            return RedirectResponse(url=self.base_url or "/", status_code=302)

        # Generate OAuth URL
        state = self.auth_state.generate_state()
        auth_url = self.auth_backend.get_authorization_url(state)

        # Store state in session for validation
        request.session["oauth_state"] = state

        login_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dagster - Login</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .login-container {{
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                    padding: 3rem;
                    text-align: center;
                    max-width: 400px;
                    width: 100%;
                    margin: 2rem;
                }}
                .logo {{
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 2rem;
                    background: linear-gradient(45deg, #3498db, #2980b9);
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2rem;
                    color: white;
                    font-weight: bold;
                }}
                h1 {{
                    color: #2c3e50;
                    margin-bottom: 0.5rem;
                    font-size: 2rem;
                    font-weight: 600;
                }}
                .subtitle {{
                    color: #7f8c8d;
                    margin-bottom: 2rem;
                    font-size: 1.1rem;
                }}
                .login-button {{
                    background: #333;
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    font-size: 1.1rem;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.8rem;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    width: 100%;
                    justify-content: center;
                    box-sizing: border-box;
                }}
                .login-button:hover {{
                    background: #555;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }}
                .github-icon {{
                    font-size: 1.2rem;
                }}
                .footer {{
                    margin-top: 2rem;
                    color: #95a5a6;
                    font-size: 0.9rem;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">D</div>
                <h1>Welcome to Dagster</h1>
                <p class="subtitle">Please sign in to access your data platform</p>
                
                <a href="{auth_url}" class="login-button">
                    <span class="github-icon">⌘</span>
                    Sign in with GitHub
                </a>
                
                <div class="footer">
                    Secure authentication powered by OAuth 2.0
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(login_html)

    async def oauth_callback(self, request: Request) -> Response:
        """Handle OAuth callback from provider."""
        try:
            # Get code and state from callback
            code = request.query_params.get("code")
            state = request.query_params.get("state")

            if not code or not state:
                return JSONResponse(
                    {"error": "Missing authorization code or state"}, status_code=400
                )

            # Validate state to prevent CSRF
            stored_state = request.session.get("oauth_state")
            if not stored_state or not self.auth_state.validate_state(state):
                return JSONResponse(
                    {"error": "Invalid state parameter"}, status_code=400
                )

            # Clear the stored state
            request.session.pop("oauth_state", None)

            # Exchange code for token
            token_data = self.auth_backend.exchange_code_for_token(code, state)
            access_token = token_data["access_token"]

            # Get user info from provider
            user_info = self.auth_backend.get_user_info(access_token)

            # Check if user already exists
            provider = self.auth_backend.__class__.__name__.lower().replace(
                "oauthbackend", ""
            )
            existing_user = self.user_store.get_user_by_provider_id(
                provider, str(user_info["id"])
            )

            if existing_user:
                # Update existing user's last login
                from datetime import datetime

                existing_user.last_login = datetime.now()
                user = self.user_store.create_or_update_user(existing_user)
            else:
                # Create new user
                user = self.auth_backend.create_user_from_info(
                    user_info, self.default_role
                )
                user = self.user_store.create_or_update_user(user)

            # Create session
            session_id = self.session_manager.create_session(user)

            # Create response with redirect
            redirect_url = self.base_url or "/"
            response = RedirectResponse(url=redirect_url, status_code=302)

            # Set session cookie
            response.set_cookie(
                "dagster_session_id",
                session_id,
                max_age=self.session_manager.session_timeout,
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax",
            )

            return response

        except Exception as e:
            return JSONResponse(
                {"error": f"Authentication failed: {str(e)}"}, status_code=500
            )

    async def logout(self, request: Request) -> Response:
        """Handle user logout."""
        # Get session ID and invalidate it
        session_id = request.cookies.get("dagster_session_id")
        if session_id:
            self.session_manager.invalidate_session(session_id)

        # Create response and clear cookie
        redirect_url = self.base_url + "/auth/login" if self.base_url else "/auth/login"
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.delete_cookie("dagster_session_id")

        return response

    async def get_current_user_info(self, request: Request) -> Response:
        """Get current user information."""
        user = get_current_user(request)
        if not user:
            return JSONResponse({"error": "Not authenticated"}, status_code=401)

        return JSONResponse(
            {
                "user": user.to_dict(),
                "permissions": list(user.permission_checker.get_permissions()),
            }
        )

    async def auth_status(self, request: Request) -> Response:
        """Get authentication status."""
        user = get_current_user(request)

        return JSONResponse(
            {
                "authenticated": user is not None,
                "user": user.to_dict() if user else None,
            }
        )
