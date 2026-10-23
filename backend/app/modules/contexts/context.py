"""Versioned context contract, independent of HTTP, persistence and fiscal calculation.

Matching a declared review is not authentication, publication permission or proof of
causality. A trusted service must resolve references and authorize the human reviewer.
"""

import hashlib
import json
import re
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

CONTEXT_CONTRACT_VERSION = "1.0.0"
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Code = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{0,79}$")]
IndicatorCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$"
    ),
]
Revision = Annotated[int, Field(ge=1, le=2147483647)]
LIMITATIONS = (
    "Revisão correspondente significa registro declarado, não autenticação ou autorização.",
    "Fonte oficial, associação e revisão não demonstram causalidade por si.",
    "Referências e permissões precisam ser conferidas por serviço confiável antes de publicar.",
    "Hipóteses e consequências não geram coeficientes nem valores para o motor fiscal.",
)


def _utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError("Data de registro deve ter fuso horário explícito.")
    return value.astimezone(UTC)


Timestamp = Annotated[datetime, AfterValidator(_utc)]


def _url(value: str) -> str:
    if any(ord(char) <= 32 or ord(char) == 127 for char in value) or "\\" in value:
        raise ValueError("URL deve ser HTTP/HTTPS sem espaços ou caracteres de controle.")
    try:
        parts = urlsplit(value)
        if parts.port is not None and not 1 <= parts.port <= 65535:
            raise ValueError("Porta inválida.")
        if (
            parts.scheme not in {"https", "http"}
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
        ):
            raise ValueError("URL deve ter host, sem credenciais.")
    except ValueError as error:
        raise ValueError("URL HTTP/HTTPS inválida.") from error
    return value


ReferenceURL = Annotated[
    str, StringConstraints(min_length=1, max_length=2083), AfterValidator(_url)
]


class FrozenRecord(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, revalidate_instances="always"
    )


class SourceReference(FrozenRecord):
    id: UUID
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    institution: ShortText
    url: ReferenceURL
    terms: Text
    terms_url: ReferenceURL
    published_date: date | None = None  # Unknown is explicit, never invented.
    consulted_at: Timestamp


class ObservationAnchor(FrozenRecord):
    observation_id: UUID
    indicator_code: IndicatorCode
    revision: Revision
    source_id: UUID
    value: Annotated[
        str, StringConstraints(pattern=r"^-?[0-9]{1,30}(?:\.[0-9]{1,12})?$", max_length=44)
    ]
    unit: ShortText
    scope: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]
    frequency: ShortText
    methodology: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)
    ]
    reference_date: date
    period_start: date
    period_end: date
    collected_at: Timestamp

    @model_validator(mode="after")
    def period(self):
        if self.period_start > self.period_end or not (
            self.period_start <= self.reference_date <= self.period_end
        ):
            raise ValueError("Referência deve pertencer ao período observado.")
        return self


class EvidenceLevel(StrEnum):
    DESCRIPTION = "DESCRIPTION"
    ASSOCIATION = "ASSOCIATION"
    HYPOTHESIS_SUPPORT = "HYPOTHESIS_SUPPORT"


class Evidence(FrozenRecord):
    id: UUID
    source_id: UUID
    level: EvidenceLevel
    claim: Text
    locator: Text  # Page/table/section, not a whole-document endorsement.
    excerpt: Text
    scope: Text
    period: ShortText
    limitations: Text


class EvidenceRelation(StrEnum):
    SUPPORTS = "SUPPORTS"
    CHALLENGES = "CHALLENGES"
    CONTEXT = "CONTEXT"


class EvidenceLink(FrozenRecord):
    evidence_id: UUID
    relation: EvidenceRelation
    justification: Text


class Hypothesis(FrozenRecord):
    id: Code
    explanation: Text
    evidence: Annotated[tuple[EvidenceLink, ...], Field(max_length=32)] = ()
    uncertainty: Text


class CounterpartAvailability(StrEnum):
    REFERENCED = "REFERENCED"
    NOT_COLLECTED = "NOT_COLLECTED"


class Counterpart(FrozenRecord):
    indicator_code: IndicatorCode
    why_read_together: Text
    availability: CounterpartAvailability
    observation_ids: Annotated[tuple[UUID, ...], Field(max_length=32)] = ()

    @model_validator(mode="after")
    def availability_matches_references(self):
        if (self.availability == CounterpartAvailability.REFERENCED) != bool(self.observation_ids):
            raise ValueError("Contrapartida deve distinguir referências de dados não coletados.")
        if len(set(self.observation_ids)) != len(self.observation_ids):
            raise ValueError("Observação de contrapartida duplicada.")
        return self


class ConsequenceKind(StrEnum):
    OBSERVED = "OBSERVED"
    PROJECTED = "PROJECTED"


class Consequence(FrozenRecord):
    id: Code
    kind: ConsequenceKind
    description: Text
    evidence_ids: Annotated[tuple[UUID, ...], Field(max_length=32)] = ()
    observation_ids: Annotated[tuple[UUID, ...], Field(max_length=32)] = ()
    premises: Annotated[tuple[Text, ...], Field(max_length=16)] = ()
    limitations: Annotated[str, StringConstraints(max_length=2000)] = ""


class ContextDraft(FrozenRecord):
    contract_version: Literal["1.0.0"] = CONTEXT_CONTRACT_VERSION
    id: UUID
    author_id: UUID
    revision: Revision
    updated_at: Timestamp
    title: Annotated[str, StringConstraints(strip_whitespace=True, max_length=180)] = ""
    observation_summary: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=4000)
    ] = ""
    primary_observation_id: UUID | None = None
    observations: Annotated[tuple[ObservationAnchor, ...], Field(max_length=64)] = ()
    sources: Annotated[tuple[SourceReference, ...], Field(max_length=64)] = ()
    counterparts: Annotated[tuple[Counterpart, ...], Field(max_length=32)] = ()
    evidence: Annotated[tuple[Evidence, ...], Field(max_length=64)] = ()
    hypotheses: Annotated[tuple[Hypothesis, ...], Field(max_length=16)] = ()
    consequences: Annotated[tuple[Consequence, ...], Field(max_length=32)] = ()
    limitations: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    unknowns: Annotated[tuple[Text, ...], Field(max_length=32)] = ()

    @model_validator(mode="after")
    def references(self):
        def unique(values, label):
            if len(values) != len(set(values)):
                raise ValueError(f"Identificador duplicado: {label}.")
            return set(values)

        sources = unique([source.id for source in self.sources], "fonte")
        observations = unique([row.observation_id for row in self.observations], "observação")
        evidence = unique([row.id for row in self.evidence], "evidência")
        unique([row.id for row in self.hypotheses], "hipótese")
        unique([row.id for row in self.consequences], "consequência")
        unique([row.indicator_code for row in self.counterparts], "contrapartida")
        if (
            self.primary_observation_id is not None
            and self.primary_observation_id not in observations
        ):
            raise ValueError("Observação principal ausente do conjunto.")
        if any(row.source_id not in sources for row in (*self.observations, *self.evidence)):
            raise ValueError("Referência a fonte ausente.")
        codes = {row.observation_id: row.indicator_code for row in self.observations}
        for row in self.counterparts:
            if any(codes.get(key) != row.indicator_code for key in row.observation_ids):
                raise ValueError("Contrapartida deve referenciar observações do próprio indicador.")
        for row in self.hypotheses:
            unique([link.evidence_id for link in row.evidence], "evidência da hipótese")
            if any(link.evidence_id not in evidence for link in row.evidence):
                raise ValueError("Hipótese aponta para evidência ausente.")
        for row in self.consequences:
            unique(list(row.evidence_ids), "evidência da consequência")
            unique(list(row.observation_ids), "observação da consequência")
            if (
                not set(row.evidence_ids) <= evidence
                or not set(row.observation_ids) <= observations
            ):
                raise ValueError("Consequência aponta para referência ausente.")
        return self


class ReviewDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REQUEST_CHANGES = "REQUEST_CHANGES"


class ContextReview(FrozenRecord):
    contract_version: Literal["1.0.0"] = CONTEXT_CONTRACT_VERSION
    context_id: UUID
    context_revision: Revision
    content_hash: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    reviewer_id: UUID
    reviewed_at: Timestamp
    decision: ReviewDecision
    rationale: Text
    references_checked: bool
    scopes_checked: bool
    alternatives_checked: bool
    limitations_checked: bool


class ContextStatus(StrEnum):
    INCOMPLETE = "INCOMPLETE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REVIEW_STALE = "REVIEW_STALE"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REVIEW_MATCHES = "REVIEW_MATCHES"


class Assessment(FrozenRecord):
    contract_version: Literal["1.0.0"] = CONTEXT_CONTRACT_VERSION
    content_hash: str
    status: ContextStatus
    missing: tuple[str, ...]
    limitations: tuple[str, ...] = LIMITATIONS


def _validated(draft: ContextDraft) -> ContextDraft:
    # Reject unvalidated model_copy/model_construct inputs as well as nested mutable data.
    return ContextDraft.model_validate(draft)


def fingerprint(draft: ContextDraft) -> str:
    content = _validated(draft).model_dump(mode="json")
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assess_context(
    draft: ContextDraft, *, assessed_at: datetime, review: ContextReview | None = None
) -> Assessment:
    """Structural readiness and review binding only; no network/database/model call."""
    draft = _validated(draft)
    now = _utc(assessed_at)
    content_hash = fingerprint(draft)
    missing = []
    if not draft.title:
        missing.append("TITLE_REQUIRED")
    if not draft.observation_summary:
        missing.append("OBSERVATION_SUMMARY_REQUIRED")
    if draft.primary_observation_id is None:
        missing.append("PRIMARY_OBSERVATION_REQUIRED")
    if not draft.counterparts:
        missing.append("COUNTERPART_REQUIRED")
    elif any(
        row.indicator_code
        == next(
            (
                anchor.indicator_code
                for anchor in draft.observations
                if anchor.observation_id == draft.primary_observation_id
            ),
            None,
        )
        for row in draft.counterparts
    ):
        missing.append("DISTINCT_COUNTERPART_REQUIRED")
    explanations = {re.sub(r"\s+", " ", row.explanation).casefold() for row in draft.hypotheses}
    if len(explanations) < 2:
        missing.append("ALTERNATIVE_HYPOTHESIS_REQUIRED")
    if not draft.evidence or not any(row.evidence for row in draft.hypotheses):
        missing.append("HYPOTHESIS_EVIDENCE_REQUIRED")
    if not draft.limitations:
        missing.append("LIMITATIONS_REQUIRED")
    if not draft.unknowns:
        missing.append("UNKNOWNS_REQUIRED")
    evidence_levels = {row.id: row.level for row in draft.evidence}
    for row in draft.consequences:
        descriptive_evidence = any(
            evidence_levels[key] in {EvidenceLevel.DESCRIPTION, EvidenceLevel.ASSOCIATION}
            for key in row.evidence_ids
        )
        if row.kind == ConsequenceKind.OBSERVED and not (
            descriptive_evidence or row.observation_ids
        ):
            missing.append(f"OBSERVED_REFERENCE_REQUIRED:{row.id}")
        if row.kind == ConsequenceKind.OBSERVED and row.premises:
            missing.append(f"OBSERVED_HAS_PROJECTION_PREMISES:{row.id}")
        if row.kind == ConsequenceKind.PROJECTED and not row.premises:
            missing.append(f"PROJECTED_PREMISES_REQUIRED:{row.id}")
        if not row.limitations.strip():
            missing.append(f"CONSEQUENCE_LIMITATIONS_REQUIRED:{row.id}")
    if draft.updated_at > now:
        missing.append("CONTEXT_DATE_IN_FUTURE")
    if any(row.consulted_at > draft.updated_at for row in draft.sources):
        missing.append("SOURCE_CONSULTED_AFTER_CONTEXT")
    if any(row.collected_at > draft.updated_at for row in draft.observations):
        missing.append("OBSERVATION_COLLECTED_AFTER_CONTEXT")
    if any(
        row.published_date and row.published_date > row.consulted_at.date() for row in draft.sources
    ):
        missing.append("SOURCE_PUBLICATION_AFTER_CONSULTATION")
    if any(row.period_end > row.collected_at.date() for row in draft.observations):
        missing.append("OBSERVED_PERIOD_AFTER_COLLECTION")
    if missing:
        return Assessment(
            content_hash=content_hash, status=ContextStatus.INCOMPLETE, missing=tuple(missing)
        )
    if review is None:
        return Assessment(
            content_hash=content_hash,
            status=ContextStatus.NEEDS_REVIEW,
            missing=("HUMAN_REVIEW_REQUIRED",),
        )
    review = ContextReview.model_validate(review)
    if (
        review.context_id != draft.id
        or review.context_revision != draft.revision
        or review.content_hash != content_hash
        or review.contract_version != draft.contract_version
        or not draft.updated_at <= review.reviewed_at <= now
    ):
        return Assessment(
            content_hash=content_hash,
            status=ContextStatus.REVIEW_STALE,
            missing=("REVIEW_NOT_BOUND_TO_CURRENT_CONTENT",),
        )
    if review.decision == ReviewDecision.REQUEST_CHANGES:
        return Assessment(
            content_hash=content_hash,
            status=ContextStatus.CHANGES_REQUESTED,
            missing=("REVIEW_REQUESTED_CHANGES",),
        )
    if not all(
        (
            review.references_checked,
            review.scopes_checked,
            review.alternatives_checked,
            review.limitations_checked,
        )
    ):
        return Assessment(
            content_hash=content_hash,
            status=ContextStatus.NEEDS_REVIEW,
            missing=("REVIEW_CHECKLIST_INCOMPLETE",),
        )
    return Assessment(content_hash=content_hash, status=ContextStatus.REVIEW_MATCHES, missing=())
