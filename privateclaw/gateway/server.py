"""Gateway server for PrivateClaw - unified architecture.

Gateway responsibilities:
- Component initialization (agent, memory, tools)
- Channel management and lifecycle
- Message routing between channels

WebChannel responsibilities:
- HTTP API endpoints
- WebSocket handling
- Static file serving
"""

import asyncio
from typing import Optional
import uvicorn

from privateclaw.config.settings import Settings, get_settings
from privateclaw.core.agent.agent import PrivateClawAgent
from privateclaw.core.llm.factory import LLMFactory
from privateclaw.core.memory.manager import MemoryManager
from privateclaw.core.tools.registry import ToolRegistry
from privateclaw.core.session.manager import SessionManager
from privateclaw.channels.base import BaseChannel


class Gateway:
    """Gateway server - manages components and channels.

    This gateway focuses on:
    1. Initializing core components (agent, memory, tools)
    2. Managing channel lifecycle
    3. Routing messages between channels
    """

    def __init__(self, config: Optional[Settings] = None):
        """Initialize gateway."""
        self.config = config or get_settings()

        # Core components
        self.agent: Optional[PrivateClawAgent] = None
        self.memory: Optional[MemoryManager] = None
        self.session_manager = SessionManager(
            storage_path=str(self.config.get_data_path() / "sessions")
        )
        self.channels: dict[str, BaseChannel] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize gateway components."""
        if self._initialized:
            return

        # Initialize memory
        self.memory = MemoryManager(self.config)

        # Initialize LLM
        llm = LLMFactory.create_from_settings(self.config)

        # Load tools
        registry = ToolRegistry()
        tools = registry.load_all()

        # Initialize agent
        self.agent = PrivateClawAgent(
            llm=llm,
            memory=self.memory,
            tools=tools,
            tool_registry=registry,
        )

        self._initialized = True

    def add_channel(self, channel: BaseChannel) -> None:
        """Add a channel to the gateway."""
        # Set dependencies on channel
        if hasattr(channel, 'set_agent'):
            channel.set_agent(self.agent)
        if hasattr(channel, 'set_memory'):
            channel.set_memory(self.memory)
        if hasattr(channel, 'set_session_manager'):
            channel.set_session_manager(self.session_manager)

        # Set message handler
        channel.on_message(self._handle_channel_message)
        self.channels[channel.name] = channel

    async def _handle_channel_message(self, channel_name: str, sender: str, message: str, **kwargs) -> None:
        """Handle message from a channel and route response."""
        if not self.agent:
            return

        metadata = kwargs.get("metadata", {})
        session_id = f"{channel_name}:{sender}"

        print(f"[Gateway] Received message from {channel_name}:{sender}: {message[:50]}...")

        # Store message to memory for web UI access
        if self.memory:
            print(f"[Gateway] Storing user message to session: {session_id}")
            await self.memory.store_conversation(
                session_id=session_id,
                user_message=message,
                channel=channel_name,
                sender=sender,
            )

        response = await self.agent.run(message, session_id)

        # Store response to memory
        if self.memory:
            print(f"[Gateway] Storing assistant response to session: {session_id}")
            await self.memory.store_conversation(
                session_id=session_id,
                assistant_message=response,
                channel=channel_name,
                sender=sender,
            )

        print(f"[Gateway] Sending response to {channel_name}:{sender}")

        # Send response back through the originating channel
        if channel_name in self.channels:
            await self.channels[channel_name].send_message(
                sender,
                response,
                **metadata
            )

    async def start(self) -> None:
        """Start the gateway and all channels."""
        # Debug: print channel config
        print(f"[Gateway] Channel config:")
        print(f"  - web_enabled: {self.config.channel_web_enabled}")
        print(f"  - qq_enabled: {self.config.channel_qq_enabled}")
        print(f"  - qq_bot_id: {self.config.channel_qq_bot_id}")
        print(f"  - feishu_enabled: {self.config.channel_feishu_enabled}")

        # Initialize components
        await self.initialize()

        # Start web channel if enabled
        if self.config.channel_web_enabled:
            from privateclaw.channels.web import WebChannel

            web_channel = WebChannel({
                "host": self.config.channel_web_host,
                "port": self.config.channel_web_port,
            })

            # Add QQ channel if enabled
            if self.config.channel_qq_enabled:
                print(f"[Gateway] Initializing QQ channel...")
                print(f"[Gateway] Bot ID: {self.config.channel_qq_bot_id}")
                try:
                    from privateclaw.channels.qq import QQChannel
                    qq_channel = QQChannel({
                        "bot_id": self.config.channel_qq_bot_id,
                        "bot_secret": self.config.channel_qq_bot_secret,
                        "sandbox": self.config.channel_qq_sandbox,
                    })
                    self.add_channel(qq_channel)

                    # Add webhook endpoint to web app
                    web_channel.add_webhook("/webhook/qq", qq_channel.handle_webhook)
                    print(f"[Gateway] ✅ QQ channel initialized successfully")
                except Exception as e:
                    print(f"[Gateway] ❌ Failed to initialize QQ channel: {e}")
                    import traceback
                    traceback.print_exc()

            # Add Feishu channel if enabled
            if self.config.channel_feishu_enabled:
                from privateclaw.channels.feishu import FeishuChannel
                feishu_channel = FeishuChannel({
                    "app_id": self.config.channel_feishu_app_id,
                    "app_secret": self.config.channel_feishu_app_secret,
                    "verification_token": self.config.channel_feishu_verification_token,
                    "encrypt_key": self.config.channel_feishu_encrypt_key,
                })
                self.add_channel(feishu_channel)

                # Add webhook endpoint to web app
                web_channel.add_webhook("/webhook/feishu", feishu_channel.handle_event)

            self.add_channel(web_channel)

            # Start the channel (this will block)
            await web_channel.start()
        else:
            # If web channel is disabled, start a minimal server
            # This is mainly for development/testing
            from fastapi import FastAPI
            app = FastAPI(title="CatClaw Gateway")

            @app.get("/")
            async def root():
                return {
                    "name": self.config.app_name,
                    "version": "0.1.0",
                    "status": "running (no web channel)",
                }

            @app.get("/health")
            async def health():
                return {"status": "healthy"}

            uvicorn_config = uvicorn.Config(
                app,
                host=self.config.gateway_host,
                port=self.config.gateway_port,
                log_level=self.config.log_level.lower(),
            )
            server = uvicorn.Server(uvicorn_config)
            await server.serve()

    async def stop(self) -> None:
        """Stop the gateway and all channels."""
        for channel in self.channels.values():
            await channel.stop()
        self.channels.clear()
        self._initialized = False

    def get_status(self) -> dict:
        """Get gateway status."""
        return {
            "initialized": self._initialized,
            "agent_ready": self.agent is not None,
            "memory_ready": self.memory is not None,
            "channels": {
                name: channel.get_info()
                for name, channel in self.channels.items()
            },
            "config": {
                "app_name": self.config.app_name,
                "web_enabled": self.config.channel_web_enabled,
                "web_port": self.config.channel_web_port,
            },
        }
