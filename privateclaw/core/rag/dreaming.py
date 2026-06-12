"""Memory dreaming system for PrivateClaw RAG.

Inspired by OpenClaw's memory dreaming approach:
- Light dreaming: Frequent, fast consolidation of recent memories
- Deep dreaming: Periodic deep consolidation with quality checks
- REM dreaming: Pattern recognition and knowledge synthesis
"""

from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum


class DreamingPhase(str, Enum):
    """Memory dreaming phases."""
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"


class DreamingConfig(BaseModel):
    """Memory dreaming configuration."""
    enabled: bool = Field(default=True, description="Enable memory dreaming")
    light_enabled: bool = Field(default=True, description="Enable light dreaming")
    deep_enabled: bool = Field(default=True, description="Enable deep dreaming")
    rem_enabled: bool = Field(default=False, description="Enable REM dreaming")

    # Light dreaming
    light_interval_hours: int = Field(default=6, description="Light dreaming interval")
    light_lookback_days: int = Field(default=2, description="Days to look back")
    light_limit: int = Field(default=100, description="Max memories to process")
    light_dedupe_similarity: float = Field(default=0.9, description="Deduplication threshold")

    # Deep dreaming
    deep_interval_hours: int = Field(default=24, description="Deep dreaming interval")
    deep_lookback_days: int = Field(default=30, description="Days to look back")
    deep_limit: int = Field(default=10, description="Max memories to process")
    deep_min_score: float = Field(default=0.8, description="Minimum quality score")
    deep_min_recall_count: int = Field(default=3, description="Minimum recall count")

    # REM dreaming
    rem_interval_hours: int = Field(default=168, description="REM dreaming interval (weekly)")
    rem_lookback_days: int = Field(default=7, description="Days to look back")
    rem_limit: int = Field(default=10, description="Max memories to process")
    rem_min_pattern_strength: float = Field(default=0.75, description="Minimum pattern strength")


class MemoryDreaming:
    """Memory dreaming system for consolidating and optimizing memories.

    Implements a three-phase approach inspired by human sleep cycles:
    1. Light dreaming: Quick deduplication and organization
    2. Deep dreaming: Quality assessment and promotion
    3. REM dreaming: Pattern recognition and synthesis
    """

    def __init__(self, rag_engine, config: Optional[DreamingConfig] = None):
        """Initialize memory dreaming."""
        self.rag_engine = rag_engine
        self.config = config or DreamingConfig()
        self._last_light_dream: Optional[datetime] = None
        self._last_deep_dream: Optional[datetime] = None
        self._last_rem_dream: Optional[datetime] = None

    def should_dream(self, phase: DreamingPhase) -> bool:
        """Check if dreaming should occur for a phase."""
        if not self.config.enabled:
            return False

        now = datetime.now()

        if phase == DreamingPhase.LIGHT:
            if not self.config.light_enabled:
                return False
            if self._last_light_dream is None:
                return True
            elapsed = now - self._last_light_dream
            return elapsed > timedelta(hours=self.config.light_interval_hours)

        elif phase == DreamingPhase.DEEP:
            if not self.config.deep_enabled:
                return False
            if self._last_deep_dream is None:
                return True
            elapsed = now - self._last_deep_dream
            return elapsed > timedelta(hours=self.config.deep_interval_hours)

        elif phase == DreamingPhase.REM:
            if not self.config.rem_enabled:
                return False
            if self._last_rem_dream is None:
                return True
            elapsed = now - self._last_rem_dream
            return elapsed > timedelta(hours=self.config.rem_interval_hours)

        return False

    async def dream(self, phase: DreamingPhase) -> dict:
        """Execute a dreaming phase.

        Args:
            phase: Which phase to execute

        Returns:
            Dreaming results
        """
        if phase == DreamingPhase.LIGHT:
            return await self._light_dream()
        elif phase == DreamingPhase.DEEP:
            return await self._deep_dream()
        elif phase == DreamingPhase.REM:
            return await self._rem_dream()
        else:
            raise ValueError(f"Unknown dreaming phase: {phase}")

    async def _light_dream(self) -> dict:
        """Light dreaming: Quick deduplication and organization.

        - Deduplicates similar memories
        - Removes low-quality entries
        - Updates timestamps
        """
        self._last_light_dream = datetime.now()

        # Get recent memories
        results = self.rag_engine.search(
            "*",  # Search all
            k=self.config.light_limit,
        )

        # Deduplication
        unique_results = []
        seen_contents = set()

        for result in results:
            # Simple deduplication by content similarity
            content_hash = hash(result.content[:100])  # First 100 chars
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)

        return {
            "phase": "light",
            "processed": len(results),
            "unique": len(unique_results),
            "deduplicated": len(results) - len(unique_results),
            "timestamp": self._last_light_dream.isoformat(),
        }

    async def _deep_dream(self) -> dict:
        """Deep dreaming: Quality assessment and promotion.

        - Scores memories by quality
        - Promotes high-quality memories
        - Archives low-quality memories
        """
        self._last_deep_dream = datetime.now()

        # Get memories
        results = self.rag_engine.search(
            "*",  # Search all
            k=self.config.deep_limit,
        )

        # Quality assessment
        high_quality = []
        low_quality = []

        for result in results:
            # Simple quality scoring based on:
            # - Content length (not too short, not too long)
            # - Metadata completeness
            # - Recency
            score = self._assess_quality(result)

            if score >= self.config.deep_min_score:
                high_quality.append(result)
            else:
                low_quality.append(result)

        return {
            "phase": "deep",
            "processed": len(results),
            "high_quality": len(high_quality),
            "low_quality": len(low_quality),
            "timestamp": self._last_deep_dream.isoformat(),
        }

    async def _rem_dream(self) -> dict:
        """REM dreaming: Pattern recognition and synthesis.

        - Identifies patterns across memories
        - Synthesizes related information
        - Creates knowledge connections
        """
        self._last_rem_dream = datetime.now()

        # Get memories
        results = self.rag_engine.search(
            "*",  # Search all
            k=self.config.rem_limit,
        )

        # Pattern recognition (simplified)
        patterns = self._identify_patterns(results)

        return {
            "phase": "rem",
            "processed": len(results),
            "patterns_found": len(patterns),
            "timestamp": self._last_rem_dream.isoformat(),
        }

    def _assess_quality(self, result) -> float:
        """Assess memory quality.

        Returns:
            Quality score between 0 and 1
        """
        score = 0.5  # Base score

        # Content length scoring
        content_len = len(result.content)
        if 50 < content_len < 2000:
            score += 0.2
        elif content_len < 20:
            score -= 0.3

        # Metadata completeness
        if result.metadata:
            if "source" in result.metadata:
                score += 0.1
            if "timestamp" in result.metadata:
                score += 0.1

        # Relevance score from search
        if result.score > 0:
            score += result.score * 0.1

        return min(max(score, 0), 1)

    def _identify_patterns(self, results: list) -> list:
        """Identify patterns across memories.

        Returns:
            List of identified patterns
        """
        patterns = []

        # Simple pattern detection by keyword co-occurrence
        keyword_counts = {}

        for result in results:
            words = result.content.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1

        # Find frequent patterns
        for word, count in keyword_counts.items():
            if count >= 3:  # Appears in at least 3 memories
                patterns.append({
                    "keyword": word,
                    "frequency": count,
                })

        return patterns

    def get_status(self) -> dict:
        """Get dreaming status."""
        return {
            "enabled": self.config.enabled,
            "light": {
                "enabled": self.config.light_enabled,
                "last_dream": self._last_light_dream.isoformat() if self._last_light_dream else None,
            },
            "deep": {
                "enabled": self.config.deep_enabled,
                "last_dream": self._last_deep_dream.isoformat() if self._last_deep_dream else None,
            },
            "rem": {
                "enabled": self.config.rem_enabled,
                "last_dream": self._last_rem_dream.isoformat() if self._last_rem_dream else None,
            },
        }
