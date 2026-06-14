"""Calculator tool for PrivateClaw with safe expression evaluation."""

import ast
import math
import operator
from typing import Type, Any, Dict
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class CalculatorInput(BaseModel):
    """Input for calculator tool."""
    expression: str = Field(description="Mathematical expression to evaluate")


def _safe_eval(node: ast.AST) -> Any:
    """Safely evaluate an AST node.

    Only allows basic math operations and safe functions.
    """
    # Allowed operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Safe functions
    SAFE_FUNCTIONS = {
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
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": math.factorial,
        "gcd": math.gcd,
    }

    # Safe constants
    SAFE_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
        "nan": math.nan,
    }

    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    elif isinstance(node, ast.Constant):
        # Only allow numeric constants
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.Name):
        # Check for safe constants
        if node.id in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[node.id]
        # Check for safe functions (return as reference for Call)
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unknown variable: {node.id}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        # Prevent division by zero
        if op_type in (ast.Div, ast.FloorDiv) and right == 0:
            raise ZeroDivisionError("Division by zero")
        # Prevent extremely large exponents
        if op_type == ast.Pow and isinstance(right, (int, float)) and abs(right) > 1000:
            raise ValueError("Exponent too large")
        return OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return OPERATORS[op_type](operand)
    elif isinstance(node, ast.Call):
        # Only allow calls to safe functions
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Unknown function: {func_name}")
        func = SAFE_FUNCTIONS[func_name]
        args = [_safe_eval(arg) for arg in node.args]
        return func(*args)
    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


class CalculatorTool(PrivateClawTool):
    """Tool for evaluating mathematical expressions safely."""

    name: str = "calculator"
    description: str = "Evaluate a mathematical expression. Supports basic arithmetic, trigonometry, and common math functions."
    category: str = "utility"
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(self, expression: str) -> str:
        """Evaluate a mathematical expression."""
        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode='eval')

            # Safely evaluate the AST
            result = _safe_eval(tree)

            # Format the result
            if isinstance(result, float):
                # Remove unnecessary trailing zeros
                if result == int(result) and not (result == 0 and str(result).startswith('-')):
                    return str(int(result))
                # Limit decimal places
                return f"{result:.10g}"
            return str(result)
        except ZeroDivisionError:
            return "Error: Division by zero"
        except ValueError as e:
            return f"Error: {str(e)}"
        except SyntaxError:
            return f"Error: Invalid expression syntax"
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"

    async def _arun(self, expression: str) -> str:
        """Evaluate a mathematical expression asynchronously."""
        return self._run(expression)
