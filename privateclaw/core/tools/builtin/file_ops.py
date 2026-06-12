"""File operations tools for PrivateClaw."""

from typing import Type
from pathlib import Path
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class FileReadInput(BaseModel):
    """Input for file read tool."""
    file_path: str = Field(description="Path to the file to read")
    encoding: str = Field(default="utf-8", description="File encoding")


class FileWriteInput(BaseModel):
    """Input for file write tool."""
    file_path: str = Field(description="Path to the file to write")
    content: str = Field(description="Content to write to the file")
    encoding: str = Field(default="utf-8", description="File encoding")


class FileReadTool(PrivateClawTool):
    """Tool for reading files."""

    name: str = "file_read"
    description: str = "Read the contents of a file. Use this to read text files, code files, or any other file."
    category: str = "file"
    args_schema: Type[BaseModel] = FileReadInput

    def _run(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read a file synchronously."""
        try:
            path = Path(file_path)
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
    """Tool for writing files."""

    name: str = "file_write"
    description: str = "Write content to a file. Use this to create or update files."
    category: str = "file"
    args_schema: Type[BaseModel] = FileWriteInput

    def _run(self, file_path: str, content: str, encoding: str = "utf-8") -> str:
        """Write to a file synchronously."""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    async def _arun(self, file_path: str, content: str, encoding: str = "utf-8") -> str:
        """Write to a file asynchronously."""
        return self._run(file_path, content, encoding)
