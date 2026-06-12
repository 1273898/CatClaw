"""LLM factory for PrivateClaw."""

from typing import Optional
from langchain_core.language_models import BaseChatModel
from privateclaw.core.llm.config import LLMConfig
from privateclaw.core.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def create_model(self, config: LLMConfig) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            "streaming": config.streaming,
            "timeout": config.timeout,
        }
        if config.api_key:
            kwargs["api_key"] = config.api_key
        if config.api_base:
            kwargs["base_url"] = config.api_base
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens

        return ChatOpenAI(**kwargs)

    def get_supported_models(self) -> list[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ]

    def validate_config(self, config: LLMConfig) -> bool:
        if not config.api_key:
            return False
        return config.model in self.get_supported_models()


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM provider (OpenAI-compatible API)."""

    def create_model(self, config: LLMConfig) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            "streaming": config.streaming,
            "timeout": config.timeout,
            "api_key": config.api_key or "dummy",  # DeepSeek requires an API key
            "base_url": config.api_base or "https://api.deepseek.com",
        }
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens

        return ChatOpenAI(**kwargs)

    def get_supported_models(self) -> list[str]:
        return [
            "deepseek-v4-flash",
            "deepseek-v4-pro",
            "deepseek-chat",
            "deepseek-reasoner",
        ]

    def validate_config(self, config: LLMConfig) -> bool:
        if not config.api_key:
            return False
        return config.model in self.get_supported_models()


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""

    def create_model(self, config: LLMConfig) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic

        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            "streaming": config.streaming,
            "timeout": config.timeout,
        }
        if config.api_key:
            kwargs["api_key"] = config.api_key
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens

        return ChatAnthropic(**kwargs)

    def get_supported_models(self) -> list[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def validate_config(self, config: LLMConfig) -> bool:
        if not config.api_key:
            return False
        return config.model in self.get_supported_models()


class OllamaProvider(LLMProvider):
    """Ollama LLM provider (local models)."""

    def create_model(self, config: LLMConfig) -> BaseChatModel:
        from langchain_community.llms import Ollama

        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
        }
        if config.api_base:
            kwargs["base_url"] = config.api_base

        return Ollama(**kwargs)

    def get_supported_models(self) -> list[str]:
        return [
            "llama3.1",
            "llama3",
            "llama2",
            "mistral",
            "mixtral",
            "codellama",
            "phi3",
            "gemma2",
        ]

    def validate_config(self, config: LLMConfig) -> bool:
        return True  # Ollama doesn't require API key


class LLMFactory:
    """Factory for creating LLM instances."""

    _providers: dict[str, LLMProvider] = {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "ollama": OllamaProvider(),
        "deepseek": DeepSeekProvider(),
    }

    @classmethod
    def register_provider(cls, name: str, provider: LLMProvider) -> None:
        """Register a new LLM provider."""
        cls._providers[name] = provider

    @classmethod
    def get_provider(cls, name: str) -> LLMProvider:
        """Get an LLM provider by name."""
        if name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {name}. Available: {list(cls._providers.keys())}"
            )
        return cls._providers[name]

    @classmethod
    def create(cls, config: LLMConfig) -> BaseChatModel:
        """Create an LLM instance from config."""
        provider = cls.get_provider(config.provider)
        return provider.create_model(config)

    @classmethod
    def create_from_settings(cls, settings) -> BaseChatModel:
        """Create an LLM instance from settings."""
        config = LLMConfig(
            provider=settings.llm_provider,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
        )
        return cls.create(config)

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers."""
        return list(cls._providers.keys())

    @classmethod
    def list_models(cls, provider_name: str) -> list[str]:
        """List all models for a provider."""
        provider = cls.get_provider(provider_name)
        return provider.get_supported_models()
