from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.modules.policies.schemas import strict_money


class IndicatorInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    code: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    category: Literal["ECONOMY", "FISCAL", "SOCIAL", "PUBLIC_SPENDING"]
    unit: str = Field(min_length=1, max_length=50)
    frequency: Literal["DAILY", "MONTHLY", "QUARTERLY", "YEARLY", "IRREGULAR"]
    scope: str = Field(min_length=1, max_length=10000)
    methodology: str = Field(min_length=1, max_length=20000)
    base_year: int | None = Field(default=None, ge=1900, le=2200)
    is_active: bool = True
    reason: str = Field(min_length=1, max_length=2000)


class ObservationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reference_date: date
    value: Annotated[
        Decimal,
        BeforeValidator(strict_money),
        Field(max_digits=20, decimal_places=6, allow_inf_nan=False),
    ]
    source_id: UUID
    retrieved_at: datetime
    revision_reason: str = Field(min_length=1, max_length=2000)
    provenance: dict[str, str] = Field(max_length=30)

    @field_validator("retrieved_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError("Collection time must include timezone.")
        return value

    @field_validator("provenance")
    @classmethod
    def bounded(cls, value):
        if any(len(k) > 100 or len(v) > 5000 for k, v in value.items()):
            raise ValueError("Provenance text is too long.")
        return value
