"""Resolve exact saved references for the author; never visit contributed URLs."""

import json

from pydantic import ValidationError
from sqlalchemy import or_, select

from app.core.config import get_settings
from app.core.errors import DomainError
from app.modules.contexts.resolver import KNOWN_CODES, _source
from app.modules.graphs.graph import GraphNodeVersion as NodeRecord
from app.modules.graphs.graph import NodeKind
from app.modules.graphs.models import (
    GraphEdge,
    GraphEdgePublication,
    GraphEdgeVersion,
    GraphNode,
    GraphNodeVersion,
)
from app.modules.indicators.models import Indicator
from app.modules.policies.models import Policy, PolicyVersion
from app.modules.sources.models import Source
from app.modules.sources.service import public_sources


def missing():
    raise DomainError(
        404, "GRAPH_REFERENCE_NOT_FOUND", "Referência não disponível para este grafo."
    )


def visible(stmt, model):
    return (
        stmt
        if get_settings().environment == "development"
        else stmt.where(model.is_example.is_(False))
    )


def node_publication(version_id, *, real_only=False):
    return (
        select(GraphEdgePublication.id)
        .join(GraphEdgeVersion, GraphEdgeVersion.id == GraphEdgePublication.edge_version_id)
        .join(GraphEdge, GraphEdge.id == GraphEdgeVersion.edge_id)
        .where(
            or_(
                GraphEdgeVersion.from_node_version_id == version_id,
                GraphEdgeVersion.to_node_version_id == version_id,
            ),
            True
            if get_settings().environment == "development" and not real_only
            else GraphEdge.is_example.is_(False),
        )
        .exists()
    )


def node_version(session, version_id, author_id):
    row = session.execute(
        visible(
            select(GraphNodeVersion, GraphNode)
            .join(GraphNode, GraphNode.id == GraphNodeVersion.node_id)
            .where(
                GraphNodeVersion.id == version_id,
                or_(GraphNode.author_id == author_id, node_publication(GraphNodeVersion.id)),
            ),
            GraphNode,
        ).with_for_update(read=True)
    ).first()
    if row is None:
        missing()
    return row


def edge_version(session, version_id, author_id):
    pub = (
        select(GraphEdgePublication.id)
        .where(GraphEdgePublication.edge_version_id == GraphEdgeVersion.id)
        .exists()
    )
    row = session.execute(
        visible(
            select(GraphEdgeVersion, GraphEdge)
            .join(GraphEdge, GraphEdge.id == GraphEdgeVersion.edge_id)
            .where(
                GraphEdgeVersion.id == version_id,
                or_(GraphEdge.author_id == author_id, pub),
            ),
            GraphEdge,
        ).with_for_update(read=True)
    ).first()
    if row is None:
        missing()
    return row


def node_content(session, content, author_id):
    fields = content.model_dump(mode="json")
    example = False
    if content.kind == NodeKind.INDICATOR:
        if content.indicator_code not in KNOWN_CODES:
            missing()
        indicator = session.scalar(
            select(Indicator)
            .where(Indicator.code == content.indicator_code, Indicator.is_active.is_(True))
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
        if indicator is None:
            missing()
        if content.unit is not None and content.unit != indicator.unit:
            raise DomainError(
                422, "GRAPH_INDICATOR_UNIT", "Unidade deve coincidir com o catálogo do indicador."
            )
        fields["unit"] = indicator.unit
    if content.kind == NodeKind.MEASURE:
        row = session.execute(
            select(PolicyVersion, Policy)
            .join(Policy, Policy.id == PolicyVersion.policy_id)
            .where(
                PolicyVersion.id == content.policy_version_id, PolicyVersion.status == "PUBLISHED"
            )
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        ).first()
        if row is None or (row[1].is_example and get_settings().environment != "development"):
            missing()
        fields["policy_version_number"] = row[0].version_number
        example = row[1].is_example
    return fields, example


def sources(session, source_ids, author_id, frozen=None):
    rows = list(
        session.scalars(
            select(Source)
            .where(Source.id.in_(source_ids))
            .order_by(Source.id)
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
    )
    if len(rows) != len(source_ids):
        missing()
    by_id = {row.id: row for row in rows}
    for row in rows:
        if (row.is_example and get_settings().environment != "development") or (
            row.created_by != author_id
            and session.scalar(public_sources().where(Source.id == row.id)) is None
        ):
            missing()
    try:
        refs = tuple(
            _source(session, by_id[key], {}, (frozen or {}).get(key)) for key in source_ids
        )
    except ValidationError as error:
        raise DomainError(
            422, "GRAPH_REFERENCE_INVALID", "Metadados da fonte precisam de correção."
        ) from error
    return refs, any(row.is_example for row in rows)


def edge_content(session, content, author_id, frozen_sources=None):
    first, first_identity = node_version(session, content.from_node_version_id, author_id)
    second, second_identity = node_version(session, content.to_node_version_id, author_id)
    # Recheck live authority/units without replacing the frozen node.
    validate_node(
        session,
        NodeRecord.model_validate_json(json.dumps(first.payload)),
        first_identity.author_id,
        first_identity.is_example,
    )
    validate_node(
        session,
        NodeRecord.model_validate_json(json.dumps(second.payload)),
        second_identity.author_id,
        second_identity.is_example,
    )
    refs, example = sources(session, content.source_ids, author_id, frozen_sources)
    fields = content.model_dump(
        mode="json", exclude={"from_node_version_id", "to_node_version_id", "source_ids"}
    )
    fields.update(
        from_node=first.payload,
        to_node=second.payload,
        sources=[ref.model_dump(mode="json") for ref in refs],
    )
    return fields, example or first_identity.is_example or second_identity.is_example


def validate_node(session, node, author_id, is_example=False):
    from app.modules.graphs.schemas import NodeContentInput

    content = NodeContentInput.model_validate_json(
        node.model_dump_json(exclude={"id", "revision", "policy_version_number"})
    )
    resolved, example = node_content(session, content, author_id)
    frozen = node.model_dump(mode="json", exclude={"id", "revision"})
    # Null policy reference number is part of pure serialization.
    resolved.setdefault("policy_version_number", None)
    if resolved != frozen:
        raise DomainError(
            409, "GRAPH_REFERENCE_CHANGED", "Referências mudaram; salve e revise uma nova versão."
        )
    if example and not is_example:
        raise DomainError(
            422,
            "EXAMPLE_GRAPH_REQUIRED",
            "A referência agora é fictícia; crie uma identidade de exemplo.",
        )


def validate_edge(session, edge, version, author_id, is_example=False):
    from app.modules.graphs.schemas import EdgeContentInput

    content = EdgeContentInput.model_validate_json(
        json.dumps(
            {
                **edge.model_dump(
                    mode="json",
                    exclude={
                        "contract_version",
                        "id",
                        "revision",
                        "author_id",
                        "updated_at",
                        "from_node",
                        "to_node",
                        "sources",
                    },
                ),
                "from_node_version_id": str(version.from_node_version_id),
                "to_node_version_id": str(version.to_node_version_id),
                "source_ids": [str(row.id) for row in edge.sources],
            }
        )
    )
    fields, example = edge_content(
        session, content, author_id, {row.id: row for row in edge.sources}
    )
    frozen = edge.model_dump(
        mode="json", exclude={"contract_version", "id", "revision", "author_id", "updated_at"}
    )
    if fields != frozen:
        raise DomainError(
            409, "GRAPH_REFERENCE_CHANGED", "Referências mudaram; salve e revise uma nova versão."
        )
    if example and not is_example:
        raise DomainError(
            422,
            "EXAMPLE_GRAPH_REQUIRED",
            "A referência agora é fictícia; crie uma identidade de exemplo.",
        )


def validate_node_reuse(session, node, is_example=False):
    """Public historical versions keep their metadata; references must still be usable."""
    if node.kind == NodeKind.INDICATOR:
        indicator = session.scalar(
            select(Indicator)
            .where(Indicator.code == node.indicator_code, Indicator.is_active.is_(True))
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
        if node.indicator_code not in KNOWN_CODES or indicator is None:
            missing()
    if node.kind == NodeKind.MEASURE:
        row = session.execute(
            select(PolicyVersion, Policy)
            .join(Policy, Policy.id == PolicyVersion.policy_id)
            .where(PolicyVersion.id == node.policy_version_id, PolicyVersion.status == "PUBLISHED")
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        ).first()
        if row is None or (row[1].is_example and get_settings().environment != "development"):
            missing()
        if row[1].is_example and not is_example:
            raise DomainError(
                422,
                "EXAMPLE_GRAPH_REQUIRED",
                "O conjunto real não pode incorporar referências agora fictícias.",
            )


def validate_edge_reuse(session, edge, author_id, is_example=False):
    ids = [row.id for row in edge.sources]
    rows = list(
        session.scalars(
            select(Source)
            .where(Source.id.in_(ids))
            .order_by(Source.id)
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
    )
    if len(rows) != len(ids):
        missing()
    for row in rows:
        if (row.is_example and get_settings().environment != "development") or (
            row.created_by != author_id
            and session.scalar(public_sources().where(Source.id == row.id)) is None
        ):
            missing()
        if row.is_example and not is_example:
            raise DomainError(
                422,
                "EXAMPLE_GRAPH_REQUIRED",
                "O conjunto real não pode incorporar referências agora fictícias.",
            )
    for node in (edge.from_node, edge.to_node):
        validate_node_reuse(session, node, is_example)
