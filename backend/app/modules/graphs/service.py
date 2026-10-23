"""Append-only graph curation with authenticated, distinct human review."""

import hashlib
import json
from datetime import UTC, datetime
from functools import wraps
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.core.errors import DomainError
from app.modules.admin.models import record
from app.modules.graphs import resolver
from app.modules.graphs.graph import (
    EdgeReview,
    EdgeReviewDecision,
    EdgeStatus,
    GraphEdgeDraft,
    GraphSnapshot,
    assess_edge,
    edge_fingerprint,
    graph_fingerprint,
    inspect_topology,
)
from app.modules.graphs.graph import (
    GraphNodeVersion as NodeRecord,
)
from app.modules.graphs.models import (
    GraphCollection,
    GraphCollectionPublication,
    GraphCollectionVersion,
    GraphEdge,
    GraphEdgePublication,
    GraphEdgeReview,
    GraphEdgeVersion,
    GraphNode,
    GraphNodeVersion,
)
from app.modules.users.models import User

MAX_NODE_PAYLOAD_BYTES = 32 * 1024
MAX_EDGE_PAYLOAD_BYTES = 1024 * 1024
MAX_GRAPH_PAYLOAD_BYTES = 4 * 1024 * 1024

KINDS = {
    "node": (GraphNode, GraphNodeVersion, "node_id", "label", None, None),
    "edge": (
        GraphEdge,
        GraphEdgeVersion,
        "edge_id",
        "statement",
        GraphEdgePublication,
        "edge_version_id",
    ),
    "graph": (
        GraphCollection,
        GraphCollectionVersion,
        "graph_id",
        "title",
        GraphCollectionPublication,
        "graph_version_id",
    ),
}


def _atomic(method):
    @wraps(method)
    def wrapped(session, *args, **kwargs):
        try:
            return method(session, *args, **kwargs)
        except Exception:
            session.rollback()
            raise

    return wrapped


def _error(status, code, text):
    raise DomainError(status, code, text)


def _actor(session, user, admin=False):
    actor = session.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    if actor is None or not actor.is_active:
        _error(401, "INVALID_SESSION", "Sessão inválida ou expirada.")
    if admin and actor.role != "ADMIN":
        _error(403, "FORBIDDEN", "Esta ação exige revisão administrativa.")
    return actor


def _identity(session, kind, identity_id, lock=False):
    model = KINDS[kind][0]
    stmt = resolver.visible(select(model).where(model.id == identity_id), model)
    if lock:
        stmt = stmt.with_for_update()
    identity = session.scalar(stmt)
    if identity is None:
        _error(404, "GRAPH_NOT_FOUND", "Registro do grafo não encontrado.")
    return identity


def _author(actor, identity):
    if actor.id != identity.author_id:
        _error(403, "FORBIDDEN", "Só o autor pode alterar ou publicar este registro.")


def _latest(session, kind, identity):
    version = KINDS[kind][1]
    result = session.scalar(
        select(version)
        .where(getattr(version, KINDS[kind][2]) == identity.id)
        .order_by(version.version_number.desc())
        .limit(1)
    )
    if result is None:
        _error(404, "GRAPH_NOT_FOUND", "Registro do grafo não encontrado.")
    return result


def _expected(version, expected):
    if version.version_number != expected:
        _error(
            409, "GRAPH_REVISION_CONFLICT", "O registro mudou. Reabra a versão antes de continuar."
        )


def _publication(session, kind, version, *, real_only=False):
    if kind == "node":
        return session.scalar(
            select(GraphEdgePublication)
            .join(GraphEdgeVersion, GraphEdgeVersion.id == GraphEdgePublication.edge_version_id)
            .join(GraphEdge, GraphEdge.id == GraphEdgeVersion.edge_id)
            .where(
                (GraphEdgeVersion.from_node_version_id == version.id)
                | (GraphEdgeVersion.to_node_version_id == version.id),
                True
                if resolver.get_settings().environment == "development" and not real_only
                else GraphEdge.is_example.is_(False),
            )
            .order_by(GraphEdgePublication.published_at, GraphEdgePublication.id)
            .limit(1)
        )
    publication, key = KINDS[kind][4:]
    return session.scalar(select(publication).where(getattr(publication, key) == version.id))


def _node_published_at(version):
    return (
        select(GraphEdgePublication.published_at)
        .join(GraphEdgeVersion, GraphEdgeVersion.id == GraphEdgePublication.edge_version_id)
        .join(GraphEdge, GraphEdge.id == GraphEdgeVersion.edge_id)
        .where(
            (GraphEdgeVersion.from_node_version_id == version.id)
            | (GraphEdgeVersion.to_node_version_id == version.id),
            True
            if resolver.get_settings().environment == "development"
            else GraphEdge.is_example.is_(False),
        )
        .order_by(GraphEdgePublication.published_at, GraphEdgePublication.id)
        .limit(1)
        .correlate(version)
        .scalar_subquery()
    )


def _review(session, version):
    return session.scalar(
        select(GraphEdgeReview)
        .where(GraphEdgeReview.edge_version_id == version.id)
        .order_by(GraphEdgeReview.review_number.desc())
        .limit(1)
    )


def _parse(model, payload):
    return model.model_validate_json(json.dumps(payload))


def _edge_review(review):
    return _parse(EdgeReview, review.payload) if review else None


def _base(identity, version, publication):
    return {
        "id": identity.id,
        "revision": version.version_number,
        "version_id": version.id,
        "content_hash": version.content_hash,
        "content": version.payload,
        "published_at": publication.published_at if publication else None,
        "is_example": identity.is_example,
    }


def _view(session, kind, identity, version, publication=None):
    publication = publication or _publication(session, kind, version)
    response = _base(identity, version, publication)
    if kind == "edge":
        review = (
            session.get(GraphEdgeReview, publication.review_id)
            if publication
            else _review(session, version)
        )
        response.update(
            assessment=assess_edge(
                _parse(GraphEdgeDraft, version.payload),
                assessed_at=datetime.now(UTC),
                review=_edge_review(review),
            ).model_dump(mode="json"),
            review=review.payload if review else None,
            publication_state=publication.published_state if publication else None,
        )
    elif kind == "graph":
        response["topology"] = inspect_topology(_parse(GraphSnapshot, version.payload)).model_dump(
            mode="json"
        )
        # One bounded metadata query, independent of the edge payload sizes.
        publications = (
            session.execute(
                select(
                    GraphEdgePublication.edge_version_id,
                    GraphEdgePublication.content_hash,
                    GraphEdgePublication.published_at,
                    GraphEdgePublication.published_state.label("publication_state"),
                    GraphEdgeReview.payload.label("review"),
                )
                .join(GraphEdgeReview, GraphEdgeReview.id == GraphEdgePublication.review_id)
                .where(GraphEdgePublication.edge_version_id.in_(version.edge_version_ids))
            )
            .mappings()
            .all()
        )
        by_id = {row["edge_version_id"]: dict(row) for row in publications}
        response["publications"] = [by_id[key] for key in version.edge_version_ids if key in by_id]
    return response


def _node_fields(session, data, identity, actor, revision):
    fields, example = resolver.node_content(session, data.content, identity.author_id)
    node = _parse(NodeRecord, {"id": "node-" + identity.id.hex, "revision": revision, **fields})
    canonical = json.dumps(
        node.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return {
        "payload": node.model_dump(mode="json"),
        "content_hash": hashlib.sha256(canonical.encode()).hexdigest(),
    }, example


def _edge_fields(session, data, identity, actor, revision):
    now = datetime.now(UTC)
    fields, example = resolver.edge_content(session, data.content, identity.author_id)
    edge = _parse(
        GraphEdgeDraft,
        {
            "id": "edge-" + identity.id.hex,
            "revision": revision,
            "author_id": str(identity.author_id),
            "updated_at": now.isoformat(),
            **fields,
        },
    )
    return {
        "payload": edge.model_dump(mode="json"),
        "content_hash": edge_fingerprint(edge),
        "created_at": now,
        "from_node_version_id": data.content.from_node_version_id,
        "to_node_version_id": data.content.to_node_version_id,
    }, example


def _graph_fields(session, data, identity, actor, revision):
    now = datetime.now(UTC)
    nodes = [
        resolver.node_version(session, key, identity.author_id)
        for key in data.content.node_version_ids
    ]
    edges = [
        resolver.edge_version(session, key, identity.author_id)
        for key in data.content.edge_version_ids
    ]
    snapshot = _parse(
        GraphSnapshot,
        {
            "id": str(identity.id),
            "revision": revision,
            "author_id": str(identity.author_id),
            "updated_at": now.isoformat(),
            "title": data.content.title,
            "nodes": [row[0].payload for row in nodes],
            "edges": [row[0].payload for row in edges],
        },
    )
    return {
        "payload": snapshot.model_dump(mode="json"),
        "content_hash": graph_fingerprint(snapshot),
        "created_at": now,
        "node_version_ids": list(data.content.node_version_ids),
        "edge_version_ids": list(data.content.edge_version_ids),
    }, any(row[1].is_example for row in [*nodes, *edges])


BUILD = {"node": _node_fields, "edge": _edge_fields, "graph": _graph_fields}


def _bounded_payload(kind, fields):
    limits = {
        "node": MAX_NODE_PAYLOAD_BYTES,
        "edge": MAX_EDGE_PAYLOAD_BYTES,
        "graph": MAX_GRAPH_PAYLOAD_BYTES,
    }
    payload_bytes = len(
        json.dumps(
            fields["payload"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )
    if payload_bytes > limits[kind]:
        _error(
            422,
            "GRAPH_CONTENT_TOO_LARGE",
            "O conteúdo excede o limite de tamanho desta etapa; divida o conjunto.",
        )


def _append(session, kind, identity, data, actor, revision):
    try:
        fields, example = BUILD[kind](session, data, identity, actor, revision)
    except ValidationError as error:
        raise DomainError(
            422, "GRAPH_INVALID_CONTENT", "Confira a estrutura e as referências do grafo."
        ) from error
    _bounded_payload(kind, fields)
    if example and not identity.is_example:
        _error(
            422,
            "EXAMPLE_GRAPH_REQUIRED",
            "Referências fictícias exigem uma nova identidade de exemplo.",
        )
    version = KINDS[kind][1](
        id=uuid4(),
        **{KINDS[kind][2]: identity.id},
        version_number=revision,
        created_by=actor.id,
        **fields,
    )
    session.add(version)
    session.flush()
    return version


@_atomic
def _create(session, kind, data, user):
    actor = _actor(session, user)
    identity = KINDS[kind][0](id=uuid4(), author_id=actor.id, is_example=False)
    # Resolve before insertion to derive examples rather than accepting a client flag.
    try:
        fields, example = BUILD[kind](session, data, identity, actor, 1)
    except ValidationError as error:
        raise DomainError(
            422, "GRAPH_INVALID_CONTENT", "Confira a estrutura e as referências do grafo."
        ) from error
    _bounded_payload(kind, fields)
    identity.is_example = example
    if example and resolver.get_settings().environment != "development":
        resolver.missing()
    session.add(identity)
    session.flush()
    version = _append(session, kind, identity, data, actor, 1)
    response = _view(session, kind, identity, version)
    session.commit()
    return response


@_atomic
def _update(session, kind, identity_id, data, user):
    identity = _identity(session, kind, identity_id, True)
    actor = _actor(session, user)
    _author(actor, identity)
    previous = _latest(session, kind, identity)
    _expected(previous, data.expected_revision)
    version = _append(session, kind, identity, data, actor, previous.version_number + 1)
    response = _view(session, kind, identity, version)
    session.commit()
    return response


def _draft(session, kind, identity_id, user):
    actor = _actor(session, user)
    identity = _identity(session, kind, identity_id)
    if actor.id != identity.author_id and actor.role != "ADMIN":
        _error(403, "FORBIDDEN", "Este rascunho não está disponível.")
    return _view(session, kind, identity, _latest(session, kind, identity))


def _published(session, kind, identity, revision=None):
    version_model, identity_key = KINDS[kind][1:3]
    stmt = select(version_model).where(getattr(version_model, identity_key) == identity.id)
    if kind == "node":
        stmt = stmt.where(resolver.node_publication(version_model.id))
    else:
        pub, key = KINDS[kind][4:]
        stmt = stmt.where(select(pub.id).where(getattr(pub, key) == version_model.id).exists())
    if revision is not None:
        stmt = stmt.where(version_model.version_number == revision)
    return stmt.order_by(version_model.version_number.desc())


def _public(session, kind, identity_id, revision=None):
    identity = _identity(session, kind, identity_id)
    version = session.scalar(_published(session, kind, identity, revision).limit(1))
    if version is None:
        _error(404, "GRAPH_NOT_FOUND", "Registro do grafo não encontrado.")
    return _view(session, kind, identity, version)


def _history(session, kind, identity_id):
    identity = _identity(session, kind, identity_id)
    version, _, title, pub, pub_key = KINDS[kind][1:]
    stmt = _published(session, kind, identity)
    if kind == "node":
        published_at = _node_published_at(version)
    else:
        stmt = stmt.join(pub, getattr(pub, pub_key) == version.id)
        published_at = pub.published_at
    rows = (
        session.execute(
            stmt.with_only_columns(
                version.version_number.label("revision"),
                version.content_hash,
                published_at.label("published_at"),
                version.payload[title].astext.label(title),
            )
        )
        .mappings()
        .all()
    )
    if not rows:
        _error(404, "GRAPH_NOT_FOUND", "Registro do grafo não encontrado.")
    return {"data": [dict(row) for row in rows]}


def _list(session, kind, page, page_size, q=None, *, user=None, queue=False):
    model, version_model, identity_key, title, pub, pub_key = KINDS[kind]
    stmt = resolver.visible(select(model.id.label("id")), model)
    if user is not None:
        actor = _actor(session, user, admin=queue)
        stmt = stmt.where(model.author_id != actor.id if queue else model.author_id == actor.id)
    elif queue:
        _error(403, "FORBIDDEN", "Esta ação exige revisão administrativa.")
    selected_version = aliased(version_model)
    selected = select(selected_version.id).where(
        getattr(selected_version, identity_key) == model.id
    )
    if user is None:
        if kind == "node":
            selected = selected.where(resolver.node_publication(selected_version.id))
        else:
            selected = selected.where(
                select(pub.id).where(getattr(pub, pub_key) == selected_version.id).exists()
            )
    selected_id = (
        selected.order_by(selected_version.version_number.desc())
        .limit(1)
        .correlate(model)
        .scalar_subquery()
    )
    stmt = stmt.where(selected_id.is_not(None))
    if queue:
        stmt = stmt.where(~select(pub.id).where(getattr(pub, pub_key) == selected_id).exists())
    displayed = aliased(version_model)
    stmt = stmt.join_from(model, displayed, displayed.id == selected_id)
    if q:
        stmt = stmt.where(displayed.payload[title].astext.ilike(f"%{q}%"))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    # Select only scalar metadata and a short JSON title. A directory must not load
    # a 4 MiB graph snapshot per row, evaluate topology or issue per-row lookups.
    if kind == "node":
        published_at = _node_published_at(displayed)
    else:
        displayed_publication = aliased(pub)
        stmt = stmt.outerjoin(
            displayed_publication, getattr(displayed_publication, pub_key) == displayed.id
        )
        published_at = displayed_publication.published_at
    columns = [
        model.id.label("id"),
        model.is_example.label("is_example"),
        displayed.version_number.label("revision"),
        displayed.id.label("version_id"),
        displayed.content_hash.label("content_hash"),
        displayed.payload[title].astext.label("title"),
        published_at.label("published_at"),
    ]
    if kind == "edge":
        columns.append(displayed_publication.published_state.label("publication_state"))
    projected = stmt.with_only_columns(*columns)
    rows = (
        session.execute(
            projected.order_by(model.created_at.desc(), model.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .mappings()
        .all()
    )
    data = []
    for row in rows:
        summary = {
            key: row[key]
            for key in (
                "id",
                "revision",
                "version_id",
                "content_hash",
                "published_at",
                "is_example",
            )
        }
        summary["content"] = {title: row["title"]}
        if kind == "edge":
            summary["publication_state"] = row["publication_state"]
        data.append(summary)
    return {
        "data": data,
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


@_atomic
def review_edge(session, edge_id, data, user):
    identity = _identity(session, "edge", edge_id, True)
    actor = _actor(session, user, True)
    if actor.id == identity.author_id:
        _error(403, "GRAPH_SELF_REVIEW", "A revisão exige outra pessoa administradora.")
    version = _latest(session, "edge", identity)
    _expected(version, data.expected_revision)
    if _publication(session, "edge", version):
        _error(409, "GRAPH_ALREADY_PUBLISHED", "Esta versão já está publicada.")
    draft = _parse(GraphEdgeDraft, version.payload)
    if data.decision in {EdgeReviewDecision.ACCEPT, EdgeReviewDecision.DISPUTE}:
        resolver.validate_edge(session, draft, version, identity.author_id, identity.is_example)
    now = datetime.now(UTC)
    review = EdgeReview(
        edge_id=draft.id,
        edge_revision=version.version_number,
        content_hash=version.content_hash,
        reviewer_id=actor.id,
        reviewed_at=now,
        **data.model_dump(exclude={"expected_revision"}),
    )
    assessment = assess_edge(draft, assessed_at=now, review=review)
    expected_status = {
        EdgeReviewDecision.ACCEPT: EdgeStatus.REVIEW_MATCHES,
        EdgeReviewDecision.DISPUTE: EdgeStatus.DISPUTE_MATCHES,
    }
    checks = all(
        (
            data.references_checked,
            data.scopes_checked,
            data.counterpoints_checked,
            data.limitations_checked,
        )
    )
    if data.decision in expected_status and (
        assessment.status != expected_status[data.decision] or not checks
    ):
        _error(
            422,
            "GRAPH_NOT_READY",
            "Complete a relação e confira o checklist antes de aceitar ou registrar disputa.",
        )
    previous = _review(session, version)
    session.add(
        GraphEdgeReview(
            id=uuid4(),
            edge_version_id=version.id,
            review_number=(previous.review_number if previous else 0) + 1,
            reviewer_id=actor.id,
            content_hash=version.content_hash,
            decision=data.decision.value,
            payload=review.model_dump(mode="json"),
            created_at=now,
        )
    )
    record(
        session,
        actor,
        "GRAPH_EDGE",
        identity.id,
        "REVIEW",
        data.rationale,
        {"revision": version.version_number, "decision": data.decision.value},
    )
    session.flush()
    response = _view(session, "edge", identity, version)
    session.commit()
    return response


@_atomic
def publish_edge(session, edge_id, data, user):
    identity = _identity(session, "edge", edge_id, True)
    actor = _actor(session, user)
    _author(actor, identity)
    version = _latest(session, "edge", identity)
    _expected(version, data.expected_revision)
    if _publication(session, "edge", version):
        _error(409, "GRAPH_ALREADY_PUBLISHED", "Esta versão já está publicada.")
    draft = _parse(GraphEdgeDraft, version.payload)
    resolver.validate_edge(session, draft, version, identity.author_id, identity.is_example)
    review = _review(session, version)
    if review is None:
        _error(
            422, "GRAPH_REVIEW_REQUIRED", "Esta relação precisa de revisão humana correspondente."
        )
    reviewer = session.scalar(
        select(User)
        .where(User.id == review.reviewer_id)
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    if (
        reviewer is None
        or not reviewer.is_active
        or reviewer.role != "ADMIN"
        or reviewer.id == identity.author_id
    ):
        _error(422, "GRAPH_REVIEW_REQUIRED", "Esta relação precisa de revisão humana autorizada.")
    now = datetime.now(UTC)
    status = assess_edge(draft, assessed_at=now, review=_edge_review(review)).status
    accepted = {
        "REVIEWED": (EdgeStatus.REVIEW_MATCHES, "ACCEPT"),
        "DISPUTED": (EdgeStatus.DISPUTE_MATCHES, "DISPUTE"),
    }
    target_status, target_decision = accepted[data.publication_state]
    if (
        status != target_status
        or review.decision != target_decision
        or not all(
            review.payload[key]
            for key in (
                "references_checked",
                "scopes_checked",
                "counterpoints_checked",
                "limitations_checked",
            )
        )
    ):
        _error(
            422,
            "GRAPH_REVIEW_REQUIRED",
            "O estado de publicação deve corresponder à última revisão completa.",
        )
    publication = GraphEdgePublication(
        id=uuid4(),
        edge_version_id=version.id,
        review_id=review.id,
        content_hash=version.content_hash,
        published_by=actor.id,
        published_at=now,
        created_at=now,
        published_state=data.publication_state,
    )
    session.add(publication)
    record(
        session,
        actor,
        "GRAPH_EDGE",
        identity.id,
        "PUBLISH",
        "Publicação explícita de relação revisada.",
        {"revision": version.version_number, "state": data.publication_state},
    )
    session.flush()
    response = _view(session, "edge", identity, version, publication)
    session.commit()
    return response


@_atomic
def publish_graph(session, graph_id, data, user):
    identity = _identity(session, "graph", graph_id, True)
    actor = _actor(session, user)
    _author(actor, identity)
    version = _latest(session, "graph", identity)
    _expected(version, data.expected_revision)
    if _publication(session, "graph", version):
        _error(409, "GRAPH_ALREADY_PUBLISHED", "Esta versão já está publicada.")
    if not version.edge_version_ids:
        _error(
            422,
            "GRAPH_PUBLIC_RELATIONS_REQUIRED",
            "Publique pelo menos uma relação revisada antes do conjunto.",
        )
    # Historical publications retain their original review and source snapshots.
    for key in version.node_version_ids:
        node_version, node_identity = resolver.node_version(session, key, identity.author_id)
        if _publication(session, "node", node_version, real_only=not identity.is_example) is None:
            _error(
                422,
                "GRAPH_PRIVATE_NODE",
                "Todos os nós precisam participar de uma relação já publicada.",
            )
        if node_identity.is_example and not identity.is_example:
            _error(422, "EXAMPLE_GRAPH_REQUIRED", "O conjunto real não pode incorporar exemplos.")
        resolver.validate_node_reuse(
            session, _parse(NodeRecord, node_version.payload), identity.is_example
        )
    for key in version.edge_version_ids:
        edge_version, edge_identity = resolver.edge_version(session, key, identity.author_id)
        if _publication(session, "edge", edge_version) is None:
            _error(
                422,
                "GRAPH_PUBLIC_RELATIONS_REQUIRED",
                "Todas as relações selecionadas precisam estar publicadas.",
            )
        if edge_identity.is_example and not identity.is_example:
            _error(422, "EXAMPLE_GRAPH_REQUIRED", "O conjunto real não pode incorporar exemplos.")
        resolver.validate_edge_reuse(
            session,
            _parse(GraphEdgeDraft, edge_version.payload),
            edge_identity.author_id,
            identity.is_example,
        )
    now = datetime.now(UTC)
    publication = GraphCollectionPublication(
        id=uuid4(),
        graph_version_id=version.id,
        content_hash=version.content_hash,
        published_by=actor.id,
        published_at=now,
        created_at=now,
    )
    session.add(publication)
    record(
        session,
        actor,
        "GRAPH",
        identity.id,
        "PUBLISH",
        "Publicação de conjunto de relações previamente revisadas e publicadas.",
        {"revision": version.version_number},
    )
    session.flush()
    response = _view(session, "graph", identity, version, publication)
    session.commit()
    return response


def create_node(session, data, user):
    return _create(session, "node", data, user)


def update_node(session, identity_id, data, user):
    return _update(session, "node", identity_id, data, user)


def draft_node(session, identity_id, user):
    return _draft(session, "node", identity_id, user)


def public_node(session, identity_id, revision=None):
    return _public(session, "node", identity_id, revision)


def list_nodes(session, page, page_size, q=None, *, user=None):
    return _list(session, "node", page, page_size, q, user=user)


def node_history(session, identity_id):
    return _history(session, "node", identity_id)


def create_edge(session, data, user):
    return _create(session, "edge", data, user)


def update_edge(session, identity_id, data, user):
    return _update(session, "edge", identity_id, data, user)


def draft_edge(session, identity_id, user):
    return _draft(session, "edge", identity_id, user)


def public_edge(session, identity_id, revision=None):
    return _public(session, "edge", identity_id, revision)


def list_edges(session, page, page_size, q=None, *, user=None, queue=False):
    return _list(session, "edge", page, page_size, q, user=user, queue=queue)


def edge_history(session, identity_id):
    return _history(session, "edge", identity_id)


def create_graph(session, data, user):
    return _create(session, "graph", data, user)


def update_graph(session, identity_id, data, user):
    return _update(session, "graph", identity_id, data, user)


def draft_graph(session, identity_id, user):
    return _draft(session, "graph", identity_id, user)


def public_graph(session, identity_id, revision=None):
    return _public(session, "graph", identity_id, revision)


def list_graphs(session, page, page_size, q=None, *, user=None):
    return _list(session, "graph", page, page_size, q, user=user)


def graph_history(session, identity_id):
    return _history(session, "graph", identity_id)
