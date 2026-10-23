"""Closed-year below-line accounts, independent from the above-line reference amounts."""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from app.integrations import treasury
from app.integrations import treasury_interest as provider
from app.modules.indicators.fiscal_baseline import current as current_fiscal
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.indicators.service import observation_view

SOURCE = {
    "title": "Resultado do Tesouro Nacional (RTN)",
    "institution": "Secretaria do Tesouro Nacional",
    "url": treasury.SOURCE_URL,
    "license": treasury.LICENSE_NAME,
    "license_url": treasury.LICENSE_URL,
    "attribution": provider.ATTRIBUTION,
}
METHOD = (
    "Somam-se doze fluxos mensais abaixo da linha do BCB republicados no RTN, "
    "no mesmo ano fechado da referência fiscal. Primário de caixa + juros líquidos "
    "assinados por competência = resultado nominal. Conjunto e impressão digital "
    "independentes do primário acima da linha. Tolerância mensal R$ 0,03 por "
    "arredondamento independente; diferença anual efetiva divulgada sem ajuste."
)
LIMITATIONS = [
    "Governo Central não inclui estados, municípios ou todo o setor público consolidado.",
    "Primário abaixo e acima da linha possuem ajustes e discrepâncias; não são intercambiáveis.",
    "Juros líquidos por competência não são juros pagos, amortizações ou Selic "
    "multiplicada pela dívida.",
    "A série nominal não considera desvalorização cambial; variação da dívida também "
    "exige ajustes.",
    "Juros mantêm sinal publicado, inclusive positivo; não subtrair novamente valores negativos.",
    "Ano observado não é projeção nem margem disponível para financiar propostas.",
    "Precisão original em R$ milhões: a conversão a centavos não cria precisão econômica.",
]


def assemble(records, year):
    result = {
        "status": "INCOMPLETE" if records else "EMPTY",
        "year": year,
        "period_start": date(year, 1, 1).isoformat() if year else None,
        "period_end": date(year, 12, 31).isoformat() if year else None,
        "scope": treasury.SCOPE,
        "currency": "BRL",
        "accounting_basis": "mixed",
        "methodology_basis": "below_line",
        "component_bases": {"primary": "cash", "interest": "accrual"},
        "price_basis": "nominal",
        "method_version": provider.METHOD_VERSION,
        "source": dict(SOURCE),
        "collected_at": None,
        "totals": None,
        "reconciliation": None,
        "months": [],
        "methodology": METHOD,
        "limitations": list(LIMITATIONS),
        "missing": [
            "Doze meses compatíveis de primário abaixo da linha, juros e resultado nominal"
        ],
    }
    if year is None:
        result["missing"] = ["Ano fechado da referência fiscal observada disponível"]
        return result
    latest = {}
    for row in records:
        key = (row["code"], row["reference_date"])
        if key not in latest or row["revision"] > latest[key]["revision"]:
            latest[key] = row
    totals = {code: Decimal("0.00") for code in provider.INTEREST_SERIES}
    months, collected = [], []
    try:
        for month in range(1, 13):
            when = date(year, month, 1)
            rows = [latest.get((code, when.isoformat())) for code in provider.INTEREST_SERIES]
            if any(row is None for row in rows):
                return result
            values = {}
            for row in rows:
                entry = provider.INTEREST_SERIES[row["code"]]
                source, provenance = row["source"], row["provenance"]
                expected = {
                    "collector": provider.COLLECTOR,
                    "method_version": provider.METHOD_VERSION,
                    "accounting_basis": entry["accounting_basis"],
                    "methodology_basis": "below_line",
                    "component": entry["component"],
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
                    "statistical_authority": "Banco Central do Brasil",
                    "methodology_url": provider.METHOD_URL,
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
                ("primary_balance", "rtn-primario-abaixo-linha"),
                ("interest", "rtn-juros-nominais"),
                ("nominal_balance", "rtn-resultado-nominal"),
            )
        },
        reconciliation={
            "monthly_tolerance": "0.03",
            "annual_difference": format(provider.difference(totals), ".2f"),
        },
    )
    return result


def current(session):
    fiscal = current_fiscal(session)
    year = fiscal["year"] if fiscal["status"] == "AVAILABLE" else None
    records = []
    if year:
        for indicator in session.scalars(
            select(Indicator).where(
                Indicator.code.in_(provider.INTEREST_SERIES), Indicator.is_active.is_(True)
            )
        ):
            entry = provider.INTEREST_SERIES[indicator.code]
            if any(
                getattr(indicator, key) != entry[key]
                for key in ("unit", "scope", "frequency", "methodology")
            ):
                continue
            rows = session.scalars(
                select(IndicatorValue)
                .where(
                    IndicatorValue.indicator_id == indicator.id,
                    IndicatorValue.reference_date >= date(year, 1, 1),
                    IndicatorValue.reference_date <= date(year, 12, 1),
                )
                .order_by(IndicatorValue.reference_date, IndicatorValue.revision.desc())
            )
            seen = set()
            for value in rows:
                if value.reference_date in seen:
                    continue
                seen.add(value.reference_date)
                records.append({"code": indicator.code, **observation_view(session, value)})
    return assemble(records, year)
