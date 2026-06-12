"""API endpoints for managing prompt MD documents."""

from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


class PromptDocument(BaseModel):
    """Prompt document model."""
    name: str = Field(description="Document name")
    filename: str = Field(description="Filename")
    content: str = Field(description="Document content")
    path: str = Field(description="File path")


class PromptUpdate(BaseModel):
    """Prompt update model."""
    content: str = Field(description="New content")


def create_prompts_router(prompts_dir: str = "prompts") -> APIRouter:
    """Create API router for prompt documents."""
    router = APIRouter(prefix="/prompts", tags=["prompts"])

    prompts_path = Path(prompts_dir)

    @router.get("/")
    async def list_prompts():
        """List all prompt documents."""
        if not prompts_path.exists():
            return {"documents": []}

        documents = []
        for md_file in prompts_path.glob("*.md"):
            stat = md_file.stat()
            documents.append({
                "name": md_file.stem,
                "filename": md_file.name,
                "path": str(md_file),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })

        return {"documents": documents}

    @router.get("/{name}")
    async def get_prompt(name: str):
        """Get a prompt document by name."""
        file_path = prompts_path / f"{name}.md"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {name}")

        content = file_path.read_text(encoding="utf-8")

        return {
            "name": name,
            "filename": file_path.name,
            "content": content,
            "path": str(file_path),
        }

    @router.put("/{name}")
    async def update_prompt(name: str, update: PromptUpdate):
        """Update a prompt document."""
        file_path = prompts_path / f"{name}.md"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {name}")

        try:
            # Create backup
            backup_path = file_path.with_suffix(".md.bak")
            if file_path.exists():
                backup_path.write_text(
                    file_path.read_text(encoding="utf-8"),
                    encoding="utf-8"
                )

            # Write new content
            file_path.write_text(update.content, encoding="utf-8")

            return {
                "success": True,
                "name": name,
                "message": "Document updated successfully",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{name}/restore")
    async def restore_prompt(name: str):
        """Restore a prompt document from backup."""
        file_path = prompts_path / f"{name}.md"
        backup_path = file_path.with_suffix(".md.bak")

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="No backup found")

        try:
            content = backup_path.read_text(encoding="utf-8")
            file_path.write_text(content, encoding="utf-8")

            return {
                "success": True,
                "name": name,
                "message": "Document restored from backup",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
