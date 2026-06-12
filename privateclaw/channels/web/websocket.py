"""WebSocket handler for PrivateClaw web interface."""

import json
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str = Field(description="Message type (message, ping, etc.)")
    content: str = Field(default="", description="Message content")
    session_id: str = Field(default="default", description="Session ID")


class WebSocketManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._agent = None
        self._memory = None

    def set_agent(self, agent):
        """Set the agent instance."""
        self._agent = agent

    def set_memory(self, memory):
        """Set the memory instance."""
        self._memory = memory

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_message(self, websocket: WebSocket, message: dict):
        """Send a message to a WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    async def broadcast(self, session_id: str, message: dict):
        """Broadcast a message to all connections in a session."""
        if session_id in self.active_connections:
            for websocket in self.active_connections[session_id]:
                await self.send_message(websocket, message)

    async def handle_message(self, websocket: WebSocket, data: dict):
        """Handle an incoming WebSocket message."""
        message_type = data.get("type", "message")
        content = data.get("content", "")
        session_id = data.get("session_id", "default")

        if message_type == "ping":
            await self.send_message(websocket, {"type": "pong"})
            return

        if message_type == "message":
            await self._handle_chat_message(websocket, content, session_id)
            return

        if message_type == "clear":
            await self._handle_clear_session(websocket, session_id)
            return

        await self.send_message(websocket, {
            "type": "error",
            "content": f"Unknown message type: {message_type}",
        })

    async def _handle_chat_message(self, websocket: WebSocket, content: str, session_id: str):
        """Handle a chat message."""
        if not self._agent:
            await self.send_message(websocket, {
                "type": "error",
                "content": "Agent not initialized",
            })
            return

        try:
            # Get response from agent
            response = await self._agent.run(content, session_id)

            # Send response
            await self.send_message(websocket, {
                "type": "message",
                "content": response,
                "session_id": session_id,
            })

        except Exception as e:
            await self.send_message(websocket, {
                "type": "error",
                "content": str(e),
            })

    async def _handle_clear_session(self, websocket: WebSocket, session_id: str):
        """Handle session clear request."""
        if self._memory:
            await self._memory.clear_session(session_id)

        await self.send_message(websocket, {
            "type": "cleared",
            "session_id": session_id,
        })

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.active_connections)
