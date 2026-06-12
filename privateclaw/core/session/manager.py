"""Session manager for PrivateClaw."""

from typing import Optional
from datetime import datetime
from privateclaw.core.session.context import SessionContext


class SessionManager:
    """Manager for handling sessions."""

    def __init__(self):
        """Initialize session manager."""
        self._sessions: dict[str, SessionContext] = {}

    async def get_or_create_session(self, session_id: str) -> SessionContext:
        """Get an existing session or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(
                session_id=session_id,
                created_at=datetime.now(),
                last_active=datetime.now(),
            )
        else:
            self._sessions[session_id].last_active = datetime.now()

        return self._sessions[session_id]

    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def list_sessions(self) -> list[str]:
        """List all session IDs."""
        return list(self._sessions.keys())

    async def get_active_sessions(self, timeout_minutes: int = 30) -> list[SessionContext]:
        """Get active sessions within timeout."""
        now = datetime.now()
        active_sessions = []

        for session in self._sessions.values():
            if (now - session.last_active).total_seconds() < timeout_minutes * 60:
                active_sessions.append(session)

        return active_sessions

    async def cleanup_inactive_sessions(self, timeout_minutes: int = 60) -> int:
        """Remove inactive sessions."""
        now = datetime.now()
        inactive_sessions = []

        for session_id, session in self._sessions.items():
            if (now - session.last_active).total_seconds() > timeout_minutes * 60:
                inactive_sessions.append(session_id)

        for session_id in inactive_sessions:
            del self._sessions[session_id]

        return len(inactive_sessions)
