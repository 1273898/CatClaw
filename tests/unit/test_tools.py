"""Unit tests for the tools system."""

import pytest
from pathlib import Path
from privateclaw.core.tools.registry import ToolRegistry
from privateclaw.core.tools.builtin.calculator import CalculatorTool
from privateclaw.core.tools.builtin.file_ops import FileReadTool, FileWriteTool


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_registry_creation(self):
        """Test creating a new registry instance."""
        registry = ToolRegistry()
        assert registry._tools == {}
        assert registry._categories == {}

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = CalculatorTool()
        registry.register(tool)

        assert "calculator" in registry._tools
        assert registry.get("calculator") == tool
        assert "utility" in registry._categories
        assert "calculator" in registry._categories["utility"]

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = CalculatorTool()
        registry.register(tool)
        registry.unregister("calculator")

        assert "calculator" not in registry._tools
        assert "calculator" not in registry._categories.get("utility", [])

    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_get_all_tools(self):
        """Test getting all registered tools."""
        registry = ToolRegistry()
        tool1 = CalculatorTool()
        tool2 = FileReadTool()
        registry.register(tool1)
        registry.register(tool2)

        all_tools = registry.get_all()
        assert len(all_tools) == 2
        assert "calculator" in all_tools
        assert "file_read" in all_tools

    def test_get_by_category(self):
        """Test getting tools by category."""
        registry = ToolRegistry()
        tool1 = CalculatorTool()
        tool2 = FileReadTool()
        registry.register(tool1)
        registry.register(tool2)

        utility_tools = registry.get_by_category("utility")
        assert len(utility_tools) == 1
        assert utility_tools[0].name == "calculator"

        file_tools = registry.get_by_category("file")
        assert len(file_tools) == 1
        assert file_tools[0].name == "file_read"

    def test_get_categories(self):
        """Test getting all categories."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(FileReadTool())

        categories = registry.get_categories()
        assert "utility" in categories
        assert "file" in categories

    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(FileReadTool())
        registry.clear()

        assert len(registry._tools) == 0
        assert len(registry._categories) == 0

    def test_load_builtin_tools(self):
        """Test loading built-in tools."""
        registry = ToolRegistry()
        registry.load_builtin_tools()

        # Should have all built-in tools
        assert "calculator" in registry._tools
        assert "file_read" in registry._tools
        assert "file_write" in registry._tools
        assert "terminal" in registry._tools
        assert "web_search" in registry._tools
        assert "fetch_url" in registry._tools


class TestCalculatorTool:
    """Tests for CalculatorTool."""

    def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        tool = CalculatorTool()
        assert tool._run("2 + 3") == "5"
        assert tool._run("10 - 4") == "6"
        assert tool._run("3 * 7") == "21"
        assert tool._run("15 / 3") == "5"

    def test_complex_expressions(self):
        """Test complex mathematical expressions."""
        tool = CalculatorTool()
        assert tool._run("2 ** 10") == "1024"
        assert tool._run("sqrt(16)") == "4"
        assert tool._run("sin(pi/2)") == "1"
        assert tool._run("log10(100)") == "2"

    def test_division_by_zero(self):
        """Test division by zero handling."""
        tool = CalculatorTool()
        result = tool._run("1 / 0")
        assert "Error" in result

    def test_invalid_expression(self):
        """Test invalid expression handling."""
        tool = CalculatorTool()
        result = tool._run("invalid +++ expression")
        assert "Error" in result

    def test_unsafe_expression_blocked(self):
        """Test that unsafe expressions are blocked."""
        tool = CalculatorTool()
        # These should fail because they use blocked features
        result = tool._run("__import__('os').system('ls')")
        assert "Error" in result


class TestFileTools:
    """Tests for FileReadTool and FileWriteTool."""

    def test_file_write_and_read(self, tmp_path):
        """Test writing and reading a file."""
        write_tool = FileWriteTool()
        read_tool = FileReadTool()

        test_file = tmp_path / "test.txt"
        content = "Hello, CatClaw!"

        # Write file
        result = write_tool._run(str(test_file), content)
        assert "Successfully" in result
        assert test_file.exists()

        # Read file
        result = read_tool._run(str(test_file))
        assert result == content

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        tool = FileReadTool()
        result = tool._run("/nonexistent/file.txt")
        assert "Error" in result

    def test_path_validation(self, tmp_path):
        """Test path validation for security."""
        write_tool = FileWriteTool()

        # Try to write outside project directory (should fail)
        result = write_tool._run("/tmp/outside_project.txt", "test")
        assert "Error" in result or "outside" in result.lower()


@pytest.mark.asyncio
class TestAsyncTools:
    """Tests for async tool operations."""

    async def test_calculator_async(self):
        """Test calculator async operation."""
        tool = CalculatorTool()
        result = await tool._arun("2 + 3")
        assert result == "5"

    async def test_file_operations_async(self, tmp_path):
        """Test file operations async."""
        write_tool = FileWriteTool()
        read_tool = FileReadTool()

        test_file = tmp_path / "async_test.txt"
        content = "Async test content"

        # Write
        await write_tool._arun(str(test_file), content)
        assert test_file.exists()

        # Read
        result = await read_tool._arun(str(test_file))
        assert result == content
