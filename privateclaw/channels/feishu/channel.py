"""Feishu (Lark) Channel implementation for CatClaw.

Supports:
- Feishu Open Platform API
- Message receiving via webhook/event
- Message sending via API
- Interactive cards
"""

import asyncio
import hashlib
import json
import time
from typing import Optional, Callable, Awaitable
from pathlib import Path

from privateclaw.channels.base import BaseChannel


class FeishuChannel(BaseChannel):
    """Feishu (Lark) channel implementation.

    Setup:
    1. Register at https://open.feishu.cn
    2. Create an application
    3. Get App ID and App Secret
    4. Configure event subscription URL
    5. Add bot capability
    """

    def __init__(self, config: dict):
        """Initialize Feishu channel."""
        super().__init__("feishu", config)
        self.app_id = config.get("app_id", "")
        self.app_secret = config.get("app_secret", "")
        self.verification_token = config.get("verification_token", "")
        self.encrypt_key = config.get("encrypt_key", "")

        self._api_base = "https://open.feishu.cn/open-apis"
        self._tenant_access_token = ""
        self._token_expires_at = 0

        self._agent = None
        self._memory = None
        self._session_manager = None

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

    async def _get_tenant_access_token(self) -> str:
        """Get tenant access token from Feishu API."""
        import httpx

        # Check if token is still valid
        if self._tenant_access_token and time.time() < self._token_expires_at:
            return self._tenant_access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_base}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret,
                }
            )
            data = response.json()

            if data.get("code") == 0:
                self._tenant_access_token = data.get("tenant_access_token", "")
                self._token_expires_at = time.time() + data.get("expire", 7200) - 300  # Refresh 5 min early
                return self._tenant_access_token
            else:
                print(f"[Feishu] Failed to get token: {data}")
                return ""

    async def send_message(self, target: str, message: str, **kwargs) -> bool:
        """Send message to Feishu.

        Args:
            target: Chat ID or user ID
            message: Message content
            **kwargs: Additional options (receive_id_type, msg_type, etc.)
        """
        import httpx

        try:
            token = await self._get_tenant_access_token()
            if not token:
                print("[Feishu] Failed to get access token")
                return False

            receive_id_type = kwargs.get("receive_id_type", "chat_id")  # open_id, user_id, union_id, chat_id, email
            msg_type = kwargs.get("msg_type", "text")  # text, post, image, interactive, etc.

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            }

            # Build message content
            if msg_type == "text":
                content = json.dumps({"text": message})
            elif msg_type == "interactive":
                content = message  # Already JSON string for cards
            else:
                content = json.dumps({"text": message})

            payload = {
                "receive_id": target,
                "msg_type": msg_type,
                "content": content,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._api_base}/im/v1/messages?receive_id_type={receive_id_type}",
                    headers=headers,
                    json=payload,
                )

                data = response.json()
                if data.get("code") == 0:
                    return True
                else:
                    print(f"[Feishu] Send failed: {data}")
                    return False

        except Exception as e:
            print(f"[Feishu] Send error: {e}")
            return False

    async def reply_message(self, message_id: str, message: str, msg_type: str = "text") -> bool:
        """Reply to a specific message."""
        import httpx

        try:
            token = await self._get_tenant_access_token()
            if not token:
                return False

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            }

            if msg_type == "text":
                content = json.dumps({"text": message})
            else:
                content = json.dumps({"text": message})

            payload = {
                "content": content,
                "msg_type": msg_type,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._api_base}/im/v1/messages/{message_id}/reply",
                    headers=headers,
                    json=payload,
                )

                data = response.json()
                return data.get("code") == 0

        except Exception as e:
            print(f"[Feishu] Reply error: {e}")
            return False

    async def handle_event(self, event_data: dict) -> dict:
        """Handle incoming event from Feishu.

        Args:
            event_data: The event payload

        Returns:
            Response data
        """
        try:
            # Handle URL verification challenge
            if "challenge" in event_data:
                return {"challenge": event_data["challenge"]}

            # Handle token verification
            token = event_data.get("token", "")
            if self.verification_token and token != self.verification_token:
                return {"code": -1, "message": "Invalid token"}

            # Get event header and body
            header = event_data.get("header", {})
            event = event_data.get("event", {})
            event_type = header.get("event_type", "")

            # Handle different event types
            if event_type == "im.message.receive_v1":
                await self._handle_message(event)

            return {"code": 0, "message": "ok"}

        except Exception as e:
            print(f"[Feishu] Event error: {e}")
            return {"code": -1, "message": str(e)}

    async def _handle_message(self, event: dict):
        """Handle incoming message event."""
        message = event.get("message", {})
        sender = event.get("sender", {})

        # Extract message info
        message_id = message.get("message_id", "")
        chat_id = message.get("chat_id", "")
        chat_type = message.get("chat_type", "")  # p2p or group
        message_type = message.get("message_type", "")
        content_str = message.get("content", "{}")
        mentions = message.get("mentions", [])

        sender_id = sender.get("sender_id", {}).get("open_id", "")

        # Parse content
        try:
            content = json.loads(content_str)
            if message_type == "text":
                text = content.get("text", "").strip()
            else:
                text = f"[{message_type} message]"
        except:
            text = content_str

        # Remove @bot mention from text
        for mention in mentions:
            key = mention.get("key", "")
            if key:
                text = text.replace(key, "").strip()

        if not text:
            return

        # Determine session ID
        if chat_type == "p2p":
            session_id = f"feishu_dm_{sender_id}"
        else:
            session_id = f"feishu_{chat_id}"

        # Process message
        if self._agent:
            response = await self._agent.run(text, session_id, sender_id)

            # Reply to the message
            await self.reply_message(message_id, response)

    async def start(self) -> None:
        """Start the Feishu channel (no-op for webhook mode)."""
        self._is_running = True
        print("[Feishu] Channel started (webhook mode)")
        print(f"[Feishu] App ID: {self.app_id}")

        # Keep running
        try:
            while self._is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Stop the Feishu channel."""
        self._is_running = False
        print("[Feishu] Channel stopped")

    def get_info(self) -> dict:
        """Get channel information."""
        info = super().get_info()
        info.update({
            "app_id": self.app_id,
            "api_base": self._api_base,
        })
        return info
