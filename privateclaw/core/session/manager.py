"""Session manager for PrivateClaw with persistence."""

from typing import Optional
from datetime import datetime
from privateclaw.core.session.context import SessionContext
from privateclaw.core.session.persistence import SessionStore


class SessionManager:
    """Manager for handling sessions with persistent storage."""

    def __init__(self, storage_path: str = "data/sessions"):
        """Initialize session manager.

        Args:
            storage_path: Directory to store session files
        """
        self._store = SessionStore(storage_path)
        self._sessions: dict[str, SessionContext] = {}
        self._load_sessions()

    def _load_sessions(self):
        """Load sessions from persistent storage."""
        for session_id in self._store.list_all():
            data = self._store.get(session_id)
            if data:
                try:
                    self._sessions[session_id] = SessionContext(
                        session_id=session_id,
                        created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                        last_active=datetime.fromisoformat(data.get("last_active", datetime.now().isoformat())),
                        metadata=data.get("metadata", {}),
                    )
                except Exception as e:
                    print(f"[SessionManager] Failed to load session {session_id}: {e}")

    def _save_session(self, session: SessionContext):
        """Save session to persistent storage."""
        self._store.put(session.session_id, {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat(),
            "metadata": session.metadata,
        })

    async def get_or_create_session(self, session_id: str) -> SessionContext:
        """Get an existing session or create a new one."""
        if session_id not in self._sessions:
            now = datetime.now()
            self._sessions[session_id] = SessionContext(
                session_id=session_id,
                created_at=now,
                last_active=now,
            )
            self._save_session(self._sessions[session_id])
        else:
            self._sessions[session_id].last_active = datetime.now()
            self._save_session(self._sessions[session_id])

        return self._sessions[session_id]

    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._store.delete(session_id)
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
            self._store.delete(session_id)

        return len(inactive_sessions)
