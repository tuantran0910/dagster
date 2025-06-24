"""User storage and management."""

import json
from typing import Dict, List, Optional
from pathlib import Path
import threading

from .models import User, UserRole


class UserStore:
    """Stores and manages user data and role assignments."""

    def __init__(
        self, storage_path: str, role_assignments: Optional[Dict[str, str]] = None
    ):
        self.storage_path = Path(storage_path)
        self.role_assignments = role_assignments or {}
        self._users: Dict[str, User] = {}
        self._lock = threading.RLock()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_users()

    def _load_users(self):
        """Load users from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    users_data = json.load(f)
                    for username, user_data in users_data.items():
                        self._users[username] = User.from_dict(user_data)
            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                self._users = {}

    def _save_users(self):
        """Save users to storage file."""
        users_data = {
            username: user.to_dict() for username, user in self._users.items()
        }
        with open(self.storage_path, "w") as f:
            json.dump(users_data, f, indent=2)

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self._lock:
            return self._users.get(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self._lock:
            for user in self._users.values():
                if user.email == email:
                    return user
        return None

    def get_user_by_provider_id(
        self, provider: str, provider_id: str
    ) -> Optional[User]:
        """Get user by provider and provider ID."""
        with self._lock:
            for user in self._users.values():
                if user.provider == provider and user.provider_id == provider_id:
                    return user
        return None

    def create_or_update_user(self, user: User) -> User:
        """Create a new user or update existing user."""
        with self._lock:
            # Check if user should have a specific role assignment
            assigned_role = self._get_assigned_role(user.username, user.email)
            if assigned_role:
                user.role = assigned_role

            self._users[user.username] = user
            self._save_users()
            return user

    def update_user_role(self, username: str, role: UserRole) -> bool:
        """Update user's role."""
        with self._lock:
            if username in self._users:
                self._users[username].role = role
                self._save_users()
                return True
        return False

    def list_users(self) -> List[User]:
        """List all users."""
        with self._lock:
            return list(self._users.values())

    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        with self._lock:
            if username in self._users:
                del self._users[username]
                self._save_users()
                return True
        return False

    def _get_assigned_role(self, username: str, email: str) -> Optional[UserRole]:
        """Get assigned role from configuration."""
        # Check username first, then email
        for identifier in [username, email]:
            if identifier in self.role_assignments:
                role_str = self.role_assignments[identifier]
                try:
                    return UserRole(role_str.lower())
                except ValueError:
                    continue
        return None

    def update_role_assignments(self, role_assignments: Dict[str, str]):
        """Update role assignments configuration."""
        with self._lock:
            self.role_assignments = role_assignments

            # Update existing users with new role assignments
            for user in self._users.values():
                assigned_role = self._get_assigned_role(user.username, user.email)
                if assigned_role:
                    user.role = assigned_role

            self._save_users()

    def get_users_with_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role."""
        with self._lock:
            return [user for user in self._users.values() if user.role == role]

    def count_users_by_role(self) -> Dict[UserRole, int]:
        """Count users by role."""
        with self._lock:
            counts = {role: 0 for role in UserRole}
            for user in self._users.values():
                counts[user.role] += 1
            return counts
