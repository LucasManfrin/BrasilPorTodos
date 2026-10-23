from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.modules.indicators.models import (
    FiscalSpendingCohort,
    GeneralGovernmentCohort,
    IndicatorValue,
)
from app.modules.policies.models import Policy, PolicySource, PolicyVersion
from app.modules.sources.models import Source
from app.modules.sources.schemas import SourceInput, SourceResponse
from app.modules.users.models import User


def public_sources():
    cited = exists(
        select(PolicySource.id)
        .join(PolicyVersion, PolicyVersion.id == PolicySource.policy_version_id)
        .join(Policy, Policy.id == PolicyVersion.policy_id)
        .where(
            PolicySource.source_id == Source.id,
            PolicyVersion.status == "PUBLISHED",
            True if get_settings().environment == "development" else Policy.is_example.is_(False),
        )
    )
    observed = exists(select(IndicatorValue.id).where(IndicatorValue.source_id == Source.id))
    spending = exists(
        select(FiscalSpendingCohort.id).where(
            FiscalSpendingCohort.source_id == Source.id,
            FiscalSpendingCohort.created_by == Source.created_by,
            Source.source_type == "OFFICIAL",
            Source.is_example.is_(False),
            Source.title == FiscalSpendingCohort.source_snapshot["title"].astext,
            Source.institution == FiscalSpendingCohort.source_snapshot["institution"].astext,
            Source.url == FiscalSpendingCohort.source_snapshot["url"].astext,
            Source.description == FiscalSpendingCohort.source_snapshot["description"].astext,
        )
    )
    general = exists(
        select(GeneralGovernmentCohort.id).where(
            GeneralGovernmentCohort.source_id == Source.id,
            GeneralGovernmentCohort.created_by == Source.created_by,
            Source.source_type == "OFFICIAL",
            Source.is_example.is_(False),
            Source.title == GeneralGovernmentCohort.source_snapshot["title"].astext,
            Source.institution == GeneralGovernmentCohort.source_snapshot["institution"].astext,
            Source.url == GeneralGovernmentCohort.source_snapshot["url"].astext,
            Source.description == GeneralGovernmentCohort.source_snapshot["description"].astext,
        )
    )
    statement = select(Source).where(or_(cited, observed, spending, general))
    if get_settings().environment != "development":
        statement = statement.where(Source.is_example.is_(False))
    return statement


def list_sources(
    session: Session,
    page: int,
    page_size: int,
    query: str | None,
    user: User | None = None,
    institution: str | None = None,
    source_type: str | None = None,
):
    statement = select(Source).where(Source.created_by == user.id) if user else public_sources()
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(Source.title.ilike(pattern), Source.institution.ilike(pattern))
        )
    if institution:
        statement = statement.where(Source.institution == institution)
    if source_type:
        statement = statement.where(Source.source_type == source_type)
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = session.scalars(
        statement.order_by(Source.created_at.desc(), Source.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "data": [source_view(session, row) for row in rows],
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


def source_view(session, row):
    data = SourceResponse.model_validate(row).model_dump(mode="json")
    data["usage_count"] = session.scalar(
        select(func.count(func.distinct(PolicyVersion.policy_id)))
        .select_from(PolicySource)
        .join(PolicyVersion, PolicySource.policy_version_id == PolicyVersion.id)
        .join(Policy, Policy.id == PolicyVersion.policy_id)
        .where(
            PolicySource.source_id == row.id,
            PolicyVersion.status == "PUBLISHED",
            True if get_settings().environment == "development" else Policy.is_example.is_(False),
        )
    )
    value = session.scalar(
        select(IndicatorValue)
        .where(IndicatorValue.source_id == row.id)
        .order_by(IndicatorValue.retrieved_at.desc())
        .limit(1)
    )
    if value:
        data["license"] = value.provenance.get("license")
        data["license_url"] = value.provenance.get("license_url")
    # A verified linked cohort supplies the marker; equal URLs never do.
    spending = session.scalar(
        select(FiscalSpendingCohort)
        .where(
            FiscalSpendingCohort.source_id == row.id,
            FiscalSpendingCohort.created_by == row.created_by,
        )
        .order_by(FiscalSpendingCohort.retrieved_at.desc(), FiscalSpendingCohort.revision.desc())
        .limit(1)
    )
    if spending:
        from app.modules.indicators.fiscal_spending import (
            assemble,
            cohort_view,
        )
        from app.modules.indicators.fiscal_spending import (
            source_view as spending_source_view,
        )

        verified = assemble(cohort_view(spending), spending.year, spending_source_view(row))
        if verified["status"] == "AVAILABLE":
            data["collection_code"] = "federal-spending"
            data["license"] = verified["source"]["license"]
            data["license_url"] = verified["source"]["license_url"]
    general = session.scalar(
        select(GeneralGovernmentCohort)
        .where(
            GeneralGovernmentCohort.source_id == row.id,
            GeneralGovernmentCohort.created_by == row.created_by,
        )
        .order_by(
            GeneralGovernmentCohort.retrieved_at.desc(), GeneralGovernmentCohort.revision.desc()
        )
        .limit(1)
    )
    if general:
        from app.modules.indicators.general_government import assemble, cohort_view
        from app.modules.indicators.general_government import source_view as general_source_view

        verified = assemble(cohort_view(general), general.year, general_source_view(row))
        if verified["status"] == "AVAILABLE":
            data["collection_code"] = "general-government"
            data["license"] = verified["source"]["license"]
            data["license_url"] = verified["source"]["license_url"]
    return data


def create_source(session: Session, data: SourceInput, user: User):
    values = data.model_dump()
    values["url"] = str(data.url)
    source = Source(**values, created_by=user.id)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def readable_source(session: Session, source_id: UUID, user: User | None = None):
    source = session.scalar(public_sources().where(Source.id == source_id))
    if source is None and user is not None:
        candidate = session.get(Source, source_id)
        if candidate and (candidate.created_by == user.id or user.role == "ADMIN"):
            source = candidate
    if source is None:
        raise DomainError(404, "SOURCE_NOT_FOUND", "Fonte não encontrada.")
    return source
