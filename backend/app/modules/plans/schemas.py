from decimal import Decimal, InvalidOperation, localcontext
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


def scenario_money(value):
    if not isinstance(value, (str, Decimal)):
        raise ValueError("Valores monetários devem ser strings decimais, não float ou bool.")
    try:
        number = Decimal(value)
        if not number.is_finite() or number < 0 or number > Decimal("9999999999999999.99"):
            raise ValueError("Valor monetário fora do limite NUMERIC(18,2).")
        if number.as_tuple().exponent < -2:
            raise ValueError("Valores monetários devem ter no máximo duas casas decimais.")
        with localcontext() as context:
            context.prec = 40
            return number.quantize(Decimal("0.01"))
    except InvalidOperation as error:
        raise ValueError("Valor monetário inválido.") from error


ScenarioMoney = Annotated[Decimal, BeforeValidator(scenario_money)]


class FiscalScenarioYearDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    year: int = Field(strict=True, ge=1900, le=2200)
    net_revenue: ScenarioMoney | None = None
    primary_expenditure: ScenarioMoney | None = None
    justification: str = Field(default="", max_length=5000)
    source_urls: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("source_urls")
    @classmethod
    def valid_urls(cls, values):
        for url in values:
            if len(url) > 4096 or any(c.isspace() or ord(c) < 32 for c in url):
                raise ValueError("Fonte deve ser URL HTTP/HTTPS sem espaços ou controles.")
            try:
                parsed = urlsplit(url)
                valid = (
                    parsed.scheme in {"http", "https"}
                    and bool(parsed.hostname)
                    and parsed.username is None
                    and parsed.password is None
                )
                _ = parsed.port
            except ValueError as error:
                raise ValueError("URL de fonte inválida.") from error
            if not valid:
                raise ValueError("Fonte deve ser URL HTTP/HTTPS, com host e sem credenciais.")
        return values

    @field_serializer("net_revenue", "primary_expenditure")
    def money_strings(self, value):
        return format(value, ".2f") if value is not None else None


class FiscalScenarioDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(default="", max_length=200)
    explanation: str = Field(default="", max_length=10000)
    reference_baseline_id: str = Field(default="", max_length=128)
    years: list[FiscalScenarioYearDraft] = Field(default_factory=list, max_length=30)


class FiscalScenarioConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_input_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class PlanItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy_version_id: UUID
    is_enabled: bool = True


class PlanInput(BaseModel):
    refresh_baseline: bool = False
    fiscal_scenario: FiscalScenarioDraft | None = None
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(default="", max_length=200)
    summary: str = Field(default="", max_length=5000)
    vision: str = Field(default="", max_length=20000)
    start_year: int = Field(ge=1900, le=2200)
    end_year: int = Field(ge=1900, le=2200)
    change_summary: str | None = Field(default=None, max_length=5000)
    policies: list[PlanItemInput] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def validate_period_and_items(self):
        if self.start_year > self.end_year:
            raise ValueError("Invalid period.")
        if len({item.policy_version_id for item in self.policies}) != len(self.policies):
            raise ValueError("Repeated policy version.")
        return self


class PlanUpdate(BaseModel):
    refresh_baseline: bool = False
    fiscal_scenario: FiscalScenarioDraft | None = None
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=5000)
    vision: str | None = Field(default=None, max_length=20000)
    start_year: int | None = Field(default=None, ge=1900, le=2200)
    end_year: int | None = Field(default=None, ge=1900, le=2200)
    change_summary: str | None = Field(default=None, max_length=5000)
    policies: list[PlanItemInput] | None = Field(default=None, max_length=200)

    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, data):
        if isinstance(data, dict) and any(
            value is None and key not in {"change_summary", "fiscal_scenario"}
            for key, value in data.items()
        ):
            raise ValueError("Plan fields cannot be null.")
        return data


class ArchiveInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str = Field(min_length=1, max_length=2000)


PlanState = Literal["DRAFT", "PUBLISHED", "ARCHIVED"]
