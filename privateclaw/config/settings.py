"""Configuration settings for PrivateClaw."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Main settings for PrivateClaw."""

    # Application
    app_name: str = Field(default="PrivateClaw", description="Application name")
    data_dir: str = Field(default="./data", description="Data directory")
    log_level: str = Field(default="INFO", description="Log level")

    # LLM Configuration
    llm_provider: str = Field(default="deepseek", description="LLM provider")
    llm_model: str = Field(default="deepseek-v4-flash", description="Model name")
    llm_temperature: float = Field(default=0.7, description="Temperature")
    llm_max_tokens: Optional[int] = Field(default=None, description="Max tokens")
    llm_api_key: Optional[str] = Field(default=None, description="API key")
    llm_api_base: Optional[str] = Field(default=None, description="API base URL")

    # Memory Configuration
    memory_short_term_limit: int = Field(default=50, description="Short-term memory limit")
    memory_long_term_enabled: bool = Field(default=True, description="Enable long-term memory")
    memory_vector_store: str = Field(default="chroma", description="Vector store type")
    memory_vector_store_path: str = Field(default="./data/chroma", description="Vector store path")
    memory_embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")

    # Gateway Configuration
    gateway_host: str = Field(default="0.0.0.0", description="Gateway host")
    gateway_port: int = Field(default=18789, description="Gateway port")
    gateway_debug: bool = Field(default=False, description="Debug mode")
    gateway_secret_key: str = Field(default="change-me-in-production", description="Secret key")

    # Channel Configuration
    channel_web_enabled: bool = Field(default=True, description="Enable Web channel")
    channel_web_host: str = Field(default="0.0.0.0", description="Web host")
    channel_web_port: int = Field(default=8000, description="Web port")
    channel_cli_enabled: bool = Field(default=True, description="Enable CLI channel")
    channel_telegram_enabled: bool = Field(default=False, description="Enable Telegram")
    channel_telegram_token: Optional[str] = Field(default=None, description="Telegram token")
    channel_discord_enabled: bool = Field(default=False, description="Enable Discord")
    channel_discord_token: Optional[str] = Field(default=None, description="Discord token")
    channel_slack_enabled: bool = Field(default=False, description="Enable Slack")
    channel_slack_token: Optional[str] = Field(default=None, description="Slack token")
    channel_slack_app_token: Optional[str] = Field(default=None, description="Slack app token")
    channel_wechat_enabled: bool = Field(default=False, description="Enable WeChat")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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
