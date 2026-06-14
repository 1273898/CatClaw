"""Short-term memory (conversation history) for PrivateClaw with persistence."""

import json
from typing import Optional
from pathlib import Path
from collections import defaultdict
from datetime import datetime


class ShortTermMemory:
    """Short-term memory for storing conversation history with persistence."""

    def __init__(self, max_messages: int = 50, storage_path: str = "data/conversations"):
        """Initialize short-term memory.

        Args:
            max_messages: Maximum messages per session
            storage_path: Directory to store conversation files
        """
        self.max_messages = max_messages
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, list[dict]] = defaultdict(list)
        self._load_all()

    def _load_all(self):
        """Load all conversations from disk."""
        for conv_file in self.storage_path.glob("*.json"):
            try:
                with open(conv_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session_id = conv_file.stem
                    self._sessions[session_id] = data
            except Exception as e:
                print(f"[ShortTermMemory] Failed to load {conv_file}: {e}")

    def _save_to_disk(self, session_id: str):
        """Save a session's messages to disk."""
        conv_file = self.storage_path / f"{session_id}.json"
        try:
            with open(conv_file, "w", encoding="utf-8") as f:
                json.dump(self._sessions[session_id], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ShortTermMemory] Failed to save {session_id}: {e}")

    def _delete_from_disk(self, session_id: str):
        """Delete a session file from disk."""
        conv_file = self.storage_path / f"{session_id}.json"
        try:
            if conv_file.exists():
                conv_file.unlink()
        except Exception as e:
            print(f"[ShortTermMemory] Failed to delete {session_id}: {e}")

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

        # Save to disk
        self._save_to_disk(session_id)

    async def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._delete_from_disk(session_id)

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
