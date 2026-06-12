"""Gateway server for PrivateClaw."""

from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

from privateclaw.config.settings import Settings, get_settings
from privateclaw.core.agent.agent import PrivateClawAgent
from privateclaw.core.llm.factory import LLMFactory
from privateclaw.core.memory.manager import MemoryManager
from privateclaw.core.tools.registry import ToolRegistry
from privateclaw.core.session.manager import SessionManager
from privateclaw.channels.base import BaseChannel
from privateclaw.channels.web import WebChannel


class Gateway:
    """Gateway server - manages channels and agent."""

    def __init__(self, config: Optional[Settings] = None):
        """Initialize gateway."""
        self.config = config or get_settings()
        self.app = FastAPI(
            title="PrivateClaw Gateway",
            description="PrivateClaw API Gateway",
            version="0.1.0",
        )

        # Core components
        self.agent: Optional[PrivateClawAgent] = None
        self.memory: Optional[MemoryManager] = None
        self.session_manager = SessionManager()
        self.channels: dict[str, BaseChannel] = {}

        # WebSocket connections
        self.websocket_connections: list[WebSocket] = []

        # Setup FastAPI
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def root():
            return {
                "name": self.config.app_name,
                "version": "0.1.0",
                "status": "running",
            }

        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}

        @self.app.post("/chat")
        async def chat(request: dict):
            message = request.get("message", "")
            session_id = request.get("session_id", "default")

            if not self.agent:
                return {"error": "Agent not initialized"}

            response = await self.agent.run(message, session_id)
            return {"response": response, "session_id": session_id}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket_connections.append(websocket)

            try:
                while True:
                    data = await websocket.receive_text()
                    request = json.loads(data)

                    message = request.get("message", "")
                    session_id = request.get("session_id", "ws_session")

                    if self.agent:
                        response = await self.agent.run(message, session_id)
                        await websocket.send_text(json.dumps({
                            "response": response,
                            "session_id": session_id,
                        }))
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)

    async def initialize(self) -> None:
        """Initialize gateway components."""
        # Initialize memory
        self.memory = MemoryManager(self.config.memory)

        # Initialize LLM
        llm = LLMFactory.create_from_settings(self.config)

        # Load tools
        tools = ToolRegistry.load_all()

        # Initialize agent
        self.agent = PrivateClawAgent(
            llm=llm,
            memory=self.memory,
            tools=tools,
        )

    async def start(self) -> None:
        """Start the gateway."""
        await self.initialize()

        # Start web channel if enabled
        if self.config.channels.web_enabled:
            web_channel = WebChannel({
                "host": self.config.channels.web_host,
                "port": self.config.channels.web_port,
            })
            web_channel.set_agent(self.agent)
            web_channel.set_memory(self.memory)
            web_channel.set_session_manager(self.session_manager)
            self.add_channel(web_channel)
            await web_channel.start()

        # Start web server for API
        uvicorn_config = uvicorn.Config(
            self.app,
            host=self.config.gateway.host,
            port=self.config.gateway.port,
            log_level=self.config.log_level.lower(),
        )
        server = uvicorn.Server(uvicorn_config)
        await server.serve()

    async def stop(self) -> None:
        """Stop the gateway."""
        # Stop all channels
        for channel in self.channels.values():
            await channel.stop()

        # Close WebSocket connections
        for ws in self.websocket_connections:
            await ws.close()

    def add_channel(self, channel: BaseChannel) -> None:
        """Add a channel to the gateway."""
        channel.on_message(self._handle_channel_message)
        self.channels[channel.name] = channel

    async def _handle_channel_message(self, channel_name: str, sender: str, message: str) -> None:
        """Handle message from a channel."""
        if not self.agent:
            return

        session_id = f"{channel_name}:{sender}"
        response = await self.agent.run(message, session_id)

        # Send response back through channel
        if channel_name in self.channels:
            await self.channels[channel_name].send_message(sender, response)

        # Broadcast to WebSocket connections
        for ws in self.websocket_connections:
            try:
                await ws.send_text(json.dumps({
                    "channel": channel_name,
                    "sender": sender,
                    "message": message,
                    "response": response,
                }))
            except Exception:
                pass
