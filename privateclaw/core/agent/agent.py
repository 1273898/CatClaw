"""Core Agent for PrivateClaw."""

from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from privateclaw.core.memory.manager import MemoryManager
from privateclaw.core.tools.registry import ToolRegistry
from privateclaw.core.agent.planner import TaskPlanner, TaskPlan
from privateclaw.core.agent.executor import TaskExecutor


def _create_agent_executor(llm, tools, prompt):
    """Create agent executor with backward compatibility."""
    try:
        # Try new LangChain API first
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        agent = create_openai_tools_agent(llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            return_intermediate_steps=True,
        )
    except ImportError:
        # Fallback: Use simple chain without agent executor
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser

        chain = prompt | llm | StrOutputParser()
        return SimpleAgentExecutor(chain, tools)


SYSTEM_PROMPT = """You are PrivateClaw, a personal AI assistant. You are helpful, harmless, and honest.

Your capabilities:
- Answer questions and provide information
- Execute tasks using available tools
- Remember context from previous conversations
- Break down complex tasks into manageable steps

Guidelines:
1. Be concise and direct in your responses
2. Use tools when necessary to complete tasks
3. Ask for clarification if a request is unclear
4. Acknowledge limitations honestly
5. Respect user privacy and security

When given a complex task:
1. Analyze what needs to be done
2. Break it down into steps if needed
3. Execute each step using appropriate tools
4. Provide clear feedback on progress and results"""


class SimpleAgentExecutor:
    """Simple agent executor fallback when AgentExecutor is not available."""

    def __init__(self, chain, tools):
        self.chain = chain
        self.tools = {t.name: t for t in tools} if tools else {}

    async def ainvoke(self, inputs: dict) -> dict:
        """Invoke the chain."""
        try:
            result = await self.chain.ainvoke(inputs)
            return {"output": result, "intermediate_steps": []}
        except Exception as e:
            return {"output": f"Error: {str(e)}", "intermediate_steps": []}


class PrivateClawAgent:
    """Core agent for PrivateClaw, powered by LangChain."""

    def __init__(
        self,
        llm: BaseChatModel,
        memory: MemoryManager,
        tools: Optional[list] = None,
        system_prompt: Optional[str] = None,
    ):
        """Initialize the agent."""
        self.llm = llm
        self.memory = memory
        self.tools = tools or []
        self.system_prompt = system_prompt or SYSTEM_PROMPT

        # Initialize components
        self.tool_registry = ToolRegistry
        self.planner = TaskPlanner(llm)
        self.executor = TaskExecutor(self.tool_registry)

        # Create agent
        self._agent_executor = self._create_agent()

    def _create_agent(self):
        """Create the LangChain agent executor."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
        ])

        return _create_agent_executor(self.llm, self.tools, prompt)

    async def run(self, input_text: str, session_id: str = "default") -> str:
        """Run the agent with input text."""
        # Get conversation history
        chat_history = await self.memory.get_history(session_id)

        # Convert to LangChain message format
        formatted_history = self._format_history(chat_history)

        try:
            # Run the agent
            result = await self._agent_executor.ainvoke({
                "input": input_text,
                "chat_history": formatted_history,
            })

            # Extract response
            response = result.get("output", "")

            # Store in memory
            await self.memory.add_message(session_id, "human", input_text)
            await self.memory.add_message(session_id, "ai", response)

            return response

        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            await self.memory.add_message(session_id, "human", input_text)
            await self.memory.add_message(session_id, "ai", error_msg)
            return error_msg

    async def run_with_planning(self, input_text: str, session_id: str = "default") -> str:
        """Run the agent with task planning for complex tasks."""
        # Create a task plan
        plan = await self.planner.plan(input_text)

        # Get memory context
        context = await self.memory.get_context(session_id, input_text)

        # Execute the plan
        result = await self.executor.execute_plan(plan, context)

        # Format response
        if result["success"]:
            response = f"Task completed successfully!\n\n"
            response += f"Completed {result['completed']}/{result['total']} steps.\n\n"
            for r in result["results"]:
                if r["success"]:
                    response += f"✓ {r['step']}\n"
                else:
                    response += f"✗ {r['step']}: {r.get('error', 'Unknown error')}\n"
        else:
            response = f"Task partially completed.\n\n"
            response += f"Completed {result['completed']}/{result['total']} steps.\n\n"
            for r in result["results"]:
                if r["success"]:
                    response += f"✓ {r['step']}\n"
                else:
                    response += f"✗ {r['step']}: {r.get('error', 'Unknown error')}\n"

        # Store in memory
        await self.memory.add_message(session_id, "human", input_text)
        await self.memory.add_message(session_id, "ai", response)

        return response

    def _format_history(self, history: list[dict]) -> list:
        """Convert history to LangChain message format."""
        messages = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))

        return messages

    async def stream(self, input_text: str, session_id: str = "default"):
        """Stream the agent response."""
        # Get conversation history
        chat_history = await self.memory.get_history(session_id)
        formatted_history = self._format_history(chat_history)

        # Stream the response
        async for event in self._agent_executor.astream_events({
            "input": input_text,
            "chat_history": formatted_history,
        }, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content

    def add_tool(self, tool) -> None:
        """Add a tool to the agent."""
        self.tools.append(tool)
        self.tool_registry.register(tool)
        # Recreate agent with new tools
        self._agent_executor = self._create_agent()

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent."""
        self.tools = [t for t in self.tools if t.name != tool_name]
        self.tool_registry.unregister(tool_name)
        # Recreate agent with new tools
        self._agent_executor = self._create_agent()

    def get_tools(self) -> list:
        """Get all available tools."""
        return self.tools.copy()
