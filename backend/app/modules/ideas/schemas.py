from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.modules.policies.schemas import PolicyInput


class IdeaInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=5000)
    content: PolicyInput = Field(default_factory=PolicyInput)
    beneficiaries: str = Field(default="", max_length=10000)
    adversely_affected: str = Field(default="", max_length=10000)
    risks: str = Field(default="", max_length=10000)
    assisted_fields: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("assisted_fields")
    @classmethod
    def assisted_names(cls, values):
        allowed = set(PolicyInput.model_fields) | {"beneficiaries", "adversely_affected", "risks"}
        if not set(values) <= allowed:
            raise ValueError("Campo assistido desconhecido.")
        return sorted(set(values))


class IdeaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, min_length=1, max_length=5000)
    content: PolicyInput | None = None
    beneficiaries: str | None = Field(default=None, max_length=10000)
    adversely_affected: str | None = Field(default=None, max_length=10000)
    risks: str | None = Field(default=None, max_length=10000)
    assisted_fields: list[str] | None = Field(default=None, max_length=30)


class SuggestionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    url: HttpUrl = Field(max_length=2083)
    note: str = Field(min_length=1, max_length=2000)

    @field_validator("url")
    @classmethod
    def no_credentials(cls, value):
        if value.username or value.password:
            raise ValueError("Não inclua credenciais no link.")
        return value


class ReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str = Field(min_length=1, max_length=2000)


class ResolutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    action: Literal["DISMISS", "ARCHIVE"]
    note: str = Field(min_length=1, max_length=2000)


class SuggestionResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["ACCEPT", "DISMISS"]
