"""Reviewed direct RTN children; separate from the historical triple identity."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from urllib.parse import urlencode

from app.integrations import treasury

METHOD_VERSION = "1.0.0"
COLLECTOR = "tesouro-rtn-composition-v1"
COMPOSITION_SERIES = {
    "rtn-receita-bruta": ("10.01.1", "Receita total antes das transferências"),
    "rtn-transferencias": ("10.02.1", "Transferências por repartição de receitas"),
    "rtn-receita-rfb": ("10.01.1.1", "Receitas administradas pela Receita Federal"),
    "rtn-incentivos-fiscais": ("10.01.1.2", "Incentivos fiscais — rubrica RTN"),
    "rtn-arrecadacao-rgps": ("10.01.1.3", "Arrecadação líquida para o RGPS"),
    "rtn-receitas-nao-administradas": (
        "10.01.1.4",
        "Receitas não administradas pela Receita Federal",
    ),
    "rtn-beneficios-previdenciarios": ("10.03.1.1", "Benefícios previdenciários"),
    "rtn-pessoal-encargos": ("10.03.1.2", "Pessoal e encargos sociais"),
    "rtn-outras-obrigatorias": ("10.03.1.3", "Outras despesas obrigatórias"),
    "rtn-executivo-programacao": (
        "10.03.1.4",
        "Executivo: despesas sujeitas à programação financeira",
    ),
}
COMPOSITION_SERIES = {
    code: {
        "series": series,
        "name": label,
        "description": label,
        "category": "FISCAL",
        "unit": "R$",
        "frequency": "MONTHLY",
        "scope": treasury.SCOPE,
        "methodology": (
            f"Série {series}. {treasury._COMMON_METHOD} "
            "Composição RTN: filhos diretos, sem somar pais e filhos; "
            "valores assinados preservados."
        ),
    }
    for code, (series, label) in COMPOSITION_SERIES.items()
}
REVENUE_CODES = tuple(list(COMPOSITION_SERIES)[2:6])
EXPENDITURE_CODES = tuple(list(COMPOSITION_SERIES)[6:])
ALL_SERIES = treasury.TREASURY_SERIES | COMPOSITION_SERIES


def parse_series(payload, series, start, end):
    return treasury._parse_series(
        payload, series, start, end, {entry["series"] for entry in ALL_SERIES.values()}
    )


def differences(values):
    return {
        "revenue_components_difference": sum(values[code] for code in REVENUE_CODES)
        - values["rtn-receita-bruta"],
        "net_revenue_difference": values["rtn-receita-bruta"]
        - values["rtn-transferencias"]
        - values["rtn-receita-liquida"],
        "expenditure_difference": sum(values[code] for code in EXPENDITURE_CODES)
        - values["rtn-despesa-primaria"],
    }


def validate_month(values):
    if set(values) != set(ALL_SERIES) or any(
        type(value) is not Decimal
        or not value.is_finite()
        or abs(value) >= Decimal("100000000000000")
        or value != value.quantize(treasury.CENT)
        for value in values.values()
    ):
        raise ValueError("Composition requires all thirteen finite cent-precision values.")
    if any(
        abs(value) > treasury.RECONCILIATION_TOLERANCE for value in differences(values).values()
    ):
        raise ValueError("RTN composition does not reconcile.")
    if (
        abs(
            values["rtn-receita-liquida"]
            - values["rtn-despesa-primaria"]
            - values["rtn-resultado-primario"]
        )
        > treasury.RECONCILIATION_TOLERANCE
    ):
        raise ValueError("Composition anchors do not reconcile.")


def period_fingerprint(when, values):
    validate_month(values)
    if not isinstance(when, date) or when.day != 1:
        raise ValueError("Composition fingerprint requires a monthly reference.")
    payload = {
        "collector": COLLECTOR,
        "method_version": METHOD_VERSION,
        "period": when.isoformat(),
        "scope": treasury.SCOPE,
        "accounting_basis": "cash",
        "price_basis": "nominal",
        "currency": "BRL",
        "original_unit": "R$ milhões",
        "scale": "1000000",
        "series": {
            code: {
                "id": ALL_SERIES[code]["series"],
                "value": format(values[code] if values[code] else Decimal("0.00"), ".2f"),
            }
            for code in sorted(values)
        },
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def fetch_year(year, as_of):
    if type(year) is not int or not 1997 <= year < as_of.year:
        raise ValueError("Choose a closed RTN calendar year.")
    from app.integrations.http import read_json

    start, end = date(year, 1, 1), date(year, 12, 1)
    expected = {date(year, month, 1) for month in range(1, 13)}
    bundle = {}
    for code, entry in ALL_SERIES.items():
        query = urlencode(
            {
                "tema": "10",
                "codigo_da_serie": entry["series"],
                "data_inicio": start.strftime("%m/%Y"),
                "data_fim": end.strftime("%m/%Y"),
                "correcao_ipca": "false",
            }
        )
        url = f"{treasury.API_URL}?{query}"
        rows = parse_series(read_json(url, decimal_numbers=True), entry["series"], start, end)
        if {when for when, _ in rows} != expected:
            raise ValueError("Composition response is incomplete; preserve previous cohort.")
        bundle[code] = {"observations": rows, "request_url": url}
    by_code = {code: dict(item["observations"]) for code, item in bundle.items()}
    for when in expected:
        validate_month({code: values[when] for code, values in by_code.items()})
    return bundle
