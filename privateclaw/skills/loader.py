"""Skills loader for PrivateClaw."""

from typing import Optional
from pathlib import Path
import importlib.util
import yaml
import json


class SkillLoader:
    """Loader for skills from files."""

    def __init__(self, skills_dir: Path):
        """Initialize skill loader."""
        self.skills_dir = skills_dir

    def load_all(self) -> dict:
        """Load all skills from directory."""
        skills = {}

        if not self.skills_dir.exists():
            return skills

        # Load YAML skills
        for yaml_file in self.skills_dir.glob("*.yaml"):
            try:
                skill = self._load_yaml_skill(yaml_file)
                if skill:
                    skills[skill["name"]] = skill
            except Exception as e:
                print(f"Error loading skill {yaml_file}: {e}")

        # Load JSON skills
        for json_file in self.skills_dir.glob("*.json"):
            try:
                skill = self._load_json_skill(json_file)
                if skill:
                    skills[skill["name"]] = skill
            except Exception as e:
                print(f"Error loading skill {json_file}: {e}")

        # Load Python skills
        for py_file in self.skills_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                skill = self._load_python_skill(py_file)
                if skill:
                    skills[skill["name"]] = skill
            except Exception as e:
                print(f"Error loading skill {py_file}: {e}")

        return skills

    def _load_yaml_skill(self, file_path: Path) -> Optional[dict]:
        """Load skill from YAML file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "name" not in data:
            return None

        return {
            "name": data["name"],
            "description": data.get("description", ""),
            "category": data.get("category", "general"),
            "parameters": data.get("parameters", {}),
            "steps": data.get("steps", []),
            "executor": None,
        }

    def _load_json_skill(self, file_path: Path) -> Optional[dict]:
        """Load skill from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data or "name" not in data:
            return None

        return {
            "name": data["name"],
            "description": data.get("description", ""),
            "category": data.get("category", "general"),
            "parameters": data.get("parameters", {}),
            "steps": data.get("steps", []),
            "executor": None,
        }

    def _load_python_skill(self, file_path: Path) -> Optional[dict]:
        """Load skill from Python file."""
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for skill definition
        if hasattr(module, "SKILL_DEFINITION"):
            skill_def = module.SKILL_DEFINITION
            skill_def["executor"] = getattr(module, "execute", None)
            return skill_def

        # Look for execute function
        if hasattr(module, "execute"):
            return {
                "name": module_name,
                "description": getattr(module, "__doc__", "") or "",
                "category": "custom",
                "parameters": {},
                "executor": module.execute,
            }

        return None
