"""BCB below-line results, republished in RTN; distinct from above-line accounts."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from urllib.parse import urlencode

from app.integrations import treasury

COLLECTOR = "tesouro-rtn-interest-v1"
METHOD_VERSION = "1.0.0"
METHOD_URL = (
    "https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/"
    "publicacoes/28153_894487/Manual%20Externo%20RTN%20VF.pdf"
)
ATTRIBUTION = "Banco Central do Brasil: apuração abaixo da linha, republicada pela STN no RTN."
INTEREST_SERIES = {
    "rtn-primario-abaixo-linha": {
        "series": "10.07.1",
        "name": "Primário do Governo Central — abaixo da linha",
        "accounting_basis": "cash",
        "component": "primary",
        "description": "Resultado primário apurado pelo BCB pela ótica do financiamento, "
        "com ajustes metodológicos próprios; não substitui o primário acima da linha.",
    },
    "rtn-juros-nominais": {
        "series": "10.08.1",
        "name": "Juros nominais do Governo Central",
        "accounting_basis": "accrual",
        "component": "interest",
        "description": "Juros líquidos apropriados por competência pelo BCB, com "
        "atualização monetária. Sinal publicado preservado; "
        "não equivale a juros pagos no orçamento.",
    },
    "rtn-resultado-nominal": {
        "series": "10.09.1",
        "name": "Resultado nominal do Governo Central",
        "accounting_basis": "mixed",
        "component": "nominal",
        "description": "Primário abaixo da linha mais juros nominais assinados, sem "
        "desvalorização cambial. Não é variação simples da dívida ou previsão.",
    },
}
for _entry in INTEREST_SERIES.values():
    _entry.update(
        category="FISCAL",
        unit="R$",
        frequency="MONTHLY",
        scope=treasury.SCOPE,
        methodology=(
            f"Série {_entry['series']}. BCB abaixo da linha, republicado pela STN/RTN, tema 10. "
            f"Registro {_entry['accounting_basis']}; preços nominais, Governo Central. "
            "R$ milhões convertidos em reais por fator 1.000.000, centavos half-even; "
            "dia 01 identifica mês. Sinais publicados preservados; juros líquidos por "
            "competência e primário por caixa. Resultado nominal = primário abaixo da "
            "linha + juros assinados. Sem desvalorização cambial; não somar ao primário "
            "acima da linha nem ao motor incremental."
        ),
    )


def parse_series(payload, series, start, end):
    return treasury._parse_series(
        payload, series, start, end, {entry["series"] for entry in INTEREST_SERIES.values()}
    )


def difference(values):
    return (
        values["rtn-primario-abaixo-linha"]
        + values["rtn-juros-nominais"]
        - values["rtn-resultado-nominal"]
    )


def validate_month(values):
    if set(values) != set(INTEREST_SERIES) or any(
        type(value) is not Decimal
        or not value.is_finite()
        or abs(value) >= Decimal("100000000000000")
        or value != value.quantize(treasury.CENT)
        for value in values.values()
    ):
        raise ValueError("Below-line cohort requires three finite cent-precision amounts.")
    if abs(difference(values)) > treasury.RECONCILIATION_TOLERANCE:
        raise ValueError("Below-line primary plus signed interest does not reconcile with nominal.")


def period_fingerprint(when, values):
    validate_month(values)
    if type(when) is not date or when.day != 1:
        raise ValueError("Fingerprint requires a monthly reference.")
    payload = {
        "collector": COLLECTOR,
        "method_version": METHOD_VERSION,
        "period": when.isoformat(),
        "scope": treasury.SCOPE,
        "accounting_basis": "mixed",
        "methodology_basis": "below_line",
        "component_bases": {"primary": "cash", "interest": "accrual"},
        "currency": "BRL",
        "price_basis": "nominal",
        "original_unit": "R$ milhões",
        "scale": "1000000",
        "statistical_authority": "Banco Central do Brasil",
        "series": {
            code: {
                "id": INTEREST_SERIES[code]["series"],
                "value": format(values[code] if values[code] else Decimal("0.00"), ".2f"),
            }
            for code in sorted(values)
        },
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def fetch_year(year, as_of):
    if type(year) is not int or type(as_of) is not date or not 1997 <= year < as_of.year:
        raise ValueError("Choose a closed calendar year for below-line results.")
    from app.integrations.http import read_json

    expected = {date(year, month, 1) for month in range(1, 13)}
    bundle = {}
    for code, entry in INTEREST_SERIES.items():
        query = urlencode(
            {
                "tema": "10",
                "codigo_da_serie": entry["series"],
                "data_inicio": f"01/{year}",
                "data_fim": f"12/{year}",
                "correcao_ipca": "false",
            }
        )
        url = f"{treasury.API_URL}?{query}"
        rows = parse_series(
            read_json(url, decimal_numbers=True),
            entry["series"],
            date(year, 1, 1),
            date(year, 12, 1),
        )
        if {when for when, _ in rows} != expected:
            raise ValueError("Below-line response omitted months; preserve the prior cohort.")
        bundle[code] = {"observations": rows, "request_url": url}
    by_code = {code: dict(item["observations"]) for code, item in bundle.items()}
    for when in expected:
        validate_month({code: values[when] for code, values in by_code.items()})
    return bundle
