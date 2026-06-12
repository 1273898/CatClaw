# 🦞 PrivateClaw

Your own private AI assistant, powered by LangChain.

## Features

- **LangChain-Powered Agent**: Built on LangChain for flexible, powerful AI agent capabilities
- **Multi-Channel Support**: Web, CLI, Telegram, Discord, Slack, and WeChat
- **Advanced Memory System**: Short-term conversation history and long-term vector-based memory
- **Task Planning**: Automatic task decomposition and execution planning
- **Extensible Tools**: Easy-to-use tool registration system with built-in tools
- **Local-First**: Your data stays on your device

## Quick Start

### Prerequisites

- Python 3.11+
- pip or poetry

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/privateclaw.git
cd privateclaw

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and settings
```

### Running

```bash
# Start the gateway server
privateclaw serve

# Or start interactive chat
privateclaw chat

# Ask a single question
privateclaw ask "What is the weather today?"
```

## Architecture

PrivateClaw is built with a modular architecture:

```
privateclaw/
├── core/           # Core engine
│   ├── agent/      # LangChain-based agent
│   ├── llm/        # LLM provider abstraction
│   ├── tools/      # Tool system
│   ├── memory/     # Multi-layer memory
│   └── session/    # Session management
├── channels/       # Channel adapters
│   ├── web/        # Web interface
│   ├── cli/        # CLI interface
│   ├── telegram/   # Telegram bot
│   ├── discord/    # Discord bot
│   ├── slack/      # Slack bot
│   └── wechat/     # WeChat integration
├── gateway/        # Gateway server
├── skills/         # Skill system
├── plugins/        # Plugin system
└── config/         # Configuration
```

### Core Components

#### Agent System

The agent is built on LangChain's agent framework with enhanced capabilities:

- **Task Planner**: Breaks down complex tasks into executable steps
- **Task Executor**: Executes planned steps using available tools
- **Memory Integration**: Seamlessly integrates with the memory system

#### Memory System

PrivateClaw uses a multi-layer memory architecture:

- **Short-Term Memory**: Recent conversation history (configurable limit)
- **Long-Term Memory**: Vector-based semantic search using ChromaDB
- **Episodic Memory**: Important events and milestones (planned)
- **Semantic Memory**: Knowledge graph for structured knowledge (planned)

#### Tool System

Extensible tool system with built-in tools:

- **Web Search**: Search the internet for information
- **File Operations**: Read and write files
- **Shell Commands**: Execute system commands
- **Calculator**: Mathematical calculations

## Configuration

PrivateClaw uses environment variables for configuration. See `.env.example` for all options.

### LLM Providers

Supported providers:

- **OpenAI**: GPT-4o, GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus
- **Ollama**: Local models (Llama, Mistral, etc.)

### Channels

Enable/disable channels in configuration:

```env
CHANNEL_WEB_ENABLED=true
CHANNEL_TELEGRAM_ENABLED=true
CHANNEL_TELEGRAM_TOKEN=your-token
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black --check .
```

### Adding Custom Tools

Create a new tool:

```python
from privateclaw.core.tools.base import PrivateClawTool

class MyTool(PrivateClawTool):
    name = "my_tool"
    description = "Description of my tool"
    category = "custom"

    def _run(self, input: str) -> str:
        # Implement tool logic
        return f"Result: {input}"
```

Register the tool:

```python
from privateclaw.core.tools.registry import ToolRegistry
ToolRegistry.register(MyTool())
```

## Roadmap

- [ ] Enhanced memory system with episodic and semantic memory
- [ ] Skill system for reusable capabilities
- [ ] Plugin system for extensibility
- [ ] Web UI dashboard
- [ ] Voice input/output
- [ ] Multi-user support
- [ ] Docker deployment
- [ ] Mobile apps

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Inspired by [OpenClaw](https://github.com/openclaw/openclaw) - the original personal AI assistant.
