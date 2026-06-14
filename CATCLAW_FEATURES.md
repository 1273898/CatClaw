# CatClaw 功能完整说明

## 核心特性

CatClaw 是一个受 OpenClaw 启发的个人 AI 助手，具备**持续自我改进**的能力。

### 🧠 自我改进系统

**核心理念**：通过与用户的每一次交互，不断学习和改进自己。

#### 功能：
1. **用户画像构建**
   - 自动分析用户的沟通风格（正式/随意/中性）
   - 记录用户的话题偏好
   - 跟踪交互历史和模式

2. **个性化响应**
   - 根据用户偏好调整响应风格
   - 记住用户喜欢和不喜欢的响应模式
   - 自动适应用户的沟通习惯

3. **反馈学习**
   - 支持显式反馈（满意度评分、喜欢/不喜欢）
   - 从隐式反馈中学习（用户纠正、重新提问）
   - 持续优化响应质量

### 💾 智能记忆系统

#### 短期记忆
- 维护当前对话的上下文
- 支持多轮对话连贯性

#### 长期记忆
- 基于向量数据库的语义存储
- 支持相关记忆检索
- 跨会话的知识保留

#### 记忆整合
- **自动对话总结**：对话结束后自动提取关键信息
- **偏好提取**：识别并存储用户偏好
- **事实提取**：记录用户提到的重要事实
- **行动项识别**：提取需要后续跟进的任务

### 🎯 技能学习系统

#### 可学习的技能类型：
1. **工具使用模式**
   - 学习在什么情况下使用哪些工具
   - 基于成功率调整工具选择

2. **响应模式**
   - 学习用户喜欢的响应风格
   - 优化回答的结构和语气

3. **工作流自动化**
   - 识别重复性任务模式
   - 自动化常见操作序列

#### 技能管理：
- 置信度评分：技能使用越多，置信度越高
- 自动清理：长时间未使用的低置信度技能会被移除
- 导入/导出：支持技能的备份和恢复

### 🌙 梦境记忆系统

受人类睡眠周期启发的三阶段记忆处理：

1. **轻度梦境**（每6小时）
   - 快速去重
   - 移除低质量记忆
   - 组织近期记忆

2. **深度梦境**（每24小时）
   - 质量评估
   - 高质量记忆提升
   - 低质量记忆归档

3. **REM梦境**（每周）
   - 跨记忆模式识别
   - 知识综合
   - 建立知识连接

### 🔧 工具系统

内置工具：
- **terminal**：沙箱化终端执行
- **fetch_url**：网页内容抓取和清理
- **read_file**：沙箱化文件读取
- **web_search**：网络搜索
- **calculator**：计算器

### 📱 多渠道支持

- **Web界面**：现代化的 React 前端
- **CLI**：命令行交互
- **可扩展**：支持 Telegram、Discord、Slack 等

## API 端点

### 对话相关
- `POST /api/chat` - 发送消息
- `POST /api/chat/stream` - 流式响应
- `POST /api/feedback` - 提供反馈

### 记忆相关
- `POST /api/memory/search` - 搜索记忆
- `POST /api/memory/ingest` - 存储记忆
- `POST /api/memory/consolidate` - 触发记忆整合
- `GET /api/memory/consolidation/stats` - 整合统计

### 技能相关
- `GET /api/skills/stats` - 技能学习统计
- `GET /api/skills/export` - 导出技能
- `POST /api/skills/import` - 导入技能

### 用户相关
- `GET /api/user/profile/{user_id}` - 获取用户画像
- `GET /api/improvement/stats` - 自我改进统计

### 其他
- `GET /api/sessions` - 会话管理
- `GET /api/tools` - 工具列表
- `GET /api/prompts/` - 提示词管理
- `GET/PUT /api/settings` - 设置管理

## 使用示例

### 基本对话
```bash
# 启动服务
.\run.bat serve

# 访问 Web 界面
http://localhost:8000
```

### 提供反馈
```javascript
// 在 Web 界面中或通过 API
await fetch('/api/feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'my_session',
    user_id: 'my_user',
    satisfaction: 0.9,
    liked: true,
    comment: '回答很有帮助'
  })
})
```

### 查看学习进度
```javascript
// 查看用户画像
const profile = await fetch('/api/user/profile/my_user').then(r => r.json())

// 查看技能统计
const stats = await fetch('/api/skills/stats').then(r => r.json())

// 查看改进统计
const improvement = await fetch('/api/improvement/stats').then(r => r.json())
```

## 配置

在 `.env` 文件中配置：

```env
# LLM 配置
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_api_key
LLM_API_BASE=https://api.deepseek.com

# 记忆配置
MEMORY_SHORT_TERM_LIMIT=50
MEMORY_LONG_TERM_ENABLED=true
MEMORY_VECTOR_STORE=chroma
MEMORY_VECTOR_STORE_PATH=./data/chroma
```

## 技术架构

```
catclaw/
├── core/
│   ├── agent/           # LangChain Agent
│   ├── memory/          # 记忆系统
│   │   ├── short_term   # 短期记忆
│   │   ├── long_term    # 长期记忆
│   │   └── consolidation # 记忆整合
│   ├── skills/          # 技能学习
│   ├── self_improvement # 自我改进
│   ├── tools/           # 工具系统
│   ├── rag/             # RAG 和梦境系统
│   └── session/         # 会话管理
├── channels/
│   ├── web/             # Web 界面
│   └── cli/             # CLI 界面
├── api/                 # API 端点
├── config/              # 配置管理
└── gateway/             # 网关服务
```

## 与 OpenClaw 的对比

| 特性 | OpenClaw | CatClaw |
|------|----------|---------|
| 自我改进 | ✅ | ✅ |
| 记忆系统 | ✅ | ✅ |
| 梦境处理 | ✅ | ✅ |
| 技能学习 | ✅ | ✅ |
| 用户画像 | ✅ | ✅ |
| 多渠道 | ✅ | ✅ (可扩展) |
| 开源 | ✅ | ✅ |

## 下一步计划

1. **增强 NLP**：使用更先进的 NLP 技术进行模式识别
2. **可视化学习进度**：在 Web 界面中展示学习曲线
3. **技能市场**：支持社区分享的技能包
4. **多模态支持**：支持图像、语音等多模态输入
5. **协作学习**：多实例间的知识共享
