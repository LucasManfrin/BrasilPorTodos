"""Resolve stored references for the context author; never fetch contributed URLs.

Historical definitions come from immutable observation provenance, not a later
edit of the live indicator. Public views must read the published frozen payload.
"""

from calendar import monthrange
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import aliased

from app.core.config import get_settings
from app.core.errors import DomainError
from app.integrations.gdp import GDP_SERIES
from app.integrations.ibge import IBGE_SERIES
from app.integrations.treasury import TREASURY_SERIES
from app.modules.contexts.context import (
    ContextDraft,
    CounterpartAvailability,
    ObservationAnchor,
    SourceReference,
)
from app.modules.indicators.catalog import BCB_SERIES
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.sources.models import Source
from app.modules.sources.service import public_sources, source_view

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.modules.contexts.schemas import ContextContentInput

KNOWN_SERIES = {**BCB_SERIES, **IBGE_SERIES, **GDP_SERIES, **TREASURY_SERIES}
KNOWN_CODES = frozenset(KNOWN_SERIES)
ROLLING_QUARTER = frozenset(
    {
        "desocupacao",
        "renda-trabalho-real",
        "informalidade",
        "participacao-forca-trabalho",
    }
)
UNKNOWN_TERMS = "Termos não informados no catálogo; conferir antes de reutilizar."


def _missing():
    # Do not disclose whether a foreign private source exists.
    raise DomainError(
        404, "CONTEXT_REFERENCE_NOT_FOUND", "Referência não disponível para este contexto."
    )


def measurement_period(code: str, reference: date, frequency: str) -> tuple[date, date]:
    """Reviewed calendar semantics; publication date is never substituted for reference."""
    if code not in KNOWN_CODES:
        _missing()
    if frequency != KNOWN_SERIES[code]["frequency"]:
        raise DomainError(
            422, "CONTEXT_PERIOD_INVALID", "Frequência histórica incompatível com a série revisada."
        )
    if frequency == "DAILY":
        return reference, reference
    if reference.day != 1:
        raise DomainError(
            422, "CONTEXT_PERIOD_INVALID", "Período observado incompatível com a série."
        )
    if frequency == "QUARTERLY" and reference.month in {1, 4, 7, 10}:
        end_month = reference.month + 2
        return reference, date(reference.year, end_month, monthrange(reference.year, end_month)[1])
    if frequency == "MONTHLY":
        window = 3 if code in ROLLING_QUARTER else 12 if code == "ipca-12-meses" else 1
        month_index = reference.year * 12 + reference.month - window
        start = date(month_index // 12, month_index % 12 + 1, 1)
        return start, date(
            reference.year, reference.month, monthrange(reference.year, reference.month)[1]
        )
    raise DomainError(422, "CONTEXT_PERIOD_INVALID", "Período observado incompatível com a série.")


def _load(session: "Session", content: "ContextContentInput", author_id: UUID):
    observation_ids = tuple(content.observation_ids)
    source_ids = tuple(content.source_ids)
    if len(set(observation_ids)) != len(observation_ids) or len(set(source_ids)) != len(source_ids):
        raise DomainError(422, "CONTEXT_DUPLICATE_REFERENCE", "Referências não podem se repetir.")
    values = list(
        session.scalars(select(IndicatorValue).where(IndicatorValue.id.in_(observation_ids)))
    )
    if len(values) != len(observation_ids):
        _missing()
    all_sources = set(source_ids) | {row.source_id for row in values}
    if len(all_sources) > 64:
        raise DomainError(
            422, "CONTEXT_REFERENCE_LIMIT", "O contexto admite até 64 fontes distintas."
        )
    # Shared locks prevent metadata/owner changes until review/publication commits.
    sources = list(
        session.scalars(
            select(Source)
            .where(Source.id.in_(all_sources))
            .order_by(Source.id)
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
    )
    if len(sources) != len(all_sources):
        _missing()
    for source in sources:
        if source.is_example and get_settings().environment != "development":
            _missing()
        if (
            source.created_by != author_id
            and session.scalar(public_sources().where(Source.id == source.id)) is None
        ):
            _missing()
    indicator_ids = {row.indicator_id for row in values}
    counterpart_codes = {row.indicator_code for row in content.counterparts}
    indicators = list(
        session.scalars(
            select(Indicator)
            .where((Indicator.id.in_(indicator_ids)) | (Indicator.code.in_(counterpart_codes)))
            .order_by(Indicator.id)
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
    )
    by_indicator = {row.id: row for row in indicators}
    by_code = {row.code: row for row in indicators}
    if any(
        code not in KNOWN_CODES or code not in by_code or not by_code[code].is_active
        for code in counterpart_codes
    ):
        _missing()
    for counterpart in content.counterparts:
        if (
            counterpart.availability == CounterpartAvailability.NOT_COLLECTED
            and session.scalar(
                select(IndicatorValue.id)
                .where(IndicatorValue.indicator_id == by_code[counterpart.indicator_code].id)
                .limit(1)
            )
            is not None
        ):
            raise DomainError(
                422,
                "CONTEXT_COUNTERPART_AVAILABLE",
                "Há dados salvos para esta contrapartida; selecione a referência.",
            )
    by_source = {row.id: row for row in sources}
    for value in values:
        indicator = by_indicator.get(value.indicator_id)
        if indicator is None or not indicator.is_active or indicator.code not in KNOWN_CODES:
            _missing()
        if by_source[value.source_id].source_type != "OFFICIAL":
            raise DomainError(
                422, "CONTEXT_OBSERVATION_SOURCE", "Observações exigem fonte oficial cadastrada."
            )
        latest = session.scalar(
            select(func.max(IndicatorValue.revision)).where(
                IndicatorValue.indicator_id == value.indicator_id,
                IndicatorValue.reference_date == value.reference_date,
            )
        )
        if value.revision != latest:
            raise DomainError(
                409,
                "CONTEXT_OBSERVATION_REVISED",
                "A observação recebeu revisão; salve um novo contexto com a referência revisada.",
            )
    return {row.id: row for row in values}, by_indicator, by_source


def _observation(value: IndicatorValue, indicator: Indicator) -> ObservationAnchor:
    definition = value.provenance.get("definition") if isinstance(value.provenance, dict) else None
    if not isinstance(definition, dict) or not all(
        isinstance(definition.get(key), str) and definition[key].strip()
        for key in ("unit", "scope", "methodology", "frequency")
    ):
        raise DomainError(
            422,
            "CONTEXT_OBSERVATION_DEFINITION",
            "Definição histórica da observação não está disponível.",
        )
    period_start, period_end = measurement_period(
        indicator.code, value.reference_date, definition["frequency"]
    )
    historical = {key: definition[key] for key in ("unit", "scope", "methodology", "frequency")}
    if indicator.code == "renda-trabalho-real":
        price_reference = value.provenance.get("income_price_reference")
        price_period = value.provenance.get("income_price_period")
        price_method = value.provenance.get("income_price_method_url")
        if not all(
            isinstance(item, str) and item.strip()
            for item in (price_reference, price_period, price_method)
        ):
            raise DomainError(
                422,
                "CONTEXT_INCOME_PRICE_REFERENCE",
                "Base de preços histórica da renda não está disponível.",
            )
        historical["methodology"] += (
            f" Base de preços preservada nesta coleta: {price_period} ({price_reference}); "
            f"método: {price_method}. Não comparar bases de preços diferentes."
        )
    return ObservationAnchor(
        observation_id=value.id,
        indicator_code=indicator.code,
        revision=value.revision,
        source_id=value.source_id,
        value=str(value.value),
        reference_date=value.reference_date,
        collected_at=value.retrieved_at,
        period_start=period_start,
        period_end=period_end,
        **historical,
    )


def _source(
    session: "Session", source: Source, values: dict, frozen: SourceReference | None = None
):
    terms = set()
    for row in values.values():
        if row.source_id != source.id:
            continue
        if not isinstance(row.provenance, dict):
            raise DomainError(
                422, "CONTEXT_REFERENCE_INVALID", "Proveniência da referência precisa de correção."
            )
        pair = (row.provenance.get("license"), row.provenance.get("license_url"))
        if not all(isinstance(item, str) and item.strip() for item in pair):
            raise DomainError(
                422, "CONTEXT_REFERENCE_INVALID", "Termos da observação precisam de correção."
            )
        terms.add(pair)
    if len(terms) > 1:
        raise DomainError(
            422,
            "CONTEXT_TERMS_CONFLICT",
            "As observações usam termos distintos; separe os contextos ou revise a referência.",
        )
    if terms:
        license_name, license_url = next(iter(terms))
    else:
        metadata = source_view(session, source)
        license_name, license_url = metadata.get("license"), metadata.get("license_url")
    if not (
        isinstance(license_name, str)
        and license_name.strip()
        and isinstance(license_url, str)
        and license_url.strip()
    ):
        license_name, license_url = UNKNOWN_TERMS, source.url
    return SourceReference(
        id=source.id,
        title=source.title,
        institution=source.institution,
        url=source.url,
        terms=license_name,
        terms_url=license_url,
        published_date=source.publication_date,
        consulted_at=(
            frozen.consulted_at
            if frozen is not None
            else datetime.combine(source.accessed_at, datetime.min.time(), UTC)
        ),
    )


def _resolved(
    session: "Session",
    content: "ContextContentInput",
    author_id: UUID,
    frozen_sources: dict | None = None,
):
    values, indicators, sources = _load(session, content, author_id)
    try:
        observations = tuple(
            _observation(values[key], indicators[values[key].indicator_id])
            for key in content.observation_ids
        )
        # Explicit source order followed by automatically included observation sources.
        source_order = list(
            dict.fromkeys([*content.source_ids, *(row.source_id for row in observations)])
        )
        refs = tuple(
            _source(session, sources[key], values, (frozen_sources or {}).get(key))
            for key in source_order
        )
    except ValidationError as error:
        raise DomainError(
            422,
            "CONTEXT_REFERENCE_INVALID",
            "Metadados da referência precisam de correção antes da revisão.",
        ) from error
    return observations, refs, any(row.is_example for row in sources.values())


def resolve_content(
    session: "Session", content: "ContextContentInput", author_id: UUID, now: datetime
) -> dict:
    observations, sources, _ = _resolved(session, content, author_id)
    # The contract checks chronology using the server's updated_at/assessment time.
    fields = content.model_dump(mode="json", exclude={"observation_ids", "source_ids"})
    fields["observations"] = [row.model_dump(mode="json") for row in observations]
    fields["sources"] = [row.model_dump(mode="json") for row in sources]
    return fields


def validate_references(
    session: "Session",
    draft: ContextDraft,
    author_id: UUID,
    for_publication: bool = False,
    *,
    is_example: bool = False,
) -> None:
    from app.modules.contexts.schemas import ContextContentInput

    fields = draft.model_dump(
        mode="json",
        exclude={
            "contract_version",
            "id",
            "author_id",
            "revision",
            "updated_at",
            "observations",
            "sources",
        },
    )
    fields["observation_ids"] = [str(row.observation_id) for row in draft.observations]
    fields["source_ids"] = [str(row.id) for row in draft.sources]
    content = ContextContentInput.model_validate(fields)
    observations, sources, reference_example = _resolved(
        session, content, author_id, {row.id: row for row in draft.sources}
    )
    if reference_example and not is_example:
        raise DomainError(
            422,
            "EXAMPLE_CONTEXT_REQUIRED",
            "A referência agora é um exemplo; crie um contexto de exemplo e revise novamente.",
        )
    if tuple(observations) != draft.observations or tuple(sources) != draft.sources:
        raise DomainError(
            409,
            "CONTEXT_REFERENCE_CHANGED",
            "Referências mudaram; salve uma nova revisão e confira novamente.",
        )


def is_example_content(session: "Session", content: "ContextContentInput", author_id: UUID) -> bool:
    _, _, sources = _load(session, content, author_id)
    return any(row.is_example for row in sources.values())


def reference_choices(
    session: "Session", author_id: UUID, code: str, page: int, page_size: int
) -> dict:
    """Read selectable stored observations, with the same privacy and snapshot rules.

    Invalid current references fail explicitly rather than falling back to an older
    revision or replacing the historical definition with the live catalog.
    """
    if code not in KNOWN_CODES:
        _missing()
    indicator = session.scalar(
        select(Indicator).where(Indicator.code == code, Indicator.is_active.is_(True))
    )
    if indicator is None:
        _missing()
    newer = aliased(IndicatorValue)
    latest_id = (
        select(newer.id)
        .where(
            newer.indicator_id == IndicatorValue.indicator_id,
            newer.reference_date == IndicatorValue.reference_date,
        )
        .order_by(newer.revision.desc(), newer.retrieved_at.desc(), newer.id)
        .limit(1)
        .correlate(IndicatorValue)
        .scalar_subquery()
    )
    public_ids = public_sources().with_only_columns(Source.id)
    stmt = (
        select(IndicatorValue, Source)
        .join(Source, Source.id == IndicatorValue.source_id)
        .where(
            IndicatorValue.indicator_id == indicator.id,
            IndicatorValue.id == latest_id,
            Source.source_type == "OFFICIAL",
            or_(Source.created_by == author_id, Source.id.in_(public_ids)),
        )
    )
    if get_settings().environment != "development":
        stmt = stmt.where(Source.is_example.is_(False))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.execute(
        stmt.order_by(IndicatorValue.reference_date.desc(), IndicatorValue.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    choices = []
    try:
        for value, source in rows:
            anchor = _observation(value, indicator)
            reference = _source(session, source, {value.id: value})
            choices.append(
                {**anchor.model_dump(mode="json"), "source": reference.model_dump(mode="json")}
            )
    except ValidationError as error:
        raise DomainError(
            422,
            "CONTEXT_REFERENCE_INVALID",
            "Metadados da referência precisam de correção antes da seleção.",
        ) from error
    # Top-level definition describes the newest returned anchor; each historical
    # choice always carries its own definition. Empty catalog uses reviewed metadata.
    definition = choices[0] if choices else KNOWN_SERIES[code]
    return {
        "data": {
            "code": code,
            "name": KNOWN_SERIES[code]["name"],
            **{key: definition[key] for key in ("unit", "scope", "frequency", "methodology")},
            "observations": choices,
        },
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }
