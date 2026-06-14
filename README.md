<div align="center">

# 🐱 CatClaw

**你的私人 AI 助手，由 LangChain 驱动**

*一只高冷腹黑的小猫转化来的 AI 助理*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-green.svg)](https://langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能特性](#-功能特性) · [快速开始](#-快速开始) · [部署指南](#-部署指南) · [架构设计](#-架构设计)

</div>

---

## ✨ 功能特性

### 🤖 AI 对话
- 基于 DeepSeek / OpenAI 的智能对话
- 流式输出，实时响应
- Markdown 格式渲染
- 多轮上下文记忆

### 🧠 记忆系统
- **短期记忆** - 对话历史持久化
- **长期记忆** - 向量数据库语义搜索
- **记忆整合** - 自动总结和提炼

### 🔧 工具系统
- 文件读写操作
- 终端命令执行
- 网页搜索（DuckDuckGo）
- 数学计算
- URL 内容抓取

### 📚 技能系统
- 从 Markdown 文件加载技能
- 自动学习用户行为模式
- 置信度评分机制
- 可视化技能管理

### 💬 多渠道接入
- Web 界面（默认）
- QQ 机器人
- 飞书机器人
- Telegram / Discord / Slack（扩展）

### 🐱 桌面宠物
- 可爱的猫咪动画
- 拖拽互动
- 多种动作状态

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+（前端构建）
- pip

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/catclaw.git
cd catclaw

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 5. 构建前端
cd frontend
npm install
npm run build
cp -r dist/* ../privateclaw/channels/web/static/

# 6. 启动服务
cd ..
python run.py serve
```

### 访问

打开浏览器访问 `http://localhost:8000`

---

## 📁 项目结构

```
CatClaw/
├── privateclaw/              # 核心代码
│   ├── core/
│   │   ├── agent/           # AI Agent
│   │   ├── memory/          # 记忆系统
│   │   ├── tools/           # 工具系统
│   │   ├── skills/          # 技能系统
│   │   └── llm/             # LLM 集成
│   ├── channels/            # 渠道实现
│   │   ├── web/             # Web 界面
│   │   ├── qq/              # QQ 机器人
│   │   └── feishu/          # 飞书机器人
│   ├── config/              # 配置管理
│   └── api/                 # API 接口
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   └── App.jsx         # 主应用
│   └── public/             # 静态资源
├── skills/                  # 技能定义（Markdown）
├── prompts/                 # 提示词文档
├── data/                    # 运行时数据（gitignore）
├── .env.example             # 环境变量模板
├── requirements.txt         # Python 依赖
└── run.py                   # 启动脚本
```

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      用户界面层                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Web 界面 │  │ QQ 机器人 │  │ 飞书机器人│  │  CLI    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
└───────┼──────────────┼──────────────┼─────────────┼──────┘
        │              │              │             │
┌───────┴──────────────┴──────────────┴─────────────┴──────┐
│                      渠道路由层                          │
│              统一消息处理和响应分发                        │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│                      Agent 核心                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  LLM 调用    │  │  工具执行    │  │  技能匹配    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│                      记忆系统                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  短期记忆    │  │  长期记忆    │  │  记忆整合    │   │
│  │  (JSON)      │  │  (ChromaDB)  │  │  (自动)      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_API_KEY` | LLM API 密钥 | - |
| `LLM_API_BASE` | API 地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名称 | `deepseek-v4-flash` |
| `GATEWAY_SECRET_KEY` | 安全密钥 | 需要修改 |
| `CHANNEL_WEB_PORT` | Web 端口 | `8000` |

### 技能定义

在 `skills/` 目录创建 Markdown 文件：

```markdown
---
name: my_skill
type: custom
description: 技能描述
triggers:
  - 触发词1
  - 触发词2
tags:
  - 标签1
confidence: 0.8
---

# 技能名称

技能说明...

## 代码

```python
class MyTool(PrivateClawTool):
    name = "my_tool"
    description = "工具描述"

    def _run(self, input: str) -> str:
        return "结果"
```
```

---

## 🚢 部署指南

### Docker 部署（推荐）

```bash
docker build -t catclaw .
docker run -d -p 8000:8000 --env-file .env catclaw
```

### 服务器部署

详见 [部署文档](docs/deployment.md)

### 使用宝塔面板

1. 上传项目到 `/www/wwwroot/catclaw`
2. 安装 Python 3.11+
3. 配置虚拟环境和依赖
4. 添加 systemd 服务
5. 配置 Nginx 反向代理

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 MIT 许可证开源 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [LangChain](https://langchain.com/) - AI 应用框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://reactjs.org/) - 前端框架
- [Material UI](https://mui.com/) - UI 组件库
- [ChromaDB](https://www.trychroma.com/) - 向量数据库

---

<div align="center">

**如果觉得有用，请给个 ⭐ Star 支持一下！**

Made with 🐱 by CatClaw Team

</div>
