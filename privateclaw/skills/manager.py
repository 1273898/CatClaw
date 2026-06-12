"""Skills manager for PrivateClaw."""

from typing import Optional
from pathlib import Path
from privateclaw.skills.loader import SkillLoader


class SkillManager:
    """Manager for loading and executing skills."""

    def __init__(self, skills_dir: Optional[str] = None):
        """Initialize skill manager."""
        self.skills_dir = Path(skills_dir) if skills_dir else Path(__file__).parent / "builtin"
        self.loader = SkillLoader(self.skills_dir)
        self._skills: dict = {}
        self._loaded = False

    def load_skills(self) -> None:
        """Load all skills from skills directory."""
        if self._loaded:
            return

        self._skills = self.loader.load_all()
        self._loaded = True

    def get_skill(self, name: str) -> Optional[dict]:
        """Get a skill by name."""
        if not self._loaded:
            self.load_skills()
        return self._skills.get(name)

    def get_all_skills(self) -> dict:
        """Get all loaded skills."""
        if not self._loaded:
            self.load_skills()
        return self._skills.copy()

    def get_skills_by_category(self, category: str) -> list:
        """Get skills by category."""
        if not self._loaded:
            self.load_skills()
        return [
            skill for skill in self._skills.values()
            if skill.get("category") == category
        ]

    def get_categories(self) -> list:
        """Get all skill categories."""
        if not self._loaded:
            self.load_skills()
        return list(set(skill.get("category", "general") for skill in self._skills.values()))

    def execute_skill(self, name: str, params: dict) -> dict:
        """Execute a skill with parameters."""
        skill = self.get_skill(name)
        if not skill:
            return {"success": False, "error": f"Skill not found: {name}"}

        try:
            executor = skill.get("executor")
            if executor and callable(executor):
                result = executor(**params)
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": "Skill has no executor"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_skill_info(self, name: str) -> Optional[dict]:
        """Get skill information without executor."""
        skill = self.get_skill(name)
        if not skill:
            return None
        return {
            "name": skill.get("name"),
            "description": skill.get("description"),
            "category": skill.get("category"),
            "parameters": skill.get("parameters"),
        }
