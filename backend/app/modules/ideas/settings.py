from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class IdeaSettings(BaseSettings):
    """Server-only participation limits, loaded from environment or backend/.env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    ideas_daily_limit: int = Field(default=10, ge=1, le=1000)
    ideas_suggestions_daily_limit: int = Field(default=20, ge=1, le=1000)
    ideas_reports_daily_limit: int = Field(default=10, ge=1, le=1000)
