"""Auto-updater for prompt documents.

Inspired by OpenClaw's approach to continuously improve system prompts
based on user interactions and feedback.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()


class PromptUpdate(BaseModel):
    """Record of a prompt update."""
    timestamp: datetime = Field(default_factory=datetime.now)
    document: str = Field(description="Document name")
    section: str = Field(description="Section that was updated")
    old_content: str = Field(description="Previous content")
    new_content: str = Field(description="New content")
    reason: str = Field(description="Reason for update")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class PromptAutoUpdater:
    """Auto-updater for prompt documents.

    Features:
    1. Analyze user interactions to extract preferences
    2. Update IDENTITY.md based on learned user info
    3. Update SOUL.md based on communication style feedback
    4. Update USER.md with user profile data
    5. Maintain update history for rollback
    """

    def __init__(self, prompts_dir: str = "prompts", llm=None):
        """Initialize prompt auto-updater."""
        self.prompts_dir = (PROJECT_ROOT / prompts_dir).resolve()
        self.llm = llm
        self.update_history: List[PromptUpdate] = []
        self._pending_updates: Dict[str, List[Dict[str, Any]]] = {}

    async def analyze_conversation(
        self,
        messages: List[Dict[str, str]],
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Analyze conversation for prompt update opportunities.

        Args:
            messages: Conversation messages
            user_id: User identifier

        Returns:
            Analysis results with potential updates
        """
        analysis = {
            "user_preferences": [],
            "communication_style": None,
            "topics_of_interest": [],
            "corrections": [],
            "feedback": [],
            "identity_updates": [],
            "soul_updates": [],
        }

        for msg in messages:
            content = msg.get("content", "")
            content_lower = content.lower()
            role = msg.get("role", "")

            if role == "human":
                # Extract identity definitions
                identity_keywords = [
                    "你是", "你的名字", "你的身份", "你的角色", "你叫",
                    "you are", "your name", "your identity", "you're"
                ]
                if any(keyword in content_lower for keyword in identity_keywords):
                    analysis["identity_updates"].append(content)

                # Extract personality/soul definitions
                soul_keywords = [
                    "你的性格", "你的风格", "你的语气", "你要", "你应该", "你需要",
                    "你的个性", "你的人格", "your personality", "your style", "you should"
                ]
                if any(keyword in content_lower for keyword in soul_keywords):
                    analysis["soul_updates"].append(content)

                # Extract preferences
                if any(keyword in content_lower for keyword in ["我喜欢", "我更喜欢", "i prefer", "i like"]):
                    analysis["user_preferences"].append(content)

                # Extract corrections
                if any(keyword in content_lower for keyword in ["不要", "不对", "错了", "don't", "wrong"]):
                    analysis["corrections"].append(content)

                # Extract feedback
                if any(keyword in content_lower for keyword in ["太好了", "不好", "good", "bad", "更好"]):
                    analysis["feedback"].append(content)

                # Extract topics
                words = content_lower.split()
                significant_words = [w for w in words if len(w) > 3 and w.isalpha()]
                analysis["topics_of_interest"].extend(significant_words[:5])

        # Deduplicate topics
        analysis["topics_of_interest"] = list(set(analysis["topics_of_interest"]))[:10]

        return analysis

    async def suggest_updates(
        self,
        analysis: Dict[str, Any],
        user_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """Suggest prompt updates based on analysis.

        Args:
            analysis: Conversation analysis results
            user_id: User identifier

        Returns:
            List of suggested updates
        """
        suggestions = []

        # Update IDENTITY.md with identity definitions
        if analysis["identity_updates"]:
            # Extract the key identity information
            identity_content = analysis["identity_updates"][-1]  # Use the latest definition
            suggestions.append({
                "document": "IDENTITY",
                "section": "identity",
                "action": "replace",
                "content": identity_content,
                "reason": "User defined identity/persona in conversation",
            })

        # Update SOUL.md with personality definitions
        if analysis["soul_updates"]:
            # Extract the key personality information
            soul_content = analysis["soul_updates"][-1]  # Use the latest definition
            suggestions.append({
                "document": "SOUL",
                "section": "personality",
                "action": "replace",
                "content": soul_content,
                "reason": "User defined personality/behavior in conversation",
            })

        # Update USER.md with preferences
        if analysis["user_preferences"]:
            suggestions.append({
                "document": "USER",
                "section": "preferences",
                "action": "append",
                "content": "\n".join(f"- {pref}" for pref in analysis["user_preferences"][:3]),
                "reason": "User expressed preferences in conversation",
            })

        # Update SOUL.md based on corrections
        if analysis["corrections"]:
            suggestions.append({
                "document": "SOUL",
                "section": "corrections",
                "action": "append",
                "content": "\n".join(f"- Avoid: {correction}" for correction in analysis["corrections"][:3]),
                "reason": "User provided corrections",
            })

        # Update IDENTITY.md with topics
        if analysis["topics_of_interest"]:
            suggestions.append({
                "document": "IDENTITY",
                "section": "interests",
                "action": "append",
                "content": f"User interests: {', '.join(analysis['topics_of_interest'][:5])}",
                "reason": "Extracted from conversation topics",
            })

        return suggestions

    async def apply_update(
        self,
        document: str,
        section: str,
        content: str,
        action: str = "append",
        reason: str = ""
    ) -> bool:
        """Apply an update to a prompt document.

        Args:
            document: Document name (without .md)
            section: Section to update
            content: New content
            action: Update action (append, replace, insert)
            reason: Reason for update

        Returns:
            Success status
        """
        file_path = self.prompts_dir / f"{document}.md"

        if not file_path.exists():
            return False

        try:
            # Read current content
            current_content = file_path.read_text(encoding="utf-8")

            # Create backup
            backup_path = file_path.with_suffix(".md.bak")
            backup_path.write_text(current_content, encoding="utf-8")

            # Apply update based on action
            if action == "append":
                # Find the section and append
                lines = current_content.split("\n")
                section_found = False
                insert_index = len(lines)

                for i, line in enumerate(lines):
                    if section.lower() in line.lower() and line.startswith("#"):
                        section_found = True
                        # Find the end of the section
                        for j in range(i + 1, len(lines)):
                            if lines[j].startswith("#") or j == len(lines) - 1:
                                insert_index = j
                                break
                        break

                if section_found:
                    lines.insert(insert_index, f"\n{content}\n")
                    new_content = "\n".join(lines)
                else:
                    # Section not found, append at end
                    new_content = current_content + f"\n\n## {section.title()}\n\n{content}\n"

            elif action == "replace":
                # Replace section content
                lines = current_content.split("\n")
                new_lines = []
                in_section = False

                for line in lines:
                    if section.lower() in line.lower() and line.startswith("#"):
                        in_section = True
                        new_lines.append(line)
                        new_lines.append(f"\n{content}\n")
                        continue

                    if in_section and line.startswith("#"):
                        in_section = False

                    if not in_section:
                        new_lines.append(line)

                new_content = "\n".join(new_lines)

            else:
                new_content = current_content

            # Write updated content
            file_path.write_text(new_content, encoding="utf-8")

            # Record update
            update = PromptUpdate(
                document=document,
                section=section,
                old_content=current_content[:200] + "..." if len(current_content) > 200 else current_content,
                new_content=content,
                reason=reason,
            )
            self.update_history.append(update)

            return True

        except Exception as e:
            print(f"Error updating prompt: {e}")
            return False

    async def auto_update_from_conversation(
        self,
        messages: List[Dict[str, str]],
        user_id: str = "default",
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Automatically update prompts based on conversation.

        Args:
            messages: Conversation messages
            user_id: User identifier
            min_confidence: Minimum confidence to apply update

        Returns:
            List of applied updates
        """
        # Analyze conversation
        analysis = await self.analyze_conversation(messages, user_id)

        # Get update suggestions
        suggestions = await self.suggest_updates(analysis, user_id)

        # Apply updates
        applied_updates = []

        for suggestion in suggestions:
            success = await self.apply_update(
                document=suggestion["document"],
                section=suggestion["section"],
                content=suggestion["content"],
                action=suggestion.get("action", "append"),
                reason=suggestion["reason"],
            )

            if success:
                applied_updates.append(suggestion)

        return applied_updates

    async def update_user_profile(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user profile in USER.md.

        Args:
            user_id: User identifier
            preferences: User preferences to store

        Returns:
            Success status
        """
        content_lines = [f"## User Profile: {user_id}\n"]

        for key, value in preferences.items():
            if isinstance(value, list):
                content_lines.append(f"### {key.title()}")
                for item in value:
                    content_lines.append(f"- {item}")
            else:
                content_lines.append(f"- **{key}**: {value}")

        content = "\n".join(content_lines)

        return await self.apply_update(
            document="USER",
            section=f"profile_{user_id}",
            content=content,
            action="replace",
            reason=f"Updated user profile for {user_id}",
        )

    async def update_identity_trait(
        self,
        trait: str,
        description: str
    ) -> bool:
        """Update a trait in IDENTITY.md.

        Args:
            trait: Trait name
            description: Trait description

        Returns:
            Success status
        """
        return await self.apply_update(
            document="IDENTITY",
            section="traits",
            content=f"- **{trait}**: {description}",
            action="append",
            reason=f"Learned new trait: {trait}",
        )

    async def update_soul_behavior(
        self,
        behavior: str,
        context: str
    ) -> bool:
        """Update behavior guidance in SOUL.md.

        Args:
            behavior: Behavior description
            context: Context for the behavior

        Returns:
            Success status
        """
        return await self.apply_update(
            document="SOUL",
            section="behaviors",
            content=f"- When {context}: {behavior}",
            action="append",
            reason=f"Learned behavior pattern",
        )

    def get_update_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent update history.

        Args:
            limit: Number of updates to return

        Returns:
            List of recent updates
        """
        recent = self.update_history[-limit:]
        return [update.model_dump() for update in recent]

    async def rollback_last_update(self) -> bool:
        """Rollback the last update.

        Returns:
            Success status
        """
        if not self.update_history:
            return False

        last_update = self.update_history[-1]
        file_path = self.prompts_dir / f"{last_update.document}.md"
        backup_path = file_path.with_suffix(".md.bak")

        if backup_path.exists():
            try:
                content = backup_path.read_text(encoding="utf-8")
                file_path.write_text(content, encoding="utf-8")
                self.update_history.pop()
                return True
            except Exception:
                return False

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get updater statistics."""
        return {
            "total_updates": len(self.update_history),
            "documents_updated": list(set(u.document for u in self.update_history)),
            "last_update": self.update_history[-1].timestamp.isoformat() if self.update_history else None,
        }
