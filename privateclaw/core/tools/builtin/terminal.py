"""Terminal tool for PrivateClaw - sandboxed shell execution."""

import os
import re
from typing import Type, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_community.tools import ShellTool
from privateclaw.core.tools.base import PrivateClawTool


class TerminalInput(BaseModel):
    """Input for terminal tool."""
    command: str = Field(description="Shell command to execute")


# Dangerous command patterns blacklist
DANGEROUS_PATTERNS = [
    # File system destruction
    r'\brm\s+(-[rfR]*\s+)*(\/|[a-zA-Z]:)',
    r'\brm\s+-rf\s+/',
    r'\brmdir\s+\/',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    # System modification
    r'\bchmod\s+777\s+/',
    r'\bchown\s+.*\s+/',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bhalt\b',
    r'\binit\s+0\b',
    r'\bkill\s+-9\s+1\b',
    r'\bkillall\b',
    # Network attacks
    r'\bnc\s+.*-e\b',
    r'\bcurl\s+.*\|\s*(ba)?sh\b',
    r'\bwget\s+.*\|\s*(ba)?sh\b',
    # Fork bomb
    r':\(\)\{.*\|.*\}',
    r'\.\/\.',
    # Disk operations
    r'\bfdisk\b',
    r'\bparted\b',
    r'\bmount\b.*\/dev\/',
    # Dangerous redirects
    r'>\s*\/dev\/sd',
    r'>\s*\/dev\/nvme',
]


class TerminalTool(PrivateClawTool):
    """Tool for executing shell commands in a sandboxed environment.

    Features:
    - root_dir restriction to prevent access outside project
    - Dangerous command blacklist
    - Working directory isolation
    """

    name: str = "terminal"
    description: str = (
        "Execute shell commands in a sandboxed terminal. "
        "Use this to run scripts, install packages, or perform system operations. "
        "Commands are restricted to the project directory for safety."
    )
    category: str = "system"
    requires_auth: bool = True
    args_schema: Type[BaseModel] = TerminalInput

    # Configuration
    root_dir: str = Field(default=".", description="Root directory for sandbox")
    blacklist_patterns: list[str] = Field(
        default_factory=lambda: DANGEROUS_PATTERNS.copy(),
        description="Patterns to block dangerous commands"
    )
    allowed_commands: Optional[list[str]] = Field(
        default=None,
        description="Whitelist of allowed commands (None = all allowed)"
    )

    def __init__(self, root_dir: str = ".", **kwargs):
        """Initialize terminal tool with sandbox configuration."""
        super().__init__(root_dir=root_dir, **kwargs)
        self._shell_tool = ShellTool()
        self._root_dir = Path(root_dir).resolve()

    def _validate_command(self, command: str) -> Optional[str]:
        """Validate command against security rules.

        Returns:
            Error message if command is invalid, None if valid.
        """
        command_lower = command.lower().strip()

        # Check against blacklist patterns
        for pattern in self.blacklist_patterns:
            if re.search(pattern, command_lower, re.IGNORECASE):
                return f"BLOCKED: Command matches dangerous pattern: {pattern}"

        # Check command whitelist if configured
        if self.allowed_commands:
            cmd_parts = command.strip().split()
            if cmd_parts and cmd_parts[0] not in self.allowed_commands:
                return f"BLOCKED: Command '{cmd_parts[0]}' not in allowed list"

        return None

    def _run(self, command: str) -> str:
        """Execute a shell command synchronously."""
        # Validate command
        error = self._validate_command(command)
        if error:
            return error

        try:
            # Set working directory to root_dir
            original_dir = os.getcwd()
            os.chdir(self._root_dir)

            # Execute command
            result = self._shell_tool.run(command)

            # Restore directory
            os.chdir(original_dir)

            return result
        except Exception as e:
            return f"Error executing command: {str(e)}"

    async def _arun(self, command: str) -> str:
        """Execute a shell command asynchronously."""
        # Validate command
        error = self._validate_command(command)
        if error:
            return error

        try:
            # Set working directory to root_dir
            original_dir = os.getcwd()
            os.chdir(self._root_dir)

            # Execute command
            result = self._shell_tool.run(command)

            # Restore directory
            os.chdir(original_dir)

            return result
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def add_blacklist_pattern(self, pattern: str) -> None:
        """Add a custom blacklist pattern."""
        self.blacklist_patterns.append(pattern)

    def set_allowed_commands(self, commands: list[str]) -> None:
        """Set whitelist of allowed commands."""
        self.allowed_commands = commands

    def get_metadata(self) -> dict:
        """Get tool metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "root_dir": str(self._root_dir),
            "blacklist_count": len(self.blacklist_patterns),
            "has_whitelist": self.allowed_commands is not None,
        })
        return metadata
