"""Observed primary accounts, with a common closed year and a verified monthly cohort."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.integrations.treasury import (
    LICENSE_NAME,
    LICENSE_URL,
    SCOPE,
    SOURCE_URL,
    TREASURY_SERIES,
    period_fingerprint,
)
from app.modules.indicators.gdp_baseline import current as current_gdp
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.indicators.service import observation_view

METHOD = (
    "RTN/Tesouro: Governo Central, regime de caixa, valores nominais. "
    "Somam-se os 12 fluxos mensais do mesmo ano fechado. Receita líquida menos "
    "despesa primária é reconciliada com o resultado primário acima da linha. "
    "Não usar o resultado abaixo da linha, que possui outro critério de apuração."
)
LIMITATIONS = [
    "Governo Central não inclui as contas dos estados e municípios.",
    "Resultado primário exclui juros; não é resultado nominal nem variação da dívida.",
    "Ano observado não é previsão: não se repete automaticamente em anos futuros.",
    (
        "Impactos declarados exigem compatibilidade de ente, critério, preços e período; "
        "a avaliação não soma medidas a esta conta."
    ),
    "Percentual do PIB indisponível: exige PIB nominal do mesmo período, com fonte e revisão.",
]


def assemble(records, as_of: date):
    """Pure validation/aggregation; no missing month is substituted with zero."""
    latest = {}
    for row in records:
        key = (row["code"], row["reference_date"])
        if key not in latest or row["revision"] > latest[key]["revision"]:
            latest[key] = row
    result = {
        "status": "INCOMPLETE" if records else "EMPTY",
        "year": None,
        "period_start": None,
        "period_end": None,
        "scope": SCOPE,
        "accounting_basis": "cash",
        "price_basis": "nominal",
        "currency": "BRL",
        "methodology": METHOD,
        "amounts": None,
        "source": None,
        "months": [],
        "missing": ["Doze meses compatíveis de receita líquida, despesa e resultado primários"],
        "limitations": list(LIMITATIONS),
    }
    years = sorted(
        {
            int(row["reference_date"][:4])
            for row in records
            if int(row["reference_date"][:4]) < as_of.year
        },
        reverse=True,
    )
    for year in years:
        months = []
        totals = {code: Decimal("0.00") for code in TREASURY_SERIES}
        complete = True
        for month in range(1, 13):
            when = date(year, month, 1)
            rows = [latest.get((code, when.isoformat())) for code in TREASURY_SERIES]
            if any(row is None for row in rows):
                complete = False
                break
            values = {}
            for row in rows:
                entry = TREASURY_SERIES[row["code"]]
                provenance = row["provenance"]
                source = row["source"]
                definition = provenance.get("definition", {})
                expected = {
                    "collector": "tesouro-rtn-v1",
                    "accounting_basis": "cash",
                    "price_basis": "nominal",
                    "currency": "BRL",
                    "original_unit": "R$ milhões",
                    "scale": "1000000",
                    "series": entry["series"],
                    "dataset_url": SOURCE_URL,
                }
                if (
                    any(provenance.get(key) != value for key, value in expected.items())
                    or source["url"] != SOURCE_URL
                    or source["source_type"] != "OFFICIAL"
                    or source.get("is_example")
                    or any(
                        definition.get(key) != entry[key]
                        for key in ("unit", "scope", "frequency", "methodology")
                    )
                ):
                    complete = False
                    break
                value = Decimal(row["value"])
                if not value.is_finite() or value != value.quantize(Decimal("0.01")):
                    complete = False
                    break
                values[row["code"]] = value
            if not complete:
                break
            fingerprint = period_fingerprint(when, values)
            difference = (
                values["rtn-receita-liquida"]
                - values["rtn-despesa-primaria"]
                - values["rtn-resultado-primario"]
            )
            if abs(difference) > Decimal("0.03") or any(
                row["provenance"].get("period_fingerprint") != fingerprint for row in rows
            ):
                complete = False
                break
            months.append({"reference_date": when.isoformat(), "observations": rows})
            for code, value in values.items():
                totals[code] += value
        if not complete:
            continue
        calculated = totals["rtn-receita-liquida"] - totals["rtn-despesa-primaria"]
        result.update(
            status="AVAILABLE",
            year=year,
            period_start=date(year, 1, 1).isoformat(),
            period_end=date(year, 12, 31).isoformat(),
            amounts={
                "net_revenue": format(totals["rtn-receita-liquida"], ".2f"),
                "primary_expenditure": format(totals["rtn-despesa-primaria"], ".2f"),
                "published_primary_balance": format(totals["rtn-resultado-primario"], ".2f"),
                "calculated_primary_balance": format(calculated, ".2f"),
                "reconciliation_difference": format(
                    calculated - totals["rtn-resultado-primario"], ".2f"
                ),
            },
            source={
                "title": "Resultado do Tesouro Nacional (RTN)",
                "institution": "Secretaria do Tesouro Nacional",
                "url": SOURCE_URL,
                "license": LICENSE_NAME,
                "license_url": LICENSE_URL,
            },
            months=months,
            missing=[],
        )
        result["limitations"].append(
            "Reconciliação mensal tolera até R$ 0,03 por arredondamento independente a centavos; "
            "a diferença anual efetiva é apresentada, sem ajustes ocultos."
        )
        if year != as_of.year - 1:
            result["limitations"].append(
                "Ano fechado mais recente ainda indisponível ou incompatível; "
                "usada a última série anual completa."
            )
        return result
    return result


def current(session):
    records = []
    # Latest revision is selected before validation: do not silently fall back within a month.
    for indicator in session.scalars(
        select(Indicator).where(Indicator.code.in_(TREASURY_SERIES), Indicator.is_active.is_(True))
    ):
        entry = TREASURY_SERIES[indicator.code]
        if any(
            getattr(indicator, key) != entry[key]
            for key in ("unit", "scope", "frequency", "methodology")
        ):
            continue
        values = session.scalars(
            select(IndicatorValue)
            .where(IndicatorValue.indicator_id == indicator.id)
            .order_by(IndicatorValue.reference_date.desc(), IndicatorValue.revision.desc())
        )
        seen = set()
        for value in values:
            if value.reference_date in seen:
                continue
            seen.add(value.reference_date)
            records.append({"code": indicator.code, **observation_view(session, value)})
    result = assemble(records, datetime.now(UTC).date())
    result["gdp"] = current_gdp(session, result["year"]) if result["year"] else None
    result["ratios"] = None
    if result["gdp"] and result["gdp"]["status"] == "AVAILABLE":
        denominator = Decimal(result["gdp"]["nominal_gdp"])
        result["ratios"] = {
            output: format(
                (Decimal(result["amounts"][input_key]) / denominator * 100).quantize(
                    Decimal("0.0001")
                ),
                ".4f",
            )
            for output, input_key in (
                ("net_revenue_pct_gdp", "net_revenue"),
                ("primary_expenditure_pct_gdp", "primary_expenditure"),
                ("primary_balance_pct_gdp", "published_primary_balance"),
            )
        }
        result["limitations"] = [
            row
            for row in result["limitations"]
            if not row.startswith("Percentual do PIB indisponível")
        ]
        result["limitations"].extend(result["gdp"]["limitations"])
    elif result["gdp"]:
        result["missing"].extend(result["gdp"]["missing"])
    return result
