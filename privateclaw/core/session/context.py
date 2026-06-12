"""Session context for PrivateClaw."""

from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SessionContext(BaseModel):
    """Session context model."""

    session_id: str = Field(description="Unique session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    channel: Optional[str] = Field(default=None, description="Channel name")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    last_active: datetime = Field(default_factory=datetime.now, description="Last activity time")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        arbitrary_types_allowed = True

    def update_activity(self) -> None:
        """Update last activity time."""
        self.last_active = datetime.now()

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

    def is_active(self, timeout_minutes: int = 30) -> bool:
        """Check if session is active within timeout."""
        elapsed = (datetime.now() - self.last_active).total_seconds()
        return elapsed < timeout_minutes * 60

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
        }
