from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.admin.models import record
from app.modules.ideas.models import Idea, IdeaReport, IdeaSuggestion
from app.modules.ideas.schemas import IdeaInput, IdeaUpdate
from app.modules.ideas.settings import IdeaSettings
from app.modules.policies import service as policies
from app.modules.policies.models import Policy
from app.modules.policies.schemas import PolicyInput, ProposalDetails
from app.modules.sources.schemas import SourceResponse
from app.modules.sources.service import readable_source
from app.modules.users.models import User


def configured_limit(name, default):
    return getattr(IdeaSettings(), name.lower(), default)


def daily_limit(session, user, model, field, name, default):
    # Serialize all allowance checks for this account across processes/concurrent requests.
    session.scalar(select(User).where(User.id == user.id).with_for_update())
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    count = session.scalar(
        select(func.count()).select_from(model).where(field == user.id, model.created_at >= today)
    )
    if count >= configured_limit(name, default):
        raise DomainError(429, "DAILY_LIMIT", "Limite diário atingido. Tente novamente amanhã.")


def owned(session, idea_id, user, *, mutable=False):
    row = session.scalar(select(Idea).where(Idea.id == idea_id).with_for_update())
    if row is None or row.author_id != user.id:
        raise DomainError(404, "IDEA_NOT_FOUND", "Ideia não encontrada.")
    if mutable and row.status in {"PROMOTED", "ARCHIVED"}:
        raise DomainError(409, "IDEA_CLOSED", "Esta ideia já foi concluída ou arquivada.")
    return row


def shared(session, idea_id):
    row = session.scalar(select(Idea).where(Idea.id == idea_id, Idea.status == "SHARED"))
    if row is None:
        raise DomainError(404, "IDEA_NOT_FOUND", "Ideia compartilhada não encontrada.")
    return row


def checklist(data: IdeaInput):
    content = data.content
    checks = [
        ("title", "Título e uma frase", bool(data.title and data.summary)),
        ("problem", "Qual é o problema", bool(content.problem.strip())),
        ("proposal", "O que você quer mudar", bool(content.proposal.strip())),
        ("beneficiaries", "Quem ganha", bool(data.beneficiaries.strip())),
        ("adversely_affected", "Quem pode perder", bool(data.adversely_affected.strip())),
        ("risks", "O que pode dar errado", bool(data.risks.strip())),
        (
            "period",
            "Quando a medida vale",
            content.implementation_start is not None and content.implementation_end is not None,
        ),
        (
            "funding",
            "De onde sai o dinheiro",
            bool(content.fundings)
            and all(item.funding_type != "UNFUNDED" for item in content.fundings),
        ),
        ("sources", "Fontes e como foram usadas", bool(content.sources)),
        (
            "impact",
            "Estimativa fiscal ou justificativa de não aplicação",
            (content.financial_impact_status == "ESTIMATED" and bool(content.impacts))
            or (
                content.financial_impact_status == "NOT_APPLICABLE"
                and bool((content.impact_justification or "").strip())
                and not content.impacts
            ),
        ),
    ]
    return [{"key": key, "label": label, "complete": complete} for key, label, complete in checks]


def input_view(row):
    return IdeaInput(
        title=row.title,
        summary=row.summary,
        content=row.content,
        beneficiaries=row.beneficiaries,
        adversely_affected=row.adversely_affected,
        risks=row.risks,
        assisted_fields=row.assisted_fields,
    )


def view(session, row):
    author = session.get(User, row.author_id)
    data = input_view(row)
    return {
        **data.model_dump(mode="json"),
        "id": str(row.id),
        "status": row.status,
        "author": {"name": author.name, "username": author.username},
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "shared_at": row.shared_at.isoformat() if row.shared_at else None,
        "promoted_policy_id": str(row.promoted_policy_id) if row.promoted_policy_id else None,
        "origin_attribution": row.origin_attribution,
        "checklist": checklist(data),
    }


def validate_sources(session, content, user):
    for item in content.sources:
        readable_source(session, item.source_id, user)


def create(session: Session, data: IdeaInput, user):
    daily_limit(session, user, Idea, Idea.author_id, "IDEAS_DAILY_LIMIT", 10)
    validate_sources(session, data.content, user)
    row = Idea(author_id=user.id, **data.model_dump(mode="json"))
    session.add(row)
    session.commit()
    return view(session, row)


def update(session, idea_id, data: IdeaUpdate, user):
    row = owned(session, idea_id, user, mutable=True)
    values = input_view(row).model_dump(mode="json")
    for field in data.model_fields_set:
        value = getattr(data, field)
        if value is None:
            raise DomainError(422, "INVALID_IDEA", "Os campos enviados não podem ser nulos.")
        values[field] = value.model_dump(mode="json") if isinstance(value, PolicyInput) else value
    try:
        validated = IdeaInput.model_validate(values)
    except ValidationError as exc:
        raise DomainError(422, "INVALID_IDEA", "Verifique os campos da ideia.") from exc
    validate_sources(session, validated.content, user)
    for key, value in validated.model_dump(mode="json").items():
        setattr(row, key, value)
    # Editing always withdraws the previous public photograph; sharing is a new explicit action.
    row.status, row.shared_snapshot, row.shared_at = "PRIVATE", None, None
    session.commit()
    return view(session, row)


def share(session, idea_id, user):
    row = owned(session, idea_id, user, mutable=True)
    if row.status == "SHARED":
        return row.shared_snapshot
    timestamp = datetime.now(UTC)
    snapshot = view(session, row)
    snapshot.update(status="SHARED", shared_at=timestamp.isoformat())
    snapshot["source_snapshots"] = [
        SourceResponse.model_validate(readable_source(session, item.source_id, user)).model_dump(
            mode="json"
        )
        for item in input_view(row).content.sources
    ]
    row.status, row.shared_at = "SHARED", timestamp
    row.shared_snapshot = snapshot
    session.commit()
    return row.shared_snapshot


def unshare(session, idea_id, user):
    row = owned(session, idea_id, user, mutable=True)
    row.status, row.shared_snapshot, row.shared_at = "PRIVATE", None, None
    session.commit()
    return view(session, row)


def listing(session, page, size, user=None):
    query = (
        select(Idea).where(Idea.author_id == user.id)
        if user
        else select(Idea).where(Idea.status == "SHARED")
    )
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.scalars(
        query.order_by(Idea.created_at.desc(), Idea.id).offset((page - 1) * size).limit(size)
    ).all()
    return {
        "data": [view(session, row) if user else row.shared_snapshot for row in rows],
        "pagination": {"page": page, "page_size": size, "total": total},
    }


def duplicate(session, idea_id, user):
    original = shared(session, idea_id)
    daily_limit(session, user, Idea, Idea.author_id, "IDEAS_DAILY_LIMIT", 10)
    snapshot = original.shared_snapshot
    data = IdeaInput.model_validate({key: snapshot[key] for key in IdeaInput.model_fields})
    # Shared private-source photographs remain attributed, but cannot become another user's
    # editable source IDs. The copy keeps the references in attribution for manual registration.
    data.content.sources = []
    row = Idea(
        author_id=user.id,
        **data.model_dump(mode="json"),
        origin_idea_id=original.id,
        origin_attribution={
            "idea_id": str(original.id),
            "title": snapshot["title"],
            "author": snapshot["author"],
            "source_snapshots": snapshot.get("source_snapshots", []),
        },
    )
    session.add(row)
    session.commit()
    return view(session, row)


def promote(session, idea_id, user):
    row = owned(session, idea_id, user)
    if row.status == "PROMOTED":
        policy = session.get(Policy, row.promoted_policy_id)
        return policies.public_policy(session, policy.slug, row.promoted_policy_version_number)
    if row.status == "ARCHIVED":
        raise DomainError(409, "IDEA_CLOSED", "Esta ideia foi arquivada.")
    data = input_view(row)
    if not all(item["complete"] for item in checklist(data)):
        raise DomainError(422, "INCOMPLETE_IDEA", "Complete o checklist antes de publicar.")
    content = data.content.model_copy(update={"title": row.title, "summary": row.summary})
    content.proposal_details = ProposalDetails.model_validate(
        {
            "beneficiaries": row.beneficiaries,
            "adversely_affected": row.adversely_affected,
            "risks": row.risks,
            "assisted_fields": row.assisted_fields,
            "idea_id": str(row.id),
            "origin_attribution": row.origin_attribution,
        }
    )
    with session.begin_nested():
        draft = policies.create_policy(session, content, user, commit=False)
        result = policies.publish_policy(session, draft.id, user, commit=False)
        row.promoted_policy_id = result.id
        row.promoted_policy_version_number = result.version.version_number
        row.status, row.shared_snapshot, row.shared_at = "PROMOTED", None, None
    session.commit()
    return result


def suggest(session, idea_id, data, user):
    shared(session, idea_id)
    daily_limit(
        session, user, IdeaSuggestion, IdeaSuggestion.author_id, "IDEAS_SUGGESTIONS_DAILY_LIMIT", 20
    )
    row = IdeaSuggestion(idea_id=idea_id, author_id=user.id, url=str(data.url), note=data.note)
    session.add(row)
    session.commit()
    return {"id": str(row.id), "status": row.status}


def suggestions(session, idea_id, user):
    owned(session, idea_id, user)
    rows = session.scalars(
        select(IdeaSuggestion)
        .where(IdeaSuggestion.idea_id == idea_id)
        .order_by(IdeaSuggestion.created_at.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": str(row.id),
            "url": row.url,
            "note": row.note,
            "status": row.status,
            "author": session.get(User, row.author_id).username,
        }
        for row in rows
    ]


def resolve_suggestion(session, idea_id, suggestion_id, action, user):
    owned(session, idea_id, user, mutable=True)
    row = session.scalar(
        select(IdeaSuggestion)
        .where(IdeaSuggestion.id == suggestion_id, IdeaSuggestion.idea_id == idea_id)
        .with_for_update()
    )
    if row is None:
        raise DomainError(404, "SUGGESTION_NOT_FOUND", "Sugestão não encontrada.")
    row.status = "ACCEPTED" if action == "ACCEPT" else "DISMISSED"
    session.commit()
    return {"id": str(row.id), "status": row.status}


def report(session, idea_id, data, user):
    idea = shared(session, idea_id)
    daily_limit(session, user, IdeaReport, IdeaReport.reporter_id, "IDEAS_REPORTS_DAILY_LIMIT", 10)
    existing = session.scalar(
        select(IdeaReport).where(
            IdeaReport.idea_id == idea_id,
            IdeaReport.reporter_id == user.id,
            IdeaReport.status == "PENDING",
        )
    )
    if existing:
        raise DomainError(409, "REPORT_EXISTS", "Sua denúncia já está em análise.")
    row = IdeaReport(
        idea_id=idea_id, reporter_id=user.id, reason=data.reason, idea_snapshot=idea.shared_snapshot
    )
    session.add(row)
    session.commit()
    return {"status": "PENDING"}


def admin(user):
    if user.role != "ADMIN":
        raise DomainError(403, "ADMIN_REQUIRED", "Acesso restrito à administração.")


def moderation(session, user):
    admin(user)
    rows = session.scalars(
        select(IdeaReport)
        .where(IdeaReport.status == "PENDING")
        .order_by(IdeaReport.created_at)
        .limit(100)
    ).all()
    return [
        {
            "id": str(row.id),
            "idea_id": str(row.idea_id),
            "reason": row.reason,
            "idea_snapshot": row.idea_snapshot,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def resolve_report(session, report_id, data, user):
    admin(user)
    report_row = session.get(IdeaReport, report_id)
    if report_row is None:
        raise DomainError(404, "REPORT_NOT_FOUND", "Denúncia não encontrada.")
    # Same order as edits/promotions: idea before dependent report lock.
    idea = session.scalar(select(Idea).where(Idea.id == report_row.idea_id).with_for_update())
    row = session.scalar(select(IdeaReport).where(IdeaReport.id == report_id).with_for_update())
    if row.status != "PENDING":
        raise DomainError(409, "REPORT_RESOLVED", "Denúncia já foi analisada.")
    row.status = "ARCHIVED" if data.action == "ARCHIVE" else "DISMISSED"
    row.resolved_by, row.resolution_note = user.id, data.note
    if data.action == "ARCHIVE" and idea.status != "PROMOTED":
        idea.status, idea.shared_snapshot, idea.shared_at = "ARCHIVED", None, None
    record(session, user, "idea", idea.id, data.action, data.note, {"report_id": str(row.id)})
    session.commit()
    return {"status": row.status}
