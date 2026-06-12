"""Base channel class for PrivateClaw."""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Awaitable


class BaseChannel(ABC):
    """Abstract base class for all channels."""

    def __init__(self, name: str, config: dict):
        """Initialize channel."""
        self.name = name
        self.config = config
        self._message_callback: Optional[Callable] = None
        self._is_running = False

    @abstractmethod
    async def start(self) -> None:
        """Start the channel."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel."""
        pass

    @abstractmethod
    async def send_message(self, target: str, message: str, **kwargs) -> bool:
        """Send a message to a target.

        Args:
            target: Message target (user ID, channel ID, etc.)
            message: Message content
            **kwargs: Additional parameters

        Returns:
            True if message was sent successfully
        """
        pass

    def on_message(self, callback: Callable[[str, str, str], Awaitable[None]]) -> None:
        """Register a message callback.

        The callback should accept:
            - channel_name (str): Name of the channel
            - sender (str): Sender identifier
            - message (str): Message content
        """
        self._message_callback = callback

    async def _handle_message(self, sender: str, message: str) -> None:
        """Handle incoming message."""
        if self._message_callback:
            await self._message_callback(self.name, sender, message)

    @property
    def is_running(self) -> bool:
        """Check if channel is running."""
        return self._is_running

    def get_info(self) -> dict:
        """Get channel information."""
        return {
            "name": self.name,
            "is_running": self._is_running,
            "config": {k: v for k, v in self.config.items() if k != "token"},
        }
