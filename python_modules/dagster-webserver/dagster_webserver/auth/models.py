"""User models and role definitions for RBAC."""

from enum import Enum
from typing import Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime


class UserRole(Enum):
    """User roles with hierarchical permissions."""

    ADMIN = "admin"
    EDITOR = "editor"
    LAUNCHER = "launcher"
    VIEWER = "viewer"

    @property
    def level(self) -> int:
        """Return role level for hierarchy checks."""
        levels = {
            UserRole.VIEWER: 1,
            UserRole.LAUNCHER: 2,
            UserRole.EDITOR: 3,
            UserRole.ADMIN: 4,
        }
        return levels[self]

    def has_permission_of(self, other_role: "UserRole") -> bool:
        """Check if this role has at least the permissions of another role."""
        return self.level >= other_role.level


@dataclass
class User:
    """User model with authentication and authorization info."""

    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    provider: str  # e.g., 'github'
    provider_id: str  # e.g., github user ID
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required role permissions."""
        return self.is_active and self.role.has_permission_of(required_role)

    @property
    def permission_checker(self):
        """Get permission checker for this user."""
        from .permissions import PermissionChecker
        return PermissionChecker(self)

    def to_dict(self) -> Dict:
        """Convert user to dictionary for serialization."""
        return {
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        """Create user from dictionary."""
        return cls(
            username=data["username"],
            email=data["email"],
            full_name=data.get("full_name"),
            role=UserRole(data["role"]),
            provider=data["provider"],
            provider_id=data["provider_id"],
            avatar_url=data.get("avatar_url"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
            last_login=datetime.fromisoformat(data["last_login"])
            if data.get("last_login")
            else None,
            is_active=data.get("is_active", True),
        )


class RolePermissions:
    """Defines permissions for each role."""

    # Base permissions for each role
    ROLE_PERMISSIONS = {
        UserRole.VIEWER: {
            "view_runs",
            "view_assets",
            "view_schedules",
            "view_sensors",
            "view_jobs",
            "view_logs",
            "view_workspace",
        },
        UserRole.LAUNCHER: {
            "launch_runs",
            "terminate_runs",
            "delete_runs",
            "reexecute_runs",
        },
        UserRole.EDITOR: {
            "start_schedules",
            "stop_schedules",
            "start_sensors",
            "stop_sensors",
            "update_workspace",
            "manage_backfills",
        },
        UserRole.ADMIN: {
            "manage_users",
            "manage_permissions",
            "view_instance_config",
            "manage_instance_config",
            "access_all_locations",
        },
    }

    @classmethod
    def get_permissions_for_role(cls, role: UserRole) -> Set[str]:
        """Get all permissions for a role (including inherited permissions)."""
        permissions = set()

        # Add permissions for this role and all lower roles
        for r in UserRole:
            if role.has_permission_of(r):
                permissions.update(cls.ROLE_PERMISSIONS.get(r, set()))

        return permissions

    @classmethod
    def has_permission(cls, user_role: UserRole, permission: str) -> bool:
        """Check if a role has a specific permission."""
        user_permissions = cls.get_permissions_for_role(user_role)
        return permission in user_permissions
