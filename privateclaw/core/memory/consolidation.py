"""Memory consolidation system for CatClaw.

Automatically consolidates conversation memories into long-term storage
with intelligent summarization and pattern extraction.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class ConsolidationConfig(BaseModel):
    """Configuration for memory consolidation."""
    enabled: bool = Field(default=True, description="Enable auto-consolidation")
    consolidation_interval_minutes: int = Field(default=30, description="Minutes between consolidations")
    min_messages_for_consolidation: int = Field(default=5, description="Min messages to trigger consolidation")
    max_summary_length: int = Field(default=500, description="Max summary length in chars")
    extract_preferences: bool = Field(default=True, description="Extract user preferences")
    extract_facts: bool = Field(default=True, description="Extract factual information")
    extract_patterns: bool = Field(default=True, description="Extract behavioral patterns")


class ConversationSummary(BaseModel):
    """Summary of a conversation session."""
    session_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    summary: str
    key_topics: List[str] = Field(default_factory=list)
    user_preferences: List[str] = Field(default_factory=list)
    facts_learned: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"  # positive, negative, neutral
    message_count: int = 0


class MemoryConsolidation:
    """Memory consolidation system for intelligent memory management.

    Features:
    1. Automatic conversation summarization
    2. Preference extraction
    3. Fact extraction
    4. Pattern recognition
    5. Action item identification
    """

    def __init__(self, memory_manager, llm=None, config: Optional[ConsolidationConfig] = None):
        """Initialize memory consolidation."""
        self.memory = memory_manager
        self.llm = llm
        self.config = config or ConsolidationConfig()
        self._last_consolidation: Dict[str, datetime] = {}  # session_id -> last consolidation time
        self._pending_consolidations: Dict[str, List[Dict[str, str]]] = {}  # session_id -> messages

    async def add_message(self, session_id: str, user_id: str, role: str, content: str) -> None:
        """Add a message and check if consolidation is needed."""
        if not self.config.enabled:
            return

        # Track messages for consolidation
        if session_id not in self._pending_consolidations:
            self._pending_consolidations[session_id] = []

        self._pending_consolidations[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

        # Check if consolidation should trigger
        await self._check_consolidation(session_id, user_id)

    async def _check_consolidation(self, session_id: str, user_id: str) -> None:
        """Check if consolidation should be triggered."""
        messages = self._pending_consolidations.get(session_id, [])

        # Check minimum messages
        if len(messages) < self.config.min_messages_for_consolidation:
            return

        # Check time since last consolidation
        last_consolidation = self._last_consolidation.get(session_id)
        if last_consolidation:
            elapsed = datetime.now() - last_consolidation
            if elapsed < timedelta(minutes=self.config.consolidation_interval_minutes):
                return

        # Trigger consolidation
        await self.consolidate_session(session_id, user_id)

    async def consolidate_session(self, session_id: str, user_id: str) -> Optional[ConversationSummary]:
        """Consolidate a session's messages into a summary."""
        messages = self._pending_consolidations.get(session_id, [])
        if not messages:
            return None

        # Generate summary
        summary = await self._generate_summary(session_id, user_id, messages)

        # Store in long-term memory
        await self._store_consolidation(summary)

        # Update tracking
        self._last_consolidation[session_id] = datetime.now()
        self._pending_consolidations[session_id] = []

        return summary

    async def _generate_summary(
        self,
        session_id: str,
        user_id: str,
        messages: List[Dict[str, str]]
    ) -> ConversationSummary:
        """Generate a summary from conversation messages."""
        # Extract key information
        key_topics = self._extract_topics(messages)
        user_preferences = self._extract_preferences(messages)
        facts_learned = self._extract_facts(messages)
        action_items = self._extract_action_items(messages)
        sentiment = self._analyze_sentiment(messages)

        # Generate text summary
        summary_text = self._create_summary_text(messages, key_topics, user_preferences)

        return ConversationSummary(
            session_id=session_id,
            user_id=user_id,
            summary=summary_text,
            key_topics=key_topics,
            user_preferences=user_preferences,
            facts_learned=facts_learned,
            action_items=action_items,
            sentiment=sentiment,
            message_count=len(messages),
        )

    def _extract_topics(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract key topics from messages using improved heuristics."""
        from collections import Counter

        # Common stop words to exclude
        stop_words = {
            # English stop words
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "shall", "can", "need", "must",
            "this", "that", "these", "those", "i", "you", "he", "she", "it", "we",
            "they", "me", "him", "her", "us", "them", "my", "your", "his", "its",
            "our", "their", "mine", "yours", "hers", "ours", "theirs", "what",
            "which", "who", "whom", "when", "where", "why", "how", "all", "each",
            "every", "both", "few", "more", "most", "other", "some", "such", "no",
            "not", "only", "own", "same", "so", "than", "too", "very", "just",
            "about", "above", "after", "again", "also", "any", "because", "before",
            "below", "between", "both", "but", "by", "during", "each", "for",
            "from", "further", "get", "got", "had", "has", "have", "he", "her",
            "here", "him", "himself", "his", "how", "if", "in", "into", "is",
            "it", "its", "just", "keep", "let", "like", "make", "many", "me",
            "might", "more", "most", "must", "my", "myself", "no", "nor", "not",
            "now", "of", "on", "once", "only", "or", "other", "our", "ours",
            "out", "over", "own", "really", "right", "said", "say", "says",
            "she", "should", "so", "some", "still", "such", "take", "than",
            "that", "the", "their", "theirs", "them", "then", "there", "these",
            "they", "thing", "things", "think", "this", "those", "through",
            "together", "too", "under", "until", "up", "upon", "us", "use",
            "used", "using", "very", "want", "was", "way", "we", "well", "were",
            "what", "when", "where", "which", "while", "who", "whom", "why",
            "will", "with", "would", "yes", "yet", "you", "your", "yours",
            # Chinese common words (particles, pronouns, etc.)
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
            "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
            "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
            "们", "我们", "你们", "他们", "她们", "它们", "这个", "那个",
            "这些", "那些", "什么", "怎么", "为什么", "哪里", "哪个", "多少",
            "几", "谁", "吗", "呢", "吧", "啊", "呀", "哦", "嗯", "哈哈",
        }

        word_counts = Counter()

        for msg in messages:
            content = msg.get("content", "").lower()

            # Split by whitespace and punctuation
            import re
            words = re.findall(r'[\w一-鿿]+', content)

            for word in words:
                # Filter out stop words, short words, and pure numbers
                if (word not in stop_words and
                    len(word) > 1 and
                    not word.isdigit()):
                    word_counts[word] += 1

        # Return top 10 most common topics
        return [word for word, count in word_counts.most_common(10)]

    def _extract_preferences(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract user preferences from messages."""
        preferences = []

        preference_indicators = [
            "我喜欢", "我更喜欢", "我想要", "我希望",
            "i like", "i prefer", "i want", "i wish",
            "请用", "请不要", "please use", "please don't",
        ]

        for msg in messages:
            if msg.get("role") != "human":
                continue

            content = msg.get("content", "").lower()
            for indicator in preference_indicators:
                if indicator in content:
                    # Extract the preference context
                    start = content.find(indicator)
                    end = min(start + 100, len(content))
                    preference = content[start:end].strip()
                    if preference and preference not in preferences:
                        preferences.append(preference)

        return preferences[:10]  # Top 10 preferences

    def _extract_facts(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract factual information from messages."""
        facts = []

        fact_indicators = [
            "我的名字是", "我住在", "我在", "我是",
            "my name is", "i live in", "i work at", "i am",
            "我有", "我养了", "i have",
        ]

        for msg in messages:
            if msg.get("role") != "human":
                continue

            content = msg.get("content", "").lower()
            for indicator in fact_indicators:
                if indicator in content:
                    # Extract the fact context
                    start = content.find(indicator)
                    end = min(start + 150, len(content))
                    fact = content[start:end].strip()
                    if fact and fact not in facts:
                        facts.append(fact)

        return facts[:10]  # Top 10 facts

    def _extract_action_items(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract action items from messages."""
        action_items = []

        action_indicators = [
            "提醒我", "记住", "帮我", "请",
            "remind me", "remember", "help me", "please",
            "需要", "应该", "must", "should",
        ]

        for msg in messages:
            content = msg.get("content", "").lower()
            for indicator in action_indicators:
                if indicator in content:
                    # Extract the action context
                    start = content.find(indicator)
                    end = min(start + 100, len(content))
                    action = content[start:end].strip()
                    if action and action not in action_items:
                        action_items.append(action)

        return action_items[:5]  # Top 5 action items

    def _analyze_sentiment(self, messages: List[Dict[str, str]]) -> str:
        """Analyze overall sentiment of the conversation."""
        positive_words = ["谢谢", "好的", "太好了", "感谢", "thanks", "good", "great", "excellent", "perfect"]
        negative_words = ["不好", "错了", "问题", "失败", "bad", "wrong", "error", "fail", "problem"]

        positive_count = 0
        negative_count = 0

        for msg in messages:
            content = msg.get("content", "").lower()
            for word in positive_words:
                if word in content:
                    positive_count += 1
            for word in negative_words:
                if word in content:
                    negative_count += 1

        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        return "neutral"

    def _create_summary_text(
        self,
        messages: List[Dict[str, str]],
        topics: List[str],
        preferences: List[str]
    ) -> str:
        """Create a text summary of the conversation."""
        # Simple extractive summary
        user_messages = [m for m in messages if m.get("role") == "human"]
        assistant_messages = [m for m in messages if m.get("role") == "ai"]

        summary_parts = []

        # Main topics
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(topics[:5])}")

        # User preferences
        if preferences:
            summary_parts.append(f"User preferences: {preferences[0][:50]}")

        # Conversation flow
        if user_messages:
            summary_parts.append(f"Conversation with {len(user_messages)} user messages")

        # Key exchanges
        if len(messages) >= 2:
            last_user_msg = next((m for m in reversed(messages) if m.get("role") == "human"), None)
            if last_user_msg:
                content = last_user_msg.get("content", "")[:100]
                summary_parts.append(f"Last topic: {content}")

        return ". ".join(summary_parts) if summary_parts else "Brief conversation"

    async def _store_consolidation(self, summary: ConversationSummary) -> None:
        """Store consolidated summary in long-term memory."""
        if not self.memory:
            return

        # Prepare metadata
        metadata = {
            "type": "conversation_summary",
            "session_id": summary.session_id,
            "user_id": summary.user_id,
            "timestamp": summary.timestamp.isoformat(),
            "sentiment": summary.sentiment,
            "message_count": summary.message_count,
        }

        # Create content for storage
        content = {
            "summary": summary.summary,
            "key_topics": summary.key_topics,
            "user_preferences": summary.user_preferences,
            "facts_learned": summary.facts_learned,
            "action_items": summary.action_items,
        }

        # Store in long-term memory
        await self.memory.store_memory(
            json.dumps(content, ensure_ascii=False),
            metadata=metadata,
        )

        # Store preferences separately for quick access
        for preference in summary.user_preferences:
            await self.memory.store_memory(
                f"User preference: {preference}",
                metadata={
                    "type": "user_preference",
                    "user_id": summary.user_id,
                    "session_id": summary.session_id,
                },
            )

        # Store facts separately
        for fact in summary.facts_learned:
            await self.memory.store_memory(
                f"User fact: {fact}",
                metadata={
                    "type": "user_fact",
                    "user_id": summary.user_id,
                    "session_id": summary.session_id,
                },
            )

    async def force_consolidation(self, session_id: str, user_id: str) -> Optional[ConversationSummary]:
        """Force consolidation for a session regardless of thresholds."""
        return await self.consolidate_session(session_id, user_id)

    def get_pending_count(self, session_id: str) -> int:
        """Get number of pending messages for a session."""
        return len(self._pending_consolidations.get(session_id, []))

    def get_stats(self) -> Dict[str, Any]:
        """Get consolidation statistics."""
        return {
            "enabled": self.config.enabled,
            "pending_sessions": len(self._pending_consolidations),
            "total_pending_messages": sum(
                len(msgs) for msgs in self._pending_consolidations.values()
            ),
            "last_consolidations": {
                sid: time.isoformat()
                for sid, time in self._last_consolidation.items()
            },
        }
