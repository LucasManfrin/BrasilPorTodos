"""Trusted context lifecycle; persisted records are never rewritten."""

import json
from datetime import UTC, datetime
from functools import wraps
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.core.config import get_settings
from app.core.errors import DomainError
from app.modules.admin.models import record
from app.modules.auth.dependencies import require_owner
from app.modules.contexts import resolver
from app.modules.contexts.context import (
    ContextDraft,
    ContextStatus,
    ReviewDecision,
    assess_context,
    fingerprint,
)
from app.modules.contexts.context import ContextReview as ContextReviewRecord
from app.modules.contexts.models import Context, ContextPublication, ContextReview, ContextVersion
from app.modules.contexts.schemas import (
    ContextCreate,
    ContextPublishInput,
    ContextReviewInput,
    ContextUpdate,
)
from app.modules.users.models import User


def _atomic(method):
    @wraps(method)
    def wrapped(session, *args, **kwargs):
        try:
            return method(session, *args, **kwargs)
        except Exception:
            session.rollback()
            raise

    return wrapped


def _actor(session: Session, user: User, *, admin=False):
    actor = session.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    if actor is None or not actor.is_active:
        raise DomainError(401, "INVALID_SESSION", "Sessão inválida ou expirada.")
    if admin and actor.role != "ADMIN":
        raise DomainError(403, "FORBIDDEN", "Esta ação exige revisão administrativa.")
    return actor


def _require_author(actor, context):
    if actor.id != context.author_id:
        raise DomainError(403, "FORBIDDEN", "Só o autor pode alterar ou publicar este contexto.")


def _visible(stmt):
    if get_settings().environment != "development":
        stmt = stmt.where(Context.is_example.is_(False))
    return stmt


def _context(session, context_id, *, lock=False):
    stmt = _visible(select(Context).where(Context.id == context_id))
    if lock:
        stmt = stmt.with_for_update()
    context = session.scalar(stmt)
    if context is None:
        raise DomainError(404, "CONTEXT_NOT_FOUND", "Contexto não encontrado.")
    return context


def _latest(session, context):
    version = session.scalar(
        select(ContextVersion)
        .where(ContextVersion.context_id == context.id)
        .order_by(ContextVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise DomainError(404, "CONTEXT_NOT_FOUND", "Contexto não encontrado.")
    return version


def _expected(version, expected):
    if version.version_number != expected:
        raise DomainError(
            409,
            "CONTEXT_REVISION_CONFLICT",
            "O contexto mudou. Reabra a versão antes de continuar.",
        )


def _review(session, version):
    return session.scalar(
        select(ContextReview)
        .where(ContextReview.context_version_id == version.id)
        .order_by(ContextReview.review_number.desc())
        .limit(1)
    )


def _draft(version):
    return ContextDraft.model_validate_json(json.dumps(version.payload))


def _review_record(review):
    return ContextReviewRecord.model_validate_json(json.dumps(review.payload)) if review else None


def context_view(session, context, version, *, publication=None):
    if publication is None:
        publication = session.scalar(
            select(ContextPublication).where(ContextPublication.context_version_id == version.id)
        )
    # A public version uses the review frozen at publication, not a subsequent queue entry.
    review = (
        session.get(ContextReview, publication.review_id)
        if publication
        else _review(session, version)
    )
    draft = _draft(version)
    assessment = assess_context(draft, assessed_at=datetime.now(UTC), review=_review_record(review))
    return {
        "id": context.id,
        "revision": version.version_number,
        "version_id": version.id,
        "content_hash": version.content_hash,
        "content": draft.model_dump(mode="json"),
        "assessment": assessment.model_dump(mode="json"),
        "review": review.payload if review else None,
        "published_at": publication.published_at if publication else None,
        "is_example": context.is_example,
    }


def _append_version(session, context, content, actor, number):
    now = datetime.now(UTC)
    fields = resolver.resolve_content(session, content, context.author_id, now)
    try:
        draft = ContextDraft.model_validate_json(
            json.dumps(
                {
                    "id": str(context.id),
                    "author_id": str(context.author_id),
                    "revision": number,
                    "updated_at": now.isoformat(),
                    **fields,
                }
            )
        )
    except ValidationError as error:
        raise DomainError(
            422, "CONTEXT_INVALID_CONTENT", "Confira as referências e a estrutura do contexto."
        ) from error
    version = ContextVersion(
        id=uuid4(),
        context_id=context.id,
        version_number=number,
        created_by=actor.id,
        created_at=now,
        content_hash=fingerprint(draft),
        payload=draft.model_dump(mode="json"),
    )
    session.add(version)
    session.flush()
    return version


@_atomic
def create_context(session: Session, data: ContextCreate, user: User):
    actor = _actor(session, user)
    example = resolver.is_example_content(session, data.content, actor.id)
    if example and get_settings().environment != "development":
        raise DomainError(404, "CONTEXT_NOT_FOUND", "Contexto não encontrado.")
    context = Context(id=uuid4(), author_id=actor.id, is_example=example)
    session.add(context)
    session.flush()
    version = _append_version(session, context, data.content, actor, 1)
    response = context_view(session, context, version)
    session.commit()
    return response


@_atomic
def update_context(session: Session, context_id: UUID, data: ContextUpdate, user: User):
    context = _context(session, context_id, lock=True)
    actor = _actor(session, user)
    _require_author(actor, context)
    latest = _latest(session, context)
    _expected(latest, data.expected_revision)
    if (
        resolver.is_example_content(session, data.content, context.author_id)
        and not context.is_example
    ):
        raise DomainError(
            422,
            "EXAMPLE_CONTEXT_REQUIRED",
            "Use um novo contexto de exemplo para referências fictícias.",
        )
    version = _append_version(session, context, data.content, actor, latest.version_number + 1)
    response = context_view(session, context, version)
    session.commit()
    return response


def draft_view(session: Session, context_id: UUID, user: User):
    actor = _actor(session, user)
    context = _context(session, context_id)
    require_owner(actor, context.author_id)
    return context_view(session, context, _latest(session, context))


@_atomic
def review_context(session: Session, context_id: UUID, data: ContextReviewInput, user: User):
    context = _context(session, context_id, lock=True)
    actor = _actor(session, user, admin=True)
    if actor.id == context.author_id:
        raise DomainError(
            403, "CONTEXT_SELF_REVIEW", "A revisão exige outra pessoa administradora."
        )
    version = _latest(session, context)
    _expected(version, data.expected_revision)
    if session.scalar(
        select(ContextPublication.id).where(ContextPublication.context_version_id == version.id)
    ):
        raise DomainError(409, "CONTEXT_ALREADY_PUBLISHED", "Esta versão já está publicada.")
    draft = _draft(version)
    resolver.validate_references(session, draft, context.author_id, is_example=context.is_example)
    now = datetime.now(UTC)
    review_record = ContextReviewRecord(
        context_id=context.id,
        context_revision=version.version_number,
        content_hash=version.content_hash,
        reviewer_id=actor.id,
        reviewed_at=now,
        **data.model_dump(exclude={"expected_revision"}),
    )
    assessment = assess_context(draft, assessed_at=now, review=review_record)
    if data.decision == ReviewDecision.ACCEPT and assessment.status != ContextStatus.REVIEW_MATCHES:
        raise DomainError(
            422, "CONTEXT_NOT_READY", "Complete o contexto e confira o checklist antes de aceitar."
        )
    previous = _review(session, version)
    review = ContextReview(
        id=uuid4(),
        context_version_id=version.id,
        review_number=(previous.review_number if previous else 0) + 1,
        reviewer_id=actor.id,
        content_hash=version.content_hash,
        decision=data.decision.value,
        payload=review_record.model_dump(mode="json"),
        created_at=now,
    )
    session.add(review)
    record(
        session,
        actor,
        "CONTEXT",
        context.id,
        "REVIEW",
        data.rationale,
        {"revision": version.version_number, "decision": data.decision.value},
    )
    response = context_view(session, context, version)
    session.commit()
    return response


@_atomic
def publish_context(session: Session, context_id: UUID, data: ContextPublishInput, user: User):
    context = _context(session, context_id, lock=True)
    actor = _actor(session, user)
    _require_author(actor, context)
    version = _latest(session, context)
    _expected(version, data.expected_revision)
    if session.scalar(
        select(ContextPublication.id).where(ContextPublication.context_version_id == version.id)
    ):
        raise DomainError(409, "CONTEXT_ALREADY_PUBLISHED", "Esta versão já está publicada.")
    draft = _draft(version)
    review = _review(session, version)
    now = datetime.now(UTC)
    if review is None:
        raise DomainError(
            422, "CONTEXT_REVIEW_REQUIRED", "Esta versão precisa de revisão humana correspondente."
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
        or reviewer.id == context.author_id
    ):
        raise DomainError(
            422, "CONTEXT_REVIEW_REQUIRED", "Esta versão precisa de revisão humana autorizada."
        )
    resolver.validate_references(
        session, draft, context.author_id, for_publication=True, is_example=context.is_example
    )
    if (
        assess_context(draft, assessed_at=now, review=_review_record(review)).status
        != ContextStatus.REVIEW_MATCHES
    ):
        raise DomainError(
            422, "CONTEXT_REVIEW_REQUIRED", "Esta versão precisa de revisão humana correspondente."
        )
    publication = ContextPublication(
        id=uuid4(),
        context_version_id=version.id,
        review_id=review.id,
        content_hash=version.content_hash,
        published_by=actor.id,
        published_at=now,
        created_at=now,
    )
    session.add(publication)
    record(
        session,
        actor,
        "CONTEXT",
        context.id,
        "PUBLISH",
        "Publicação de conteúdo revisado.",
        {"revision": version.version_number},
    )
    response = context_view(session, context, version, publication=publication)
    session.commit()
    return response


def public_context(session: Session, context_id: UUID, revision: int | None = None):
    context = _context(session, context_id)
    stmt = (
        select(ContextVersion, ContextPublication)
        .join(ContextPublication, ContextPublication.context_version_id == ContextVersion.id)
        .where(ContextVersion.context_id == context.id)
    )
    if revision is not None:
        stmt = stmt.where(ContextVersion.version_number == revision)
    row = session.execute(stmt.order_by(ContextVersion.version_number.desc()).limit(1)).first()
    if row is None:
        raise DomainError(404, "CONTEXT_NOT_FOUND", "Contexto não encontrado.")
    return context_view(session, context, row[0], publication=row[1])


def history(session: Session, context_id: UUID):
    context = _context(session, context_id)
    rows = session.execute(
        select(ContextVersion, ContextPublication)
        .join(ContextPublication, ContextPublication.context_version_id == ContextVersion.id)
        .where(ContextVersion.context_id == context.id)
        .order_by(ContextVersion.version_number.desc())
    ).all()
    if not rows:
        raise DomainError(404, "CONTEXT_NOT_FOUND", "Contexto não encontrado.")
    return {
        "data": [
            {
                "revision": version.version_number,
                "content_hash": version.content_hash,
                "published_at": pub.published_at,
                "title": version.payload["title"],
            }
            for version, pub in rows
        ]
    }


def list_contexts(
    session: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    *,
    user: User | None = None,
    queue=False,
    indicator_code: str | None = None,
):
    stmt = _visible(select(Context))
    if user is not None:
        actor = _actor(session, user, admin=queue)
        if not queue:
            stmt = stmt.where(Context.author_id == actor.id)
    elif queue:
        raise DomainError(403, "FORBIDDEN", "Esta ação exige revisão administrativa.")
    latest_id = (
        select(ContextVersion.id)
        .where(ContextVersion.context_id == Context.id)
        .order_by(ContextVersion.version_number.desc())
        .limit(1)
        .correlate(Context)
        .scalar_subquery()
    )
    if queue:
        stmt = stmt.where(
            Context.author_id != actor.id,
            ~select(ContextPublication.id)
            .where(ContextPublication.context_version_id == latest_id)
            .exists(),
        )
    # Both matching and rendering use the latest visible publication, never a draft
    # or an older published title/primary indicator.
    published_version = aliased(ContextVersion)
    public_latest_id = (
        select(published_version.id)
        .join(
            ContextPublication,
            ContextPublication.context_version_id == published_version.id,
        )
        .where(published_version.context_id == Context.id)
        .order_by(published_version.version_number.desc())
        .limit(1)
        .correlate(Context)
        .scalar_subquery()
    )
    selected_id = latest_id if user is not None else public_latest_id
    if user is None:
        stmt = stmt.where(public_latest_id.is_not(None))
    if q or indicator_code:
        matched_version = aliased(ContextVersion)
        match = select(matched_version.id).where(matched_version.id == selected_id)
        if q:
            match = match.where(matched_version.payload["title"].astext.ilike(f"%{q}%"))
        if indicator_code:
            anchors = func.jsonb_array_elements(
                matched_version.payload["observations"]
            ).table_valued("value")
            # JSONB contains immutable strings; compare without casting client text.
            primary = (
                select(anchors.c.value)
                .where(
                    anchors.c.value.op("->>")("observation_id")
                    == matched_version.payload["primary_observation_id"].astext,
                    anchors.c.value.op("->>")("indicator_code") == indicator_code,
                )
                .correlate(matched_version)
                .exists()
            )
            match = match.where(primary)
        stmt = stmt.where(match.correlate(Context).exists())
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    # Select the version/publication alongside the identity in the same statement.
    # A publication or edit committed during rendering cannot move these targets.
    displayed_version = aliased(ContextVersion)
    displayed_publication = aliased(ContextPublication)
    selected = (
        stmt.add_columns(displayed_version, displayed_publication)
        .join_from(Context, displayed_version, displayed_version.id == selected_id)
        .outerjoin_from(
            displayed_version,
            displayed_publication,
            displayed_publication.context_version_id == displayed_version.id,
        )
    )
    rows = session.execute(
        selected.order_by(Context.created_at.desc(), Context.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    data = [
        context_view(session, context, version, publication=publication)
        for context, version, publication in rows
    ]
    return {"data": data, "pagination": {"page": page, "page_size": page_size, "total": total}}


def review_queue(session: Session, user: User, page: int, page_size: int):
    return list_contexts(session, page, page_size, user=user, queue=True)


def reference_choices(session: Session, user: User, code: str, page: int, page_size: int):
    actor = _actor(session, user)
    return resolver.reference_choices(session, actor.id, code, page, page_size)
