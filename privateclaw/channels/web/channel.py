"""Web channel for PrivateClaw - handles all HTTP/WebSocket responsibilities.

This channel is responsible for:
- HTTP API endpoints (chat, sessions, memory, etc.)
- WebSocket handling for real-time chat
- Static file serving for frontend
- CORS configuration
"""

import asyncio
import logging
from typing import Optional, Callable, Awaitable, List
from pathlib import Path

from privateclaw.channels.base import BaseChannel
from privateclaw.channels.web.websocket import WebSocketManager


class WebChannel(BaseChannel):
    """Web channel implementation.

    Provides a complete web interface for interacting with CatClaw.
    All HTTP/WS logic is contained here, Gateway only manages lifecycle.
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
        self._webhooks: dict = {}  # path -> handler

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

    def add_webhook(self, path: str, handler):
        """Add a webhook endpoint.

        Args:
            path: URL path for the webhook (e.g., /webhook/qq)
            handler: Async function to handle webhook events
        """
        self._webhooks[path] = handler

    def _create_app(self):
        """Create the FastAPI application with all routes."""
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import HTMLResponse
        from fastapi.middleware.cors import CORSMiddleware

        from privateclaw.channels.web.api import create_api_router
        from privateclaw.api.prompts import create_prompts_router
        from privateclaw.config.settings import get_settings

        settings = get_settings()

        app = FastAPI(
            title="CatClaw",
            description="Your private AI assistant",
            version="0.1.0",
        )

        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        )

        # API router - pass agent's tool_registry if available
        tool_registry = None
        if self._agent and hasattr(self._agent, 'tool_registry'):
            tool_registry = self._agent.tool_registry

        api_router = create_api_router(
            agent=self._agent,
            memory=self._memory,
            session_manager=self._session_manager,
            ws_manager=self._ws_manager,
            tool_registry=tool_registry,
        )
        app.include_router(api_router, prefix="/api")

        # Prompts router
        prompts_router = create_prompts_router()
        app.include_router(prompts_router, prefix="/api")

        # WebSocket endpoint
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
            await self._ws_manager.connect(websocket, session_id)
            try:
                while True:
                    data = await websocket.receive_json()
                    await self._ws_manager.handle_message(websocket, data)
            except Exception:
                self._ws_manager.disconnect(websocket, session_id)

        # Webhook endpoints
        for path, handler in self._webhooks.items():
            # Create endpoint function with proper closure
            def create_webhook_endpoint(h):
                async def webhook_endpoint(request: Request):
                    """Handle webhook request."""
                    try:
                        # Read raw body
                        body_bytes = await request.body()
                        body_str = body_bytes.decode('utf-8')

                        # Parse JSON
                        import json
                        body = json.loads(body_str)

                        logging.info(f"[Web] Webhook received: {body_str[:200]}")

                        result = await h(body)
                        return result
                    except Exception as e:
                        logging.error(f"[Web] Webhook error: {e}")
                        return {"code": -1, "message": str(e)}
                return webhook_endpoint

            # Register endpoint with proper path
            endpoint_func = create_webhook_endpoint(handler)
            app.add_api_route(path, endpoint_func, methods=["POST"])

        # Static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            # Filter out noisy static file logs
            logging.getLogger("uvicorn.access").addFilter(
                _EndpointFilter(["/pet", "/cats", "/assets"])
            )

            app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
            app.mount("/cats", StaticFiles(directory=str(static_dir / "cats")), name="cats")
            app.mount("/pet", StaticFiles(directory=str(static_dir / "pet")), name="pet")

            # Serve vite.svg
            @app.get("/vite.svg")
            async def serve_vite_svg():
                svg_path = static_dir / "vite.svg"
                if svg_path.exists():
                    from fastapi.responses import FileResponse
                    return FileResponse(str(svg_path), media_type="image/svg+xml")
                return {"error": "Not found"}

        # Serve index.html at root
        @app.get("/", response_class=HTMLResponse)
        async def root():
            index_path = static_dir / "index.html"
            if index_path.exists():
                return index_path.read_text(encoding="utf-8")
            return _get_default_index()

        # Health check
        @app.get("/health")
        async def health():
            return {"status": "healthy", "channel": "web"}

        return app

    async def start(self) -> None:
        """Start the web channel."""
        import uvicorn

        # Create FastAPI app
        self._app = self._create_app()

        # Start server
        config = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        self._server = uvicorn.Server(config)
        self._is_running = True

        # Run server (blocks until shutdown)
        await self._server.serve()

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


class _EndpointFilter(logging.Filter):
    """Filter out specific endpoint logs to reduce noise."""

    def __init__(self, paths: List[str]):
        super().__init__()
        self.paths = paths

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args and len(record.args) >= 3:
            path = record.args[2] if len(record.args) > 2 else ""
            for p in self.paths:
                if p in str(path):
                    return False
        return True


def _get_default_index() -> str:
    """Get default index HTML if static files don't exist."""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CatClaw</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        h1 { color: #e94560; }
        p { color: #aaa; }
        code { background: #16213e; padding: 2px 8px; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>CatClaw</h1>
    <p>Your private AI assistant</p>
    <p>Frontend not built. Run <code>cd frontend && npm run build</code></p>
</body>
</html>
"""
