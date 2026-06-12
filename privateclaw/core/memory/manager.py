"""Memory manager for PrivateClaw."""

from typing import Optional
from privateclaw.core.memory.short_term import ShortTermMemory
from privateclaw.core.memory.long_term import LongTermMemory


class MemoryManager:
    """Multi-layer memory manager for PrivateClaw."""

    def __init__(self, config):
        """Initialize memory manager with config."""
        self.short_term = ShortTermMemory(max_messages=config.short_term_limit)
        self.long_term = None

        if config.long_term_enabled:
            self.long_term = LongTermMemory(
                vector_store_type=config.vector_store,
                vector_store_path=config.vector_store_path,
                embedding_model=config.embedding_model,
            )

    async def get_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        return await self.short_term.get_history(session_id)

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to conversation history."""
        await self.short_term.add_message(session_id, role, content)

    async def search_memory(self, query: str, k: int = 5) -> list:
        """Search long-term memory for relevant information."""
        if not self.long_term:
            return []
        return await self.long_term.search(query, k=k)

    async def store_memory(self, content: str, metadata: Optional[dict] = None) -> None:
        """Store content in long-term memory."""
        if not self.long_term:
            return
        await self.long_term.store(content, metadata=metadata)

    async def consolidate(self, session_id: str) -> None:
        """Consolidate short-term memory to long-term memory."""
        if not self.long_term:
            return

        messages = await self.short_term.get_history(session_id)
        if not messages:
            return

        # Create a summary of the conversation
        summary = self._summarize_conversation(messages)

        # Store in long-term memory
        await self.long_term.store(
            summary,
            metadata={"session_id": session_id, "type": "conversation_summary"}
        )

    def _summarize_conversation(self, messages: list) -> str:
        """Create a summary of a conversation."""
        # Simple summary - can be enhanced with LLM-based summarization
        summary_parts = []
        for msg in messages[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            summary_parts.append(f"{role}: {content[:100]}...")
        return "\n".join(summary_parts)

    async def clear_session(self, session_id: str) -> None:
        """Clear all memory for a session."""
        await self.short_term.clear_session(session_id)

    async def get_context(self, session_id: str, query: str) -> dict:
        """Get comprehensive memory context for a query."""
        history = await self.get_history(session_id)
        relevant_memories = await self.search_memory(query)

        return {
            "chat_history": history,
            "relevant_memories": relevant_memories,
        }
