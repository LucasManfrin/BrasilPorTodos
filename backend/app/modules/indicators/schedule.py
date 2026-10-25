"""Calendar schedule; no external requests, writes, or inferred observations."""

from datetime import UTC, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectionSchedule(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    collection_schedule_enabled: bool = False
    collection_daily_at: str = Field(default="00:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    collection_timezone: str = "America/Sao_Paulo"
    collection_retry_minutes: int = Field(default=60, ge=60, le=1440)
    collection_username: str | None = Field(default=None, max_length=50)

    @field_validator("collection_timezone")
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Fuso IANA inválido para a coleta.") from error
        return value


@lru_cache
def get_schedule() -> CollectionSchedule:
    return CollectionSchedule()


def next_attempt_at(
    now: datetime,
    last_started: datetime | None,
    last_status: str | None,
    settings: CollectionSchedule,
) -> datetime:
    if now.utcoffset() is None or (last_started is not None and last_started.utcoffset() is None):
        raise ValueError("Agendamento exige timestamps com fuso horário.")
    now = now.astimezone(UTC)
    zone = ZoneInfo(settings.collection_timezone)
    local = now.astimezone(zone)
    hour, minute = map(int, settings.collection_daily_at.split(":"))
    slot = datetime.combine(local.date(), time(hour, minute), zone)
    if slot > local:
        slot -= timedelta(days=1)
    if last_started is None:
        # A stopped computer catches up once when the worker comes back.
        return now
    last_started = last_started.astimezone(UTC)
    minimum = last_started + timedelta(minutes=settings.collection_retry_minutes)
    if last_started < slot.astimezone(UTC) or last_status != "SUCCESS":
        return max(now, minimum)
    tomorrow = slot + timedelta(days=1)
    return max(tomorrow.astimezone(UTC), minimum)


def public_schedule(now: datetime, latest) -> dict:
    settings = get_schedule()
    return {
        "enabled": settings.collection_schedule_enabled,
        "daily_at": settings.collection_daily_at,
        "timezone": settings.collection_timezone,
        "retry_minutes": settings.collection_retry_minutes,
        "next_attempt_at": next_attempt_at(
            now, latest.created_at if latest else None, latest.status if latest else None, settings
        ).isoformat()
        if settings.collection_schedule_enabled
        else None,
    }
