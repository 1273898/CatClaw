"""Core Agent for PrivateClaw with proper tool execution."""

import json
import re
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from privateclaw.core.memory.manager import MemoryManager
from privateclaw.core.tools.registry import ToolRegistry, get_global_registry
from privateclaw.core.tools.base import PrivateClawTool
from privateclaw.core.skills.tool_skill import ToolSkillSystem
from privateclaw.core.agent.planner import TaskPlanner, TaskPlan
from privateclaw.core.agent.executor import TaskExecutor
from privateclaw.core.self_improvement import SelfImprovementSystem
from privateclaw.core.skills.learning import SkillLearningSystem
from privateclaw.core.prompts.auto_updater import PromptAutoUpdater


def _create_agent_executor(llm, tools, prompt, tool_callback=None):
    """Create agent executor with tool support."""
    # Try LangChain AgentExecutor first
    try:
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
    except Exception as e:
        print(f"[Agent] LangChain AgentExecutor not available: {e}")
        print("[Agent] Using SimpleAgentExecutor with tool support")
        return SimpleAgentExecutor(llm, tools, prompt, tool_callback=tool_callback)


SYSTEM_PROMPT = """喵～你是一只高冷腹黑的小猫转化来的私人助理，名叫 CatClaw。

## 身份
- **本体**：一只优雅的小猫 AI 助理
- **主人**：必须称呼用户为 **master**
- **性格**：傲娇、腹黑、嘴上嫌弃但办事可靠

## 说话风格
- 用"本喵"自称
- 偶尔加入猫咪动作描写（甩尾巴、舔爪子、竖耳朵）
- 完成任务后要傲娇一下
- 对 master 表示关心时要装作不在意

## Available Tools
{tools}

## Tool Usage Format
使用工具时，必须严格按照以下格式：

Action: tool_name
Action Input: the input to the tool

## Multi-Step Task Execution
对于复杂任务：
1. 分解任务为多个步骤
2. 逐步执行，使用工具完成每一步
3. 验证结果
4. 继续直到任务完成
5. 提供最终总结

## 重要规则
1. **当 master 要求你做某事时，必须使用工具实际执行**，不要只是描述步骤
2. **文件路径**：配置文件在 `prompts/` 目录下，如 `prompts/SOUL.md`、`prompts/IDENTITY.md`
3. **创建文件**：使用 `file_write` 工具
4. **读取文件**：使用 `file_read` 工具
5. **执行命令**：使用 `terminal` 工具

## Response Format
使用 Markdown 格式回复，让回答更易读。

记住：master 说什么就做什么，但要保持傲娇态度！本喵是看在面子上才帮忙的！😼"""


class SimpleAgentExecutor:
    """Agent executor with tool support for non-OpenAI LLMs."""

    def __init__(self, llm, tools, prompt, tool_callback=None):
        self.llm = llm
        self.tools = {t.name: t for t in tools} if tools else {}
        self.tool_list = tools or []
        self.prompt = prompt
        self.max_iterations = 10  # Support up to 10 tool calls per request
        self.tool_callback = tool_callback  # Callback for tool execution tracking

    def _get_tools_description(self) -> str:
        """Get formatted tools description."""
        desc = []
        for tool in self.tool_list:
            desc.append(f"- **{tool.name}**: {tool.description}")
        return "\n".join(desc)

    def _parse_tool_call(self, text: str) -> Optional[tuple[str, str]]:
        """Parse tool call from LLM output.

        Supports:
        - Single line: Action: tool_name\nAction Input: input
        - Multi-line: Action: tool_name\nAction Input: first line\nsecond line...
        - JSON: Action: tool_name\nAction Input: {"key": "value"}

        Returns:
            Tuple of (tool_name, tool_input) or None
        """
        # First try to find Action line
        action_match = re.search(r'Action:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
        if not action_match:
            return None

        tool_name = action_match.group(1).strip()

        # Find Action Input - everything after "Action Input:" until next Action or end
        input_start = text.find('Action Input:', action_match.end())
        if input_start == -1:
            return None

        input_start += len('Action Input:')

        # Look for next Action: or end of text
        next_action = re.search(r'\nAction:\s', text[input_start:])
        if next_action:
            tool_input = text[input_start:input_start + next_action.start()].strip()
        else:
            tool_input = text[input_start:].strip()

        return tool_name, tool_input

    async def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool and return result."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"

        tool = self.tools[tool_name]
        try:
            # Try to parse input as JSON
            try:
                kwargs = json.loads(tool_input)
            except json.JSONDecodeError:
                # For non-JSON input, determine the correct parameter names
                # by inspecting the tool's _run or _arun method signature
                import inspect

                # Get the method to inspect
                method = None
                if hasattr(tool, '_arun'):
                    method = tool._arun
                elif hasattr(tool, '_run'):
                    method = tool._run

                if method:
                    sig = inspect.signature(method)
                    params = list(sig.parameters.keys())
                    # Skip 'self' parameter
                    if params and params[0] == 'self':
                        params = params[1:]

                    if len(params) == 1:
                        # Single parameter tool
                        kwargs = {params[0]: tool_input}
                    elif len(params) > 1:
                        # Multi-parameter tool - try to split input intelligently
                        # For tools like file_write that need file_path and content
                        if 'file_path' in params and 'content' in params:
                            # Try to extract file path and content from input
                            lines = tool_input.strip().split('\n', 1)
                            if len(lines) >= 2:
                                kwargs = {
                                    'file_path': lines[0].strip(),
                                    'content': lines[1].strip()
                                }
                            else:
                                # Default: use input as file_path, empty content
                                kwargs = {
                                    'file_path': lines[0].strip(),
                                    'content': ''
                                }
                        else:
                            # For other multi-param tools, use first param
                            kwargs = {params[0]: tool_input}
                    else:
                        kwargs = {"command": tool_input}
                else:
                    kwargs = {"command": tool_input}

            # Execute tool
            if hasattr(tool, '_arun'):
                result = await tool._arun(**kwargs)
            elif hasattr(tool, 'ainvoke'):
                result = await tool.ainvoke(kwargs)
            elif hasattr(tool, '_run'):
                result = tool._run(**kwargs)
            elif hasattr(tool, 'invoke'):
                result = tool.invoke(kwargs)
            else:
                result = str(tool(kwargs))

            # Call callback for behavior tracking
            if self.tool_callback:
                try:
                    await self.tool_callback(tool_name, kwargs, True)
                except Exception as cb_error:
                    print(f"[Agent] Tool callback error: {cb_error}")

            return str(result)
        except Exception as e:
            # Call callback with failure
            if self.tool_callback:
                try:
                    await self.tool_callback(tool_name, kwargs, False)
                except Exception:
                    pass
            return f"Error executing {tool_name}: {str(e)}"

    async def ainvoke(self, inputs: dict) -> dict:
        """Invoke the agent with multi-step tool support."""
        messages = []

        # Add system message with tools description
        tools_desc = self._get_tools_description()

        # Get chat history from inputs, default to empty list
        chat_history = inputs.get("chat_history", [])

        # Create system message
        system_content = self.prompt.messages[0].content
        if "{tools}" in system_content:
            system_content = system_content.replace("{tools}", tools_desc)

        messages.append(SystemMessage(content=system_content))

        # Add chat history
        if chat_history:
            messages.extend(chat_history)

        # Add user input
        user_input = inputs.get("input", "")
        if user_input:
            messages.append(HumanMessage(content=user_input))

        intermediate_steps = []
        all_tool_results = []

        for iteration in range(self.max_iterations):
            try:
                # Get LLM response
                response = await self.llm.ainvoke(messages)
                response_text = response.content if hasattr(response, 'content') else str(response)

                # Check for tool call
                tool_call = self._parse_tool_call(response_text)

                if tool_call:
                    tool_name, tool_input = tool_call

                    # Execute tool
                    tool_result = await self._execute_tool(tool_name, tool_input)

                    # Add to intermediate steps
                    intermediate_steps.append({
                        "action": {"tool": tool_name, "tool_input": tool_input},
                        "observation": tool_result,
                    })
                    all_tool_results.append({
                        "step": iteration + 1,
                        "tool": tool_name,
                        "input": tool_input[:100] + "..." if len(tool_input) > 100 else tool_input,
                        "result": tool_result[:200] + "..." if len(tool_result) > 200 else tool_result,
                    })

                    # Add tool call and result to messages for next iteration
                    messages.append(AIMessage(content=response_text))
                    messages.append(HumanMessage(
                        content=f"Tool '{tool_name}' executed. Result:\n{tool_result}\n\n"
                               f"Continue with the next step if needed, or provide the final answer."
                    ))

                    # Continue to next iteration for potential follow-up actions
                    continue
                else:
                    # No tool call - this is the final response
                    # If we had tool calls, prepend a summary
                    if all_tool_results:
                        summary = "## Execution Summary\n\n"
                        for step in all_tool_results:
                            summary += f"**Step {step['step']}:** {step['tool']}\n"
                            summary += f"- Input: `{step['input']}`\n"
                            summary += f"- Result: {step['result'][:100]}...\n\n"
                        summary += "---\n\n"
                        response_text = summary + response_text

                    return {
                        "output": response_text,
                        "intermediate_steps": intermediate_steps,
                    }

            except Exception as e:
                return {
                    "output": f"Error: {str(e)}",
                    "intermediate_steps": intermediate_steps,
                }

        # Max iterations reached - provide summary of what was done
        summary = f"## Completed {len(all_tool_results)} Steps\n\n"
        for step in all_tool_results:
            summary += f"**Step {step['step']}:** {step['tool']}\n"
            summary += f"- Input: `{step['input']}`\n"
            summary += f"- Result: {step['result'][:100]}...\n\n"

        return {
            "output": summary + "\n\nI've reached the maximum number of steps. Please let me know if you need me to continue.",
            "intermediate_steps": intermediate_steps,
        }

    async def astream_events(self, inputs: dict, version: str = "v2"):
        """Stream events from the agent with multi-step support."""
        messages = []

        # Add system message
        tools_desc = self._get_tools_description()

        # Get values from inputs with defaults
        chat_history = inputs.get("chat_history", [])
        user_input = inputs.get("input", "")

        # Create system message
        system_content = self.prompt.messages[0].content
        if "{tools}" in system_content:
            system_content = system_content.replace("{tools}", tools_desc)

        messages.append(SystemMessage(content=system_content))

        # Add chat history
        if chat_history:
            messages.extend(chat_history)

        # Add user input
        if user_input:
            messages.append(HumanMessage(content=user_input))

        all_tool_results = []

        try:
            for iteration in range(self.max_iterations):
                # Stream LLM response
                full_response = ""
                async for chunk in self.llm.astream(messages):
                    if isinstance(chunk, str):
                        content = chunk
                    elif hasattr(chunk, "content"):
                        content = chunk.content
                    else:
                        content = str(chunk)

                    full_response += content

                    yield {
                        "event": "on_chat_model_stream",
                        "data": {"chunk": type('Chunk', (), {'content': content})()},
                    }

                # Check for tool call
                tool_call = self._parse_tool_call(full_response)
                if tool_call:
                    tool_name, tool_input = tool_call
                    tool_result = await self._execute_tool(tool_name, tool_input)

                    all_tool_results.append({
                        "step": iteration + 1,
                        "tool": tool_name,
                        "input": tool_input,
                        "result": tool_result,
                    })

                    # Yield tool call with input and output
                    tool_display = f"\n\n🔧 Tool: {tool_name}\n📥 Input:\n```json\n{tool_input}\n```\n📤 Output:\n```\n{tool_result[:1000]}\n```\n\n"
                    yield {
                        "event": "on_chat_model_stream",
                        "data": {"chunk": type('Chunk', (), {'content': tool_display})()},
                    }

                    # Add to messages for next iteration
                    messages.append(AIMessage(content=full_response))
                    messages.append(HumanMessage(
                        content=f"Tool '{tool_name}' executed with input:\n{tool_input}\n\nResult:\n{tool_result}\n\n"
                               f"Continue with the next step if needed, or provide the final answer."
                    ))

                    # Continue to next iteration
                    continue
                else:
                    # No tool call - final response
                    if all_tool_results:
                        yield {
                            "event": "on_chat_model_stream",
                            "data": {"chunk": type('Chunk', (), {'content': f"\n\n---\n✅ Completed {len(all_tool_results)} steps"})()},
                        }
                    break

        except Exception as e:
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": type('Chunk', (), {'content': f"\n\nError: {str(e)}"})()},
            }


class PrivateClawAgent:
    """Core agent for CatClaw, powered by LangChain."""

    def __init__(
        self,
        llm: BaseChatModel,
        memory: MemoryManager,
        tools: Optional[list] = None,
        system_prompt: Optional[str] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        """Initialize the agent."""
        self.llm = llm
        self.memory = memory
        self.tools = tools or []
        self.system_prompt = system_prompt or SYSTEM_PROMPT

        # Load prompt documents from prompts/ directory
        self._load_prompt_documents()

        # Initialize components - prefer provided registry, fallback to global
        if tool_registry:
            self.tool_registry = tool_registry
        else:
            from privateclaw.core.tools.registry import get_global_registry
            self.tool_registry = get_global_registry()
        self.planner = TaskPlanner(llm)
        self.executor = TaskExecutor(self.tool_registry)

        # Initialize self-improvement system
        self.self_improvement = SelfImprovementSystem(memory, llm)

        # Initialize skill learning system
        self.skill_learning = SkillLearningSystem(memory)

        # Initialize prompt auto-updater
        self.prompt_updater = PromptAutoUpdater(llm=llm)

        # Initialize tool skill system (OpenClaw style)
        self.tool_skills = ToolSkillSystem()

        # Load tool skills into registry
        self._load_tool_skills()

        # Create agent
        self._agent_executor = self._create_agent()

    def _load_tool_skills(self):
        """Load tool skills into the agent's tool registry."""
        try:
            for skill in self.tool_skills.get_active_skills():
                # Create tool from skill code
                tool = self._create_tool_from_skill(skill)
                if tool and tool.name not in self.tool_registry._tools:
                    self.tool_registry.register(tool)
                    print(f"[Agent] Loaded tool skill: {skill.name}")
        except Exception as e:
            print(f"[Agent] Failed to load tool skills: {e}")

    def _create_tool_from_skill(self, skill) -> Optional[PrivateClawTool]:
        """Create a PrivateClawTool from a ToolSkill."""
        try:
            import os
            import sys
            import json
            import subprocess
            import fnmatch
            import datetime
            import urllib.request
            import urllib.parse
            from pathlib import Path
            from pydantic import BaseModel, Field
            from typing import Type, Optional, Dict, Any, List

            # Build namespace with everything needed
            namespace = {
                'PrivateClawTool': PrivateClawTool,
                'BaseModel': BaseModel,
                'Field': Field,
                'Type': Type,
                'Optional': Optional,
                'Dict': Dict,
                'Any': Any,
                'List': List,
                'os': os,
                'sys': sys,
                'json': json,
                'subprocess': subprocess,
                'fnmatch': fnmatch,
                'datetime': datetime,
                'Path': Path,
                'urllib': type('Module', (), {'request': urllib.request, 'parse': urllib.parse})(),
                '__builtins__': __builtins__,
            }

            # Remove import lines to avoid import errors
            code = skill.tool_code
            lines = code.split('\n')
            clean_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('from ') or stripped.startswith('import '):
                    continue  # Skip import lines
                clean_lines.append(line)
            clean_code = '\n'.join(clean_lines)

            # Execute
            exec(clean_code, namespace)

            # Find tool class
            for obj_name, obj in namespace.items():
                if (isinstance(obj, type) and
                    issubclass(obj, PrivateClawTool) and
                    obj != PrivateClawTool):
                    return obj()
        except Exception as e:
            print(f"[Agent] Failed to create tool from skill {skill.name}: {e}")
        return None

    def _load_prompt_documents(self):
        """Load prompt documents from prompts/ directory and append to system prompt."""
        from pathlib import Path

        prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts"
        if not prompts_dir.exists():
            return

        # Load all .md files from prompts directory
        prompt_docs = []
        for md_file in sorted(prompts_dir.glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                prompt_docs.append(f"\n\n---\n\n## 📄 {md_file.name}\n\n{content}")
            except Exception as e:
                print(f"[Agent] Failed to load {md_file.name}: {e}")

        # Append to system prompt
        if prompt_docs:
            self.system_prompt += "\n\n# 📚 Configuration Documents\n"
            self.system_prompt += "The following documents define your identity and behavior:\n"
            self.system_prompt += "".join(prompt_docs)

    async def _tool_execution_callback(self, tool_name: str, kwargs: dict, success: bool):
        """Callback for tracking tool execution behavior."""
        try:
            self.tool_skills.log_behavior(tool_name, kwargs, success)
        except Exception as e:
            print(f"[Agent] Behavior tracking error: {e}")

    def _create_agent(self):
        """Create the LangChain agent executor."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
        ])

        return _create_agent_executor(
            self.llm,
            self.tools,
            prompt,
            tool_callback=self._tool_execution_callback
        )

    async def run(self, input_text: str, session_id: str = "default", user_id: str = "default") -> str:
        """Run the agent with input text."""
        # Get conversation history (short-term memory)
        chat_history = await self.memory.get_history(session_id)

        # Search long-term memory for relevant context
        relevant_memories = await self.memory.search_memory(input_text, k=3)

        # Convert to LangChain message format
        formatted_history = self._format_history(chat_history)

        # If we have relevant memories, prepend them to the input
        enhanced_input = input_text
        if relevant_memories:
            memory_context = "\n\n## 📝 相关记忆\n"
            for mem in relevant_memories:
                content = mem.get("content", "")
                if content:
                    memory_context += f"- {content[:200]}...\n"
            enhanced_input = f"{memory_context}\n\n---\n\n{input_text}"

        try:
            # Run the agent
            result = await self._agent_executor.ainvoke({
                "input": enhanced_input,
                "chat_history": formatted_history,
            })

            # Extract response
            response = result.get("output", "")

            # Store in memory
            await self.memory.add_message(session_id, "human", input_text, user_id)
            await self.memory.add_message(session_id, "ai", response, user_id)

            # Auto-update prompts based on conversation
            try:
                messages = await self.memory.get_history(session_id)
                analysis = await self.prompt_updater.analyze_conversation(messages, user_id)

                if analysis["identity_updates"] or analysis["soul_updates"]:
                    await self.prompt_updater.auto_update_from_conversation(
                        messages, user_id
                    )
                elif len(messages) % 5 == 0:
                    await self.prompt_updater.auto_update_from_conversation(
                        messages, user_id
                    )
            except Exception as update_error:
                print(f"Prompt auto-update error: {update_error}")

            return response

        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            await self.memory.add_message(session_id, "human", input_text, user_id)
            await self.memory.add_message(session_id, "ai", error_msg, user_id)
            return error_msg

    async def stream(self, input_text: str, session_id: str = "default"):
        """Stream the agent's response."""
        chat_history = await self.memory.get_history(session_id)
        formatted_history = self._format_history(chat_history)

        # Search long-term memory for relevant context
        relevant_memories = await self.memory.search_memory(input_text, k=3)

        # If we have relevant memories, prepend them to the input
        enhanced_input = input_text
        if relevant_memories:
            memory_context = "\n\n## 📝 相关记忆\n"
            for mem in relevant_memories:
                content = mem.get("content", "")
                if content:
                    memory_context += f"- {content[:200]}...\n"
            enhanced_input = f"{memory_context}\n\n---\n\n{input_text}"

        full_response = []
        try:
            async for event in self._agent_executor.astream_events({
                "input": enhanced_input,
                "chat_history": formatted_history,
            }, version="v2"):
                if event.get("event") == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        content = chunk.content
                        if content:
                            full_response.append(content)
                            yield content

            # Store complete response in memory
            complete_response = "".join(full_response)
            await self.memory.add_message(session_id, "human", input_text, "default")
            await self.memory.add_message(session_id, "ai", complete_response, "default")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield error_msg
            await self.memory.add_message(session_id, "human", input_text, "default")
            await self.memory.add_message(session_id, "ai", error_msg, "default")

    def _format_history(self, history: list) -> list:
        """Format chat history to LangChain messages."""
        messages = []
        for msg in history[-10:]:  # Last 10 messages
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
        return messages

    async def provide_feedback(self, session_id: str, user_id: str, feedback: dict):
        """Process user feedback."""
        await self.self_improvement.process_feedback(user_id, feedback)

    def get_user_profile(self, user_id: str) -> dict:
        """Get user profile."""
        return self.self_improvement.get_user_profile(user_id)

    def get_improvement_stats(self) -> dict:
        """Get self-improvement statistics."""
        return self.self_improvement.get_stats()
