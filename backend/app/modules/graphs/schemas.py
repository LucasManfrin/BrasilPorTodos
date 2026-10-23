"""Graph transport accepts author content, never managed identities or approval."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StrictBool, StrictInt, field_validator, model_validator

from app.modules.contexts.context import (
    Evidence,
    EvidenceLink,
    IndicatorCode,
    ShortText,
    Text,
    Timestamp,
)
from app.modules.contexts.schemas import InputModel, nested_contract
from app.modules.graphs.graph import (
    ConsensusLevel,
    CounterpointStatus,
    EdgeAuthorship,
    EdgeDirection,
    EdgeHorizon,
    EdgeReviewDecision,
    EdgeTrigger,
    EffectKind,
    NodeKind,
)

ExpectedRevision = Annotated[StrictInt, Field(ge=1, le=2147483647)]


class NodeContentInput(InputModel):
    kind: NodeKind
    label: ShortText
    definition: Text
    dimension: Text
    unit: ShortText | None = None
    indicator_code: IndicatorCode | None = None
    policy_version_id: UUID | None = None

    @model_validator(mode="after")
    def references(self):
        if (self.kind == NodeKind.INDICATOR) != (self.indicator_code is not None):
            raise ValueError("Código pertence exclusivamente a indicador.")
        if (self.kind == NodeKind.MEASURE) != (self.policy_version_id is not None):
            raise ValueError("Versão de proposta pertence exclusivamente a medida.")
        return self


class NodeCreate(InputModel):
    content: NodeContentInput


class NodeUpdate(NodeCreate):
    expected_revision: ExpectedRevision


class EdgeContentInput(InputModel):
    from_node_version_id: UUID
    to_node_version_id: UUID
    statement: Text
    trigger: EdgeTrigger
    direction: EdgeDirection
    horizon: EdgeHorizon
    effect: EffectKind
    consensus: ConsensusLevel
    authorship: EdgeAuthorship
    source_ids: Annotated[tuple[UUID, ...], Field(min_length=1, max_length=32)]
    evidence: Annotated[
        tuple[Annotated[Evidence, nested_contract(Evidence)], ...],
        Field(min_length=1, max_length=64),
    ]
    links: Annotated[
        tuple[Annotated[EvidenceLink, nested_contract(EvidenceLink)], ...],
        Field(min_length=1, max_length=64),
    ]
    premises: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    scope: Text
    period: ShortText
    limitations: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    unknowns: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    counterpoint_status: CounterpointStatus = CounterpointStatus.NOT_RESEARCHED
    counterpoint_search_notes: Annotated[tuple[Text, ...], Field(max_length=16)] = ()
    counterpoint_searched_at: Timestamp | None = None
    counterargument_note: Annotated[str, Field(max_length=2000)] = ""

    @field_validator("counterpoint_searched_at", mode="before")
    @classmethod
    def explicit_timestamp(cls, value):
        if value is not None and not isinstance(value, (str, datetime)):
            raise ValueError("Data da busca deve ser uma data explícita com fuso horário.")
        return value

    @model_validator(mode="after")
    def references(self):
        if self.from_node_version_id == self.to_node_version_id:
            raise ValueError("Origem e destino precisam ser distintos.")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("Fonte duplicada.")
        return self


class EdgeCreate(InputModel):
    content: EdgeContentInput


class EdgeUpdate(EdgeCreate):
    expected_revision: ExpectedRevision


class EdgeReviewInput(InputModel):
    expected_revision: ExpectedRevision
    decision: EdgeReviewDecision
    rationale: Text
    references_checked: StrictBool
    scopes_checked: StrictBool
    counterpoints_checked: StrictBool
    limitations_checked: StrictBool


class EdgePublishInput(InputModel):
    expected_revision: ExpectedRevision
    publication_state: Literal["REVIEWED", "DISPUTED"]


class GraphContentInput(InputModel):
    title: ShortText
    node_version_ids: Annotated[tuple[UUID, ...], Field(max_length=200)] = ()
    edge_version_ids: Annotated[tuple[UUID, ...], Field(max_length=400)] = ()

    @model_validator(mode="after")
    def references(self):
        if len(set(self.node_version_ids)) != len(self.node_version_ids) or len(
            set(self.edge_version_ids)
        ) != len(self.edge_version_ids):
            raise ValueError("Referência duplicada.")
        return self


class GraphCreate(InputModel):
    content: GraphContentInput


class GraphUpdate(GraphCreate):
    expected_revision: ExpectedRevision


class GraphPublishInput(InputModel):
    expected_revision: ExpectedRevision
