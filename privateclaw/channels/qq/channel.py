"""QQ Channel implementation for CatClaw.

Supports:
- QQ Official Bot API (QQ开放平台)
- Message receiving via webhook
- Message sending via API
"""

import asyncio
import hashlib
import json
from typing import Optional, Callable, Awaitable
from pathlib import Path

from privateclaw.channels.base import BaseChannel


class QQChannel(BaseChannel):
    """QQ channel implementation using QQ Official Bot API.

    Setup:
    1. Register at https://q.qq.com
    2. Create a bot application
    3. Get bot token and secret
    4. Configure webhook URL
    """

    def __init__(self, config: dict):
        """Initialize QQ channel."""
        super().__init__("qq", config)
        self.bot_id = config.get("bot_id", "")
        self.bot_secret = config.get("bot_secret", "")
        self.sandbox = config.get("sandbox", True)  # Use sandbox by default

        self._api_base = "https://api.sgroup.qq.com" if not self.sandbox else "https://sandbox.api.sgroup.qq.com"
        self._agent = None
        self._memory = None
        self._session_manager = None
        self._message_handler = None

        # Message callback
        self._on_message: Optional[Callable[[str, str, str], Awaitable[None]]] = None

    def set_agent(self, agent):
        """Set the agent instance."""
        self._agent = agent

    def set_memory(self, memory):
        """Set the memory instance."""
        self._memory = memory

    def set_session_manager(self, session_manager):
        """Set the session manager."""
        self._session_manager = session_manager

    def on_message(self, callback: Callable[[str, str, str], Awaitable[None]]):
        """Set message callback."""
        self._on_message = callback

    async def _get_access_token(self) -> str:
        """Get access token from QQ API."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_base}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.bot_id,
                    "client_secret": self.bot_secret,
                }
            )
            data = response.json()
            return data.get("access_token", "")

    async def send_message(self, target: str, message: str, **kwargs) -> bool:
        """Send message to QQ.

        Args:
            target: Channel ID or user ID
            message: Message content
            **kwargs: Additional options (msg_type, etc.)
        """
        import httpx

        try:
            token = await self._get_access_token()
            if not token:
                print("[QQ] Failed to get access token")
                return False

            msg_type = kwargs.get("msg_type", 0)  # 0=text, 1=rich, 2=markdown, 3=ark, 4=embed, 7=media

            headers = {
                "Authorization": f"Bot {self.bot_id}.{token}",
                "Content-Type": "application/json",
            }

            payload = {
                "content": message,
                "msg_type": msg_type,
            }

            # Add message ID for reply if provided
            if "msg_id" in kwargs:
                payload["msg_id"] = kwargs["msg_id"]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._api_base}/channels/{target}/messages",
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    return True
                else:
                    print(f"[QQ] Send failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"[QQ] Send error: {e}")
            return False

    async def handle_webhook(self, event_data: dict) -> dict:
        """Handle incoming webhook event from QQ.

        Args:
            event_data: The webhook event payload

        Returns:
            Response data
        """
        try:
            event_type = event_data.get("t", "")
            data = event_data.get("d", {})

            # Handle different event types
            if event_type == "AT_MESSAGE_CREATE":
                # Someone @mentioned the bot
                await self._handle_at_message(data)
            elif event_type == "DIRECT_MESSAGE_CREATE":
                # Direct message to bot
                await self._handle_direct_message(data)
            elif event_type == "MESSAGE_CREATE":
                # Regular message (if bot has intent)
                await self._handle_message(data)

            return {"code": 0, "message": "ok"}

        except Exception as e:
            print(f"[QQ] Webhook error: {e}")
            return {"code": -1, "message": str(e)}

    async def _handle_at_message(self, data: dict):
        """Handle @mention message."""
        content = data.get("content", "").strip()
        channel_id = data.get("channel_id", "")
        msg_id = data.get("id", "")
        author = data.get("author", {})
        user_id = author.get("id", "")

        # Remove @bot mention from content
        # QQ format: <@!bot_id> message
        import re
        content = re.sub(r'<@!\d+>', '', content).strip()

        if not content:
            return

        # Use channel_id as session
        session_id = f"qq_{channel_id}"

        if self._agent:
            response = await self._agent.run(content, session_id, user_id)
            await self.send_message(
                channel_id,
                response,
                msg_id=msg_id,
            )

    async def _handle_direct_message(self, data: dict):
        """Handle direct message."""
        content = data.get("content", "").strip()
        msg_id = data.get("id", "")
        author = data.get("author", {})
        user_id = author.get("id", "")
        guild_id = data.get("guild_id", "")

        if not content:
            return

        session_id = f"qq_dm_{user_id}"

        if self._agent:
            response = await self._agent.run(content, session_id, user_id)
            await self.send_message(
                guild_id,
                response,
                msg_id=msg_id,
            )

    async def _handle_message(self, data: dict):
        """Handle regular message."""
        # Similar to at_message but for groups where bot has message intent
        await self._handle_at_message(data)

    async def start(self) -> None:
        """Start the QQ channel (no-op for webhook mode)."""
        self._is_running = True
        print("[QQ] Channel started (webhook mode)")
        print(f"[QQ] Bot ID: {self.bot_id}")
        print(f"[QQ] Sandbox: {self.sandbox}")

        # Keep running
        try:
            while self._is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Stop the QQ channel."""
        self._is_running = False
        print("[QQ] Channel stopped")

    def get_info(self) -> dict:
        """Get channel information."""
        info = super().get_info()
        info.update({
            "bot_id": self.bot_id,
            "sandbox": self.sandbox,
            "api_base": self._api_base,
        })
        return info
