from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

SourceType = Literal[
    "OFFICIAL",
    "LEGISLATION",
    "SCIENTIFIC_STUDY",
    "TECHNICAL_REPORT",
    "INSTITUTIONAL_REPORT",
    "JOURNALISM",
    "OTHER",
]


class SourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=300)
    institution: str = Field(min_length=1, max_length=200)
    url: HttpUrl = Field(max_length=2083)
    source_type: SourceType = "OTHER"
    publication_date: date | None = None
    accessed_at: date
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("url")
    @classmethod
    def no_credentials(cls, url):
        if url.username or url.password:
            raise ValueError("Source URLs cannot include credentials.")
        return url


class SourceResponse(BaseModel):
    collection_code: str | None = Field(default=None, exclude_if=lambda value: value is None)
    is_example: bool = False
    usage_count: int = 0
    license: str | None = None
    license_url: str | None = None
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    institution: str
    url: str
    source_type: str
    publication_date: date | None
    accessed_at: date
    description: str | None


class SourceEnvelope(BaseModel):
    data: SourceResponse
