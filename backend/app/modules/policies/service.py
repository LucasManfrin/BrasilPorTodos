import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Integer, case, delete, exists, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.modules.admin.models import record
from app.modules.auth.dependencies import require_owner
from app.modules.indicators.baseline import current as current_baseline
from app.modules.policies.models import (
    FinancialImpact,
    Policy,
    PolicyFunding,
    PolicySource,
    PolicyVersion,
)
from app.modules.policies.schemas import (
    EvidenceResponse,
    FundingResponse,
    ImpactResponse,
    PolicyInput,
    PolicyResponse,
    PolicyUpdate,
    VersionResponse,
)
from app.modules.sources.models import Source
from app.modules.sources.schemas import SourceResponse
from app.modules.sources.service import readable_source
from app.modules.users.models import User
from app.simulation.compatibility import METADATA_FIELDS

VERSION_FIELDS = (
    "proposal_details",
    "title",
    "summary",
    "problem",
    "proposal",
    "category",
    "implementation_start",
    "implementation_end",
    "financial_impact_status",
    "impact_justification",
    "change_summary",
)


def make_slug(title: str, prefix: str) -> str:
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:140] or prefix
    return f"{value}-{uuid4().hex[:12]}"


def owned_policy(session: Session, policy_id: UUID, user: User) -> Policy:
    policy = session.scalar(select(Policy).where(Policy.id == policy_id).with_for_update())
    if policy is None:
        raise DomainError(404, "POLICY_NOT_FOUND", "Proposta não encontrada.")
    require_owner(user, policy.author_id)
    if policy.status == "ARCHIVED":
        raise DomainError(409, "CONTENT_ARCHIVED", "Esta proposta está arquivada.")
    return policy


def policy_view(session: Session, policy: Policy, version: PolicyVersion):
    author = session.get(User, policy.author_id)
    impacts = session.scalars(
        select(FinancialImpact)
        .where(FinancialImpact.policy_version_id == version.id)
        .order_by(FinancialImpact.year, FinancialImpact.id)
    ).all()
    fundings = session.scalars(
        select(PolicyFunding)
        .where(PolicyFunding.policy_version_id == version.id)
        .order_by(PolicyFunding.id)
    ).all()
    links = session.scalars(
        select(PolicySource)
        .where(PolicySource.policy_version_id == version.id)
        .order_by(PolicySource.id)
    ).all()
    evidence = []
    for link in links:
        source = SourceResponse.model_validate(
            link.source_snapshot if link.source_snapshot else session.get(Source, link.source_id)
        )
        evidence.append(EvidenceResponse(source=source, usage_description=link.usage_description))
    content = {field: getattr(version, field) for field in VERSION_FIELDS}
    content.update(
        baseline_snapshot=version.baseline_snapshot,
        id=version.id,
        version_number=version.version_number,
        status=version.status,
        created_at=version.created_at,
        published_at=version.published_at,
        impacts=[ImpactResponse.model_validate(row) for row in impacts],
        fundings=[FundingResponse.model_validate(row) for row in fundings],
        sources=evidence,
    )
    complete_version = (version.proposal_details or {}).get("level") == "COMPLETE"
    return PolicyResponse(
        solidity={
            "level": "COMPLETE" if complete_version else "LEGACY",
            "score": (
                int(bool(links))
                + int(bool(fundings) and all(row.funding_type != "UNFUNDED" for row in fundings))
            )
            if complete_version
            else None,
            "has_sources": bool(links),
            "funding_defined": bool(fundings)
            and all(row.funding_type != "UNFUNDED" for row in fundings),
        },
        id=policy.id,
        is_example=policy.is_example,
        slug=policy.slug,
        status=policy.status,
        archive_reason=policy.archive_reason,
        author={"id": str(author.id), "name": author.name, "username": author.username},
        version=VersionResponse(**content),
    )


def write_fields(
    session: Session, version: PolicyVersion, data: PolicyInput, user: User, partial=False
):
    fields = data.model_fields_set if partial else set(PolicyInput.model_fields)
    if not partial or data.refresh_baseline:
        version.baseline_snapshot = current_baseline(session)
    readable = (
        {link.source_id: readable_source(session, link.source_id, user) for link in data.sources}
        if "sources" in fields
        else {}
    )
    start = (
        data.implementation_start
        if "implementation_start" in fields
        else version.implementation_start
    )
    end = data.implementation_end if "implementation_end" in fields else version.implementation_end
    if start is not None and end is not None and start > end:
        raise DomainError(422, "INVALID_PERIOD", "O período de implementação é inválido.")
    for field in VERSION_FIELDS:
        if field in fields:
            value = getattr(data, field)
            if field == "proposal_details":
                policy = session.get(Policy, version.policy_id)
                if policy.accessible_creation and value is None:
                    raise DomainError(
                        422, "DETAILS_REQUIRED", "Preserve os detalhes da proposta completa."
                    )
                if value is not None:
                    policy.accessible_creation = True
                    value = value.model_dump(mode="json")
                    value["level"] = "COMPLETE"
                    previous = version.proposal_details or {}
                    for key in ("idea_id", "origin_attribution"):
                        if previous.get(key) is not None:
                            value[key] = previous[key]
                    value["assisted_fields"] = sorted(
                        set(value.get("assisted_fields", []))
                        | set(previous.get("assisted_fields", []))
                    )
            setattr(version, field, value)
    for field, model in (
        ("impacts", FinancialImpact),
        ("fundings", PolicyFunding),
        ("sources", PolicySource),
    ):
        if field not in fields:
            continue
        session.execute(delete(model).where(model.policy_version_id == version.id))
        for item in getattr(data, field):
            values = item.model_dump()
            if field == "sources":
                values["source_snapshot"] = None
                assert item.source_id in readable
            session.add(model(policy_version_id=version.id, **values))


def ensure_draft(session: Session, policy: Policy, user: User):
    draft = session.scalar(
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == policy.id, PolicyVersion.status == "DRAFT")
        .with_for_update()
    )
    if draft:
        return draft
    previous = session.get(PolicyVersion, policy.current_version_id)
    number = (
        session.scalar(
            select(func.max(PolicyVersion.version_number)).where(
                PolicyVersion.policy_id == policy.id
            )
        )
        or 0
    )
    draft = PolicyVersion(
        policy_id=policy.id,
        created_by=user.id,
        version_number=number + 1,
        baseline_snapshot=current_baseline(session),
        **{field: getattr(previous, field) for field in VERSION_FIELDS},
    )
    session.add(draft)
    session.flush()
    for model, fields in (
        (FinancialImpact, ("year", "impact_type", "amount", "description", *METADATA_FIELDS)),
        (PolicyFunding, ("funding_type", "amount", "year", "description")),
        (PolicySource, ("source_id", "usage_description")),
    ):
        for row in session.scalars(select(model).where(model.policy_version_id == previous.id)):
            session.add(
                model(
                    policy_version_id=draft.id, **{field: getattr(row, field) for field in fields}
                )
            )
    session.flush()
    return draft


def create_policy(session: Session, data: PolicyInput, user: User, *, commit=True):
    # Validate source visibility before persisting any draft content.
    for link in data.sources:
        readable_source(session, link.source_id, user)
    policy = Policy(
        accessible_creation=data.proposal_details is not None,
        author_id=user.id,
        slug=make_slug(data.title, "proposta"),
        is_example=any(
            readable_source(session, link.source_id, user).is_example for link in data.sources
        ),
    )
    session.add(policy)
    session.flush()
    draft = PolicyVersion(policy_id=policy.id, created_by=user.id, version_number=1)
    session.add(draft)
    session.flush()
    write_fields(session, draft, data, user)
    if commit:
        session.commit()
    else:
        session.flush()
    return policy_view(session, policy, draft)


def update_policy(session: Session, policy_id: UUID, data: PolicyUpdate, user: User):
    policy = owned_policy(session, policy_id, user)
    draft = ensure_draft(session, policy, user)
    write_fields(session, draft, data, user, partial=True)
    session.commit()
    return policy_view(session, policy, draft)


def draft_view(session: Session, policy_id: UUID, user: User, create=False):
    policy = owned_policy(session, policy_id, user)
    if create:
        version = ensure_draft(session, policy, user)
        session.commit()
    else:
        version = session.scalar(
            select(PolicyVersion).where(
                PolicyVersion.policy_id == policy.id, PolicyVersion.status == "DRAFT"
            )
        )
        if version is None:
            raise DomainError(404, "DRAFT_NOT_FOUND", "Não há rascunho desta proposta.")
    return policy_view(session, policy, version)


def publish_policy(session: Session, policy_id: UUID, user: User, *, commit=True):
    policy = owned_policy(session, policy_id, user)
    version = session.scalar(
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == policy.id, PolicyVersion.status == "DRAFT")
        .with_for_update()
    )
    if version is None:
        raise DomainError(409, "DRAFT_REQUIRED", "Crie um rascunho antes de publicar.")
    if (
        not all(
            getattr(version, field).strip() for field in ("title", "summary", "problem", "proposal")
        )
        or version.implementation_start is None
        or version.implementation_end is None
    ):
        raise DomainError(
            422, "INCOMPLETE_POLICY", "Preencha título, resumo, problema, solução e período."
        )
    if policy.accessible_creation:
        # Server-owned identity survives removal of fields in a subsequent draft. Existing
        # legacy publications retain their original publication rules and their old snapshots.
        from app.modules.ideas.schemas import IdeaInput
        from app.modules.ideas.service import checklist

        details = version.proposal_details or {}
        response = policy_view(session, policy, version)
        complete = IdeaInput(
            title=version.title,
            summary=version.summary,
            content=PolicyInput(
                problem=version.problem,
                proposal=version.proposal,
                implementation_start=version.implementation_start,
                implementation_end=version.implementation_end,
                financial_impact_status=version.financial_impact_status,
                impact_justification=version.impact_justification,
                impacts=[item.model_dump(exclude={"id"}) for item in response.version.impacts],
                fundings=[item.model_dump(exclude={"id"}) for item in response.version.fundings],
                sources=[
                    {"source_id": item.source.id, "usage_description": item.usage_description}
                    for item in response.version.sources
                ],
            ),
            beneficiaries=details.get("beneficiaries", ""),
            adversely_affected=details.get("adversely_affected", ""),
            risks=details.get("risks", ""),
        )
        if details.get("level") != "COMPLETE" or not all(
            item["complete"] for item in checklist(complete)
        ):
            raise DomainError(
                422, "INCOMPLETE_POLICY", "Complete o checklist antes de publicar esta nova versão."
            )
    impacts = session.scalars(
        select(FinancialImpact).where(FinancialImpact.policy_version_id == version.id)
    ).all()
    if (version.financial_impact_status == "ESTIMATED") != bool(impacts):
        raise DomainError(
            422, "INVALID_ESTIMATE", "Informe impactos anuais somente para uma proposta estimada."
        )
    if (
        version.financial_impact_status == "NOT_APPLICABLE"
        and not (version.impact_justification or "").strip()
    ):
        raise DomainError(
            422, "JUSTIFICATION_REQUIRED", "Justifique por que o impacto fiscal não se aplica."
        )
    if (
        any(
            row.amount > 0 and row.impact_type in ("NEW_EXPENSE", "REVENUE_REDUCTION")
            for row in impacts
        )
        and session.scalar(
            select(PolicyFunding.id).where(PolicyFunding.policy_version_id == version.id).limit(1)
        )
        is None
    ):
        raise DomainError(
            422,
            "FUNDING_REQUIRED",
            "Informe o financiamento, inclusive se ainda não estiver definido.",
        )
    links = session.scalars(
        select(PolicySource).where(PolicySource.policy_version_id == version.id)
    ).all()
    if not links:
        raise DomainError(
            422, "SOURCE_REQUIRED", "Vincule uma fonte e explique seu uso antes de publicar."
        )
    for link in links:
        source = readable_source(session, link.source_id, user)
        link.source_snapshot = SourceResponse.model_validate(source).model_dump(mode="json")
    session.flush()
    version.status = "PUBLISHED"
    version.published_at = datetime.now(UTC)
    session.flush()
    policy.status = "PUBLISHED"
    policy.current_version_id = version.id
    policy.published_at = policy.published_at or version.published_at
    if commit:
        session.commit()
    else:
        session.flush()
    return policy_view(session, policy, version)


def public_policy(session: Session, slug: str, version_number: int | None = None):
    policy = session.scalar(
        select(Policy).where(Policy.slug == slug, Policy.current_version_id.is_not(None))
    )
    if policy is None:
        raise DomainError(404, "POLICY_NOT_FOUND", "Proposta não encontrada.")
    if policy.is_example and get_settings().environment != "development":
        raise DomainError(404, "CONTENT_NOT_FOUND", "Conteúdo não encontrado.")
    if version_number is None:
        version = session.get(PolicyVersion, policy.current_version_id)
    else:
        version = session.scalar(
            select(PolicyVersion).where(
                PolicyVersion.policy_id == policy.id,
                PolicyVersion.version_number == version_number,
                PolicyVersion.status == "PUBLISHED",
            )
        )
    if version is None:
        raise DomainError(404, "VERSION_NOT_FOUND", "Versão publicada não encontrada.")
    return policy_view(session, policy, version)


def list_policies(
    session: Session,
    page: int,
    size: int,
    query: str | None = None,
    category: str | None = None,
    user: User | None = None,
    author: str | None = None,
    year: int | None = None,
):
    statement = select(Policy)
    if user:
        statement = statement.where(Policy.author_id == user.id)
    else:
        statement = statement.join(
            PolicyVersion, PolicyVersion.id == Policy.current_version_id
        ).where(Policy.status == "PUBLISHED")
        if query:
            statement = statement.where(PolicyVersion.title.ilike(f"%{query}%"))
        if category:
            statement = statement.where(PolicyVersion.category == category)
        if author:
            statement = statement.join(User, User.id == Policy.author_id).where(
                User.username == author.lower()
            )
        if year is not None:
            statement = statement.where(
                PolicyVersion.implementation_start <= year,
                PolicyVersion.implementation_end >= year,
            )
    if not user and get_settings().environment != "development":
        statement = statement.where(Policy.is_example.is_(False))
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    if user:
        ordering = [Policy.created_at.desc(), Policy.id]
    else:
        has_sources = exists(
            select(PolicySource.id).where(PolicySource.policy_version_id == PolicyVersion.id)
        ).correlate(PolicyVersion)
        has_funding = exists(
            select(PolicyFunding.id).where(PolicyFunding.policy_version_id == PolicyVersion.id)
        ).correlate(PolicyVersion)
        undefined_funding = exists(
            select(PolicyFunding.id).where(
                PolicyFunding.policy_version_id == PolicyVersion.id,
                PolicyFunding.funding_type == "UNFUNDED",
            )
        ).correlate(PolicyVersion)
        score = has_sources.cast(Integer) + (has_funding & ~undefined_funding).cast(Integer)
        complete_version = func.coalesce(
            PolicyVersion.proposal_details["level"].astext == "COMPLETE", False
        )
        ordering = [
            complete_version.desc(),
            case((complete_version, score), else_=0).desc(),
            Policy.created_at.desc(),
            Policy.id,
        ]
    rows = session.scalars(
        statement.order_by(*ordering).offset((page - 1) * size).limit(size)
    ).all()
    result = []
    for policy in rows:
        version = (
            session.scalar(
                select(PolicyVersion)
                .where(PolicyVersion.policy_id == policy.id)
                .order_by(PolicyVersion.version_number.desc())
                .limit(1)
            )
            if user
            else session.get(PolicyVersion, policy.current_version_id)
        )
        result.append(policy_view(session, policy, version))
    return {"data": result, "pagination": {"page": page, "page_size": size, "total": total}}


def history(session: Session, slug: str):
    public_policy(session, slug)
    policy = session.scalar(
        select(Policy).where(Policy.slug == slug, Policy.current_version_id.is_not(None))
    )
    if policy is None:
        raise DomainError(404, "POLICY_NOT_FOUND", "Proposta não encontrada.")
    rows = session.scalars(
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == policy.id, PolicyVersion.status == "PUBLISHED")
        .order_by(PolicyVersion.version_number)
    ).all()
    return {
        "data": [
            {
                "id": str(row.id),
                "version_number": row.version_number,
                "title": row.title,
                "published_at": row.published_at,
                "change_summary": row.change_summary,
            }
            for row in rows
        ]
    }


def archive(session: Session, policy_id: UUID, user: User, reason: str):
    policy = owned_policy(session, policy_id, user)
    if policy.current_version_id is None:
        raise DomainError(
            409, "PUBLICATION_REQUIRED", "Somente propostas publicadas podem ser arquivadas."
        )
    policy.status = "ARCHIVED"
    policy.archive_reason = reason
    policy.archived_at = datetime.now(UTC)
    record(session, user, "policy", policy.id, "ARCHIVE", reason)
    session.commit()
    return policy_view(session, policy, session.get(PolicyVersion, policy.current_version_id))


def delete_draft(session: Session, policy_id: UUID, user: User):
    policy = owned_policy(session, policy_id, user)
    draft = session.scalar(
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == policy.id, PolicyVersion.status == "DRAFT")
        .with_for_update()
    )
    if draft is None:
        raise DomainError(409, "DRAFT_REQUIRED", "Não há rascunho para remover.")
    for model in (FinancialImpact, PolicyFunding, PolicySource):
        session.execute(delete(model).where(model.policy_version_id == draft.id))
    session.delete(draft)
    session.flush()
    if policy.current_version_id is None:
        session.delete(policy)
    session.commit()
    return {"data": {"status": "deleted"}}
