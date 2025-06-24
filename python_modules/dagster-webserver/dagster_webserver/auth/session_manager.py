"""Session management for user authentication."""

import time
import secrets
from typing import Dict, Optional
import threading
from datetime import datetime

from .models import User


class SessionManager:
    """Manages user sessions and authentication state."""

    def __init__(self, session_timeout: int = 3600 * 24):  # 24 hours default
        self.session_timeout = session_timeout
        self._sessions: Dict[str, Dict] = {}
        self._lock = threading.RLock()

    def create_session(self, user: User) -> str:
        """Create a new session for a user."""
        with self._lock:
            session_id = secrets.token_urlsafe(32)
            self._sessions[session_id] = {
                "user": user,
                "created_at": time.time(),
                "last_accessed": time.time(),
            }
            return session_id

    def get_user_from_session(self, session_id: str) -> Optional[User]:
        """Get user from session ID, checking validity."""
        with self._lock:
            if session_id not in self._sessions:
                return None

            session_data = self._sessions[session_id]
            current_time = time.time()

            # Check if session has expired
            if current_time - session_data["last_accessed"] > self.session_timeout:
                del self._sessions[session_id]
                return None

            # Update last accessed time
            session_data["last_accessed"] = current_time
            return session_data["user"]

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
        return False

    def invalidate_all_user_sessions(self, username: str):
        """Invalidate all sessions for a specific user."""
        with self._lock:
            sessions_to_remove = []
            for session_id, session_data in self._sessions.items():
                if session_data["user"].username == username:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self._sessions[session_id]

    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        with self._lock:
            current_time = time.time()
            expired_sessions = []

            for session_id, session_data in self._sessions.items():
                if current_time - session_data["last_accessed"] > self.session_timeout:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self._sessions[session_id]

    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        with self._lock:
            self.cleanup_expired_sessions()
            return len(self._sessions)

    def get_user_session_count(self, username: str) -> int:
        """Get count of active sessions for a user."""
        with self._lock:
            self.cleanup_expired_sessions()
            count = 0
            for session_data in self._sessions.values():
                if session_data["user"].username == username:
                    count += 1
            return count

    def refresh_session(self, session_id: str) -> bool:
        """Refresh a session's last accessed time."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["last_accessed"] = time.time()
                return True
        return False

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information."""
        with self._lock:
            if session_id not in self._sessions:
                return None

            session_data = self._sessions[session_id]
            current_time = time.time()

            # Check if session has expired
            if current_time - session_data["last_accessed"] > self.session_timeout:
                del self._sessions[session_id]
                return None

            return {
                "user": session_data["user"],
                "created_at": datetime.fromtimestamp(session_data["created_at"]),
                "last_accessed": datetime.fromtimestamp(session_data["last_accessed"]),
                "expires_at": datetime.fromtimestamp(
                    session_data["last_accessed"] + self.session_timeout
                ),
            }
