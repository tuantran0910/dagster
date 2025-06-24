"""Authentication and authorization module for Dagster webserver."""

from .models import User, UserRole
from .auth_backend import AuthBackend, GitHubOAuthBackend
from .middleware import AuthenticationMiddleware
from .permissions import Permission, has_permission, check_permission
from .context import AuthenticatedWorkspaceRequestContext
from .auth_manager import AuthManager, create_auth_manager_from_instance_config

__all__ = [
    "User",
    "UserRole",
    "AuthBackend",
    "GitHubOAuthBackend",
    "AuthenticationMiddleware",
    "Permission",
    "has_permission",
    "check_permission",
    "AuthenticatedWorkspaceRequestContext",
    "AuthManager",
    "create_auth_manager_from_instance_config",
]
