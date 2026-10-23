from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://brasil:brasil_local@localhost:5432/brasil_portodos"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    jwt_secret: SecretStr | None = Field(default=None, min_length=32)
    jwt_issuer: str = "brasil-portodos"
    jwt_audience: str = "brasil-portodos-api"
    jwt_access_minutes: int = Field(default=15, ge=1, le=60)
    refresh_days: int = Field(default=30, ge=1, le=90)
    cookie_secure: bool = True
    environment: str = "production"

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def empty_secret(cls, value):
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
