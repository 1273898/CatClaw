"""Tool registry for PrivateClaw with instance-based state."""

from typing import Optional, Type
from privateclaw.core.tools.base import PrivateClawTool


class ToolRegistry:
    """Registry for managing tools.

    Uses instance variables instead of class variables to avoid
    global state pollution between multiple agent instances.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: dict[str, PrivateClawTool] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, tool: PrivateClawTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

        # Update category index
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            tool = self._tools[name]
            if tool.category in self._categories:
                self._categories[tool.category].remove(name)
            del self._tools[name]

    def get(self, name: str) -> Optional[PrivateClawTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self) -> dict[str, PrivateClawTool]:
        """Get all registered tools."""
        return self._tools.copy()

    def get_by_category(self, category: str) -> list[PrivateClawTool]:
        """Get tools by category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_categories(self) -> list[str]:
        """Get all categories."""
        return list(self._categories.keys())

    def get_langchain_tools(self) -> list:
        """Get tools in LangChain format."""
        return list(self._tools.values())

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()

    def load_builtin_tools(self, root_dir: str = ".") -> None:
        """Load all built-in tools.

        Args:
            root_dir: Root directory for sandboxed tools (terminal)
        """
        from privateclaw.core.tools.builtin import (
            WebSearchTool,
            FileReadTool,
            FileWriteTool,
            CalculatorTool,
            TerminalTool,
            FetchUrlTool,
        )

        self.register(WebSearchTool())
        self.register(FileReadTool())
        self.register(FileWriteTool())
        self.register(CalculatorTool())
        self.register(TerminalTool(root_dir=root_dir))
        self.register(FetchUrlTool())

    def load_all(self, config: Optional[dict] = None) -> list:
        """Load all tools based on config.

        Note: This preserves existing tools and only adds built-in tools.
        Use reload() to clear and reload everything.
        """
        # Only load if no tools are registered yet
        if not self._tools:
            self.load_builtin_tools()

        # Load custom tools from config if provided
        if config and "custom" in config:
            for tool_config in config["custom"]:
                # TODO: Implement custom tool loading
                pass

        return self.get_langchain_tools()

    def reload(self, config: Optional[dict] = None) -> list:
        """Clear and reload all tools."""
        self.clear()
        return self.load_all(config)


# Global registry instance for backward compatibility
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """Get or create the global registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
