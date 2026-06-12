"""Configuration settings for PrivateClaw."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class LLMSettings(BaseSettings):
    """LLM configuration."""

    provider: str = Field(default="deepseek", description="LLM provider (openai, anthropic, ollama, deepseek)")
    model: str = Field(default="deepseek-v4-flash", description="Model name")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens for generation")
    api_key: Optional[str] = Field(default=None, description="API key")
    api_base: Optional[str] = Field(default=None, description="API base URL")

    model_config = SettingsConfigDict(env_prefix="LLM_")


class MemorySettings(BaseSettings):
    """Memory configuration."""

    short_term_limit: int = Field(default=50, description="Max messages in short-term memory")
    long_term_enabled: bool = Field(default=True, description="Enable long-term memory")
    vector_store: str = Field(default="chroma", description="Vector store type")
    vector_store_path: str = Field(default="./data/chroma", description="Vector store path")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")

    model_config = SettingsConfigDict(env_prefix="MEMORY_")


class ChannelSettings(BaseSettings):
    """Channel configuration."""

    # Web
    web_enabled: bool = Field(default=True, description="Enable Web channel")
    web_host: str = Field(default="0.0.0.0", description="Web host")
    web_port: int = Field(default=8000, description="Web port")

    # CLI
    cli_enabled: bool = Field(default=True, description="Enable CLI channel")

    # Telegram
    telegram_enabled: bool = Field(default=False, description="Enable Telegram channel")
    telegram_token: Optional[str] = Field(default=None, description="Telegram bot token")

    # Discord
    discord_enabled: bool = Field(default=False, description="Enable Discord channel")
    discord_token: Optional[str] = Field(default=None, description="Discord bot token")

    # Slack
    slack_enabled: bool = Field(default=False, description="Enable Slack channel")
    slack_token: Optional[str] = Field(default=None, description="Slack bot token")
    slack_app_token: Optional[str] = Field(default=None, description="Slack app token")

    # WeChat
    wechat_enabled: bool = Field(default=False, description="Enable WeChat channel")

    model_config = SettingsConfigDict(env_prefix="CHANNEL_")


class GatewaySettings(BaseSettings):
    """Gateway configuration."""

    host: str = Field(default="0.0.0.0", description="Gateway host")
    port: int = Field(default=18789, description="Gateway port")
    debug: bool = Field(default=False, description="Debug mode")
    secret_key: str = Field(default="change-me-in-production", description="Secret key for auth")

    model_config = SettingsConfigDict(env_prefix="GATEWAY_")


class Settings(BaseSettings):
    """Main settings for PrivateClaw."""

    # Application
    app_name: str = Field(default="PrivateClaw", description="Application name")
    data_dir: str = Field(default="./data", description="Data directory")
    log_level: str = Field(default="INFO", description="Log level")

    # Sub-settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    channels: ChannelSettings = Field(default_factory=ChannelSettings)
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)

    model_config = SettingsConfigDict(
        env_prefix="PRIVATECLAW_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists."""
        data_path = Path(self.data_dir)
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
