"""Unit tests for the memory system."""

import pytest
from pathlib import Path
from privateclaw.core.memory.short_term import ShortTermMemory
from privateclaw.core.memory.consolidation import MemoryConsolidation, ConsolidationConfig


class TestShortTermMemory:
    """Tests for ShortTermMemory."""

    def test_create_memory(self, tmp_path):
        """Test creating a new memory instance."""
        memory = ShortTermMemory(
            max_messages=10,
            storage_path=str(tmp_path / "conversations")
        )
        assert memory.max_messages == 10

    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, tmp_path):
        """Test adding and retrieving messages."""
        memory = ShortTermMemory(
            max_messages=10,
            storage_path=str(tmp_path / "conversations")
        )

        # Add messages
        await memory.add_message("session1", "human", "Hello")
        await memory.add_message("session1", "ai", "Hi there!")
        await memory.add_message("session1", "human", "How are you?")

        # Get history
        history = await memory.get_history("session1")
        assert len(history) == 3
        assert history[0]["role"] == "human"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "ai"
        assert history[1]["content"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_max_messages_limit(self, tmp_path):
        """Test that messages are trimmed when exceeding max."""
        memory = ShortTermMemory(
            max_messages=3,
            storage_path=str(tmp_path / "conversations")
        )

        # Add more messages than the limit
        for i in range(5):
            await memory.add_message("session1", "human", f"Message {i}")

        # Should only have the last 3 messages
        history = await memory.get_history("session1")
        assert len(history) == 3
        assert history[0]["content"] == "Message 2"
        assert history[2]["content"] == "Message 4"

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, tmp_path):
        """Test managing multiple sessions."""
        memory = ShortTermMemory(
            max_messages=10,
            storage_path=str(tmp_path / "conversations")
        )

        # Add messages to different sessions
        await memory.add_message("session1", "human", "Hello from session 1")
        await memory.add_message("session2", "human", "Hello from session 2")

        # Check each session has its own history
        history1 = await memory.get_history("session1")
        history2 = await memory.get_history("session2")

        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0]["content"] == "Hello from session 1"
        assert history2[0]["content"] == "Hello from session 2"

    @pytest.mark.asyncio
    async def test_clear_session(self, tmp_path):
        """Test clearing a session."""
        memory = ShortTermMemory(
            max_messages=10,
            storage_path=str(tmp_path / "conversations")
        )

        # Add messages
        await memory.add_message("session1", "human", "Hello")
        await memory.add_message("session1", "ai", "Hi!")

        # Clear session
        await memory.clear_session("session1")

        # History should be empty
        history = await memory.get_history("session1")
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_get_last_n_messages(self, tmp_path):
        """Test getting last N messages."""
        memory = ShortTermMemory(
            max_messages=10,
            storage_path=str(tmp_path / "conversations")
        )

        # Add several messages
        for i in range(5):
            await memory.add_message("session1", "human", f"Message {i}")

        # Get last 3 messages
        last_3 = await memory.get_last_n_messages("session1", 3)
        assert len(last_3) == 3
        assert last_3[0]["content"] == "Message 2"
        assert last_3[2]["content"] == "Message 4"

    @pytest.mark.asyncio
    async def test_persistence(self, tmp_path):
        """Test that messages persist to disk."""
        storage_path = str(tmp_path / "conversations")

        # Create memory and add messages
        memory1 = ShortTermMemory(max_messages=10, storage_path=storage_path)
        await memory1.add_message("session1", "human", "Persistent message")

        # Create new memory instance with same storage path
        memory2 = ShortTermMemory(max_messages=10, storage_path=storage_path)
        history = await memory2.get_history("session1")

        assert len(history) == 1
        assert history[0]["content"] == "Persistent message"


class TestMemoryConsolidation:
    """Tests for MemoryConsolidation."""

    def test_create_consolidation(self):
        """Test creating consolidation system."""
        config = ConsolidationConfig(
            enabled=True,
            min_messages_for_consolidation=3
        )
        consolidation = MemoryConsolidation(
            memory_manager=None,  # Not needed for basic tests
            config=config
        )
        assert consolidation.config.enabled is True
        assert consolidation.config.min_messages_for_consolidation == 3

    @pytest.mark.asyncio
    async def test_extract_topics(self, sample_messages):
        """Test topic extraction from messages."""
        consolidation = MemoryConsolidation(memory_manager=None)
        topics = consolidation._extract_topics(sample_messages)

        # Should extract meaningful topics
        assert len(topics) > 0
        # Common words should be filtered out
        assert "the" not in topics
        assert "a" not in topics

    @pytest.mark.asyncio
    async def test_extract_preferences(self, sample_messages):
        """Test preference extraction from messages."""
        consolidation = MemoryConsolidation(memory_manager=None)
        preferences = consolidation._extract_preferences(sample_messages)

        # Should find the preference about Python
        assert len(preferences) > 0
        # Check if any preference contains "python"
        has_python_pref = any("python" in p.lower() for p in preferences)
        assert has_python_pref
