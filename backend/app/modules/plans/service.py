from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.modules.admin.models import record
from app.modules.auth.dependencies import require_owner
from app.modules.indicators.baseline import current as current_baseline
from app.modules.plans.models import Plan, PlanPolicy, PlanVersion
from app.modules.plans.scenario import (
    clear_review,
    domain_scenario,
    review_input_hash,
    scenario_view,
)
from app.modules.plans.schemas import PlanInput, PlanUpdate
from app.modules.policies.models import FinancialImpact, Policy, PolicyFunding, PolicyVersion
from app.modules.policies.service import make_slug
from app.modules.simulations.models import Simulation
from app.modules.simulations.service import execution_view, run_simulation
from app.modules.users.models import User
from app.simulation.compatibility import METADATA_FIELDS

FIELDS = ("title", "summary", "vision", "start_year", "end_year", "change_summary")


def owned(session: Session, plan_id: UUID, user: User):
    plan = session.scalar(select(Plan).where(Plan.id == plan_id).with_for_update())
    if plan is None:
        raise DomainError(404, "PLAN_NOT_FOUND", "Plano não encontrado.")
    require_owner(user, plan.author_id)
    if plan.status == "ARCHIVED":
        raise DomainError(409, "CONTENT_ARCHIVED", "Este plano está arquivado.")
    return plan


def validate_items(session: Session, items):
    versions = []
    for item in items:
        version = session.get(PolicyVersion, item.policy_version_id)
        if version is None or version.status != "PUBLISHED":
            raise DomainError(
                422,
                "PUBLISHED_POLICY_REQUIRED",
                "O plano aceita apenas versões publicadas de propostas.",
            )
        versions.append(version)
    if len({version.policy_id for version in versions}) != len(versions):
        raise DomainError(
            422, "DUPLICATE_POLICY", "Inclua uma única versão de cada proposta no plano."
        )
    return versions


def view(session: Session, plan: Plan, version: PlanVersion):
    author = session.get(User, plan.author_id)
    items = session.scalars(
        select(PlanPolicy)
        .where(PlanPolicy.plan_version_id == version.id)
        .order_by(PlanPolicy.position)
    ).all()
    proposals = []
    for item in items:
        policy = session.get(PolicyVersion, item.policy_version_id)
        proposals.append(
            {
                "policy_version_id": str(policy.id),
                "estimate_status": policy.financial_impact_status,
                "baseline_id": (policy.baseline_snapshot or {}).get("id"),
                "impacts": [
                    {
                        "year": row.year,
                        "impact_type": row.impact_type,
                        "amount": str(row.amount),
                        "description": row.description,
                        **{field: getattr(row, field) for field in METADATA_FIELDS},
                    }
                    for row in session.scalars(
                        select(FinancialImpact).where(
                            FinancialImpact.policy_version_id == policy.id
                        )
                    )
                ],
                "unfunded": bool(
                    session.scalar(
                        select(PolicyFunding.id)
                        .where(
                            PolicyFunding.policy_version_id == policy.id,
                            PolicyFunding.funding_type == "UNFUNDED",
                        )
                        .limit(1)
                    )
                ),
                "policy_id": str(policy.policy_id),
                "slug": session.get(Policy, policy.policy_id).slug,
                "version_number": policy.version_number,
                "title": policy.title,
                "position": item.position,
                "is_enabled": item.is_enabled,
            }
        )
    execution = session.get(Simulation, version.simulation_id) if version.simulation_id else None
    return {
        "id": str(plan.id),
        "is_example": plan.is_example,
        "slug": plan.slug,
        "status": plan.status,
        "archive_reason": plan.archive_reason,
        "author": {"id": str(author.id), "name": author.name, "username": author.username},
        "version": {
            "id": str(version.id),
            "baseline_snapshot": version.baseline_snapshot,
            "fiscal_scenario": scenario_view(session, version),
            "version_number": version.version_number,
            "status": version.status,
            **{field: getattr(version, field) for field in FIELDS},
            "created_at": version.created_at.isoformat(),
            "published_at": version.published_at.isoformat() if version.published_at else None,
            "policies": proposals,
            "simulation": execution_view(session, execution) if execution else None,
        },
    }


def write(session: Session, version: PlanVersion, data, partial=False):
    previous_scenario = deepcopy(version.fiscal_scenario)
    previous_hash = review_input_hash(session, version)
    fields = data.model_fields_set if partial else set(PlanInput.model_fields)
    if not partial or data.refresh_baseline:
        version.baseline_snapshot = current_baseline(session)
    versions = validate_items(session, data.policies) if "policies" in fields else []
    start = data.start_year if "start_year" in fields else version.start_year
    end = data.end_year if "end_year" in fields else version.end_year
    if start > end:
        raise DomainError(422, "INVALID_PERIOD", "O período do plano é inválido.")
    for field in FIELDS:
        if field in fields:
            setattr(version, field, getattr(data, field))
    if "fiscal_scenario" in fields:
        version.fiscal_scenario = (
            data.fiscal_scenario.model_dump(mode="json") if data.fiscal_scenario else None
        )
    version.simulation_id = None
    if "policies" in fields:
        session.execute(delete(PlanPolicy).where(PlanPolicy.plan_version_id == version.id))
        for position, (item, policy) in enumerate(zip(data.policies, versions, strict=True)):
            session.add(
                PlanPolicy(
                    plan_version_id=version.id,
                    policy_version_id=policy.id,
                    position=position,
                    is_enabled=item.is_enabled,
                )
            )

    session.flush()
    if version.fiscal_scenario is not None:
        current_hash = review_input_hash(session, version)
        if (
            previous_scenario is not None
            and previous_hash == current_hash
            and not data.refresh_baseline
        ):
            version.fiscal_scenario = previous_scenario
        else:
            version.fiscal_scenario = clear_review(version.fiscal_scenario)


def ensure_draft(session: Session, plan: Plan, user: User):
    version = session.scalar(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id, PlanVersion.status == "DRAFT")
        .with_for_update()
    )
    if version:
        return version
    previous = session.get(PlanVersion, plan.current_version_id)
    number = (
        session.scalar(
            select(func.max(PlanVersion.version_number)).where(PlanVersion.plan_id == plan.id)
        )
        or 0
    )
    version = PlanVersion(
        plan_id=plan.id,
        created_by=user.id,
        version_number=number + 1,
        baseline_snapshot=current_baseline(session),
        fiscal_scenario=clear_review(previous.fiscal_scenario),
        **{field: getattr(previous, field) for field in FIELDS},
    )
    session.add(version)
    session.flush()
    for item in session.scalars(
        select(PlanPolicy).where(PlanPolicy.plan_version_id == previous.id)
    ):
        session.add(
            PlanPolicy(
                plan_version_id=version.id,
                policy_version_id=item.policy_version_id,
                position=item.position,
                is_enabled=item.is_enabled,
            )
        )
    session.flush()
    return version


def create(session: Session, data: PlanInput, user: User):
    validate_items(session, data.policies)
    plan = Plan(
        author_id=user.id,
        slug=make_slug(data.title, "plano"),
        is_example=any(
            session.get(Policy, v.policy_id).is_example
            for v in validate_items(session, data.policies)
        ),
    )
    session.add(plan)
    session.flush()
    version = PlanVersion(
        plan_id=plan.id,
        created_by=user.id,
        version_number=1,
        start_year=data.start_year,
        end_year=data.end_year,
    )
    session.add(version)
    session.flush()
    write(session, version, data)
    session.commit()
    return view(session, plan, version)


def update(session: Session, plan_id: UUID, data: PlanUpdate, user: User):
    plan = owned(session, plan_id, user)
    if "policies" in data.model_fields_set:
        validate_items(session, data.policies)
    version = ensure_draft(session, plan, user)
    write(session, version, data, partial=True)
    session.commit()
    return view(session, plan, version)


def draft(session: Session, plan_id: UUID, user: User, create=False):
    plan = owned(session, plan_id, user)
    if create:
        version = ensure_draft(session, plan, user)
        session.commit()
    else:
        version = session.scalar(
            select(PlanVersion).where(PlanVersion.plan_id == plan.id, PlanVersion.status == "DRAFT")
        )
    if version is None:
        raise DomainError(404, "DRAFT_NOT_FOUND", "Não há rascunho deste plano.")
    return view(session, plan, version)


def confirm_fiscal_scenario(session: Session, plan_id: UUID, expected_input_hash: str, user: User):
    plan = owned(session, plan_id, user)
    version = session.scalar(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id, PlanVersion.status == "DRAFT")
        .with_for_update()
    )
    if version is None:
        raise DomainError(409, "DRAFT_REQUIRED", "Confirme o cenário em um rascunho do plano.")
    current_hash = review_input_hash(session, version)
    if current_hash is None:
        raise DomainError(422, "SCENARIO_INCOMPLETE", "Este plano não tem cenário futuro ativo.")
    if current_hash != expected_input_hash:
        raise DomainError(
            409,
            "SCENARIO_CHANGED",
            "As premissas ou propostas mudaram. Revise o cenário salvo antes de confirmar.",
        )
    domain_scenario(session, version)
    if not scenario_view(session, version)["excludes_plan_impacts"]:
        version.fiscal_scenario = {
            **clear_review(version.fiscal_scenario),
            "excludes_plan_impacts": True,
            "reviewed_input_hash": current_hash,
            "reviewed_at": datetime.now(UTC).isoformat(),
        }
        version.simulation_id = None
    session.commit()
    return view(session, plan, version)


def simulate_plan(session: Session, plan_id: UUID, user: User):
    plan = owned(session, plan_id, user)
    version = session.scalar(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id, PlanVersion.status == "DRAFT")
        .with_for_update()
    )
    if version is None:
        version = session.get(PlanVersion, plan.current_version_id)
    execution = run_simulation(session, version)
    if version.status == "DRAFT":
        version.simulation_id = execution.id
    session.commit()
    return execution_view(session, execution)


def publish(session: Session, plan_id: UUID, user: User):
    plan = owned(session, plan_id, user)
    version = session.scalar(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id, PlanVersion.status == "DRAFT")
        .with_for_update()
    )
    if version is None:
        raise DomainError(409, "DRAFT_REQUIRED", "Crie um rascunho antes de publicar.")
    if not all(getattr(version, field).strip() for field in ("title", "summary", "vision")):
        raise DomainError(422, "INCOMPLETE_PLAN", "Preencha título, resumo e visão do plano.")
    if not session.scalar(
        select(PlanPolicy.id)
        .where(PlanPolicy.plan_version_id == version.id, PlanPolicy.is_enabled.is_(True))
        .limit(1)
    ):
        raise DomainError(
            422, "POLICY_REQUIRED", "Inclua ao menos uma proposta habilitada antes de publicar."
        )
    execution = run_simulation(session, version)
    version.simulation_id = execution.id
    version.status = "PUBLISHED"
    version.published_at = datetime.now(UTC)
    session.flush()
    plan.status = "PUBLISHED"
    plan.current_version_id = version.id
    plan.published_at = plan.published_at or version.published_at
    session.commit()
    return view(session, plan, version)


def public(session: Session, slug: str, number: int | None = None):
    plan = session.scalar(
        select(Plan).where(Plan.slug == slug, Plan.current_version_id.is_not(None))
    )
    if plan is None:
        raise DomainError(404, "PLAN_NOT_FOUND", "Plano não encontrado.")
    if plan.is_example and get_settings().environment != "development":
        raise DomainError(404, "CONTENT_NOT_FOUND", "Conteúdo não encontrado.")
    version = (
        session.get(PlanVersion, plan.current_version_id)
        if number is None
        else session.scalar(
            select(PlanVersion).where(
                PlanVersion.plan_id == plan.id,
                PlanVersion.version_number == number,
                PlanVersion.status == "PUBLISHED",
            )
        )
    )
    if version is None:
        raise DomainError(404, "VERSION_NOT_FOUND", "Versão publicada não encontrada.")
    return view(session, plan, version)


def list_plans(
    session: Session,
    page: int,
    size: int,
    q: str | None = None,
    user: User | None = None,
    author: str | None = None,
    year: int | None = None,
):
    statement = (
        select(Plan).where(Plan.author_id == user.id)
        if user
        else select(Plan)
        .join(PlanVersion, PlanVersion.id == Plan.current_version_id)
        .where(Plan.status == "PUBLISHED")
    )
    if q and not user:
        statement = statement.where(PlanVersion.title.ilike(f"%{q}%"))
    if not user:
        if author:
            statement = statement.join(User, User.id == Plan.author_id).where(
                User.username == author.lower()
            )
        if year is not None:
            statement = statement.where(
                PlanVersion.start_year <= year, PlanVersion.end_year >= year
            )
    if not user and get_settings().environment != "development":
        statement = statement.where(Plan.is_example.is_(False))
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = session.scalars(
        statement.order_by(Plan.created_at.desc(), Plan.id).offset((page - 1) * size).limit(size)
    ).all()
    data = []
    for plan in rows:
        version = (
            session.scalar(
                select(PlanVersion)
                .where(PlanVersion.plan_id == plan.id)
                .order_by(PlanVersion.version_number.desc())
                .limit(1)
            )
            if user
            else session.get(PlanVersion, plan.current_version_id)
        )
        data.append(view(session, plan, version))
    return {"data": data, "pagination": {"page": page, "page_size": size, "total": total}}


def history(session: Session, slug: str):
    public_view = public(session, slug)
    plan_id = UUID(public_view["id"])
    rows = session.scalars(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan_id, PlanVersion.status == "PUBLISHED")
        .order_by(PlanVersion.version_number)
    ).all()
    return {
        "data": [
            {
                "id": str(row.id),
                "version_number": row.version_number,
                "title": row.title,
                "published_at": row.published_at,
            }
            for row in rows
        ]
    }


def archive(session: Session, plan_id: UUID, user: User, reason: str):
    plan = owned(session, plan_id, user)
    if plan.current_version_id is None:
        raise DomainError(
            409, "PUBLICATION_REQUIRED", "Somente planos publicados podem ser arquivados."
        )
    plan.status = "ARCHIVED"
    plan.archive_reason = reason
    plan.archived_at = datetime.now(UTC)
    record(session, user, "plan", plan.id, "ARCHIVE", reason)
    session.commit()
    return view(session, plan, session.get(PlanVersion, plan.current_version_id))
