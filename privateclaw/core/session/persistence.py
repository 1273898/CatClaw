"""Persistent session storage for PrivateClaw."""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class SessionStore:
    """Persistent storage for sessions using JSON files."""

    def __init__(self, storage_path: str = "data/sessions"):
        """Initialize session store.

        Args:
            storage_path: Directory to store session files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict] = {}
        self._load_all()

    def _load_all(self):
        """Load all sessions from disk into cache."""
        for session_file in self.storage_path.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session_id = session_file.stem
                    self._cache[session_id] = data
            except Exception as e:
                print(f"[SessionStore] Failed to load {session_file}: {e}")

    def _save_to_disk(self, session_id: str, data: dict):
        """Save a single session to disk."""
        session_file = self.storage_path / f"{session_id}.json"
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SessionStore] Failed to save {session_id}: {e}")

    def _delete_from_disk(self, session_id: str):
        """Delete a session file from disk."""
        session_file = self.storage_path / f"{session_id}.json"
        try:
            if session_file.exists():
                session_file.unlink()
        except Exception as e:
            print(f"[SessionStore] Failed to delete {session_id}: {e}")

    def get(self, session_id: str) -> Optional[dict]:
        """Get a session by ID."""
        return self._cache.get(session_id)

    def put(self, session_id: str, data: dict):
        """Save a session."""
        self._cache[session_id] = data
        self._save_to_disk(session_id, data)

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._cache:
            del self._cache[session_id]
            self._delete_from_disk(session_id)
            return True
        return False

    def list_all(self) -> list[str]:
        """List all session IDs."""
        return list(self._cache.keys())

    def update(self, session_id: str, updates: dict):
        """Update specific fields in a session."""
        if session_id in self._cache:
            self._cache[session_id].update(updates)
            self._save_to_disk(session_id, self._cache[session_id])
