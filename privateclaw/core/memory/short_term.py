"""Short-term memory (conversation history) for PrivateClaw."""

from typing import Optional
from collections import defaultdict
from datetime import datetime


class ShortTermMemory:
    """Short-term memory for storing conversation history."""

    def __init__(self, max_messages: int = 50):
        """Initialize short-term memory."""
        self.max_messages = max_messages
        self._sessions: dict[str, list[dict]] = defaultdict(list)

    async def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        return self._sessions.get(session_id, [])

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self._sessions[session_id].append(message)

        # Trim if exceeds max messages
        if len(self._sessions[session_id]) > self.max_messages:
            self._sessions[session_id] = self._sessions[session_id][-self.max_messages:]

    async def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def get_last_n_messages(self, session_id: str, n: int = 10) -> list[dict]:
        """Get last N messages for a session."""
        history = self._sessions.get(session_id, [])
        return history[-n:]

    async def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session."""
        return len(self._sessions.get(session_id, []))

    async def get_all_sessions(self) -> list[str]:
        """Get all session IDs."""
        return list(self._sessions.keys())
