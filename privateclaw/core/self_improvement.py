"""Self-improvement system for CatClaw.

Inspired by OpenClaw's approach to continuous learning and self-improvement
through user interactions.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile built from interactions."""
    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    communication_style: str = "neutral"  # formal, casual, neutral
    topics_of_interest: List[str] = Field(default_factory=list)
    interaction_patterns: Dict[str, Any] = Field(default_factory=dict)
    feedback_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ConversationInsight(BaseModel):
    """Insights extracted from a conversation."""
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    user_satisfaction: Optional[float] = None  # 0-1
    topics_discussed: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    feedback_signals: List[Dict[str, Any]] = Field(default_factory=list)
    learning_points: List[str] = Field(default_factory=list)


class SelfImprovementSystem:
    """System for continuous self-improvement through user interactions.

    Key capabilities:
    1. Build and maintain user profiles
    2. Extract insights from conversations
    3. Adapt behavior based on feedback
    4. Learn new patterns and preferences
    """

    def __init__(self, memory_manager, llm=None):
        """Initialize self-improvement system."""
        self.memory = memory_manager
        self.llm = llm
        self.user_profiles: Dict[str, UserProfile] = {}
        self.conversation_insights: List[ConversationInsight] = []
        self._adaptation_rules: Dict[str, Any] = {}

    async def process_conversation(
        self,
        session_id: str,
        user_id: str,
        messages: List[Dict[str, str]],
        feedback: Optional[Dict[str, Any]] = None
    ) -> ConversationInsight:
        """Process a completed conversation for learning.

        Args:
            session_id: Session identifier
            user_id: User identifier
            messages: Conversation messages
            feedback: Optional explicit feedback

        Returns:
            Extracted insights
        """
        # Extract insights from conversation
        insight = await self._extract_insights(session_id, messages, feedback)

        # Update user profile
        await self._update_user_profile(user_id, insight, messages)

        # Store insight
        self.conversation_insights.append(insight)

        # Learn from feedback if provided
        if feedback:
            await self._process_feedback(user_id, feedback)

        # Store in long-term memory
        await self._store_learning(insight, user_id)

        return insight

    async def _extract_insights(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        feedback: Optional[Dict[str, Any]]
    ) -> ConversationInsight:
        """Extract insights from conversation messages."""
        insight = ConversationInsight(session_id=session_id)

        # Extract topics from conversation
        topics = set()
        tools_used = set()

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Simple topic extraction (can be enhanced with NLP)
            words = content.lower().split()
            for word in words:
                if len(word) > 4 and word.isalpha():
                    topics.add(word)

            # Track tool usage
            if role == "system" and "tool" in content.lower():
                tools_used.add(content)

        insight.topics_discussed = list(topics)[:10]  # Top 10 topics
        insight.tools_used = list(tools_used)

        # Analyze feedback signals
        if feedback:
            insight.feedback_signals.append(feedback)
            if "satisfaction" in feedback:
                insight.user_satisfaction = feedback["satisfaction"]

        # Extract learning points
        insight.learning_points = await self._identify_learning_points(messages)

        return insight

    async def _identify_learning_points(self, messages: List[Dict[str, str]]) -> List[str]:
        """Identify key learning points from conversation."""
        learning_points = []

        # Look for correction patterns
        for i, msg in enumerate(messages):
            content = msg.get("content", "").lower()
            role = msg.get("role", "")

            # User corrections
            if role == "human" and any(word in content for word in ["不要", "不对", "错了", "应该是", "don't", "wrong", "should be"]):
                learning_points.append(f"User correction at message {i}: {msg.get('content', '')[:100]}")

            # User preferences expressed
            if role == "human" and any(word in content for word in ["我喜欢", "我更喜欢", "prefer", "like", "favorite"]):
                learning_points.append(f"User preference at message {i}: {msg.get('content', '')[:100]}")

        return learning_points

    async def _update_user_profile(
        self,
        user_id: str,
        insight: ConversationInsight,
        messages: List[Dict[str, str]]
    ) -> None:
        """Update user profile based on conversation insights."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)

        profile = self.user_profiles[user_id]

        # Update topics of interest
        for topic in insight.topics_discussed:
            if topic not in profile.topics_of_interest:
                profile.topics_of_interest.append(topic)
                # Keep only top 50 topics
                if len(profile.topics_of_interest) > 50:
                    profile.topics_of_interest = profile.topics_of_interest[-50:]

        # Analyze communication style
        style = await self._analyze_communication_style(messages)
        if style:
            profile.communication_style = style

        # Update interaction patterns
        profile.interaction_patterns["total_conversations"] = \
            profile.interaction_patterns.get("total_conversations", 0) + 1
        profile.interaction_patterns["last_active"] = datetime.now().isoformat()

        # Store feedback
        if insight.feedback_signals:
            profile.feedback_history.extend(insight.feedback_signals)
            # Keep only recent feedback
            if len(profile.feedback_history) > 100:
                profile.feedback_history = profile.feedback_history[-100:]

        profile.updated_at = datetime.now()

    async def _analyze_communication_style(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Analyze user's communication style."""
        user_messages = [m for m in messages if m.get("role") == "human"]
        if not user_messages:
            return None

        # Simple heuristic analysis
        total_length = sum(len(m.get("content", "")) for m in user_messages)
        avg_length = total_length / len(user_messages) if user_messages else 0

        # Check for formal markers
        formal_markers = ["请", "您", "请问", "please", "would you", "could you"]
        casual_markers = ["哈", "嘿", "哈哈", "hey", "lol", "haha"]

        formal_count = 0
        casual_count = 0

        for msg in user_messages:
            content = msg.get("content", "").lower()
            for marker in formal_markers:
                if marker in content:
                    formal_count += 1
            for marker in casual_markers:
                if marker in content:
                    casual_count += 1

        if formal_count > casual_count * 2:
            return "formal"
        elif casual_count > formal_count * 2:
            return "casual"
        return "neutral"

    async def _process_feedback(self, user_id: str, feedback: Dict[str, Any]) -> None:
        """Process explicit feedback for behavior adaptation."""
        if user_id not in self.user_profiles:
            return

        profile = self.user_profiles[user_id]

        # Extract adaptation rules from feedback
        if "preferred_style" in feedback:
            self._adaptation_rules[f"{user_id}_style"] = feedback["preferred_style"]

        if "disliked_responses" in feedback:
            for response in feedback["disliked_responses"]:
                # Store pattern to avoid
                pattern_key = f"avoid_{hash(response) % 10000}"
                self._adaptation_rules[pattern_key] = {
                    "type": "avoid",
                    "pattern": response,
                    "user_id": user_id,
                }

        if "liked_responses" in feedback:
            for response in feedback["liked_responses"]:
                # Store pattern to replicate
                pattern_key = f"prefer_{hash(response) % 10000}"
                self._adaptation_rules[pattern_key] = {
                    "type": "prefer",
                    "pattern": response,
                    "user_id": user_id,
                }

    async def _store_learning(self, insight: ConversationInsight, user_id: str) -> None:
        """Store learning insights in long-term memory."""
        if not self.memory:
            return

        # Create a summary of the learning
        summary = {
            "type": "conversation_insight",
            "user_id": user_id,
            "session_id": insight.session_id,
            "topics": insight.topics_discussed,
            "learning_points": insight.learning_points,
            "satisfaction": insight.user_satisfaction,
            "timestamp": insight.timestamp.isoformat(),
        }

        # Store in long-term memory
        await self.memory.store_memory(
            json.dumps(summary, ensure_ascii=False),
            metadata={
                "type": "learning",
                "user_id": user_id,
                "session_id": insight.session_id,
            }
        )

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        return self.user_profiles.get(user_id)

    def get_adaptation_context(self, user_id: str) -> Dict[str, Any]:
        """Get adaptation context for response generation."""
        context = {}

        # Get user profile
        profile = self.user_profiles.get(user_id)
        if profile:
            context["communication_style"] = profile.communication_style
            context["topics_of_interest"] = profile.topics_of_interest[:10]
            context["interaction_count"] = profile.interaction_patterns.get("total_conversations", 0)

        # Get relevant adaptation rules
        relevant_rules = []
        for key, rule in self._adaptation_rules.items():
            if rule.get("user_id") == user_id or not rule.get("user_id"):
                relevant_rules.append(rule)

        if relevant_rules:
            context["adaptation_rules"] = relevant_rules[:5]  # Top 5 rules

        return context

    async def generate_personalized_prompt(self, user_id: str, base_prompt: str) -> str:
        """Generate personalized system prompt based on user profile."""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return base_prompt

        # Add personalization to prompt
        personalization = []

        if profile.communication_style == "formal":
            personalization.append("Use formal and professional language.")
        elif profile.communication_style == "casual":
            personalization.append("Use casual and friendly language.")

        if profile.topics_of_interest:
            topics = ", ".join(profile.topics_of_interest[:5])
            personalization.append(f"The user is interested in: {topics}")

        # Check for specific adaptations
        for key, rule in self._adaptation_rules.items():
            if rule.get("user_id") == user_id:
                if rule.get("type") == "avoid":
                    personalization.append(f"Avoid this pattern: {rule.get('pattern', '')[:50]}")
                elif rule.get("type") == "prefer":
                    personalization.append(f"Try to use this style: {rule.get('pattern', '')[:50]}")

        if personalization:
            return f"{base_prompt}\n\nPersonalization:\n" + "\n".join(f"- {p}" for p in personalization)

        return base_prompt

    def get_stats(self) -> Dict[str, Any]:
        """Get self-improvement statistics."""
        return {
            "total_users": len(self.user_profiles),
            "total_insights": len(self.conversation_insights),
            "adaptation_rules": len(self._adaptation_rules),
            "avg_satisfaction": self._calculate_avg_satisfaction(),
        }

    def _calculate_avg_satisfaction(self) -> Optional[float]:
        """Calculate average user satisfaction."""
        satisfactions = [
            i.user_satisfaction
            for i in self.conversation_insights
            if i.user_satisfaction is not None
        ]
        return sum(satisfactions) / len(satisfactions) if satisfactions else None
