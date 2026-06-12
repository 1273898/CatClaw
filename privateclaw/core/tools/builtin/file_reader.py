"""File reader tool for PrivateClaw - sandboxed file reading."""

import os
from typing import Type, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_community.tools import ReadFileTool
from privateclaw.core.tools.base import PrivateClawTool


class ReadFileInput(BaseModel):
    """Input for file reader tool."""
    file_path: str = Field(description="Path to the file to read (relative to project root or absolute)")


class FileReaderTool(PrivateClawTool):
    """Tool for reading files in a sandboxed environment.

    Features:
    - root_dir restriction to prevent reading files outside project
    - Path traversal protection
    - Safe file reading with encoding detection
    """

    name: str = "read_file"
    description: str = (
        "Read the contents of a local file. "
        "Use this to read configuration files, source code, documentation, or any text file. "
        "File access is restricted to the project directory for security."
    )
    category: str = "file"
    args_schema: Type[BaseModel] = ReadFileInput

    # Configuration
    root_dir: str = Field(default=".", description="Root directory for file access")
    allowed_extensions: Optional[list[str]] = Field(
        default=None,
        description="Whitelist of allowed file extensions (None = all allowed)"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file size in bytes"
    )

    def __init__(self, root_dir: str = ".", **kwargs):
        """Initialize file reader tool with sandbox configuration."""
        super().__init__(root_dir=root_dir, **kwargs)
        self._read_tool = ReadFileTool()
        self._root_dir = Path(root_dir).resolve()

    def _validate_path(self, file_path: str) -> Optional[str]:
        """Validate file path against security rules.

        Returns:
            Error message if path is invalid, None if valid.
        """
        try:
            # Resolve the path
            if os.path.isabs(file_path):
                resolved_path = Path(file_path).resolve()
            else:
                resolved_path = (self._root_dir / file_path).resolve()

            # Check if path is inside root_dir
            try:
                resolved_path.relative_to(self._root_dir)
            except ValueError:
                return f"BLOCKED: Path '{file_path}' is outside allowed directory"

            # Check if file exists
            if not resolved_path.exists():
                return f"Error: File not found: {file_path}"

            if not resolved_path.is_file():
                return f"Error: Not a file: {file_path}"

            # Check file extension if whitelist is configured
            if self.allowed_extensions:
                ext = resolved_path.suffix.lower()
                if ext not in self.allowed_extensions:
                    return f"BLOCKED: File extension '{ext}' not allowed"

            # Check file size
            file_size = resolved_path.stat().st_size
            if file_size > self.max_file_size:
                return f"BLOCKED: File too large ({file_size} bytes, max {self.max_file_size})"

            return None

        except Exception as e:
            return f"Error validating path: {str(e)}"

    def _run(self, file_path: str) -> str:
        """Read a file synchronously."""
        # Validate path
        error = self._validate_path(file_path)
        if error:
            return error

        try:
            # Resolve path
            if os.path.isabs(file_path):
                resolved_path = Path(file_path)
            else:
                resolved_path = self._root_dir / file_path

            # Use the LangChain ReadFileTool
            return self._read_tool.run(str(resolved_path))

        except Exception as e:
            return f"Error reading file: {str(e)}"

    async def _arun(self, file_path: str) -> str:
        """Read a file asynchronously."""
        # Validate path
        error = self._validate_path(file_path)
        if error:
            return error

        try:
            # Resolve path
            if os.path.isabs(file_path):
                resolved_path = Path(file_path)
            else:
                resolved_path = self._root_dir / file_path

            # Read file manually for async support
            return resolved_path.read_text(encoding='utf-8')

        except UnicodeDecodeError:
            # Try with different encoding
            try:
                return resolved_path.read_text(encoding='latin-1')
            except Exception as e:
                return f"Error reading file with alternative encoding: {str(e)}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def add_allowed_extension(self, extension: str) -> None:
        """Add an allowed file extension."""
        if self.allowed_extensions is None:
            self.allowed_extensions = []
        if not extension.startswith('.'):
            extension = '.' + extension
        self.allowed_extensions.append(extension.lower())

    def set_allowed_extensions(self, extensions: list[str]) -> None:
        """Set whitelist of allowed file extensions."""
        self.allowed_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]

    def get_metadata(self) -> dict:
        """Get tool metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "root_dir": str(self._root_dir),
            "has_extension_whitelist": self.allowed_extensions is not None,
            "max_file_size": self.max_file_size,
        })
        return metadata
