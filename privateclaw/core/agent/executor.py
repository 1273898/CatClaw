"""Task executor for PrivateClaw Agent."""

from typing import Optional
from privateclaw.core.agent.planner import TaskPlan
from privateclaw.core.tools.registry import ToolRegistry


class TaskExecutor:
    """Task executor - executes planned steps using tools."""

    def __init__(self, tool_registry: ToolRegistry):
        """Initialize task executor."""
        self.tool_registry = tool_registry
        self.execution_history: list[dict] = []

    async def execute_step(self, step: str, context: dict) -> dict:
        """Execute a single step."""
        # Determine which tool to use
        tool_name = self._identify_tool(step)
        if not tool_name:
            return {
                "success": False,
                "error": f"No suitable tool found for step: {step}",
                "step": step,
            }

        tool = self.tool_registry.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "step": step,
            }

        try:
            # Execute the tool
            result = await tool.ainvoke({"query": step, **context})

            # Record execution
            self.execution_history.append({
                "step": step,
                "tool": tool_name,
                "result": result,
                "success": True,
            })

            return {
                "success": True,
                "result": result,
                "step": step,
                "tool": tool_name,
            }
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "step": step,
                "tool": tool_name,
            }
            self.execution_history.append(error_result)
            return error_result

    async def execute_plan(self, plan: TaskPlan, context: dict) -> dict:
        """Execute a complete task plan."""
        results = []
        completed_steps = set()

        for step in plan.steps:
            # Check dependencies
            dependencies = plan.dependencies.get(step, [])
            if not all(dep in completed_steps for dep in dependencies):
                results.append({
                    "success": False,
                    "error": f"Dependencies not met for step: {step}",
                    "step": step,
                })
                continue

            # Execute step
            result = await self.execute_step(step, context)
            results.append(result)

            if result["success"]:
                completed_steps.add(step)

        return {
            "completed": len(completed_steps),
            "total": len(plan.steps),
            "results": results,
            "success": len(completed_steps) == len(plan.steps),
        }

    def _identify_tool(self, step: str) -> Optional[str]:
        """Identify which tool to use for a step."""
        step_lower = step.lower()

        # Simple keyword-based tool selection
        # Can be enhanced with LLM-based tool selection
        if any(word in step_lower for word in ["search", "find", "look up", "query"]):
            return "web_search"
        elif any(word in step_lower for word in ["read", "load", "open file"]):
            return "file_read"
        elif any(word in step_lower for word in ["write", "save", "create file"]):
            return "file_write"
        elif any(word in step_lower for word in ["run", "execute", "command", "shell"]):
            return "shell"
        elif any(word in step_lower for word in ["calculate", "compute", "math"]):
            return "calculator"

        return None

    def get_execution_history(self) -> list[dict]:
        """Get execution history."""
        return self.execution_history.copy()

    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()
