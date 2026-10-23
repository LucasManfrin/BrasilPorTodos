from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GuidanceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    gemini_api_key: SecretStr | None = None
    guidance_ai_enabled: bool = False
    guidance_model: str = Field(
        default="gemini-3.5-flash-lite", pattern=r"^gemini-[a-z0-9.-]{1,80}$"
    )
    guidance_daily_limit: int = Field(default=20, ge=1, le=500)
    guidance_log_retention_days: int = Field(default=7, ge=1, le=30)
    guidance_timeout_seconds: int = Field(default=30, ge=2, le=45)

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def empty_key(cls, value):
        return None if value == "" else value

    @property
    def available(self) -> bool:
        return self.guidance_ai_enabled and bool(self.gemini_api_key)


@lru_cache
def get_guidance_settings() -> GuidanceSettings:
    return GuidanceSettings()
