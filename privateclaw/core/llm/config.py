"""LLM configuration for PrivateClaw."""

from typing import Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration model."""

    provider: str = Field(description="LLM provider name (openai, anthropic, ollama)")
    model: str = Field(description="Model name")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens for generation")
    api_key: Optional[str] = Field(default=None, description="API key")
    api_base: Optional[str] = Field(default=None, description="API base URL")
    streaming: bool = Field(default=True, description="Enable streaming")
    timeout: int = Field(default=60, description="Request timeout in seconds")

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
