"""Authenticated workspace request context."""

from typing import Optional, Mapping

from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.permissions import PermissionResult

from .models import User
from .permissions import PermissionChecker, has_permission, Permission


class AuthenticatedWorkspaceRequestContext(WorkspaceRequestContext):
    """Workspace request context with authentication information."""

    def __init__(self, *args, user: Optional[User] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        self._permission_checker = PermissionChecker(user)

    @property
    def user(self) -> Optional[User]:
        """Get the authenticated user."""
        return self._user

    @property
    def permission_checker(self) -> PermissionChecker:
        """Get the permission checker for this user."""
        return self._permission_checker

    @property
    def permissions(self) -> Mapping[str, PermissionResult]:
        """Override permissions based on user's role."""
        if not self._user:
            # No user, return all permissions as disabled
            return {
                perm.value: PermissionResult(
                    enabled=False, message="Authentication required"
                )
                for perm in Permission
            }

        user_permissions = self._permission_checker.get_permissions()

        return {
            perm.value: PermissionResult(
                enabled=perm.value in user_permissions,
                message=""
                if perm.value in user_permissions
                else f"Role '{self._user.role.value}' does not have this permission",
            )
            for perm in Permission
        }

    def permissions_for_location(
        self, *, location_name: str
    ) -> Mapping[str, PermissionResult]:
        """Override location-specific permissions based on user's role."""
        # For now, use the same permissions for all locations
        # This can be extended to support location-specific permissions
        return self.permissions

    def has_permission(self, permission: str) -> bool:
        """Check if the user has a specific permission."""
        if not self._user:
            return False

        try:
            perm = Permission(permission)
            return has_permission(self._user, perm)
        except ValueError:
            # Unknown permission, default to False
            return False

    def get_viewer_tags(self) -> dict[str, str]:
        """Get tags to identify the current viewer."""
        if not self._user:
            return {}

        return {
            "dagster.user.username": self._user.username,
            "dagster.user.email": self._user.email,
            "dagster.user.role": self._user.role.value,
            "dagster.user.provider": self._user.provider,
        }

    def get_reporting_user_tags(self) -> dict[str, str]:
        """Get tags for reporting purposes."""
        if not self._user:
            return {}

        return {
            "user": self._user.username,
            "user_email": self._user.email,
            "user_role": self._user.role.value,
        }

    @property
    def show_instance_config(self) -> bool:
        """Determine if instance config should be shown to the user."""
        return has_permission(self._user, Permission.VIEW_INSTANCE_CONFIG)

    def is_read_only_for_location(self, location_name: str) -> bool:
        """Check if a location is read-only for the current user."""
        # Users with only view permissions should have read-only access
        if not self._user:
            return True

        # Viewers and below get read-only access
        from .models import UserRole

        return not self._user.has_permission(UserRole.LAUNCHER)

    def can_terminate_runs(self) -> bool:
        """Check if user can terminate runs."""
        return has_permission(self._user, Permission.TERMINATE_RUNS)

    def can_delete_runs(self) -> bool:
        """Check if user can delete runs."""
        return has_permission(self._user, Permission.DELETE_RUNS)

    def can_launch_runs(self) -> bool:
        """Check if user can launch runs."""
        return has_permission(self._user, Permission.LAUNCH_RUNS)

    def can_manage_schedules(self) -> bool:
        """Check if user can manage schedules."""
        return has_permission(
            self._user, Permission.START_SCHEDULES
        ) and has_permission(self._user, Permission.STOP_SCHEDULES)

    def can_manage_sensors(self) -> bool:
        """Check if user can manage sensors."""
        return has_permission(self._user, Permission.START_SENSORS) and has_permission(
            self._user, Permission.STOP_SENSORS
        )
