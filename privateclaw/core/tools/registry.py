"""Tool registry for PrivateClaw."""

from typing import Optional, Type
from privateclaw.core.tools.base import PrivateClawTool


class ToolRegistry:
    """Registry for managing tools."""

    _tools: dict[str, PrivateClawTool] = {}
    _categories: dict[str, list[str]] = {}

    @classmethod
    def register(cls, tool: PrivateClawTool) -> None:
        """Register a tool."""
        cls._tools[tool.name] = tool

        # Update category index
        if tool.category not in cls._categories:
            cls._categories[tool.category] = []
        if tool.name not in cls._categories[tool.category]:
            cls._categories[tool.category].append(tool.name)

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a tool."""
        if name in cls._tools:
            tool = cls._tools[name]
            if tool.category in cls._categories:
                cls._categories[tool.category].remove(name)
            del cls._tools[name]

    @classmethod
    def get(cls, name: str) -> Optional[PrivateClawTool]:
        """Get a tool by name."""
        return cls._tools.get(name)

    @classmethod
    def get_all(cls) -> dict[str, PrivateClawTool]:
        """Get all registered tools."""
        return cls._tools.copy()

    @classmethod
    def get_by_category(cls, category: str) -> list[PrivateClawTool]:
        """Get tools by category."""
        tool_names = cls._categories.get(category, [])
        return [cls._tools[name] for name in tool_names if name in cls._tools]

    @classmethod
    def get_categories(cls) -> list[str]:
        """Get all categories."""
        return list(cls._categories.keys())

    @classmethod
    def get_langchain_tools(cls) -> list:
        """Get tools in LangChain format."""
        return list(cls._tools.values())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools."""
        cls._tools.clear()
        cls._categories.clear()

    @classmethod
    def load_builtin_tools(cls, root_dir: str = ".") -> None:
        """Load all built-in tools.

        Args:
            root_dir: Root directory for sandboxed tools (terminal, file_reader)
        """
        from privateclaw.core.tools.builtin import (
            WebSearchTool,
            FileReadTool,
            FileWriteTool,
            ShellTool,
            CalculatorTool,
            TerminalTool,
            FetchUrlTool,
            FileReaderTool,
        )

        cls.register(WebSearchTool())
        cls.register(FileReadTool())
        cls.register(FileWriteTool())
        cls.register(ShellTool())
        cls.register(CalculatorTool())
        cls.register(TerminalTool(root_dir=root_dir))
        cls.register(FetchUrlTool())
        cls.register(FileReaderTool(root_dir=root_dir))

    @classmethod
    def load_all(cls, config: Optional[dict] = None) -> list:
        """Load all tools based on config."""
        cls.clear()
        cls.load_builtin_tools()

        # Load custom tools from config if provided
        if config and "custom" in config:
            for tool_config in config["custom"]:
                # TODO: Implement custom tool loading
                pass

        return cls.get_langchain_tools()
