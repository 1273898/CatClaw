"""API routes for PrivateClaw web interface."""

from typing import Optional
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
) -> APIRouter:
    """Create API router.

    Args:
        agent: PrivateClaw agent instance
        memory: Memory manager instance
        session_manager: Session manager instance
        ws_manager: WebSocket manager instance

    Returns:
        APIRouter instance
    """
    router = APIRouter()

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
            response = await agent.run(request.message, request.session_id)
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
            async for chunk in agent.stream(request.message, request.session_id):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )

    @router.get("/sessions")
    async def list_sessions():
        """List all sessions."""
        if not session_manager:
            return {"sessions": []}

        sessions = await session_manager.list_sessions()
        return {"sessions": sessions}

    @router.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get session details."""
        if not session_manager:
            raise HTTPException(status_code=404, detail="Session manager not initialized")

        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return session.to_dict()

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
        from privateclaw.core.tools.registry import ToolRegistry
        tools = ToolRegistry.get_all()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                }
                for tool in tools.values()
            ]
        }

    return router
