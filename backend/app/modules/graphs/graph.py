"""Frozen qualitative graph records and bounded structural diagnostics.

References and reviews are declarations, not authentication, causal proof or
publication permission. No graph relation supplies a fiscal coefficient.
"""

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, TypeAdapter, model_validator

from app.modules.contexts.context import (
    Code,
    Evidence,
    EvidenceLink,
    EvidenceRelation,
    FrozenRecord,
    IndicatorCode,
    Revision,
    ShortText,
    SourceReference,
    Text,
    Timestamp,
)

GRAPH_CONTRACT_VERSION = "1.0.0"
LIMITATIONS = (
    "Estrutura e revisão declaradas não autenticam pessoas nem autorizam publicação.",
    "Fonte, trecho e suporte declarados não demonstram causalidade por si.",
    "IDs, permissões, termos e conteúdo das fontes exigem conferência por serviço confiável.",
    "Relações qualitativas não fornecem coeficientes, probabilidades ou resultados fiscais.",
    "Ciclos podem representar realimentação; diagnósticos não somam nem propagam efeitos.",
    "Ciclos estruturais ignoram escopo/período e não demonstram realimentação econômica.",
)


class NodeKind(StrEnum):
    INDICATOR = "INDICATOR"
    MEASURE = "MEASURE"
    MECHANISM = "MECHANISM"
    AFFECTED_GROUP = "AFFECTED_GROUP"


class GraphNodeVersion(FrozenRecord):
    id: Code
    revision: Revision
    kind: NodeKind
    label: ShortText
    definition: Text
    dimension: Text
    indicator_code: IndicatorCode | None = None
    policy_version_id: UUID | None = None
    policy_version_number: Revision | None = None
    unit: ShortText | None = None

    @model_validator(mode="after")
    def references(self):
        if (self.kind == NodeKind.INDICATOR) != (self.indicator_code is not None):
            raise ValueError("Somente indicador exige código de indicador.")
        has_policy = self.policy_version_id is not None
        has_number = self.policy_version_number is not None
        if self.kind == NodeKind.MEASURE:
            if not has_policy or not has_number:
                raise ValueError("Medida exige ID e número da versão de proposta.")
        elif has_policy or has_number:
            raise ValueError("Referência de proposta só pertence a medida.")
        return self


class EdgeTrigger(StrEnum):
    INCREASE = "INCREASE"
    ADOPTION = "ADOPTION"


class EdgeDirection(StrEnum):
    INCREASES = "INCREASES"
    DECREASES = "DECREASES"
    UNCERTAIN = "UNCERTAIN"


class EdgeHorizon(StrEnum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class EffectKind(StrEnum):
    ACCOUNTING_DIRECT = "ACCOUNTING_DIRECT"
    INDIRECT_ESTIMATE = "INDIRECT_ESTIMATE"
    QUALITATIVE = "QUALITATIVE"


class ConsensusLevel(StrEnum):
    ESTABLISHED = "ESTABLISHED"
    DEBATED = "DEBATED"
    SPECULATIVE = "SPECULATIVE"


class EdgeAuthorship(StrEnum):
    HUMAN = "HUMAN"
    AI_ASSISTED = "AI_ASSISTED"


class CounterpointStatus(StrEnum):
    NOT_RESEARCHED = "NOT_RESEARCHED"
    NOT_FOUND = "NOT_FOUND"
    DOCUMENTED = "DOCUMENTED"


def _unique(values, label):
    if len(values) != len(set(values)):
        raise ValueError(f"Identificador duplicado: {label}.")
    return set(values)


class GraphEdgeDraft(FrozenRecord):
    contract_version: Literal["1.0.0"] = GRAPH_CONTRACT_VERSION
    id: Code
    revision: Revision
    author_id: UUID
    updated_at: Timestamp
    from_node: GraphNodeVersion
    to_node: GraphNodeVersion
    statement: Text
    trigger: EdgeTrigger
    direction: EdgeDirection
    horizon: EdgeHorizon
    effect: EffectKind
    consensus: ConsensusLevel
    authorship: EdgeAuthorship
    sources: Annotated[tuple[SourceReference, ...], Field(min_length=1, max_length=32)]
    evidence: Annotated[tuple[Evidence, ...], Field(min_length=1, max_length=64)]
    links: Annotated[tuple[EvidenceLink, ...], Field(min_length=1, max_length=64)]
    premises: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    scope: Text
    period: ShortText
    limitations: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    unknowns: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    counterpoint_status: CounterpointStatus = CounterpointStatus.NOT_RESEARCHED
    counterpoint_search_notes: Annotated[tuple[Text, ...], Field(max_length=16)] = ()
    counterpoint_searched_at: Timestamp | None = None
    counterargument_note: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=2000)
    ] = ""

    @model_validator(mode="after")
    def references(self):
        if self.from_node.id == self.to_node.id:
            raise ValueError("Origem e destino precisam ser nós distintos.")
        if (self.from_node.kind == NodeKind.MEASURE) != (self.trigger == EdgeTrigger.ADOPTION):
            raise ValueError("Adoção é exclusiva e obrigatória para origem do tipo medida.")
        sources = _unique([row.id for row in self.sources], "fonte")
        evidence = _unique([row.id for row in self.evidence], "evidência")
        linked = _unique([row.evidence_id for row in self.links], "ligação de evidência")
        if {row.source_id for row in self.evidence} != sources:
            raise ValueError("Toda fonte precisa ser referenciada, sem fontes ausentes ou órfãs.")
        if linked != evidence:
            raise ValueError("Toda evidência precisa ser ligada, sem evidência ausente ou órfã.")
        has_challenges = any(link.relation == EvidenceRelation.CHALLENGES for link in self.links)
        if has_challenges != (self.counterpoint_status == CounterpointStatus.DOCUMENTED):
            raise ValueError("Contraponto documentado exige ligação CHALLENGES e vice-versa.")
        if self.counterpoint_status == CounterpointStatus.NOT_RESEARCHED and (
            self.counterpoint_search_notes or self.counterpoint_searched_at is not None
        ):
            raise ValueError("Busca não realizada não pode declarar notas ou data de busca.")
        return self


class GraphSnapshot(FrozenRecord):
    contract_version: Literal["1.0.0"] = GRAPH_CONTRACT_VERSION
    id: UUID
    revision: Revision
    author_id: UUID
    updated_at: Timestamp
    title: ShortText
    nodes: Annotated[tuple[GraphNodeVersion, ...], Field(max_length=200)] = ()
    edges: Annotated[tuple[GraphEdgeDraft, ...], Field(max_length=400)] = ()

    @model_validator(mode="after")
    def references(self):
        _unique([row.id for row in self.nodes], "nó")
        _unique([row.id for row in self.edges], "aresta")
        nodes = {row.id: row for row in self.nodes}
        for edge in self.edges:
            if edge.updated_at > self.updated_at:
                raise ValueError("Snapshot não pode anteceder a atualização de suas arestas.")
            for node in (edge.from_node, edge.to_node):
                if nodes.get(node.id) != node:
                    raise ValueError("Aresta exige exatamente a versão/conteúdo do nó selecionado.")
        return self


class EdgeReviewDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    DISPUTE = "DISPUTE"
    REJECT = "REJECT"


class EdgeReview(FrozenRecord):
    contract_version: Literal["1.0.0"] = GRAPH_CONTRACT_VERSION
    edge_id: Code
    edge_revision: Revision
    content_hash: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    reviewer_id: UUID
    reviewed_at: Timestamp
    decision: EdgeReviewDecision
    rationale: Text
    references_checked: bool
    scopes_checked: bool
    counterpoints_checked: bool
    limitations_checked: bool


class EdgeStatus(StrEnum):
    INCOMPLETE = "INCOMPLETE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REVIEW_STALE = "REVIEW_STALE"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    DISPUTE_MATCHES = "DISPUTE_MATCHES"
    REJECTION_MATCHES = "REJECTION_MATCHES"
    REVIEW_MATCHES = "REVIEW_MATCHES"


class EdgeAssessment(FrozenRecord):
    contract_version: Literal["1.0.0"] = GRAPH_CONTRACT_VERSION
    content_hash: str
    status: EdgeStatus
    missing: tuple[str, ...]
    limitations: tuple[str, ...] = LIMITATIONS


def _hash(record: FrozenRecord) -> str:
    canonical = json.dumps(
        record.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def edge_fingerprint(edge: GraphEdgeDraft) -> str:
    return _hash(GraphEdgeDraft.model_validate(edge))


def graph_fingerprint(graph: GraphSnapshot) -> str:
    return _hash(GraphSnapshot.model_validate(graph))


def assess_edge(
    edge: GraphEdgeDraft, *, assessed_at: datetime, review: EdgeReview | None = None
) -> EdgeAssessment:
    """Check declared content/review binding; never authenticate or permit publication."""
    edge = GraphEdgeDraft.model_validate(edge)
    if review is not None:
        review = EdgeReview.model_validate(review)
    # Validate explicit timezone with the same domain type used for record timestamps.
    now = TypeAdapter(Timestamp).validate_python(assessed_at, strict=True)
    content_hash = edge_fingerprint(edge)
    missing = []
    if edge.updated_at > now:
        missing.append("EDGE_DATE_IN_FUTURE")
    if any(source.consulted_at > edge.updated_at for source in edge.sources):
        missing.append("SOURCE_CONSULTED_AFTER_EDGE")
    if any(
        source.published_date and source.published_date > source.consulted_at.date()
        for source in edge.sources
    ):
        missing.append("SOURCE_PUBLICATION_AFTER_CONSULTATION")
    if not any(link.relation == EvidenceRelation.SUPPORTS for link in edge.links):
        missing.append("SUPPORTING_EVIDENCE_REQUIRED")
    if not edge.premises:
        missing.append("PREMISES_REQUIRED")
    if not edge.limitations:
        missing.append("LIMITATIONS_REQUIRED")
    if not edge.unknowns:
        missing.append("UNKNOWNS_REQUIRED")
    if edge.counterpoint_status == CounterpointStatus.NOT_FOUND:
        if not edge.counterargument_note:
            missing.append("COUNTERPOINT_NOT_FOUND_NOTE_REQUIRED")
        if not edge.counterpoint_search_notes:
            missing.append("COUNTERPOINT_SEARCH_NOTES_REQUIRED")
        if edge.counterpoint_searched_at is None:
            missing.append("COUNTERPOINT_SEARCH_DATE_REQUIRED")
    if edge.counterpoint_searched_at is not None:
        if edge.counterpoint_searched_at > edge.updated_at:
            missing.append("COUNTERPOINT_SEARCH_AFTER_EDGE")
        if edge.counterpoint_searched_at > now:
            missing.append("COUNTERPOINT_SEARCH_IN_FUTURE")
    if (
        edge.consensus in {ConsensusLevel.ESTABLISHED, ConsensusLevel.DEBATED}
        and edge.counterpoint_status == CounterpointStatus.NOT_RESEARCHED
    ):
        missing.append("COUNTERPOINT_REQUIRED")
    if missing:
        return EdgeAssessment(
            content_hash=content_hash, status=EdgeStatus.INCOMPLETE, missing=tuple(missing)
        )
    if review is None:
        return EdgeAssessment(
            content_hash=content_hash,
            status=EdgeStatus.NEEDS_REVIEW,
            missing=("DISTINCT_HUMAN_REVIEW_REQUIRED",),
        )
    if (
        review.edge_id != edge.id
        or review.edge_revision != edge.revision
        or review.content_hash != content_hash
        or review.contract_version != edge.contract_version
        or review.reviewer_id == edge.author_id
        or not edge.updated_at <= review.reviewed_at <= now
    ):
        return EdgeAssessment(
            content_hash=content_hash,
            status=EdgeStatus.REVIEW_STALE,
            missing=("REVIEW_NOT_BOUND_TO_CURRENT_CONTENT_OR_DISTINCT_REVIEWER",),
        )
    decisions = {
        EdgeReviewDecision.REQUEST_CHANGES: EdgeStatus.CHANGES_REQUESTED,
        EdgeReviewDecision.DISPUTE: EdgeStatus.DISPUTE_MATCHES,
        EdgeReviewDecision.REJECT: EdgeStatus.REJECTION_MATCHES,
    }
    if review.decision in decisions:
        return EdgeAssessment(
            content_hash=content_hash,
            status=decisions[review.decision],
            missing=(f"REVIEW_{review.decision.value}",),
        )
    if not all(
        (
            review.references_checked,
            review.scopes_checked,
            review.counterpoints_checked,
            review.limitations_checked,
        )
    ):
        return EdgeAssessment(
            content_hash=content_hash,
            status=EdgeStatus.NEEDS_REVIEW,
            missing=("REVIEW_CHECKLIST_INCOMPLETE",),
        )
    return EdgeAssessment(content_hash=content_hash, status=EdgeStatus.REVIEW_MATCHES, missing=())


class TopologyDiagnostics(FrozenRecord):
    duplicate_edges: tuple[tuple[str, ...], ...]
    conflicting_edges: tuple[tuple[str, ...], ...]
    cycle_components: tuple[tuple[str, ...], ...]
    isolated_nodes: tuple[str, ...]
    limitations: tuple[str, ...] = LIMITATIONS


def inspect_topology(graph: GraphSnapshot) -> TopologyDiagnostics:
    """Deterministic iterative traversal, bounded by 200 nodes / 400 edges.

    Duplicate signatures ignore revision, trigger and supporting metadata by design.
    Conflicts identify opposed directions in the same declared scope and period.
    Strongly connected components diagnose feedback without interpreting its effect.
    Components use node identity regardless of scope/period: they may join different
    places or times and do not establish an economically coherent feedback loop.
    """
    graph = GraphSnapshot.model_validate(graph)
    duplicates = defaultdict(list)
    pairs = defaultdict(list)
    adjacency = {node.id: set() for node in graph.nodes}
    reverse = {node.id: set() for node in graph.nodes}
    for edge in graph.edges:
        pair = (
            edge.from_node.id,
            edge.to_node.id,
            re.sub(r"\s+", " ", edge.scope).strip().casefold(),
            re.sub(r"\s+", " ", edge.period).strip().casefold(),
        )
        duplicates[(*pair, edge.direction)].append(edge.id)
        pairs[pair].append(edge)
        adjacency[edge.from_node.id].add(edge.to_node.id)
        reverse[edge.to_node.id].add(edge.from_node.id)
    visited = set()
    finish_order = []
    for start in sorted(adjacency):
        if start in visited:
            continue
        visited.add(start)
        stack = [(start, iter(sorted(adjacency[start])))]
        while stack:
            node, neighbors = stack[-1]
            neighbor = next(neighbors, None)
            if neighbor is None:
                finish_order.append(node)
                stack.pop()
            elif neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, iter(sorted(adjacency[neighbor]))))
    assigned = set()
    cycles = []
    for start in reversed(finish_order):
        if start in assigned:
            continue
        component = []
        assigned.add(start)
        stack = [start]
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(reverse[node], reverse=True):
                if neighbor not in assigned:
                    assigned.add(neighbor)
                    stack.append(neighbor)
        if len(component) > 1:
            cycles.append(tuple(sorted(component)))
    return TopologyDiagnostics(
        duplicate_edges=tuple(
            sorted(tuple(sorted(ids)) for ids in duplicates.values() if len(ids) > 1)
        ),
        conflicting_edges=tuple(
            sorted(
                tuple(sorted(edge.id for edge in rows if edge.direction != EdgeDirection.UNCERTAIN))
                for rows in pairs.values()
                if {EdgeDirection.INCREASES, EdgeDirection.DECREASES}
                <= {edge.direction for edge in rows}
            )
        ),
        cycle_components=tuple(sorted(cycles)),
        isolated_nodes=tuple(
            sorted(node for node in adjacency if not adjacency[node] and not reverse[node])
        ),
    )
