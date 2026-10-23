from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.modules.sources.schemas import SourceResponse

Category = Literal[
    "ECONOMY",
    "TAXATION",
    "EDUCATION",
    "HEALTH",
    "SECURITY",
    "PENSION",
    "INFRASTRUCTURE",
    "SOCIAL_ASSISTANCE",
    "PUBLIC_ADMINISTRATION",
    "SCIENCE_TECHNOLOGY",
    "HOUSING",
    "ENERGY",
    "ENVIRONMENT",
    "OTHER",
]
FiscalStatus = Literal["ESTIMATED", "NOT_ESTIMATED", "NOT_APPLICABLE"]
ImpactKind = Literal["NEW_EXPENSE", "EXPENSE_REDUCTION", "NEW_REVENUE", "REVENUE_REDUCTION"]
FundingKind = Literal[
    "SPENDING_CUT",
    "NEW_REVENUE",
    "TAX_INCREASE",
    "DEBT",
    "PROGRAM_REPLACEMENT",
    "REVENUE_GROWTH",
    "UNFUNDED",
    "OTHER",
]


def strict_money(value):
    if not isinstance(value, (str, Decimal)):
        raise ValueError("Money must be a decimal string.")
    return value


Money = Annotated[
    Decimal,
    BeforeValidator(strict_money),
    Field(ge=0, max_digits=18, decimal_places=2, allow_inf_nan=False),
]


FiscalScope = Literal[
    "CENTRAL_GOVERNMENT", "GENERAL_GOVERNMENT", "STATE", "MUNICIPAL", "OTHER", "UNSPECIFIED"
]
AccountingBasis = Literal["CASH", "ACCRUAL", "UNSPECIFIED"]
PriceBasis = Literal["NOMINAL", "CONSTANT", "UNSPECIFIED"]
FiscalComponent = Literal["PRIMARY", "INTEREST", "UNSPECIFIED"]
PeriodBasis = Literal["FULL_YEAR", "PARTIAL_YEAR", "UNSPECIFIED"]


class FiscalMetadata(BaseModel):
    fiscal_scope: FiscalScope = "UNSPECIFIED"
    accounting_basis: AccountingBasis = "UNSPECIFIED"
    price_basis: PriceBasis = "UNSPECIFIED"
    price_base_year: int | None = Field(default=None, ge=1900, le=2200)
    component: FiscalComponent = "UNSPECIFIED"
    period_basis: PeriodBasis = "UNSPECIFIED"

    @model_validator(mode="after")
    def validate_price_reference(self):
        if self.price_basis == "CONSTANT" and self.price_base_year is None:
            raise ValueError("Valores a preços constantes exigem o ano-base de preços.")
        if self.price_basis != "CONSTANT" and self.price_base_year is not None:
            raise ValueError("Ano-base de preços só se aplica a preços constantes.")
        return self


class ImpactInput(FiscalMetadata):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    year: int = Field(ge=1900, le=2200)
    impact_type: ImpactKind
    amount: Money
    description: str = Field(min_length=1, max_length=5000)


class FundingInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    funding_type: FundingKind
    amount: Money | None = None
    year: int | None = Field(default=None, ge=1900, le=2200)
    description: str = Field(min_length=1, max_length=5000)


class EvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_id: UUID
    usage_description: str = Field(min_length=1, max_length=5000)


class ProposalDetails(BaseModel):
    level: Literal["COMPLETE"] | None = None
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    beneficiaries: str = Field(default="", max_length=10000)
    adversely_affected: str = Field(default="", max_length=10000)
    risks: str = Field(default="", max_length=10000)
    assisted_fields: list[str] = Field(default_factory=list, max_length=30)
    idea_id: UUID | None = None
    origin_attribution: dict | None = None


class PolicyInput(BaseModel):
    proposal_details: ProposalDetails | None = None
    refresh_baseline: bool = False
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(default="", max_length=200)
    summary: str = Field(default="", max_length=5000)
    problem: str = Field(default="", max_length=20000)
    proposal: str = Field(default="", max_length=20000)
    category: Category = "OTHER"
    implementation_start: int | None = Field(default=None, ge=1900, le=2200)
    implementation_end: int | None = Field(default=None, ge=1900, le=2200)
    financial_impact_status: FiscalStatus = "NOT_ESTIMATED"
    impact_justification: str | None = Field(default=None, max_length=5000)
    change_summary: str | None = Field(default=None, max_length=5000)
    impacts: list[ImpactInput] = Field(default_factory=list, max_length=1000)
    fundings: list[FundingInput] = Field(default_factory=list, max_length=300)
    sources: list[EvidenceInput] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_collections(self):
        if len({source.source_id for source in self.sources}) != len(self.sources):
            raise ValueError("Source references cannot be repeated.")
        if (
            self.implementation_start is not None
            and self.implementation_end is not None
            and self.implementation_end < self.implementation_start
        ):
            raise ValueError("Implementation period is invalid.")
        return self


class PolicyUpdate(PolicyInput):
    # PATCH reuses validation and only writes fields explicitly supplied.
    pass


class ImpactResponse(FiscalMetadata):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    year: int
    impact_type: str
    amount: Decimal
    description: str


class FundingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    funding_type: str
    amount: Decimal | None
    year: int | None
    description: str


class EvidenceResponse(BaseModel):
    source: SourceResponse
    usage_description: str


class VersionResponse(BaseModel):
    proposal_details: ProposalDetails | None = None
    baseline_snapshot: dict | None = None
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    version_number: int
    status: str
    title: str
    summary: str
    problem: str
    proposal: str
    category: str
    implementation_start: int | None
    implementation_end: int | None
    financial_impact_status: str
    impact_justification: str | None
    change_summary: str | None
    created_at: datetime
    published_at: datetime | None
    impacts: list[ImpactResponse]
    fundings: list[FundingResponse]
    sources: list[EvidenceResponse]


class SolidityResponse(BaseModel):
    method: Literal["DOC_COMPLETENESS1"] = "DOC_COMPLETENESS1"
    level: Literal["COMPLETE", "LEGACY"]
    score: int | None
    max_score: int = 3
    has_sources: bool
    funding_defined: bool
    reviewed: bool = False
    review_status: Literal["NOT_ASSESSED"] = "NOT_ASSESSED"


class PolicyResponse(BaseModel):
    solidity: SolidityResponse | None = None
    is_example: bool = False
    id: UUID
    slug: str
    status: str
    author: dict[str, str]
    archive_reason: str | None
    version: VersionResponse


class PolicyEnvelope(BaseModel):
    data: PolicyResponse
