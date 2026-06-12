"""Shell command tool for PrivateClaw."""

import subprocess
import asyncio
from typing import Type
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class ShellInput(BaseModel):
    """Input for shell tool."""
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=30, description="Command timeout in seconds")


class ShellTool(PrivateClawTool):
    """Tool for executing shell commands."""

    name: str = "shell"
    description: str = "Execute a shell command. Use this to run system commands, scripts, or programs."
    category: str = "system"
    requires_auth: bool = True
    args_schema: Type[BaseModel] = ShellInput

    def _run(self, command: str, timeout: int = 30) -> str:
        """Execute a shell command synchronously."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[Exit code: {result.returncode}]"
            return output
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    async def _arun(self, command: str, timeout: int = 30) -> str:
        """Execute a shell command asynchronously."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: Command timed out after {timeout} seconds"

            output = stdout.decode("utf-8", errors="replace")
            if stderr:
                output += f"\n[STDERR]\n{stderr.decode('utf-8', errors='replace')}"
            if process.returncode != 0:
                output += f"\n[Exit code: {process.returncode}]"
            return output
        except Exception as e:
            return f"Error executing command: {str(e)}"
