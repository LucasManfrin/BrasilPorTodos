"""Annual direct-child composition, bound to the current historical RTN anchors."""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from app.integrations import treasury
from app.integrations import treasury_composition as provider
from app.modules.indicators.fiscal_baseline import current as current_fiscal
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.indicators.service import observation_view

METHOD = (
    "Soma dos doze fluxos mensais do mesmo ano fechado e recorte RTN. Quatro filhos diretos "
    "compõem a receita total e quatro a despesa primária. Transferências são descontadas "
    "uma única vez da receita total. Incentivos preservam o sinal publicado. "
    "Diferenças mensais de até R$ 0,03 são toleradas por arredondamento independente; "
    "a diferença anual efetiva é mostrada sem ajuste de valores."
)
SOURCE = {
    "title": "Resultado do Tesouro Nacional (RTN)",
    "institution": "Secretaria do Tesouro Nacional",
    "url": treasury.SOURCE_URL,
    "license": treasury.LICENSE_NAME,
    "license_url": treasury.LICENSE_URL,
}
LIMITATIONS = [
    "Governo Central: não inclui estados e municípios; despesas primárias excluem juros.",
    "Classificação do RTN não equivale a funções orçamentárias de Saúde ou Educação.",
    "Incentivos fiscais nesta rubrica são devoluções específicas, não o total de "
    "renúncias tributárias.",
    "Programação financeira do Executivo inclui despesas obrigatórias e discricionárias.",
    "Valores observados não indicam margem disponível para cortes nem efeitos causais de "
    "propostas.",
    "Centavos resultam da conversão de R$ milhões e não representam precisão maior da fonte.",
]


def assemble(records, fiscal):
    available = fiscal.get("status") == "AVAILABLE"
    result = {
        "status": "INCOMPLETE" if records else "EMPTY",
        "year": fiscal.get("year") if available else None,
        "period_start": fiscal.get("period_start") if available else None,
        "period_end": fiscal.get("period_end") if available else None,
        "scope": treasury.SCOPE,
        "currency": "BRL",
        "accounting_basis": "cash",
        "price_basis": "nominal",
        "method_version": provider.METHOD_VERSION,
        "source": dict(SOURCE),
        "collected_at": None,
        "reference_amounts": {
            key: fiscal["amounts"][key]
            for key in ("net_revenue", "primary_expenditure", "published_primary_balance")
        }
        if available
        else None,
        "totals": None,
        "revenue": [],
        "expenditure": [],
        "reconciliation": None,
        "months": [],
        "methodology": METHOD,
        "limitations": list(LIMITATIONS),
        "missing": ["Doze meses de composição compatíveis com a referência fiscal atual"],
    }
    if not available:
        result["missing"] = ["Referência fiscal observada anual disponível"]
        return result
    latest = {}
    for row in records:
        key = (row["code"], row["reference_date"])
        if key not in latest or row["revision"] > latest[key]["revision"]:
            latest[key] = row
    anchors = {month["reference_date"]: month["observations"] for month in fiscal["months"]}
    totals = {code: Decimal("0.00") for code in provider.ALL_SERIES}
    months = []
    collected = []
    try:
        for month in range(1, 13):
            when = date(fiscal["year"], month, 1)
            rows = [latest.get((code, when.isoformat())) for code in provider.COMPOSITION_SERIES]
            if any(row is None for row in rows):
                return result
            values = {row["code"]: Decimal(row["value"]) for row in anchors[when.isoformat()]}
            for row in rows:
                entry = provider.COMPOSITION_SERIES[row["code"]]
                provenance, source = row["provenance"], row["source"]
                expected = {
                    "collector": provider.COLLECTOR,
                    "method_version": provider.METHOD_VERSION,
                    "accounting_basis": "cash",
                    "price_basis": "nominal",
                    "currency": "BRL",
                    "original_unit": "R$ milhões",
                    "scale": "1000000",
                    "series": entry["series"],
                    "dataset_url": treasury.SOURCE_URL,
                    "institution": SOURCE["institution"],
                    "license": treasury.LICENSE_NAME,
                    "license_url": treasury.LICENSE_URL,
                    "method": entry["methodology"],
                }
                if (
                    any(provenance.get(key) != value for key, value in expected.items())
                    or source.get("url") != treasury.SOURCE_URL
                    or source.get("source_type") != "OFFICIAL"
                    or source.get("is_example")
                    or source.get("institution") != SOURCE["institution"]
                    or source.get("title") != SOURCE["title"]
                    or source.get("description")
                    != (
                        f"Dados oficiais de {SOURCE['institution']}. "
                        f"Termos: {treasury.LICENSE_NAME}. {treasury.LICENSE_URL}"
                    )
                    or any(
                        provenance.get("definition", {}).get(key) != entry[key]
                        for key in ("unit", "scope", "frequency", "methodology")
                    )
                ):
                    return result
                values[row["code"]] = Decimal(row["value"])
                collected.append(row["retrieved_at"])
            fingerprint = provider.period_fingerprint(when, values)
            if any(row["provenance"].get("period_fingerprint") != fingerprint for row in rows):
                return result
            months.append(
                {
                    "reference_date": when.isoformat(),
                    "period_fingerprint": fingerprint,
                    "observations": rows,
                    "reference_observations": anchors[when.isoformat()],
                }
            )
            for code, value in values.items():
                totals[code] += value
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return result
    result.update(
        status="AVAILABLE",
        collected_at=max(collected),
        missing=[],
        months=months,
        totals={
            key: format(totals[code], ".2f")
            for key, code in (
                ("gross_revenue", "rtn-receita-bruta"),
                ("transfers", "rtn-transferencias"),
                ("net_revenue", "rtn-receita-liquida"),
                ("primary_expenditure", "rtn-despesa-primaria"),
            )
        },
        reconciliation={
            **{key: format(value, ".2f") for key, value in provider.differences(totals).items()},
            "monthly_tolerance": "0.03",
        },
    )
    for key, codes in (
        ("revenue", provider.REVENUE_CODES),
        ("expenditure", provider.EXPENDITURE_CODES),
    ):
        result[key] = [
            {
                "code": code,
                "series": provider.COMPOSITION_SERIES[code]["series"],
                "label": provider.COMPOSITION_SERIES[code]["name"],
                "amount": format(totals[code], ".2f"),
            }
            for code in codes
        ]
    return result


def current(session):
    fiscal = current_fiscal(session)
    records = []
    if fiscal["status"] == "AVAILABLE":
        for indicator in session.scalars(
            select(Indicator).where(
                Indicator.code.in_(provider.COMPOSITION_SERIES), Indicator.is_active.is_(True)
            )
        ):
            entry = provider.COMPOSITION_SERIES[indicator.code]
            if any(
                getattr(indicator, key) != entry[key]
                for key in ("unit", "scope", "frequency", "methodology")
            ):
                continue
            values = session.scalars(
                select(IndicatorValue)
                .where(
                    IndicatorValue.indicator_id == indicator.id,
                    IndicatorValue.reference_date >= date(fiscal["year"], 1, 1),
                    IndicatorValue.reference_date <= date(fiscal["year"], 12, 1),
                )
                .order_by(IndicatorValue.reference_date, IndicatorValue.revision.desc())
            )
            seen = set()
            for value in values:
                if value.reference_date in seen:
                    continue
                seen.add(value.reference_date)
                records.append({"code": indicator.code, **observation_view(session, value)})
    return assemble(records, fiscal)
