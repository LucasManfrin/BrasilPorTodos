"""Nominal national GDP denominator, from four CNT quarters of the fiscal year."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.integrations.gdp import GDP_CODE, GDP_SERIES, SOURCE_URL, year_fingerprint
from app.integrations.ibge import IBGE_TERMS
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.indicators.service import observation_view

LIMITATIONS = [
    "PIB nacional é denominador de escala; não é receita disponível para gastar.",
    (
        "Soma dos quatro trimestres das Contas Nacionais Trimestrais, sujeita a revisões; "
        "não é série anual definitiva."
    ),
    "Precisão publicada: 0,01 milhão de reais (R$ 10.000); conversão não cria precisão adicional.",
    "Usar PIB nacional não amplia o recorte fiscal Governo Central para estados e municípios.",
]


def assemble(records, year):
    result = {
        "status": "INCOMPLETE" if records else "EMPTY",
        "year": year,
        "nominal_gdp": None,
        "aggregation": "sum_four_quarters_cnt",
        "source_precision": "0.01_million_brl",
        "source": {
            "title": "PIB a preços correntes — Contas Nacionais Trimestrais",
            "institution": "IBGE",
            "url": SOURCE_URL,
            "license": "Termos do portal IBGE",
            "license_url": IBGE_TERMS,
        },
        "quarters": [],
        "missing": ["Quatro trimestres compatíveis de PIB nominal do mesmo ano fiscal"],
        "limitations": list(LIMITATIONS),
    }
    entry = GDP_SERIES[GDP_CODE]
    latest = {}
    for row in records:
        key = row["reference_date"]
        if key not in latest or row["revision"] > latest[key]["revision"]:
            latest[key] = row
    rows = [latest.get(date(year, month, 1).isoformat()) for month in (1, 4, 7, 10)]
    if any(row is None for row in rows):
        return result
    values = {}
    for row in rows:
        source = row["source"]
        provenance = row["provenance"]
        definition = provenance.get("definition", {})
        expected = {
            "collector": "ibge-cnt-gdp-v1",
            "original_unit": "Milhões de Reais",
            "scale": "1000000",
            "series": "585",
            "aggregation": "sum_four_quarters_cnt",
            "source_precision": "0.01_million_brl",
            "dataset_url": SOURCE_URL,
        }
        value = Decimal(row["value"])
        if (
            source["url"] != SOURCE_URL
            or source["source_type"] != "OFFICIAL"
            or source.get("is_example")
            or any(provenance.get(key) != value for key, value in expected.items())
            or any(
                definition.get(key) != entry[key]
                for key in ("unit", "scope", "frequency", "methodology")
            )
            or not value.is_finite()
            or value <= 0
            or value != value.quantize(Decimal("0.01"))
        ):
            return result
        values[date.fromisoformat(row["reference_date"])] = value
    fingerprint = year_fingerprint(year, values)
    if any(row["provenance"].get("annual_fingerprint") != fingerprint for row in rows):
        return result
    result.update(
        status="AVAILABLE",
        nominal_gdp=format(sum(values.values(), Decimal("0.00")), ".2f"),
        missing=[],
        quarters=[{"reference_date": row["reference_date"], "observation": row} for row in rows],
    )
    return result


def current(session, year):
    records = []
    indicator = session.scalar(
        select(Indicator).where(Indicator.code == GDP_CODE, Indicator.is_active.is_(True))
    )
    if indicator:
        entry = GDP_SERIES[GDP_CODE]
        if all(
            getattr(indicator, key) == entry[key]
            for key in ("unit", "scope", "frequency", "methodology")
        ):
            values = session.scalars(
                select(IndicatorValue)
                .where(
                    IndicatorValue.indicator_id == indicator.id,
                    IndicatorValue.reference_date >= date(year, 1, 1),
                    IndicatorValue.reference_date <= date(year, 12, 31),
                )
                .order_by(IndicatorValue.reference_date, IndicatorValue.revision.desc())
            )
            records = [observation_view(session, row) for row in values]
    return assemble(records, year)
