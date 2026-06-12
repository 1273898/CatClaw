"""Calculator tool for PrivateClaw."""

import math
from typing import Type
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class CalculatorInput(BaseModel):
    """Input for calculator tool."""
    expression: str = Field(description="Mathematical expression to evaluate")


class CalculatorTool(PrivateClawTool):
    """Tool for evaluating mathematical expressions."""

    name: str = "calculator"
    description: str = "Evaluate a mathematical expression. Supports basic arithmetic, trigonometry, and common math functions."
    category: str = "utility"
    args_schema: Type[BaseModel] = CalculatorInput

    # Safe math functions to expose
    _SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "ceil": math.ceil,
        "floor": math.floor,
        "pi": math.pi,
        "e": math.e,
    }

    def _run(self, expression: str) -> str:
        """Evaluate a mathematical expression."""
        try:
            # Create a safe evaluation environment
            safe_dict = {"__builtins__": {}}
            safe_dict.update(self._SAFE_FUNCTIONS)

            result = eval(expression, safe_dict)
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"

    async def _arun(self, expression: str) -> str:
        """Evaluate a mathematical expression asynchronously."""
        return self._run(expression)
