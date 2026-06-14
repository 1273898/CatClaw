"""Configuration settings for PrivateClaw."""

import warnings
import secrets
from typing import Optional, List
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()


class Settings(BaseSettings):
    """Main settings for PrivateClaw."""

    # Application
    app_name: str = Field(default="CatClaw", description="Application name")
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

    # CORS Configuration (not from env, hardcoded for security)
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000", "http://localhost:5173", "http://127.0.0.1:8000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_allow_methods: List[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")

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

    # QQ Configuration
    channel_qq_enabled: bool = Field(default=False, description="Enable QQ Bot")
    channel_qq_bot_id: Optional[str] = Field(default=None, description="QQ AppID")
    channel_qq_bot_secret: Optional[str] = Field(default=None, description="QQ AppSecret")
    channel_qq_sandbox: bool = Field(default=True, description="QQ Sandbox mode")

    # Feishu Configuration
    channel_feishu_enabled: bool = Field(default=False, description="Enable Feishu Bot")
    channel_feishu_app_id: Optional[str] = Field(default=None, description="Feishu App ID")
    channel_feishu_app_secret: Optional[str] = Field(default=None, description="Feishu App Secret")
    channel_feishu_verification_token: Optional[str] = Field(default=None, description="Feishu Verification Token")
    channel_feishu_encrypt_key: Optional[str] = Field(default=None, description="Feishu Encrypt Key")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode='after')
    def check_secret_key(self) -> 'Settings':
        """Check if secret key is still the default value."""
        if self.gateway_secret_key == "change-me-in-production":
            warnings.warn(
                "⚠️  WARNING: Using default secret key! "
                "Please set GATEWAY_SECRET_KEY in your .env file. "
                "Generating a temporary key for this session.",
                UserWarning,
                stacklevel=2
            )
            # Generate a temporary key
            self.gateway_secret_key = secrets.token_urlsafe(32)
        return self

    @field_validator("data_dir", "memory_vector_store_path")
    @classmethod
    def ensure_relative_path(cls, v: str) -> str:
        """Ensure paths are relative and safe."""
        path = Path(v)
        # Convert to absolute and check it's within project root
        abs_path = (PROJECT_ROOT / path).resolve()
        if not str(abs_path).startswith(str(PROJECT_ROOT)):
            raise ValueError(f"Path {v} is outside project directory")
        return v

    def get_data_path(self) -> Path:
        """Get absolute data directory path within project."""
        return (PROJECT_ROOT / self.data_dir).resolve()

    def get_vector_store_path(self) -> Path:
        """Get absolute vector store path within project."""
        return (PROJECT_ROOT / self.memory_vector_store_path).resolve()

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists."""
        data_path = self.get_data_path()
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
