"""Pytest configuration for PrivateClaw tests."""

import pytest
import asyncio
from pathlib import Path
from typing import Generator

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def project_root() -> Path:
    """Get project root path."""
    return PROJECT_ROOT


@pytest.fixture
def tmp_data_dir(tmp_path) -> Path:
    """Create temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing."""
    return """
    CatClaw is a personal AI assistant powered by LangChain.
    It provides features like memory management, tool execution,
    and multi-channel support including web, CLI, and more.
    """


@pytest.fixture
def sample_messages() -> list:
    """Sample conversation messages for testing."""
    return [
        {"role": "human", "content": "Hello, how are you?"},
        {"role": "ai", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "human", "content": "Can you help me with Python programming?"},
        {"role": "ai", "content": "Of course! I'd be happy to help with Python. What do you need?"},
        {"role": "human", "content": "I like using Python for data analysis"},
        {"role": "ai", "content": "Python is great for data analysis! Libraries like pandas and numpy are very useful."},
    ]
