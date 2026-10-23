from datetime import UTC, datetime

from sqlalchemy import func, select

from app.core.errors import DomainError
from app.modules.admin.models import record
from app.modules.indicators.auxiliary import AUXILIARY_CODES
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.sources.models import Source
from app.modules.sources.schemas import SourceResponse

FIELDS = (
    "id",
    "code",
    "name",
    "description",
    "category",
    "unit",
    "frequency",
    "scope",
    "methodology",
    "base_year",
    "is_active",
)


def observation_view(session, value):
    return {
        "id": str(value.id),
        "reference_date": value.reference_date.isoformat(),
        "value": str(value.value),
        "retrieved_at": value.retrieved_at.isoformat(),
        "revision": value.revision,
        "revision_reason": value.revision_reason,
        "provenance": value.provenance,
        "source": SourceResponse.model_validate(session.get(Source, value.source_id)).model_dump(
            mode="json"
        ),
    }


def series_view(session, indicator_id):
    rows = session.scalars(
        select(IndicatorValue)
        .where(IndicatorValue.indicator_id == indicator_id)
        .order_by(IndicatorValue.reference_date.desc(), IndicatorValue.revision.desc())
        .limit(2000)
    )
    unique = {}
    for row in rows:
        if row.reference_date not in unique:
            unique[row.reference_date] = {
                "reference_date": row.reference_date.isoformat(),
                "value": str(row.value),
                "revision": row.revision,
            }
        if len(unique) == 365:
            break
    return list(reversed(list(unique.values())))


def view(session, indicator):
    latest = session.scalar(
        select(IndicatorValue)
        .where(IndicatorValue.indicator_id == indicator.id)
        .order_by(IndicatorValue.reference_date.desc(), IndicatorValue.revision.desc())
        .limit(1)
    )
    return {
        **{
            field: str(indicator.id) if field == "id" else getattr(indicator, field)
            for field in FIELDS
        },
        "latest": observation_view(session, latest) if latest else None,
        "series": series_view(session, indicator.id),
        "data_status": "AVAILABLE" if latest else "NO_DATA",
    }


def catalog(session, page, size, q=None, category=None, include_inactive=False):
    statement = select(Indicator)
    if not include_inactive:
        statement = statement.where(
            Indicator.is_active.is_(True), Indicator.code.not_in(AUXILIARY_CODES)
        )
    if q:
        statement = statement.where(Indicator.name.ilike(f"%{q}%"))
    if category:
        statement = statement.where(Indicator.category == category)
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = session.scalars(
        statement.order_by(Indicator.name, Indicator.id).offset((page - 1) * size).limit(size)
    )
    return {
        "data": [view(session, row) for row in rows],
        "pagination": {"page": page, "page_size": size, "total": total},
    }


def detail(session, code, page, size):
    indicator = session.scalar(
        select(Indicator).where(Indicator.code == code, Indicator.is_active.is_(True))
    )
    if indicator is None:
        raise DomainError(404, "INDICATOR_NOT_FOUND", "Indicador não encontrado.")
    statement = select(IndicatorValue).where(IndicatorValue.indicator_id == indicator.id)
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = session.scalars(
        statement.order_by(
            IndicatorValue.reference_date.desc(), IndicatorValue.revision.desc(), IndicatorValue.id
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    return {
        "data": {
            **view(session, indicator),
            "history": [observation_view(session, row) for row in rows],
        },
        "pagination": {"page": page, "page_size": size, "total": total},
    }


def save(session, data, actor, indicator_id=None, *, commit=True):
    row = (
        session.scalar(select(Indicator).where(Indicator.id == indicator_id).with_for_update())
        if indicator_id
        else None
    )
    if indicator_id and row is None:
        raise DomainError(404, "INDICATOR_NOT_FOUND", "Indicador não encontrado.")
    duplicate = session.scalar(select(Indicator).where(Indicator.code == data.code))
    if duplicate and duplicate.id != indicator_id:
        raise DomainError(409, "INDICATOR_CODE_TAKEN", "Código já cadastrado.")
    if row and session.scalar(
        select(IndicatorValue.id).where(IndicatorValue.indicator_id == row.id).limit(1)
    ):
        if any(
            getattr(row, field) != getattr(data, field)
            for field in ("code", "unit", "scope", "frequency", "base_year", "methodology")
        ):
            raise DomainError(
                409,
                "SERIES_DEFINITION_FROZEN",
                "Crie outro indicador para mudar a definição de uma série com dados.",
            )
    before = {field: getattr(row, field) for field in FIELDS if field != "id"} if row else None
    values = data.model_dump(exclude={"reason"})
    if row:
        for field, value in values.items():
            setattr(row, field, value)
    else:
        row = Indicator(**values)
        session.add(row)
    session.flush()
    record(
        session,
        actor,
        "indicator",
        row.id,
        "UPDATE" if indicator_id else "CREATE",
        data.reason,
        {"before": before, "after": values},
    )
    if commit:
        session.commit()
    return view(session, row)


def add_observation(session, indicator_id, data, actor, *, commit=True):
    indicator = session.scalar(
        select(Indicator).where(Indicator.id == indicator_id).with_for_update()
    )
    if indicator is None:
        raise DomainError(404, "INDICATOR_NOT_FOUND", "Indicador não encontrado.")
    if session.get(Source, data.source_id) is None:
        raise DomainError(422, "SOURCE_REQUIRED", "Cadastre a fonte antes de registrar o dado.")
    now = datetime.now(UTC)
    if data.reference_date > now.date() or data.retrieved_at > now:
        raise DomainError(
            422, "FUTURE_OBSERVATION", "Não registre observações ou coletas no futuro."
        )
    required = ("dataset_url", "license", "license_url", "method", "institution")
    if not all(data.provenance.get(key, " ").strip() for key in required):
        raise DomainError(
            422,
            "PROVENANCE_REQUIRED",
            "Informe instituição, conjunto, método e termos de reutilização.",
        )
    # A lock on the indicator serializes revision numbering for all of its sources.
    previous = session.scalar(
        select(IndicatorValue)
        .where(
            IndicatorValue.indicator_id == indicator.id,
            IndicatorValue.reference_date == data.reference_date,
        )
        .order_by(IndicatorValue.revision.desc())
        .limit(1)
    )
    if (
        previous
        and previous.source_id == data.source_id
        and previous.value == data.value
        and all(
            previous.provenance.get(key) == value
            for key, value in data.provenance.items()
            if key not in ("request_url", "retrieved_at")
        )
    ):
        return observation_view(session, previous)
    snapshot = {
        key: getattr(indicator, key)
        for key in ("unit", "scope", "methodology", "frequency", "base_year")
    }
    value = IndicatorValue(
        indicator_id=indicator.id,
        **data.model_dump(exclude={"provenance"}),
        revision=(previous.revision + 1 if previous else 1),
        provenance={**data.provenance, "definition": snapshot},
    )
    session.add(value)
    session.flush()
    record(
        session,
        actor,
        "indicator_value",
        value.id,
        "REVISE" if previous else "CREATE",
        data.revision_reason,
        {
            "indicator_id": str(indicator.id),
            "revision": value.revision,
            "reference_date": str(value.reference_date),
        },
    )
    if commit:
        session.commit()
    return observation_view(session, value)
