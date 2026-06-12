"""LLM provider abstraction for PrivateClaw."""

from typing import Optional
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from privateclaw.core.llm.config import LLMConfig


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    def create_model(self, config: LLMConfig) -> BaseChatModel:
        """Create a chat model instance."""
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """Get list of supported models."""
        pass

    @abstractmethod
    def validate_config(self, config: LLMConfig) -> bool:
        """Validate provider configuration."""
        pass
