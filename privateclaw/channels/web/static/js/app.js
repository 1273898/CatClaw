/**
 * PrivateClaw Web UI - Main Application
 */

class PrivateClawApp {
    constructor() {
        this.ws = null;
        this.sessionId = this.generateSessionId();
        this.messages = [];
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.initElements();
        this.initEventListeners();
        this.connectWebSocket();
        this.loadSessions();
        this.loadTools();
    }

    generateSessionId() {
        return 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initElements() {
        // Chat elements
        this.chatContainer = document.getElementById('chatContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');

        // Sidebar elements
        this.sidebar = document.getElementById('sidebar');
        this.sessionList = document.getElementById('sessionList');
        this.toolsList = document.getElementById('toolsList');

        // Settings elements
        this.settingsPanel = document.getElementById('settingsPanel');
        this.settingsForm = document.getElementById('settingsForm');

        // Status elements
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.connectionStatus = document.getElementById('connectionStatus');
    }

    initEventListeners() {
        // 发送消息 (Enter键)
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 自动调整输入框高度
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
        });

        // 发送按钮点击
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // 切换侧边栏
        document.getElementById('toggleSidebar')?.addEventListener('click', () => {
            this.sidebar.classList.toggle('hidden');
        });

        // 切换设置面板
        document.getElementById('toggleSettings')?.addEventListener('click', () => {
            this.settingsPanel.classList.toggle('active');
        });

        // 关闭设置面板
        document.getElementById('closeSettings')?.addEventListener('click', () => {
            this.settingsPanel.classList.remove('active');
        });

        // 新建会话
        document.getElementById('newSession')?.addEventListener('click', () => {
            this.newSession();
        });

        // 清空聊天
        document.getElementById('clearChat')?.addEventListener('click', () => {
            this.clearChat();
        });

        // 保存设置
        this.settingsForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });
    }

    // WebSocket Connection
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws?session_id=${this.sessionId}`;

        this.updateConnectionStatus('connecting');

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket 已连接');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('解析消息失败:', e);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket 已断开');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
                this.updateConnectionStatus('disconnected');
            };
        } catch (e) {
            console.error('连接 WebSocket 失败:', e);
            this.updateConnectionStatus('disconnected');
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`${delay}ms 后重连 (第 ${this.reconnectAttempts} 次尝试)`);
            setTimeout(() => this.connectWebSocket(), delay);
        }
    }

    updateConnectionStatus(status) {
        this.statusDot.className = 'status-dot ' + status;
        const statusTexts = {
            'connected': '已连接',
            'disconnected': '已断开',
            'connecting': '连接中...'
        };
        this.statusText.textContent = statusTexts[status] || status;
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.hideTyping();
                this.addMessage(data.content, 'assistant');
                break;
            case 'error':
                this.hideTyping();
                this.addMessage('错误: ' + data.content, 'error');
                break;
            case 'cleared':
                this.messages = [];
                this.renderMessages();
                break;
            case 'pong':
                // 保活响应
                break;
            default:
                console.log('未知消息类型:', data.type);
        }
    }

    // Message Handling
    sendMessage() {
        const content = this.messageInput.value.trim();
        if (!content) return;

        this.addMessage(content, 'user');
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.showTyping();

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'message',
                content: content,
                session_id: this.sessionId,
            }));
        } else {
            // Fallback to HTTP
            this.sendViaHttp(content);
        }
    }

    async sendViaHttp(content) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: content,
                    session_id: this.sessionId,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            const data = await response.json();
            this.hideTyping();
            this.addMessage(data.response, 'assistant');
        } catch (error) {
            this.hideTyping();
            this.addMessage('错误: ' + error.message, 'error');
        }
    }

    addMessage(content, role) {
        const message = {
            id: Date.now(),
            content: content,
            role: role,
            timestamp: new Date(),
        };

        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.dataset.id = message.id;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message.content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(message.timestamp);

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);

        this.chatContainer.appendChild(messageDiv);
    }

    renderMessages() {
        this.chatContainer.innerHTML = '';
        this.messages.forEach(msg => this.renderMessage(msg));
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    showTyping() {
        this.typingIndicator.classList.add('active');
        this.scrollToBottom();
    }

    hideTyping() {
        this.typingIndicator.classList.remove('active');
    }

    // Session Management
    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            if (response.ok) {
                const data = await response.json();
                this.renderSessions(data.sessions);
            }
        } catch (e) {
            console.error('加载会话失败:', e);
        }
    }

    renderSessions(sessions) {
        this.sessionList.innerHTML = '';

        sessions.forEach(sessionId => {
            const li = document.createElement('li');
            li.className = 'session-item' + (sessionId === this.sessionId ? ' active' : '');
            li.innerHTML = `
                <div>
                    <div class="session-name">${sessionId}</div>
                </div>
                <button class="session-delete" onclick="app.deleteSession('${sessionId}')">×</button>
            `;
            li.addEventListener('click', () => this.switchSession(sessionId));
            this.sessionList.appendChild(li);
        });
    }

    switchSession(sessionId) {
        this.sessionId = sessionId;
        this.messages = [];
        this.renderMessages();
        this.loadSessionHistory(sessionId);
        this.loadSessions();
    }

    async loadSessionHistory(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}/history`);
            if (response.ok) {
                const data = await response.json();
                data.history.forEach(msg => {
                    this.addMessage(msg.content, msg.role);
                });
            }
        } catch (e) {
            console.error('加载会话历史失败:', e);
        }
    }

    newSession() {
        this.sessionId = this.generateSessionId();
        this.messages = [];
        this.renderMessages();
        this.loadSessions();
    }

    async deleteSession(sessionId) {
        try {
            await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
            if (sessionId === this.sessionId) {
                this.newSession();
            }
            this.loadSessions();
        } catch (e) {
            console.error('删除会话失败:', e);
        }
    }

    clearChat() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'clear',
                session_id: this.sessionId,
            }));
        }
        this.messages = [];
        this.renderMessages();
    }

    // Tools
    async loadTools() {
        try {
            const response = await fetch('/api/tools');
            if (response.ok) {
                const data = await response.json();
                this.renderTools(data.tools);
            }
        } catch (e) {
            console.error('加载工具失败:', e);
        }
    }

    renderTools(tools) {
        this.toolsList.innerHTML = '';

        tools.forEach(tool => {
            const li = document.createElement('li');
            li.className = 'tool-item';
            li.innerHTML = `
                <div class="tool-name">${tool.name}</div>
                <div class="tool-description">${tool.description}</div>
                <span class="tool-category">${tool.category}</span>
            `;
            this.toolsList.appendChild(li);
        });
    }

    // Settings
    saveSettings() {
        // TODO: 实现设置保存
        console.log('设置已保存');
        this.settingsPanel.classList.remove('active');
    }
}

// Initialize app
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new PrivateClawApp();
});
