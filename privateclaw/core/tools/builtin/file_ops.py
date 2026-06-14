"""File operations tools for PrivateClaw with security restrictions."""

from typing import Type
from pathlib import Path
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()


def _validate_path(file_path: str) -> tuple[bool, Path, str]:
    """Validate that a path is within the project directory.

    Args:
        file_path: Path to validate

    Returns:
        Tuple of (is_valid, resolved_path, error_message)
    """
    try:
        # Resolve the path to handle .. and symlinks
        path = Path(file_path).resolve()
        project_root = PROJECT_ROOT.resolve()

        # Check if path is within project directory
        try:
            path.relative_to(project_root)
        except ValueError:
            return False, path, f"Path '{file_path}' is outside the project directory"

        return True, path, ""
    except Exception as e:
        return False, Path(file_path), f"Invalid path: {str(e)}"


class FileReadInput(BaseModel):
    """Input for file read tool."""
    file_path: str = Field(description="Path to the file to read (relative to project root)")
    encoding: str = Field(default="utf-8", description="File encoding")


class FileWriteInput(BaseModel):
    """Input for file write tool."""
    file_path: str = Field(description="Path to the file to write (relative to project root)")
    content: str = Field(description="Content to write to the file")
    encoding: str = Field(default="utf-8", description="File encoding")


class FileReadTool(PrivateClawTool):
    """Tool for reading files within the project directory."""

    name: str = "file_read"
    description: str = "Read the contents of a file within the project directory."
    category: str = "file"
    args_schema: Type[BaseModel] = FileReadInput

    def _run(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read a file synchronously."""
        # Validate path
        is_valid, path, error = _validate_path(file_path)
        if not is_valid:
            return f"Error: {error}"

        try:
            if not path.exists():
                return f"Error: File not found: {file_path}"
            if not path.is_file():
                return f"Error: Not a file: {file_path}"

            content = path.read_text(encoding=encoding)
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    async def _arun(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read a file asynchronously."""
        return self._run(file_path, encoding)


class FileWriteTool(PrivateClawTool):
    """Tool for writing files within the project directory."""

    name: str = "file_write"
    description: str = "Write content to a file within the project directory."
    category: str = "file"
    args_schema: Type[BaseModel] = FileWriteInput

    def _run(self, file_path: str, content: str, encoding: str = "utf-8") -> str:
        """Write to a file synchronously."""
        # Validate path
        is_valid, path, error = _validate_path(file_path)
        if not is_valid:
            return f"Error: {error}"

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    async def _arun(self, file_path: str, content: str, encoding: str = "utf-8") -> str:
        """Write to a file asynchronously."""
        return self._run(file_path, content, encoding)
