"""QQ Bot channel for PrivateClaw."""

import asyncio
import json
import logging
import hashlib
import hmac
from typing import Optional, Callable, Awaitable, Dict, Any, List
from pathlib import Path
from datetime import datetime

from privateclaw.channels.base import BaseChannel

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QQChannel(BaseChannel):
    """QQ Bot channel implementation.

    Supports QQ official bot API for receiving and sending messages.
    """

    def __init__(self, config: dict):
        """Initialize QQ channel."""
        super().__init__("qq", config)
        self.bot_id = config.get("bot_id", "")
        self.bot_secret = config.get("bot_secret", "")
        self.sandbox = config.get("sandbox", True)
        self._message_handler: Optional[Callable] = None
        self._agent = None
        self._memory = None
        self._session_manager = None
        self._api_base = "https://api.sgroup.qq.com" if not self.sandbox else "https://sandbox.api.sgroup.qq.com"
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

        # Data storage
        self.storage_dir = Path("data/qq")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        console.print(Panel(
            f"[bold green]QQ Channel Configuration[/bold green]\n\n"
            f"Bot ID: {self.bot_id}\n"
            f"Sandbox: {self.sandbox}\n"
            f"API Base: {self._api_base}\n"
            f"Storage: {self.storage_dir}",
            title="📱 QQ Bot",
            style="blue",
        ))

    def _generate_signature(self, plain_token: str, event_ts: str) -> str:
        """Generate ed25519 signature for QQ webhook validation.

        Args:
            plain_token: Token from QQ validation request
            event_ts: Timestamp from QQ validation request

        Returns:
            Hex-encoded signature string
        """
        try:
            import nacl.signing
            import nacl.encoding

            # Use bot_secret as seed for ed25519 key generation
            # Pad or truncate to 32 bytes (ed25519 seed size)
            seed = self.bot_secret.encode('utf-8')
            # Pad seed to 32 bytes if shorter
            while len(seed) < 32:
                seed = seed + seed
            seed = seed[:32]

            # Generate signing key from seed
            signing_key = nacl.signing.SigningKey(seed)

            # Create message: event_ts + plain_token
            message = (event_ts + plain_token).encode('utf-8')

            # Sign the message
            signed = signing_key.sign(message)
            signature = signed.signature.hex()

            return signature

        except ImportError:
            # Fallback: use hashlib if nacl is not available
            logger.warning("[QQ] nacl library not available, using fallback signature method")

            # Simple fallback - this may not work for QQ validation
            # but allows the service to start
            message = (event_ts + plain_token).encode('utf-8')
            key = self.bot_secret.encode('utf-8')
            signature = hmac.new(key, message, hashlib.sha256).hexdigest()

            return signature

    def set_agent(self, agent):
        """Set the agent instance."""
        self._agent = agent

    def set_memory(self, memory):
        """Set the memory instance."""
        self._memory = memory

    def set_session_manager(self, session_manager):
        """Set the session manager instance."""
        self._session_manager = session_manager

    def on_message(self, handler: Callable) -> None:
        """Register message handler."""
        self._message_handler = handler
        logger.info(f"[QQ] Message handler registered: {handler}")

    async def handle_webhook(self, data: dict) -> dict:
        """Handle incoming webhook from QQ.

        Args:
            data: Webhook payload from QQ

        Returns:
            Response dict
        """
        try:
            logger.info(f"[QQ] Received webhook: {json.dumps(data, ensure_ascii=False)[:200]}")
            logger.info(f"[QQ] _message_handler is set: {self._message_handler is not None}")

            # Check if this is a validation request (op: 13)
            op = data.get("op")
            if op == 13:
                # Callback address validation
                d = data.get("d", {})
                plain_token = d.get("plain_token", "")
                event_ts = d.get("event_ts", "")

                logger.info(f"[QQ] Validation request: plain_token={plain_token}, event_ts={event_ts}")

                # Generate signature
                signature = self._generate_signature(plain_token, event_ts)

                response = {
                    "plain_token": plain_token,
                    "signature": signature
                }

                logger.info(f"[QQ] Validation response: {response}")
                return response

            # Handle regular events (op: 0)
            if op == 0:
                event_type = data.get("t", "")
                event_data = data.get("d", {})

                logger.info(f"[QQ] Event: {event_type}")

                # Handle different event types
                if event_type == "C2C_MESSAGE_CREATE":
                    # User sent a direct message to bot
                    await self._handle_c2c_message(event_data)

                elif event_type == "GROUP_AT_MESSAGE_CREATE":
                    # User @mentioned bot in a group
                    await self._handle_group_message(event_data)

                elif event_type == "FRIEND_ADD":
                    # User added bot as friend
                    logger.info(f"[QQ] Friend added: {event_data}")

                elif event_type == "FRIEND_DEL":
                    # User removed bot from friends
                    logger.info(f"[QQ] Friend removed: {event_data}")

                elif event_type == "GROUP_ADD_ROBOT":
                    # Bot added to group
                    logger.info(f"[QQ] Bot added to group: {event_data}")

                elif event_type == "GROUP_DEL_ROBOT":
                    # Bot removed from group
                    logger.info(f"[QQ] Bot removed from group: {event_data}")

                return {"code": 0, "message": "ok"}

            # Default response for other ops
            return {"code": 0, "message": "ok"}

        except Exception as e:
            logger.error(f"[QQ] Webhook error: {e}")
            return {"code": -1, "message": str(e)}

    async def _handle_c2c_message(self, data: dict) -> None:
        """Handle C2C (direct) message from user.

        Args:
            data: Message event data
        """
        try:
            msg_id = data.get("id", "")
            content = data.get("content", "")
            author = data.get("author", {})
            user_openid = author.get("user_openid", "")

            logger.info(f"[QQ] C2C message from {user_openid}: {content[:100]}")
            logger.info(f"[QQ] Message ID: {msg_id}")

            if not content.strip():
                return

            # Store message to local storage
            await self._store_message({
                "type": "c2c",
                "msg_id": msg_id,
                "user_openid": user_openid,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            })

            # Process message and get response
            session_id = f"qq:{user_openid}"

            # Store user message to memory for web UI access
            if self._memory:
                await self._memory.store_conversation(
                    session_id=session_id,
                    user_message=content,
                    channel="qq",
                    sender=user_openid,
                )

            # Get agent response
            response = ""
            if self._agent:
                response = await self._agent.run(content, session_id, user_openid)
            else:
                response = f"您好，我收到了您的消息：「{content}」。当前 Agent 未初始化，请稍后再试。"

            # Store assistant response to memory
            if self._memory and response:
                await self._memory.store_conversation(
                    session_id=session_id,
                    assistant_message=response,
                    channel="qq",
                    sender=user_openid,
                )

            # Send response to QQ (生成新的msg_id，不使用原来的msg_id)
            import uuid
            reply_msg_id = str(uuid.uuid4())
            await self._send_c2c_message(user_openid, response, reply_msg_id)

        except Exception as e:
            logger.error(f"[QQ] Handle C2C message error: {e}")
            import traceback
            traceback.print_exc()

    async def _handle_group_message(self, data: dict) -> None:
        """Handle group message with @mention.

        Args:
            data: Message event data
        """
        try:
            msg_id = data.get("id", "")
            content = data.get("content", "")
            author = data.get("author", {})
            member_openid = author.get("member_openid", "")
            group_openid = data.get("group_openid", "")

            logger.info(f"[QQ] Group message from {member_openid} in {group_openid}: {content[:100]}")

            if not content.strip():
                return

            # Store message to local storage
            await self._store_message({
                "type": "group",
                "msg_id": msg_id,
                "group_openid": group_openid,
                "member_openid": member_openid,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            })

            # Process message and get response
            session_id = f"qq:group:{group_openid}:{member_openid}"

            # Store user message to memory for web UI access
            if self._memory:
                await self._memory.store_conversation(
                    session_id=session_id,
                    user_message=content,
                    channel="qq",
                    sender=member_openid,
                )

            # Get agent response
            response = ""
            if self._agent:
                response = await self._agent.run(content, session_id, member_openid)
            else:
                response = f"您好，我收到了您的消息：「{content}」。当前 Agent 未初始化，请稍后再试。"

            # Store assistant response to memory
            if self._memory and response:
                await self._memory.store_conversation(
                    session_id=session_id,
                    assistant_message=response,
                    channel="qq",
                    sender=member_openid,
                )

            # Send response to group (生成新的msg_id)
            import uuid
            reply_msg_id = str(uuid.uuid4())
            await self._send_group_message(group_openid, response, reply_msg_id)

        except Exception as e:
            logger.error(f"[QQ] Handle group message error: {e}")
            import traceback
            traceback.print_exc()

    async def _store_message(self, message: dict) -> None:
        """Store message to local storage.

        Args:
            message: Message data to store
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            file_path = self.storage_dir / f"messages_{today}.json"

            # Read existing messages
            messages = []
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    messages = json.load(f)

            # Append new message
            messages.append(message)

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"[QQ] Store message error: {e}")

    async def send_message(self, target: str, message: str, **kwargs) -> bool:
        """Send message to QQ user or group.

        Args:
            target: User openid or group openid
            message: Message content
            **kwargs: Additional options (msg_type, group_openid, msg_id, etc.)

        Returns:
            True if successful
        """
        try:
            msg_type = kwargs.get("msg_type", "c2c")
            msg_id = kwargs.get("msg_id")

            if msg_type == "group":
                # Send to group
                group_openid = kwargs.get("group_openid", target)
                result = await self._send_group_message(group_openid, message, msg_id)
            else:
                # Send direct message
                result = await self._send_c2c_message(target, message, msg_id)

            return result

        except Exception as e:
            logger.error(f"[QQ] Send message error: {e}")
            return False

    async def _send_c2c_message(self, user_openid: str, content: str, msg_id: str = None) -> bool:
        """Send direct message to user.

        Args:
            user_openid: User's openid
            content: Message content
            msg_id: Original message ID for reply

        Returns:
            True if successful
        """
        try:
            import aiohttp

            # Get access token
            token = await self._get_access_token()
            if not token:
                return False

            url = f"{self._api_base}/v2/users/{user_openid}/messages"

            payload = {
                "content": content,
                "msg_type": 0,  # Text message
            }

            # Add msg_id if provided (for reply)
            if msg_id:
                payload["msg_id"] = msg_id

            headers = {
                "Authorization": f"QQBot {token}",
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        logger.info(f"[QQ] Message sent to {user_openid}")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"[QQ] Send message failed: {resp.status} - {error}")
                        return False

        except Exception as e:
            logger.error(f"[QQ] Send C2C message error: {e}")
            return False

    async def _send_group_message(self, group_openid: str, content: str, msg_id: str = None) -> bool:
        """Send message to group.

        Args:
            group_openid: Group's openid
            content: Message content
            msg_id: Original message ID for reply

        Returns:
            True if successful
        """
        try:
            import aiohttp

            # Get access token
            token = await self._get_access_token()
            if not token:
                return False

            url = f"{self._api_base}/v2/groups/{group_openid}/messages"

            payload = {
                "content": content,
                "msg_type": 0,  # Text message
            }

            # Add msg_id if provided (for reply)
            if msg_id:
                payload["msg_id"] = msg_id

            headers = {
                "Authorization": f"QQBot {token}",
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        logger.info(f"[QQ] Message sent to group {group_openid}")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"[QQ] Send group message failed: {resp.status} - {error}")
                        return False

        except Exception as e:
            logger.error(f"[QQ] Send group message error: {e}")
            return False

    async def _get_access_token(self) -> Optional[str]:
        """Get QQ bot access token.

        Returns:
            Access token string or None
        """
        try:
            import aiohttp
            import time

            # Check if token is still valid
            if self._access_token and time.time() < self._token_expires_at:
                return self._access_token

            # Request new token
            url = "https://bots.qq.com/app/getAppAccessToken"

            payload = {
                "appId": self.bot_id,
                "clientSecret": self.bot_secret,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._access_token = data.get("access_token")
                        expires_in = int(data.get("expires_in", 7200))
                        self._token_expires_at = time.time() + expires_in - 300  # 5 min buffer

                        logger.info(f"[QQ] Access token refreshed, expires in {expires_in}s")
                        return self._access_token
                    else:
                        error = await resp.text()
                        logger.error(f"[QQ] Get access token failed: {resp.status} - {error}")
                        return None

        except Exception as e:
            logger.error(f"[QQ] Get access token error: {e}")
            return None

    async def start(self) -> None:
        """Start the QQ channel."""
        logger.info("[QQ] Channel started (webhook mode)")
        self._is_running = True

    async def stop(self) -> None:
        """Stop the QQ channel."""
        logger.info("[QQ] Channel stopped")
        self._is_running = False

    def get_info(self) -> dict:
        """Get channel information."""
        info = super().get_info()
        info.update({
            "bot_id": self.bot_id,
            "sandbox": self.sandbox,
            "api_base": self._api_base,
        })
        return info
