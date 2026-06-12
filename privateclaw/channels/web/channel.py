"""Web channel for PrivateClaw."""

import asyncio
from typing import Optional, Callable, Awaitable
from pathlib import Path

from privateclaw.channels.base import BaseChannel
from privateclaw.channels.web.app import create_web_app
from privateclaw.channels.web.websocket import WebSocketManager


class WebChannel(BaseChannel):
    """Web channel implementation.

    Provides a web interface for interacting with PrivateClaw.
    Includes:
    - REST API for chat and management
    - WebSocket for real-time chat
    - Static file serving for frontend
    """

    def __init__(self, config: dict):
        """Initialize web channel."""
        super().__init__("web", config)
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 8000)
        self._app = None
        self._server = None
        self._ws_manager = WebSocketManager()
        self._agent = None
        self._memory = None
        self._session_manager = None

    def set_agent(self, agent):
        """Set the agent instance."""
        self._agent = agent
        self._ws_manager.set_agent(agent)

    def set_memory(self, memory):
        """Set the memory instance."""
        self._memory = memory
        self._ws_manager.set_memory(memory)

    def set_session_manager(self, session_manager):
        """Set the session manager instance."""
        self._session_manager = session_manager

    async def start(self) -> None:
        """Start the web channel."""
        import uvicorn

        # Create FastAPI app
        self._app = create_web_app(
            agent=self._agent,
            memory=self._memory,
            session_manager=self._session_manager,
            config=self.config,
        )

        # Add WebSocket endpoint
        @self._app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
            await self._ws_manager.connect(websocket, session_id)
            try:
                while True:
                    data = await websocket.receive_json()
                    await self._ws_manager.handle_message(websocket, data)
            except Exception:
                self._ws_manager.disconnect(websocket, session_id)

        # Start server
        config = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        self._server = uvicorn.Server(config)
        self._is_running = True

        # Run server in background
        asyncio.create_task(self._server.serve())

    async def stop(self) -> None:
        """Stop the web channel."""
        if self._server:
            self._server.should_exit = True
            self._is_running = False

    async def send_message(self, target: str, message: str, **kwargs) -> bool:
        """Send a message via WebSocket."""
        session_id = kwargs.get("session_id", target)
        await self._ws_manager.broadcast(session_id, {
            "type": "message",
            "content": message,
            "session_id": session_id,
        })
        return True

    def get_info(self) -> dict:
        """Get channel information."""
        info = super().get_info()
        info.update({
            "host": self.host,
            "port": self.port,
            "active_connections": self._ws_manager.get_connection_count(),
            "active_sessions": self._ws_manager.get_session_count(),
        })
        return info
