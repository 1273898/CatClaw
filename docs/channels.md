# CatClaw 渠道接入指南

## QQ 机器人

### 1. 注册 QQ 开放平台

访问 https://q.qq.com 注册并创建机器人应用。

### 2. 获取凭证

在开放平台获取：
- **Bot ID** (AppID)
- **Bot Token** (AppSecret)
- **Bot Secret** (用于验证)

### 3. 配置 webhook

在开放平台设置回调地址：
```
http://你的域名:8000/webhook/qq
```

如果是本地开发，可以使用内网穿透工具（如 ngrok）。

### 4. 修改配置

编辑 `.env` 文件：

```env
CHANNEL_QQ_ENABLED=true
CHANNEL_QQ_BOT_ID=你的BotID
CHANNEL_QQ_BOT_TOKEN=你的BotToken
CHANNEL_QQ_BOT_SECRET=你的BotSecret
CHANNEL_QQ_SANDBOX=false  # 生产环境设为false
```

### 5. 权限设置

在开放平台配置机器人权限：
- 发送消息
- 接收消息
- @消息

---

## 飞书机器人

### 1. 注册飞书开放平台

访问 https://open.feishu.cn 注册并创建应用。

### 2. 获取凭证

在应用管理页面获取：
- **App ID**
- **App Secret**
- **Verification Token** (事件订阅)
- **Encrypt Key** (可选，用于事件加密)

### 3. 配置事件订阅

在飞书开放平台设置：
- **请求网址 URL**: `http://你的域名:8000/webhook/feishu`
- **事件订阅**: 添加 `im.message.receive_v1` 事件

### 4. 启用机器人能力

在应用能力中启用"机器人"功能。

### 5. 修改配置

编辑 `.env` 文件：

```env
CHANNEL_FEISHU_ENABLED=true
CHANNEL_FEISHU_APP_ID=你的AppID
CHANNEL_FEISHU_APP_SECRET=你的AppSecret
CHANNEL_FEISHU_VERIFICATION_TOKEN=你的VerificationToken
CHANNEL_FEISHU_ENCRYPT_KEY=你的EncryptKey  # 可选
```

### 6. 权限配置

在应用权限中申请：
- `im:message` - 获取与发送单聊、群组消息
- `im:message:send_as_bot` - 以应用的身份发消息

---

## Webhook 说明

CatClaw 使用 webhook 接收消息，端点地址：

| 渠道 | Webhook 地址 |
|------|-------------|
| QQ | `http://域名:8000/webhook/qq` |
| 飞书 | `http://域名:8000/webhook/feishu` |

---

## 本地开发

如果在本地开发，需要使用内网穿透工具让外部能访问你的服务：

### 使用 ngrok

```bash
# 安装 ngrok
npm install -g ngrok

# 启动隧道
ngrok http 8000
```

然后将 ngrok 提供的 URL 配置到开放平台。

### 使用 cpolar

```bash
# 安装 cpolar
# 访问 https://www.cpolar.com

# 启动隧道
cpolar http 8000
```

---

## 测试

启动服务后：

```powershell
.\run.bat serve
```

检查渠道状态：
```powershell
curl http://localhost:8000/api/status
```

应该能看到已启用的渠道列表。

---

## 常见问题

### Q: QQ 机器人收不到消息？

1. 检查 Bot ID 和 Token 是否正确
2. 确认 webhook URL 配置正确
3. 检查是否在沙箱模式（测试用）
4. 确认机器人已上线

### Q: 飞书机器人回复失败？

1. 检查 App ID 和 Secret 是否正确
2. 确认事件订阅 URL 可访问
3. 检查权限是否申请通过
4. 查看服务日志排查错误

### Q: 如何同时使用多个渠道？

在 `.env` 中同时启用多个渠道：

```env
CHANNEL_WEB_ENABLED=true
CHANNEL_QQ_ENABLED=true
CHANNEL_FEISHU_ENABLED=true
```

所有渠道共享同一个 Agent 实例。
