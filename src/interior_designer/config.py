"""Configuration management using pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        case_sensitive=False,
    )

    # Claude Code settings
    claude_model: str = Field(
        default="sonnet",
        description="Model to use with Claude Code (e.g., 'sonnet', 'opus', 'haiku')",
    )

    # OpenRouter settings (for image generation)
    openrouter_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenRouter API key",
    )
    openrouter_image_model: str = Field(
        default="sourceful/riverflow-v2-fast-preview",
        description="OpenRouter model for image generation",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )

    # Output settings
    output_dir: Path = Field(
        default=Path("./output"),
        description="Directory for output files",
    )

    def ensure_output_dir(self) -> Path:
        """Ensure output directory exists and return it."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
