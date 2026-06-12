/**
 * PrivateClaw Web UI - 主应用程序
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
        // 聊天元素
        this.chatContainer = document.getElementById('chatContainer');
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.messagesList = document.getElementById('messagesList');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');

        // 侧边栏元素
        this.sidebar = document.getElementById('sidebar');
        this.sessionList = document.getElementById('sessionList');
        this.toolsList = document.getElementById('toolsList');
        this.sessionCount = document.getElementById('sessionCount');
        this.toolCount = document.getElementById('toolCount');

        // 设置元素
        this.settingsOverlay = document.getElementById('settingsOverlay');
        this.settingsPanel = document.getElementById('settingsPanel');
        this.settingsForm = document.getElementById('settingsForm');

        // 头部元素
        this.headerTitle = document.querySelector('.header-title');
        this.currentModel = document.getElementById('currentModel');
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
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';

            // 更新发送按钮状态
            this.sendButton.disabled = !this.messageInput.value.trim();
        });

        // 发送按钮点击
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // 切换侧边栏
        document.getElementById('toggleSidebar')?.addEventListener('click', () => {
            this.sidebar.classList.toggle('visible');
        });

        // 切换设置面板
        document.getElementById('toggleSettings')?.addEventListener('click', () => {
            this.settingsOverlay.classList.add('active');
        });

        // 关闭设置面板
        document.getElementById('closeSettings')?.addEventListener('click', () => {
            this.settingsOverlay.classList.remove('active');
        });

        // 点击遮罩关闭设置
        this.settingsOverlay?.addEventListener('click', (e) => {
            if (e.target === this.settingsOverlay) {
                this.settingsOverlay.classList.remove('active');
            }
        });

        // 新建会话
        document.getElementById('newSession')?.addEventListener('click', () => {
            this.newSession();
        });

        // 清空聊天
        document.getElementById('clearChat')?.addEventListener('click', () => {
            this.clearChat();
        });

        // 导出聊天
        document.getElementById('exportChat')?.addEventListener('click', () => {
            this.exportChat();
        });

        // 快捷操作
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', () => {
                const message = btn.dataset.message;
                if (message) {
                    this.messageInput.value = message;
                    this.sendMessage();
                }
            });
        });

        // 保存设置
        this.settingsForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });

        // 温度滑块
        const tempSlider = document.querySelector('.settings-range[name="temperature"]');
        const tempValue = document.querySelector('.temperature-value');
        if (tempSlider && tempValue) {
            tempSlider.addEventListener('input', () => {
                tempValue.textContent = tempSlider.value;
            });
        }

        // 快捷键
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K: 聚焦输入框
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.messageInput.focus();
            }

            // Escape: 关闭设置
            if (e.key === 'Escape') {
                this.settingsOverlay.classList.remove('active');
            }
        });
    }

    // WebSocket 连接
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
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        if (statusDot) {
            statusDot.className = 'status-dot ' + (status === 'connected' ? 'online' : 'offline');
        }

        if (statusText) {
            const statusTexts = {
                'connected': '在线',
                'disconnected': '离线',
                'connecting': '连接中...'
            };
            statusText.textContent = statusTexts[status] || status;
        }
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

    // 消息处理
    sendMessage() {
        const content = this.messageInput.value.trim();
        if (!content) return;

        this.addMessage(content, 'user');
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.sendButton.disabled = true;
        this.showTyping();

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'message',
                content: content,
                session_id: this.sessionId,
            }));
        } else {
            // 回退到 HTTP
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
        // 隐藏欢迎页面，显示消息列表
        if (this.welcomeScreen) {
            this.welcomeScreen.style.display = 'none';
        }
        if (this.messagesList) {
            this.messagesList.style.display = 'flex';
        }

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

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = message.role === 'user'
            ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
            : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';

        const senderSpan = document.createElement('span');
        senderSpan.className = 'message-sender';
        senderSpan.textContent = message.role === 'user' ? '你' : 'PrivateClaw';

        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = this.formatTime(message.timestamp);

        headerDiv.appendChild(senderSpan);
        headerDiv.appendChild(timeSpan);

        const bodyDiv = document.createElement('div');
        bodyDiv.className = 'message-body';
        bodyDiv.textContent = message.content;

        contentDiv.appendChild(headerDiv);
        contentDiv.appendChild(bodyDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        this.messagesList.appendChild(messageDiv);
    }

    renderMessages() {
        if (!this.messagesList) return;

        this.messagesList.innerHTML = '';

        if (this.messages.length === 0) {
            if (this.welcomeScreen) {
                this.welcomeScreen.style.display = 'flex';
            }
            this.messagesList.style.display = 'none';
        } else {
            if (this.welcomeScreen) {
                this.welcomeScreen.style.display = 'none';
            }
            this.messagesList.style.display = 'flex';
            this.messages.forEach(msg => this.renderMessage(msg));
        }

        this.scrollToBottom();
    }

    scrollToBottom() {
        if (this.messagesList) {
            this.messagesList.scrollTop = this.messagesList.scrollHeight;
        }
    }

    formatTime(date) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }

    showTyping() {
        if (this.typingIndicator) {
            this.typingIndicator.classList.add('active');
            this.scrollToBottom();
        }
    }

    hideTyping() {
        if (this.typingIndicator) {
            this.typingIndicator.classList.remove('active');
        }
    }

    // 会话管理
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
        if (!this.sessionList) return;

        this.sessionList.innerHTML = '';
        this.sessionCount.textContent = sessions.length;

        sessions.forEach(sessionId => {
            const li = document.createElement('li');
            li.className = 'session-item' + (sessionId === this.sessionId ? ' active' : '');
            li.innerHTML = `
                <span class="session-name">${sessionId}</span>
                <button class="session-delete" onclick="app.deleteSession('${sessionId}')">×</button>
            `;
            li.addEventListener('click', (e) => {
                if (!e.target.classList.contains('session-delete')) {
                    this.switchSession(sessionId);
                }
            });
            this.sessionList.appendChild(li);
        });
    }

    switchSession(sessionId) {
        this.sessionId = sessionId;
        this.messages = [];
        this.renderMessages();
        this.loadSessionHistory(sessionId);
        this.loadSessions();

        // 更新头部标题
        if (this.headerTitle) {
            this.headerTitle.textContent = sessionId;
        }
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

        // 更新头部标题
        if (this.headerTitle) {
            this.headerTitle.textContent = '新对话';
        }

        // 聚焦输入框
        this.messageInput.focus();
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

    exportChat() {
        if (this.messages.length === 0) {
            alert('没有可导出的消息');
            return;
        }

        const exportData = {
            sessionId: this.sessionId,
            exportTime: new Date().toISOString(),
            messages: this.messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp.toISOString(),
            })),
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `privateclaw-chat-${this.sessionId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // 工具列表
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
        if (!this.toolsList) return;

        this.toolsList.innerHTML = '';
        this.toolCount.textContent = tools.length;

        tools.forEach(tool => {
            const li = document.createElement('li');
            li.className = 'tool-item';
            li.innerHTML = `
                <span class="tool-name">${tool.name}</span>
                <span class="tool-badge">${tool.category}</span>
            `;
            this.toolsList.appendChild(li);
        });
    }

    // 设置
    saveSettings() {
        // TODO: 实现设置保存
        console.log('设置已保存');
        this.settingsOverlay.classList.remove('active');
    }
}

// 初始化应用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new PrivateClawApp();
});
