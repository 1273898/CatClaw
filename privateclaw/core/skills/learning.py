"""Skill learning system for CatClaw.

Learns new skills and patterns from user interactions,
allowing the agent to improve its capabilities over time.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SkillType(str, Enum):
    """Types of learnable skills."""
    TOOL_USAGE = "tool_usage"
    RESPONSE_PATTERN = "response_pattern"
    WORKFLOW = "workflow"
    PREFERENCE = "preference"
    COMMAND = "command"


class LearnedSkill(BaseModel):
    """A skill learned from user interaction."""
    skill_id: str
    name: str
    skill_type: SkillType
    description: str
    pattern: str  # The pattern to match
    action: str  # What to do when matched
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    usage_count: int = 0
    success_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SkillLearningConfig(BaseModel):
    """Configuration for skill learning."""
    enabled: bool = Field(default=True, description="Enable skill learning")
    min_confidence: float = Field(default=0.3, description="Minimum confidence to use skill")
    max_skills: int = Field(default=100, description="Maximum number of learned skills")
    learning_rate: float = Field(default=0.1, description="Confidence update rate")
    pattern_min_length: int = Field(default=5, description="Minimum pattern length")
    auto_cleanup_days: int = Field(default=30, description="Days before unused skills are removed")


class SkillLearningSystem:
    """System for learning new skills from user interactions.

    Features:
    1. Pattern recognition from successful interactions
    2. Tool usage learning
    3. Response pattern optimization
    4. Workflow automation
    5. Confidence-based skill selection
    """

    def __init__(self, memory_manager=None, config: Optional[SkillLearningConfig] = None):
        """Initialize skill learning system."""
        self.memory = memory_manager
        self.config = config or SkillLearningConfig()
        self.learned_skills: Dict[str, LearnedSkill] = {}
        self._interaction_buffer: List[Dict[str, Any]] = []

    async def observe_interaction(
        self,
        session_id: str,
        user_input: str,
        agent_response: str,
        tools_used: List[str],
        success: bool,
        feedback: Optional[Dict[str, Any]] = None
    ) -> None:
        """Observe an interaction for potential skill learning.

        Args:
            session_id: Session identifier
            user_input: User's input
            agent_response: Agent's response
            tools_used: Tools used in this interaction
            success: Whether the interaction was successful
            feedback: Optional feedback from user
        """
        if not self.config.enabled:
            return

        # Buffer the interaction
        interaction = {
            "session_id": session_id,
            "user_input": user_input,
            "agent_response": agent_response,
            "tools_used": tools_used,
            "success": success,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
        }
        self._interaction_buffer.append(interaction)

        # Analyze for learning opportunities
        await self._analyze_interaction(interaction)

    async def _analyze_interaction(self, interaction: Dict[str, Any]) -> None:
        """Analyze an interaction for learning opportunities."""
        user_input = interaction["user_input"]
        success = interaction["success"]
        tools_used = interaction["tools_used"]

        # Learn tool usage patterns
        if tools_used and success:
            await self._learn_tool_usage(user_input, tools_used)

        # Learn response patterns
        if success and interaction.get("feedback", {}).get("liked"):
            await self._learn_response_pattern(user_input, interaction["agent_response"])

        # Learn from explicit feedback
        if interaction.get("feedback"):
            await self._process_feedback(interaction)

    async def _learn_tool_usage(self, user_input: str, tools_used: List[str]) -> None:
        """Learn tool usage patterns from successful interactions."""
        # Extract pattern from user input
        pattern = self._extract_pattern(user_input)

        if not pattern or len(pattern) < self.config.pattern_min_length:
            return

        # Check if similar skill exists
        skill_id = f"tool_{hash(pattern) % 10000}"

        if skill_id in self.learned_skills:
            # Update existing skill
            skill = self.learned_skills[skill_id]
            skill.usage_count += 1
            skill.success_count += 1
            skill.confidence = min(1.0, skill.confidence + self.config.learning_rate)
            skill.last_used = datetime.now()
        else:
            # Create new skill
            if len(self.learned_skills) < self.config.max_skills:
                skill = LearnedSkill(
                    skill_id=skill_id,
                    name=f"Tool usage for: {pattern[:30]}...",
                    skill_type=SkillType.TOOL_USAGE,
                    description=f"Use tools {', '.join(tools_used)} when user says something like: {pattern}",
                    pattern=pattern,
                    action=json.dumps({"tools": tools_used}),
                    confidence=0.5,
                    usage_count=1,
                    success_count=1,
                )
                self.learned_skills[skill_id] = skill

                # Store in long-term memory
                if self.memory:
                    await self.memory.store_memory(
                        f"Learned skill: Use {', '.join(tools_used)} for pattern: {pattern}",
                        metadata={"type": "learned_skill", "skill_id": skill_id}
                    )

    async def _learn_response_pattern(self, user_input: str, response: str) -> None:
        """Learn successful response patterns."""
        pattern = self._extract_pattern(user_input)

        if not pattern or len(pattern) < self.config.pattern_min_length:
            return

        # Create a response pattern skill
        skill_id = f"response_{hash(pattern) % 10000}"

        if skill_id not in self.learned_skills and len(self.learned_skills) < self.config.max_skills:
            # Extract key part of response (first 100 chars)
            response_pattern = response[:100]

            skill = LearnedSkill(
                skill_id=skill_id,
                name=f"Response pattern for: {pattern[:30]}...",
                skill_type=SkillType.RESPONSE_PATTERN,
                description=f"Respond with style similar to: {response_pattern}...",
                pattern=pattern,
                action=response_pattern,
                confidence=0.4,
                usage_count=1,
                success_count=1,
            )
            self.learned_skills[skill_id] = skill

    async def _process_feedback(self, interaction: Dict[str, Any]) -> None:
        """Process feedback to improve skills."""
        feedback = interaction.get("feedback", {})
        user_input = interaction["user_input"]

        # Find matching skills
        matching_skills = self.find_matching_skills(user_input)

        for skill in matching_skills:
            if feedback.get("liked"):
                skill.confidence = min(1.0, skill.confidence + self.config.learning_rate * 2)
                skill.success_count += 1
            elif feedback.get("disliked"):
                skill.confidence = max(0.0, skill.confidence - self.config.learning_rate * 3)
                skill.success_count = max(0, skill.success_count - 1)

            skill.usage_count += 1
            skill.last_used = datetime.now()

    def _extract_pattern(self, text: str) -> Optional[str]:
        """Extract a learnable pattern from text."""
        # Simple pattern extraction: lowercase, remove common words
        common_words = {"的", "了", "是", "在", "我", "你", "他", "她", "它", "the", "a", "an", "is", "are", "was", "were"}

        words = text.lower().split()
        significant_words = [w for w in words if w not in common_words and len(w) > 1]

        if not significant_words:
            return None

        # Take first 5 significant words as pattern
        pattern = " ".join(significant_words[:5])
        return pattern if len(pattern) >= self.config.pattern_min_length else None

    def find_matching_skills(self, user_input: str) -> List[LearnedSkill]:
        """Find skills matching the user input."""
        if not self.config.enabled:
            return []

        pattern = self._extract_pattern(user_input)
        if not pattern:
            return []

        matching_skills = []

        for skill in self.learned_skills.values():
            if skill.confidence < self.config.min_confidence:
                continue

            # Simple pattern matching
            if self._patterns_match(pattern, skill.pattern):
                matching_skills.append(skill)

        # Sort by confidence and usage
        matching_skills.sort(
            key=lambda s: (s.confidence, s.usage_count),
            reverse=True
        )

        return matching_skills[:5]  # Return top 5 matches

    def _patterns_match(self, pattern1: str, pattern2: str) -> bool:
        """Check if two patterns match."""
        # Simple word overlap matching
        words1 = set(pattern1.split())
        words2 = set(pattern2.split())

        if not words1 or not words2:
            return False

        overlap = len(words1.intersection(words2))
        min_len = min(len(words1), len(words2))

        # Require at least 50% overlap
        return overlap / min_len >= 0.5

    def get_skill_suggestions(self, user_input: str) -> List[Dict[str, Any]]:
        """Get skill suggestions for user input."""
        matching_skills = self.find_matching_skills(user_input)

        suggestions = []
        for skill in matching_skills:
            suggestions.append({
                "skill_id": skill.skill_id,
                "name": skill.name,
                "type": skill.skill_type.value,
                "confidence": skill.confidence,
                "description": skill.description,
            })

        return suggestions

    def update_skill_confidence(self, skill_id: str, success: bool) -> None:
        """Update skill confidence based on usage result."""
        if skill_id not in self.learned_skills:
            return

        skill = self.learned_skills[skill_id]

        if success:
            skill.confidence = min(1.0, skill.confidence + self.config.learning_rate)
            skill.success_count += 1
        else:
            skill.confidence = max(0.0, skill.confidence - self.config.learning_rate)

        skill.usage_count += 1
        skill.last_used = datetime.now()

    async def cleanup_old_skills(self) -> int:
        """Remove old, unused skills."""
        if not self.config.auto_cleanup_days:
            return 0

        cutoff = datetime.now() - __import__('datetime').timedelta(days=self.config.auto_cleanup_days)
        skills_to_remove = []

        for skill_id, skill in self.learned_skills.items():
            if skill.last_used and skill.last_used < cutoff:
                if skill.usage_count < 3:  # Only remove rarely used skills
                    skills_to_remove.append(skill_id)

        for skill_id in skills_to_remove:
            del self.learned_skills[skill_id]

        return len(skills_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get skill learning statistics."""
        total_skills = len(self.learned_skills)
        active_skills = sum(1 for s in self.learned_skills.values() if s.confidence >= self.config.min_confidence)

        skill_types = {}
        for skill in self.learned_skills.values():
            skill_type = skill.skill_type.value
            skill_types[skill_type] = skill_types.get(skill_type, 0) + 1

        avg_confidence = (
            sum(s.confidence for s in self.learned_skills.values()) / total_skills
            if total_skills > 0 else 0
        )

        return {
            "enabled": self.config.enabled,
            "total_skills": total_skills,
            "active_skills": active_skills,
            "skill_types": skill_types,
            "average_confidence": round(avg_confidence, 2),
            "buffered_interactions": len(self._interaction_buffer),
        }

    def export_skills(self) -> List[Dict[str, Any]]:
        """Export all learned skills."""
        return [skill.model_dump() for skill in self.learned_skills.values()]

    async def import_skills(self, skills_data: List[Dict[str, Any]]) -> int:
        """Import skills from data."""
        imported = 0

        for skill_data in skills_data:
            try:
                skill = LearnedSkill(**skill_data)
                if len(self.learned_skills) < self.config.max_skills:
                    self.learned_skills[skill.skill_id] = skill
                    imported += 1
            except Exception:
                continue

        return imported
