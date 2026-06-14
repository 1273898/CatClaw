"""Tool Skill system for CatClaw - OpenClaw style.

Skills are stored as Markdown files with frontmatter metadata.
Each skill file contains:
- YAML frontmatter with metadata
- Markdown content describing the skill
- Optional Python code blocks for tool implementation
"""

import json
import re
import hashlib
import yaml
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ToolSkillType(str, Enum):
    """Types of tool skills."""
    FILE_OPERATION = "file_operation"
    COMMAND_EXECUTION = "command_execution"
    WEB_SEARCH = "web_search"
    DATA_TRANSFORMATION = "data_transformation"
    CODE_GENERATION = "code_generation"
    CUSTOM = "custom"


class ToolSkill(BaseModel):
    """A tool represented as a skill."""
    skill_id: str
    name: str
    skill_type: ToolSkillType = ToolSkillType.CUSTOM
    description: str

    # Pattern matching
    trigger_patterns: List[str] = Field(default_factory=list)
    example_inputs: List[str] = Field(default_factory=list)

    # Tool implementation
    tool_code: str = ""  # Python code for the tool
    parameters: Dict[str, str] = Field(default_factory=dict)

    # Usage tracking
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    usage_count: int = 0
    success_count: int = 0
    last_used: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    source: str = "file"  # file, learned, downloaded, manual
    tags: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None  # Path to the md file

    class Config:
        use_enum_values = True


def parse_skill_md(file_path: Path) -> Optional[ToolSkill]:
    """Parse a skill markdown file.

    Expected format:
    ---
    name: skill_name
    type: file_operation
    description: What this skill does
    triggers:
      - pattern1
      - pattern2
    tags:
      - tag1
      - tag2
    confidence: 0.8
    ---

    # Skill Name

    Description of the skill...

    ## Parameters

    - param1: description
    - param2: description

    ## Code

    ```python
    class MyTool(PrivateClawTool):
        ...
    ```
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        # Clean up content - remove leading ```markdown or ``` if present
        content = re.sub(r'^```\w*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)

        # Parse frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not frontmatter_match:
            print(f"[ToolSkill] No frontmatter found in {file_path}")
            return None

        frontmatter_yaml = frontmatter_match.group(1)
        metadata = yaml.safe_load(frontmatter_yaml)

        if not metadata or 'name' not in metadata:
            print(f"[ToolSkill] No name in frontmatter: {file_path}")
            return None

        # Extract code blocks
        code_blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)
        tool_code = code_blocks[0].strip() if code_blocks else ""

        # Generate skill ID from file name
        skill_id = f"skill_{file_path.stem}"

        # Parse skill type
        skill_type_str = metadata.get('type', 'custom')
        try:
            skill_type = ToolSkillType(skill_type_str)
        except ValueError:
            skill_type = ToolSkillType.CUSTOM

        # Parse parameters
        params = metadata.get('parameters', {})
        if not isinstance(params, dict):
            params = {}

        return ToolSkill(
            skill_id=skill_id,
            name=metadata.get('name', file_path.stem),
            skill_type=skill_type,
            description=metadata.get('description', ''),
            trigger_patterns=metadata.get('triggers', []),
            example_inputs=metadata.get('examples', []),
            tool_code=tool_code,
            parameters=params,
            confidence=metadata.get('confidence', 0.5),
            source='file',
            tags=metadata.get('tags', []),
            file_path=str(file_path),
        )
    except Exception as e:
        print(f"[ToolSkill] Failed to parse {file_path}: {e}")
        return None


def create_skill_md(file_path: Path, skill: ToolSkill) -> bool:
    """Create a skill markdown file from a ToolSkill object."""
    try:
        # Build frontmatter
        frontmatter = {
            'name': skill.name,
            'type': skill.skill_type if isinstance(skill.skill_type, str) else skill.skill_type.value,
            'description': skill.description,
            'triggers': skill.trigger_patterns,
            'tags': skill.tags,
            'confidence': skill.confidence,
        }

        # Build content
        content = "---\n"
        content += yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        content += "---\n\n"
        content += f"# {skill.name}\n\n"
        content += f"{skill.description}\n\n"

        if skill.trigger_patterns:
            content += "## 触发模式\n\n"
            for pattern in skill.trigger_patterns:
                content += f"- {pattern}\n"
            content += "\n"

        if skill.parameters:
            content += "## 参数\n\n"
            for param, desc in skill.parameters.items():
                content += f"- **{param}**: {desc}\n"
            content += "\n"

        if skill.tool_code:
            content += "## 代码\n\n"
            content += f"```python\n{skill.tool_code}\n```\n"

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"[ToolSkill] Failed to create {file_path}: {e}")
        return False


class ToolSkillSystem:
    """System for managing tool skills from markdown files.

    Features:
    1. Load skills from markdown files
    2. Track behavior and generate skills
    3. Confidence-based selection
    4. Auto-improve from usage feedback
    """

    def __init__(self, skills_dir: str = "skills", storage_path: str = "data/skills"):
        """Initialize tool skill system."""
        self.skills_dir = Path(skills_dir)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._skills: Dict[str, ToolSkill] = {}
        self._behavior_log: List[Dict[str, Any]] = []

        # Load skills from md files
        self._load_from_md_files()

        # Load runtime data (usage stats, etc.)
        self._load_runtime_data()

    def _load_from_md_files(self):
        """Load skills from markdown files."""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return

        for md_file in self.skills_dir.glob("*.md"):
            skill = parse_skill_md(md_file)
            if skill:
                self._skills[skill.skill_id] = skill
                print(f"[ToolSkill] Loaded skill: {skill.name}")

    def _load_runtime_data(self):
        """Load runtime data (usage stats, learned skills)."""
        runtime_file = self.storage_path / "runtime.json"
        if runtime_file.exists():
            try:
                with open(runtime_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Update skills with runtime stats
                for skill_id, stats in data.get("skills", {}).items():
                    if skill_id in self._skills:
                        self._skills[skill_id].usage_count = stats.get("usage_count", 0)
                        self._skills[skill_id].success_count = stats.get("success_count", 0)
                        self._skills[skill_id].confidence = stats.get("confidence", 0.5)
                        if stats.get("last_used"):
                            self._skills[skill_id].last_used = datetime.fromisoformat(stats["last_used"])

                # Load behavior log
                self._behavior_log = data.get("behavior_log", [])
            except Exception as e:
                print(f"[ToolSkill] Failed to load runtime data: {e}")

    def _save_runtime_data(self):
        """Save runtime data."""
        runtime_file = self.storage_path / "runtime.json"
        try:
            data = {
                "skills": {},
                "behavior_log": self._behavior_log[-100:],  # Keep last 100 entries
            }

            for skill_id, skill in self._skills.items():
                data["skills"][skill_id] = {
                    "usage_count": skill.usage_count,
                    "success_count": skill.success_count,
                    "confidence": skill.confidence,
                    "last_used": skill.last_used.isoformat() if skill.last_used else None,
                }

            with open(runtime_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"[ToolSkill] Failed to save runtime data: {e}")

    def log_behavior(self, tool_name: str, input_data: Dict[str, Any], success: bool):
        """Log tool usage behavior for learning."""
        self._behavior_log.append({
            "tool": tool_name,
            "input": input_data,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })

        # Update skill stats
        for skill in self._skills.values():
            if skill.name == tool_name or tool_name in skill.tags:
                skill.usage_count += 1
                if success:
                    skill.success_count += 1
                skill.last_used = datetime.now()

        # Save periodically
        if len(self._behavior_log) % 10 == 0:
            self._save_runtime_data()

    def match_skill(self, user_input: str) -> Optional[ToolSkill]:
        """Find a skill matching the user input."""
        if not self._skills:
            return None

        input_words = set(user_input.lower().split())
        best_match = None
        best_score = 0

        for skill in self._skills.values():
            if skill.confidence < 0.3:
                continue

            score = 0

            # Check trigger patterns
            for pattern in skill.trigger_patterns:
                pattern_words = set(pattern.lower().split())
                overlap = len(input_words.intersection(pattern_words))
                if overlap > 0:
                    score += overlap / len(pattern_words)

            # Check tags
            for tag in skill.tags:
                if tag.lower() in user_input.lower():
                    score += 0.5

            # Weight by confidence
            score *= skill.confidence

            if score > best_score:
                best_score = score
                best_match = skill

        return best_match if best_score > 0.3 else None

    def update_skill_feedback(self, skill_id: str, success: bool):
        """Update skill based on feedback."""
        if skill_id not in self._skills:
            return

        skill = self._skills[skill_id]
        skill.usage_count += 1

        if success:
            skill.success_count += 1
            skill.confidence = min(1.0, skill.confidence + 0.05)
        else:
            skill.confidence = max(0.0, skill.confidence - 0.1)

        skill.last_used = datetime.now()
        self._save_runtime_data()

    def create_skill(self, name: str, description: str = "",
                     skill_type: ToolSkillType = ToolSkillType.CUSTOM,
                     code: str = "", triggers: List[str] = None,
                     tags: List[str] = None) -> str:
        """Create a new skill and save as md file."""
        skill_id = f"skill_{name.lower().replace(' ', '_')}"

        skill = ToolSkill(
            skill_id=skill_id,
            name=name,
            skill_type=skill_type,
            description=description or f"Custom skill: {name}",
            trigger_patterns=triggers or [],
            tool_code=code,
            confidence=0.7,
            source='manual',
            tags=tags or [name],
        )

        # Save as md file
        md_file = self.skills_dir / f"{name.lower().replace(' ', '_')}.md"
        if create_skill_md(md_file, skill):
            skill.file_path = str(md_file)
            self._skills[skill_id] = skill
            self._save_runtime_data()
            return skill_id

        return ""

    def get_all_skills(self) -> List[ToolSkill]:
        """Get all skills."""
        return list(self._skills.values())

    def get_active_skills(self) -> List[ToolSkill]:
        """Get skills with sufficient confidence."""
        return [s for s in self._skills.values() if s.confidence >= 0.3]

    def get_skill_stats(self) -> Dict[str, Any]:
        """Get skill statistics."""
        total = len(self._skills)
        active = len([s for s in self._skills.values() if s.confidence >= 0.3])

        type_counts = {}
        for skill in self._skills.values():
            t = skill.skill_type if isinstance(skill.skill_type, str) else skill.skill_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        source_counts = {}
        for skill in self._skills.values():
            source_counts[skill.source] = source_counts.get(skill.source, 0) + 1

        return {
            "total_skills": total,
            "active_skills": active,
            "by_type": type_counts,
            "by_source": source_counts,
            "average_confidence": round(
                sum(s.confidence for s in self._skills.values()) / total if total > 0 else 0,
                2
            ),
        }

    def get_suggestions(self) -> List[str]:
        """Get suggestions for new skills based on behavior."""
        suggestions = []

        if len(self._behavior_log) >= 10:
            tool_counts = {}
            for entry in self._behavior_log[-50:]:
                tool = entry["tool"]
                tool_counts[tool] = tool_counts.get(tool, 0) + 1

            for tool, count in tool_counts.items():
                if count >= 3:
                    # Check if skill exists
                    has_skill = any(
                        tool in s.name or tool in s.tags
                        for s in self._skills.values()
                    )
                    if not has_skill:
                        suggestions.append(
                            f"为频繁使用的工具 '{tool}' 创建技能 (已使用 {count} 次)"
                        )

        return suggestions

    def export_skills(self) -> List[Dict[str, Any]]:
        """Export all skills."""
        return [skill.model_dump() for skill in self._skills.values()]

    def import_skills(self, skills_data: List[Dict[str, Any]]) -> int:
        """Import skills."""
        imported = 0
        for data in skills_data:
            try:
                skill = ToolSkill(**data)
                # Save as md file
                md_file = self.skills_dir / f"{skill.name.lower().replace(' ', '_')}.md"
                if create_skill_md(md_file, skill):
                    skill.file_path = str(md_file)
                    self._skills[skill.skill_id] = skill
                    imported += 1
            except Exception:
                continue

        if imported > 0:
            self._save_runtime_data()

        return imported

    def reload_from_files(self):
        """Reload all skills from md files."""
        self._skills.clear()
        self._load_from_md_files()
        self._load_runtime_data()
