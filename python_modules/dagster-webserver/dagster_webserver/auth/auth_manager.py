"""Authentication manager to coordinate all auth components."""

from typing import Optional, Dict, Any, List
from pathlib import Path

from .models import UserRole
from .auth_backend import AuthBackend, GitHubOAuthBackend
from .session_manager import SessionManager
from .user_store import UserStore
from .middleware import AuthenticationMiddleware
from .routes import AuthRoutes


class AuthManager:
    """Manages authentication system for Dagster webserver."""

    def __init__(
        self,
        auth_config: Dict[str, Any],
        storage_dir: str,
        base_url: str = "",
    ):
        self.auth_config = auth_config
        self.storage_dir = Path(storage_dir)
        self.base_url = base_url

        # Create storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.auth_backend = self._create_auth_backend()
        self.session_manager = self._create_session_manager()
        self.user_store = self._create_user_store()
        self.middleware = self._create_middleware()
        self.routes = self._create_routes()

    def _create_auth_backend(self) -> AuthBackend:
        """Create authentication backend based on configuration."""
        provider = self.auth_config.get("provider", "github")

        if provider == "github":
            client_id = self.auth_config.get("github", {}).get("client_id")
            client_secret = self.auth_config.get("github", {}).get("client_secret")
            redirect_uri = self.auth_config.get("github", {}).get("redirect_uri")

            if not all([client_id, client_secret, redirect_uri]):
                raise ValueError(
                    "GitHub OAuth requires client_id, client_secret, and redirect_uri"
                )

            return GitHubOAuthBackend(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
            )
        else:
            raise ValueError(f"Unsupported authentication provider: {provider}")

    def _create_session_manager(self) -> SessionManager:
        """Create session manager."""
        session_timeout = self.auth_config.get("session_timeout", 24 * 3600)  # 24 hours
        return SessionManager(session_timeout=session_timeout)

    def _create_user_store(self) -> UserStore:
        """Create user store."""
        users_file = self.storage_dir / "users.json"
        role_assignments = self.auth_config.get("role_assignments", {})

        return UserStore(
            storage_path=str(users_file),
            role_assignments=role_assignments,
        )

    def _create_middleware(self) -> AuthenticationMiddleware:
        """Create authentication middleware."""
        login_url = f"{self.base_url}/auth/login"
        public_paths = self.auth_config.get("public_paths", [])

        return AuthenticationMiddleware(
            app=None,  # Will be set when creating the app
            session_manager=self.session_manager,
            user_store=self.user_store,
            login_url=login_url,
            public_paths=public_paths,
        )

    def _create_routes(self) -> AuthRoutes:
        """Create authentication routes."""
        default_role_str = self.auth_config.get("default_role", "viewer")
        try:
            default_role = UserRole(default_role_str.lower())
        except ValueError:
            default_role = UserRole.VIEWER

        return AuthRoutes(
            auth_backend=self.auth_backend,
            session_manager=self.session_manager,
            user_store=self.user_store,
            default_role=default_role,
            base_url=self.base_url,
        )

    def get_middleware(self) -> AuthenticationMiddleware:
        """Get the authentication middleware."""
        return self.middleware

    def get_auth_routes(self) -> List:
        """Get the authentication routes."""
        return self.routes.get_routes()

    def update_role_assignments(self, role_assignments: Dict[str, str]):
        """Update role assignments configuration."""
        self.auth_config["role_assignments"] = role_assignments
        self.user_store.update_role_assignments(role_assignments)

    def get_stats(self) -> Dict[str, Any]:
        """Get authentication system statistics."""
        return {
            "active_sessions": self.session_manager.get_active_session_count(),
            "total_users": len(self.user_store.list_users()),
            "users_by_role": {
                role.value: count
                for role, count in self.user_store.count_users_by_role().items()
            },
            "provider": self.auth_config.get("provider"),
        }

    def cleanup(self):
        """Cleanup authentication resources."""
        self.session_manager.cleanup_expired_sessions()


def create_auth_manager_from_instance_config(
    instance_config: Dict[str, Any],
    storage_dir: str,
    base_url: str = "",
) -> Optional[AuthManager]:
    """Create AuthManager from Dagster instance configuration."""
    auth_config = instance_config.get("authentication")

    if not auth_config or not auth_config.get("enabled", False):
        return None

    return AuthManager(
        auth_config=auth_config,
        storage_dir=storage_dir,
        base_url=base_url,
    )
