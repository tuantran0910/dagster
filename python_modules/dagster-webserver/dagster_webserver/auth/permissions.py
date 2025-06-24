"""Permission system for fine-grained access control."""

from enum import Enum
from typing import Optional
from functools import wraps

from starlette.requests import Request
from starlette.responses import JSONResponse

from .models import User, UserRole, RolePermissions


class Permission(Enum):
    """Enumeration of all permissions in the system."""

    # View permissions
    VIEW_RUNS = "view_runs"
    VIEW_ASSETS = "view_assets"
    VIEW_SCHEDULES = "view_schedules"
    VIEW_SENSORS = "view_sensors"
    VIEW_JOBS = "view_jobs"
    VIEW_LOGS = "view_logs"
    VIEW_WORKSPACE = "view_workspace"

    # Launcher permissions
    LAUNCH_RUNS = "launch_runs"
    TERMINATE_RUNS = "terminate_runs"
    DELETE_RUNS = "delete_runs"
    REEXECUTE_RUNS = "reexecute_runs"

    # Editor permissions
    START_SCHEDULES = "start_schedules"
    STOP_SCHEDULES = "stop_schedules"
    START_SENSORS = "start_sensors"
    STOP_SENSORS = "stop_sensors"
    UPDATE_WORKSPACE = "update_workspace"
    MANAGE_BACKFILLS = "manage_backfills"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_PERMISSIONS = "manage_permissions"
    VIEW_INSTANCE_CONFIG = "view_instance_config"
    MANAGE_INSTANCE_CONFIG = "manage_instance_config"
    ACCESS_ALL_LOCATIONS = "access_all_locations"


def has_permission(user: Optional[User], permission: Permission) -> bool:
    """Check if user has a specific permission."""
    if not user or not user.is_active:
        return False

    return RolePermissions.has_permission(user.role, permission.value)


def check_permission(user: Optional[User], permission: Permission) -> bool:
    """Check permission and raise exception if not authorized."""
    if not has_permission(user, permission):
        raise PermissionError(f"Permission '{permission.value}' required")
    return True


def require_permission(permission: Permission):
    """Decorator to require a specific permission."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]

            if not request:
                raise ValueError("Request object not found in function arguments")

            user = getattr(request.state, "user", None)

            if not has_permission(user, permission):
                return JSONResponse(
                    {"error": f"Permission '{permission.value}' required"},
                    status_code=403,
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(required_role: UserRole):
    """Decorator to require a minimum role level."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]

            if not request:
                raise ValueError("Request object not found in function arguments")

            user = getattr(request.state, "user", None)

            if not user or not user.has_permission(required_role):
                return JSONResponse(
                    {"error": f"Role '{required_role.value}' or higher required"},
                    status_code=403,
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class PermissionChecker:
    """Helper class for checking permissions in different contexts."""

    def __init__(self, user: Optional[User]):
        self.user = user

    def can_view_runs(self) -> bool:
        return has_permission(self.user, Permission.VIEW_RUNS)

    def can_launch_runs(self) -> bool:
        return has_permission(self.user, Permission.LAUNCH_RUNS)

    def can_terminate_runs(self) -> bool:
        return has_permission(self.user, Permission.TERMINATE_RUNS)

    def can_delete_runs(self) -> bool:
        return has_permission(self.user, Permission.DELETE_RUNS)

    def can_reexecute_runs(self) -> bool:
        return has_permission(self.user, Permission.REEXECUTE_RUNS)

    def can_view_assets(self) -> bool:
        return has_permission(self.user, Permission.VIEW_ASSETS)

    def can_manage_schedules(self) -> bool:
        return has_permission(self.user, Permission.START_SCHEDULES) and has_permission(
            self.user, Permission.STOP_SCHEDULES
        )

    def can_manage_sensors(self) -> bool:
        return has_permission(self.user, Permission.START_SENSORS) and has_permission(
            self.user, Permission.STOP_SENSORS
        )

    def can_manage_users(self) -> bool:
        return has_permission(self.user, Permission.MANAGE_USERS)

    def can_view_instance_config(self) -> bool:
        return has_permission(self.user, Permission.VIEW_INSTANCE_CONFIG)

    def can_manage_instance_config(self) -> bool:
        return has_permission(self.user, Permission.MANAGE_INSTANCE_CONFIG)

    def is_admin(self) -> bool:
        return self.user is not None and self.user.role == UserRole.ADMIN

    def get_role(self) -> Optional[UserRole]:
        return self.user.role if self.user else None

    def get_permissions(self) -> set[str]:
        """Get all permissions for the user."""
        if not self.user:
            return set()
        return RolePermissions.get_permissions_for_role(self.user.role)
