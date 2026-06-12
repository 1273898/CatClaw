"""Web application for PrivateClaw."""

from typing import Optional
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from privateclaw.channels.web.api import create_api_router
from privateclaw.channels.web.websocket import WebSocketManager


def create_web_app(
    agent=None,
    memory=None,
    session_manager=None,
    ws_manager=None,
    config=None,
) -> FastAPI:
    """Create the Web application.

    Args:
        agent: PrivateClaw agent instance
        memory: Memory manager instance
        session_manager: Session manager instance
        ws_manager: WebSocket manager instance
        config: Configuration object

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="PrivateClaw",
        description="Your private AI assistant",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # WebSocket manager
    if ws_manager is None:
        ws_manager = WebSocketManager()

    # API router
    api_router = create_api_router(
        agent=agent,
        memory=memory,
        session_manager=session_manager,
        ws_manager=ws_manager,
    )
    app.include_router(api_router, prefix="/api")

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
        await ws_manager.connect(websocket, session_id)
        try:
            while True:
                data = await websocket.receive_json()
                await ws_manager.handle_message(websocket, data)
        except Exception:
            ws_manager.disconnect(websocket, session_id)

    # Static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Serve index.html at root
    @app.get("/", response_class=HTMLResponse)
    async def root():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return _get_default_index()

    return app


def _get_default_index() -> str:
    """Get default index HTML if static files don't exist."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrivateClaw</title>
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
        }
        .header {
            background: #16213e;
            padding: 16px 24px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header h1 {
            margin: 0;
            font-size: 20px;
            color: #e94560;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
        }
        .message.user {
            align-self: flex-end;
            background: #0f3460;
            border-bottom-right-radius: 4px;
        }
        .message.assistant {
            align-self: flex-start;
            background: #16213e;
            border-bottom-left-radius: 4px;
        }
        .input-container {
            padding: 16px 24px;
            background: #16213e;
            border-top: 1px solid #0f3460;
            display: flex;
            gap: 12px;
        }
        .input-container input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #0f3460;
            border-radius: 8px;
            background: #1a1a2e;
            color: #eee;
            font-size: 14px;
            outline: none;
        }
        .input-container input:focus {
            border-color: #e94560;
        }
        .input-container button {
            padding: 12px 24px;
            background: #e94560;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        .input-container button:hover {
            background: #c73e54;
        }
        .input-container button:disabled {
            background: #555;
            cursor: not-allowed;
        }
        .typing-indicator {
            display: none;
            align-self: flex-start;
            padding: 12px 16px;
            background: #16213e;
            border-radius: 12px;
            border-bottom-left-radius: 4px;
        }
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #e94560;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-8px); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🦞 PrivateClaw</h1>
        <span>Your Private AI Assistant</span>
    </div>
    <div class="chat-container" id="chatContainer">
        <div class="message assistant">
            Hello! I'm PrivateClaw, your private AI assistant. How can I help you today?
        </div>
    </div>
    <div class="typing-indicator" id="typingIndicator">
        <span></span><span></span><span></span>
    </div>
    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Type your message..." autocomplete="off">
        <button id="sendButton" onclick="sendMessage()">Send</button>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');

        let ws = null;
        let sessionId = 'web_' + Date.now();

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws?session_id=${sessionId}`);

            ws.onopen = () => {
                console.log('Connected to PrivateClaw');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'message') {
                    addMessage(data.content, 'assistant');
                    hideTyping();
                } else if (data.type === 'error') {
                    addMessage('Error: ' + data.content, 'assistant');
                    hideTyping();
                }
            };

            ws.onclose = () => {
                console.log('Disconnected from PrivateClaw');
                setTimeout(connectWebSocket, 3000);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        function addMessage(content, role) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            messageDiv.textContent = content;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function showTyping() {
            typingIndicator.style.display = 'block';
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function hideTyping() {
            typingIndicator.style.display = 'none';
        }

        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            messageInput.value = '';
            showTyping();

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'message',
                    content: message,
                    session_id: sessionId,
                }));
            } else {
                // Fallback to HTTP
                fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId,
                    }),
                })
                .then(res => res.json())
                .then(data => {
                    addMessage(data.response, 'assistant');
                    hideTyping();
                })
                .catch(err => {
                    addMessage('Error: ' + err.message, 'assistant');
                    hideTyping();
                });
            }
        }

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        connectWebSocket();
    </script>
</body>
</html>
"""
