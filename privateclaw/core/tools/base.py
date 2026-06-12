"""Base tool class for PrivateClaw."""

from typing import Optional, Type
from abc import abstractmethod
from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import Field, BaseModel


class PrivateClawToolInput(BaseModel):
    """Base input model for PrivateClaw tools."""
    pass


class PrivateClawTool(LangChainBaseTool):
    """Base class for all PrivateClaw tools."""

    category: str = Field(default="general", description="Tool category")
    requires_auth: bool = Field(default=False, description="Whether tool requires authentication")
    description: str = Field(description="Tool description")
    name: str = Field(description="Tool name")

    class Config:
        arbitrary_types_allowed = True

    def _run(self, *args, **kwargs) -> str:
        """Synchronous run implementation."""
        raise NotImplementedError("Subclass must implement _run")

    async def _arun(self, *args, **kwargs) -> str:
        """Asynchronous run implementation."""
        # Default: call sync version
        return self._run(*args, **kwargs)

    def get_metadata(self) -> dict:
        """Get tool metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "requires_auth": self.requires_auth,
        }
