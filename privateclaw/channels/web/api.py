"""API routes for PrivateClaw web interface."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(description="Message content")
    session_id: str = Field(default="default", description="Session ID")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(description="Response content")
    session_id: str = Field(description="Session ID")


class MemorySearchRequest(BaseModel):
    """Memory search request model."""
    query: str = Field(description="Search query")
    k: int = Field(default=5, description="Number of results")


class MemorySearchResponse(BaseModel):
    """Memory search response model."""
    results: list[dict] = Field(description="Search results")


class IngestRequest(BaseModel):
    """Document ingestion request model."""
    text: str = Field(description="Text to ingest")
    metadata: Optional[dict] = Field(default=None, description="Optional metadata")


class IngestResponse(BaseModel):
    """Document ingestion response model."""
    ids: list[str] = Field(description="Document IDs")
    message: str = Field(description="Status message")


def create_api_router(
    agent=None,
    memory=None,
    session_manager=None,
    ws_manager=None,
    tool_registry=None,
) -> APIRouter:
    """Create API router.

    Args:
        agent: PrivateClaw agent instance
        memory: Memory manager instance
        session_manager: Session manager instance
        ws_manager: WebSocket manager instance
        tool_registry: Tool registry instance

    Returns:
        APIRouter instance
    """
    router = APIRouter()

    # Store tool_registry reference for use in endpoints
    _tool_registry = tool_registry

    @router.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    @router.get("/status")
    async def status():
        """Get system status."""
        return {
            "agent_initialized": agent is not None,
            "memory_initialized": memory is not None,
            "active_sessions": len(session_manager._sessions) if session_manager else 0,
        }

    @router.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Send a chat message."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        try:
            response = await agent.run(
                request.message,
                session_id=request.session_id,
                user_id=request.session_id  # Use session_id as user_id for now
            )
            return ChatResponse(
                response=response,
                session_id=request.session_id,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/chat/stream")
    async def chat_stream(request: ChatRequest):
        """Stream a chat response."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        from fastapi.responses import StreamingResponse
        import json

        async def generate():
            full_response = []
            async for chunk in agent.stream(request.message, request.session_id):
                full_response.append(chunk)
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )

    @router.get("/sessions")
    async def list_sessions():
        """List all sessions with details."""
        if not session_manager:
            return {"sessions": []}

        sessions = await session_manager.list_sessions()
        session_list = []

        for session_id in sessions:
            session = await session_manager.get_session(session_id)
            if session:
                # Get message count from memory
                message_count = 0
                last_message = None
                if memory:
                    history = await memory.get_history(session_id)
                    message_count = len(history)
                    if history:
                        last_message = history[-1].get("content", "")[:100]

                session_list.append({
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "last_active": session.last_active.isoformat(),
                    "message_count": message_count,
                    "last_message": last_message,
                    "is_active": session.is_active(),
                })

        return {"sessions": session_list}

    @router.post("/sessions")
    async def create_session(session_data: dict):
        """Create a new session."""
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")

        session_id = session_data.get("session_id", f"session_{datetime.now().timestamp()}")
        session = await session_manager.get_or_create_session(session_id)

        return {"session_id": session.session_id, "message": "Session created"}

    @router.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get session details."""
        if not session_manager:
            raise HTTPException(status_code=404, detail="Session manager not initialized")

        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get message count from memory
        message_count = 0
        if memory:
            history = await memory.get_history(session_id)
            message_count = len(history)

        result = session.to_dict()
        result["message_count"] = message_count
        return result

    @router.put("/sessions/{session_id}")
    async def update_session(session_id: str, update_data: dict):
        """Update session metadata."""
        if not session_manager:
            raise HTTPException(status_code=404, detail="Session manager not initialized")

        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Update metadata
        if "metadata" in update_data:
            session.metadata.update(update_data["metadata"])

        return {"message": "Session updated", "session": session.to_dict()}

    @router.delete("/sessions/{session_id}")
    async def delete_session(session_id: str):
        """Delete a session."""
        if not session_manager:
            raise HTTPException(status_code=404, detail="Session manager not initialized")

        success = await session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session deleted"}

    @router.get("/sessions/{session_id}/history")
    async def get_session_history(session_id: str):
        """Get session conversation history."""
        if not memory:
            raise HTTPException(status_code=503, detail="Memory not initialized")

        history = await memory.get_history(session_id)
        return {"history": history}

    @router.post("/memory/search", response_model=MemorySearchResponse)
    async def search_memory(request: MemorySearchRequest):
        """Search long-term memory."""
        if not memory:
            raise HTTPException(status_code=503, detail="Memory not initialized")

        results = await memory.search_memory(request.query, k=request.k)
        return MemorySearchResponse(results=results)

    @router.post("/memory/ingest", response_model=IngestResponse)
    async def ingest_document(request: IngestRequest):
        """Ingest a document into memory."""
        if not memory:
            raise HTTPException(status_code=503, detail="Memory not initialized")

        try:
            await memory.store_memory(request.text, request.metadata)
            return IngestResponse(
                ids=["memory_stored"],
                message="Document ingested successfully",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/memory/{session_id}")
    async def clear_memory(session_id: str):
        """Clear session memory."""
        if not memory:
            raise HTTPException(status_code=503, detail="Memory not initialized")

        await memory.clear_session(session_id)
        return {"message": "Memory cleared"}

    @router.get("/tools")
    async def list_tools():
        """List available tools."""
        # Use the registry passed to create_api_router, or get from agent
        nonlocal _tool_registry
        if _tool_registry is None and agent and hasattr(agent, 'tool_registry'):
            _tool_registry = agent.tool_registry

        if _tool_registry is None:
            return {"tools": [], "error": "No tool registry available"}

        tools = _tool_registry.get_all()
        return {
            "tools": [
                {
                    "name": name,
                    "description": tool.description,
                    "category": tool.category,
                }
                for name, tool in tools.items()
            ]
        }

    @router.get("/settings")
    async def get_settings():
        """Get current settings."""
        from privateclaw.config.settings import get_settings
        settings = get_settings()
        return {
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "llm_temperature": settings.llm_temperature,
            "memory_short_term_limit": settings.memory_short_term_limit,
            "memory_long_term_enabled": settings.memory_long_term_enabled,
        }

    @router.put("/settings")
    async def update_settings(settings_update: dict):
        """Update settings (in-memory only)."""
        # For now, just return success
        # In production, this would update the actual settings
        return {"message": "Settings updated", "settings": settings_update}

    @router.post("/feedback")
    async def provide_feedback(feedback: dict):
        """Provide feedback for self-improvement."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        session_id = feedback.get("session_id", "default")
        user_id = feedback.get("user_id", "default")

        await agent.provide_feedback(session_id, user_id, feedback)
        return {"message": "Feedback processed"}

    @router.get("/user/profile/{user_id}")
    async def get_user_profile(user_id: str):
        """Get user profile."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        profile = agent.get_user_profile(user_id)
        return {"profile": profile}

    @router.get("/improvement/stats")
    async def get_improvement_stats():
        """Get self-improvement statistics."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        stats = agent.get_improvement_stats()
        return {"stats": stats}

    @router.post("/memory/consolidate")
    async def trigger_consolidation(session_id: str = "default", user_id: str = "default"):
        """Manually trigger memory consolidation for a session."""
        if not memory:
            raise HTTPException(status_code=503, detail="Memory not initialized")

        summary = await memory.consolidation.force_consolidation(session_id, user_id)
        if summary:
            return {"message": "Consolidation completed", "summary": summary.model_dump()}
        return {"message": "No messages to consolidate"}

    @router.get("/memory/consolidation/stats")
    async def get_consolidation_stats():
        """Get memory consolidation statistics."""
        if not memory:
            raise HTTPException(status_code=503, detail="Memory not initialized")

        stats = memory.consolidation.get_stats()
        return {"stats": stats}

    @router.get("/skills/stats")
    async def get_skill_stats():
        """Get skill learning statistics."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        stats = agent.skill_learning.get_stats()
        return {"stats": stats}

    @router.get("/skills/export")
    async def export_skills():
        """Export all learned skills."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        skills = agent.skill_learning.export_skills()
        return {"skills": skills}

    @router.post("/skills/import")
    async def import_skills(skills_data: List[Dict[str, Any]]):
        """Import skills."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        imported = await agent.skill_learning.import_skills(skills_data)
        return {"message": f"Imported {imported} skills"}

    @router.get("/prompts/auto-update/history")
    async def get_prompt_update_history():
        """Get prompt auto-update history."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        history = agent.prompt_updater.get_update_history()
        return {"history": history}

    @router.get("/prompts/auto-update/stats")
    async def get_prompt_update_stats():
        """Get prompt auto-update statistics."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        stats = agent.prompt_updater.get_stats()
        return {"stats": stats}

    @router.post("/prompts/auto-update/rollback")
    async def rollback_prompt_update():
        """Rollback the last prompt update."""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        success = await agent.prompt_updater.rollback_last_update()
        if success:
            return {"message": "Rollback successful"}
        return {"message": "No updates to rollback"}

    # Tool Skills API (OpenClaw style)
    @router.get("/skills/tools/stats")
    async def get_tool_skills_stats():
        """Get tool skill system statistics."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        stats = agent.tool_skills.get_skill_stats()
        return {"stats": stats}

    @router.get("/skills/tools/suggestions")
    async def get_skill_suggestions():
        """Get suggestions for new skills based on behavior patterns."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        suggestions = agent.tool_skills.get_suggestions()
        return {"suggestions": suggestions}

    @router.get("/skills/tools/list")
    async def list_tool_skills():
        """List all tool skills."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        skills = agent.tool_skills.get_all_skills()
        return {
            "skills": [
                {
                    "id": s.skill_id,
                    "name": s.name,
                    "type": s.skill_type if isinstance(s.skill_type, str) else s.skill_type.value,
                    "description": s.description,
                    "confidence": s.confidence,
                    "usage_count": s.usage_count,
                    "source": s.source,
                    "tags": s.tags,
                }
                for s in skills
            ]
        }

    @router.post("/skills/tools/create")
    async def create_tool_skill(skill_data: dict):
        """Create a new tool skill."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        name = skill_data.get("name")
        description = skill_data.get("description", "")
        code = skill_data.get("code", "")
        tags = skill_data.get("tags", [])
        triggers = skill_data.get("triggers", [])

        if not name:
            raise HTTPException(status_code=400, detail="Name is required")

        skill_id = agent.tool_skills.create_skill(
            name=name,
            description=description,
            code=code,
            tags=tags,
            triggers=triggers,
        )

        # Reload skills
        agent._load_tool_skills()
        return {"message": f"Skill '{name}' created", "skill_id": skill_id}

    @router.post("/skills/tools/download")
    async def download_tool_skill(url_data: dict):
        """Download a tool skill from URL."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        url = url_data.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        skill_id = agent.tool_skills.download_skill(url)
        if skill_id:
            # Reload skills
            agent._load_tool_skills()
            return {"message": "Skill downloaded", "skill_id": skill_id}
        return {"message": "Failed to download skill"}

    @router.post("/skills/tools/reload")
    async def reload_tool_skills():
        """Reload all tool skills from md files."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        # Reload from md files
        agent.tool_skills.reload_from_files()
        agent._load_tool_skills()
        return {"message": "Tool skills reloaded from files"}

    @router.get("/skills/tools/export")
    async def export_tool_skills():
        """Export all tool skills."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        skills = agent.tool_skills.export_skills()
        return {"skills": skills}

    @router.post("/skills/tools/import")
    async def import_tool_skills(data: dict):
        """Import tool skills."""
        if not agent or not hasattr(agent, 'tool_skills'):
            raise HTTPException(status_code=503, detail="Agent not initialized")

        skills_data = data.get("skills", [])
        imported = agent.tool_skills.import_skills(skills_data)

        # Reload skills
        agent._load_tool_skills()
        return {"message": f"Imported {imported} skills"}

    # Channels Configuration API
    @router.get("/channels/config")
    async def get_channels_config():
        """Get all channels configuration."""
        from privateclaw.config.settings import get_settings
        settings = get_settings()

        config = {
            "web": {
                "enabled": settings.channel_web_enabled,
                "host": settings.channel_web_host,
                "port": settings.channel_web_port,
            },
            "qq": {
                "enabled": settings.channel_qq_enabled,
                "bot_id": settings.channel_qq_bot_id or "",
                "bot_secret": settings.channel_qq_bot_secret or "",
                "sandbox": settings.channel_qq_sandbox,
            },
            "feishu": {
                "enabled": settings.channel_feishu_enabled,
                "app_id": settings.channel_feishu_app_id or "",
                "app_secret": settings.channel_feishu_app_secret or "",
                "verification_token": settings.channel_feishu_verification_token or "",
                "encrypt_key": settings.channel_feishu_encrypt_key or "",
            },
            "telegram": {
                "enabled": settings.channel_telegram_enabled,
                "token": settings.channel_telegram_token or "",
            },
            "discord": {
                "enabled": settings.channel_discord_enabled,
                "token": settings.channel_discord_token or "",
            },
            "slack": {
                "enabled": settings.channel_slack_enabled,
                "token": settings.channel_slack_token or "",
                "app_token": settings.channel_slack_app_token or "",
            },
        }

        return {"config": config}

    @router.post("/channels/config")
    async def update_channel_config(data: dict):
        """Update channel configuration."""
        from privateclaw.config.settings import get_settings
        import os

        channel = data.get("channel")
        config = data.get("config", {})

        if not channel:
            raise HTTPException(status_code=400, detail="Channel name required")

        # Map channel config to env vars
        env_mapping = {
            "qq": {
                "enabled": "CHANNEL_QQ_ENABLED",
                "bot_id": "CHANNEL_QQ_BOT_ID",
                "bot_secret": "CHANNEL_QQ_BOT_SECRET",
                "sandbox": "CHANNEL_QQ_SANDBOX",
            },
            "feishu": {
                "enabled": "CHANNEL_FEISHU_ENABLED",
                "app_id": "CHANNEL_FEISHU_APP_ID",
                "app_secret": "CHANNEL_FEISHU_APP_SECRET",
                "verification_token": "CHANNEL_FEISHU_VERIFICATION_TOKEN",
                "encrypt_key": "CHANNEL_FEISHU_ENCRYPT_KEY",
            },
            "telegram": {
                "enabled": "CHANNEL_TELEGRAM_ENABLED",
                "token": "CHANNEL_TELEGRAM_TOKEN",
            },
            "discord": {
                "enabled": "CHANNEL_DISCORD_ENABLED",
                "token": "CHANNEL_DISCORD_TOKEN",
            },
            "slack": {
                "enabled": "CHANNEL_SLACK_ENABLED",
                "token": "CHANNEL_SLACK_TOKEN",
                "app_token": "CHANNEL_SLACK_APP_TOKEN",
            },
        }

        if channel not in env_mapping:
            raise HTTPException(status_code=400, detail=f"Unknown channel: {channel}")

        # Update .env file
        env_file = Path(".env")
        env_lines = []
        if env_file.exists():
            env_lines = env_file.read_text(encoding="utf-8").splitlines()

        # Update or add env vars
        mapping = env_mapping[channel]
        for config_key, env_key in mapping.items():
            value = config.get(config_key, "")
            if isinstance(value, bool):
                value = str(value).lower()

            # Find and update existing line
            found = False
            for i, line in enumerate(env_lines):
                if line.startswith(f"{env_key}="):
                    env_lines[i] = f"{env_key}={value}"
                    found = True
                    break

            if not found:
                env_lines.append(f"{env_key}={value}")

        # Write back to .env
        env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

        return {"message": f"Channel '{channel}' configuration updated. Restart server to apply changes."}

    return router
