"""Task planner for PrivateClaw Agent."""

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel


class TaskPlan(BaseModel):
    """Task plan structure."""

    goal: str = Field(description="The final goal")
    steps: list[str] = Field(description="Execution steps")
    dependencies: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Step dependencies (step -> list of required steps)"
    )
    estimated_complexity: str = Field(
        default="medium",
        description="Complexity assessment: low, medium, high"
    )
    requires_tools: list[str] = Field(
        default_factory=list,
        description="Tools required for this task"
    )


class TaskPlanner:
    """Task planner - breaks down complex tasks into executable steps."""

    def __init__(self, llm: BaseChatModel):
        """Initialize task planner with LLM."""
        self.llm = llm.with_structured_output(TaskPlan)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a task planning expert. Break down user requests into clear, executable steps.

Consider:
1. Dependencies between steps
2. Potential failure points and fallback strategies
3. Steps that can be executed in parallel
4. Required tools or resources

Provide a structured plan with clear, actionable steps."""),
            ("human", "{task}"),
        ])

    async def plan(self, task: str) -> TaskPlan:
        """Create a task plan."""
        chain = self.prompt | self.llm
        result = await chain.ainvoke({"task": task})
        return result

    async def replan(self, task: str, current_progress: str, failed_step: str) -> TaskPlan:
        """Replan when a step fails."""
        replan_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a task planning expert. The original plan had a failure.
Create a new plan that:
1. Accounts for the failed step
2. Includes alternative approaches
3. Maintains progress on completed steps

Original task: {task}
Current progress: {current_progress}
Failed step: {failed_step}"""),
            ("human", "Create a revised plan."),
        ])

        chain = replan_prompt | self.llm
        result = await chain.ainvoke({
            "task": task,
            "current_progress": current_progress,
            "failed_step": failed_step,
        })
        return result
