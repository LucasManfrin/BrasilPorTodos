"""Reviewed RTN monthly bundle, nominal reais and Government Central only.

The API's generic unit is checked against the official RTN historical worksheet:
theme 10 is R$ million, current prices. Never follows pagination or contributed URLs.
"""

import hashlib
import json
import re
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from urllib.parse import urlencode

SOURCE_URL = "https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional"
LICENSE_NAME = "ODbL 1.0"
LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"
SCOPE = (
    "Governo Central: Tesouro Nacional, Previdência Social e Banco Central; "
    "exclui estados e municípios"
)
ACCOUNTING_BASIS = "cash"
PRICE_BASIS = "nominal"
SCALE = Decimal("1000000")
CENT = Decimal("0.01")
RECONCILIATION_TOLERANCE = Decimal("0.03")
THEME_NAME = "Resultado Fiscal do Governo Central - Valores Mensais"
API_URL = "https://apiapex.tesouro.gov.br/aria/v1/series-temporais/custom/resultado-fiscal"
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-01T00:00:00(?:\.000)?Z\Z")
_COMMON_METHOD = (
    "RTN/Tesouro Nacional, tema 10, valores mensais correntes. Regime de caixa, "
    "critério de pagamento efetivo e ajustes metodológicos do RTN. A API fornece "
    "R$ milhões; valor armazenado em reais nominais após multiplicar por 1.000.000, "
    "arredondado a centavos (half-even). O dia 01 identifica o mês. Não inclui "
    "estados e municípios; resultado primário não inclui juros e não é resultado "
    "nominal, orçamento futuro ou previsão."
)
TREASURY_SERIES = {
    "rtn-receita-liquida": {
        "series": "10.01.2",
        "name": "Receita líquida do Governo Central",
        "description": "Receita total menos transferências por repartição de receitas, no RTN.",
    },
    "rtn-despesa-primaria": {
        "series": "10.03.1",
        "name": "Despesa primária do Governo Central",
        "description": "Despesa primária total do Governo Central, sem juros, no RTN.",
    },
    "rtn-resultado-primario": {
        "series": "10.04.1",
        "name": "Resultado primário do Governo Central",
        "description": (
            "Receita líquida menos despesa primária: positivo é superávit; negativo, déficit."
        ),
    },
}
for _entry in TREASURY_SERIES.values():
    _entry.update(
        category="FISCAL",
        unit="R$",
        frequency="MONTHLY",
        scope=SCOPE,
        methodology=f"Série {_entry['series']}. {_COMMON_METHOD}",
    )


def _interval(start: date, end: date) -> tuple[date, date]:
    if (
        not isinstance(start, date)
        or not isinstance(end, date)
        or isinstance(start, datetime)
        or isinstance(end, datetime)
        or start > end
        or start.year != end.year
        or end > datetime.now(UTC).date()
    ):
        raise ValueError("Choose a past RTN interval within one calendar year.")
    return start.replace(day=1), end.replace(day=1)


def parse_series(payload, series: str, start: date, end: date):
    return _parse_series(
        payload, series, start, end, {entry["series"] for entry in TREASURY_SERIES.values()}
    )


def _parse_series(payload, series: str, start: date, end: date, approved_series):
    """Shared strict numeric/envelope parser; each caller supplies its reviewed IDs."""
    start, end = _interval(start, end)
    if series not in approved_series:
        raise ValueError("Unapproved RTN series.")
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise ValueError("Unexpected RTN envelope.")
    page = payload.get("page")
    page_size = payload.get("pageSize")
    rows = payload.get("registros")
    if (
        type(page) is not int
        or page != 1
        or type(page_size) is not int
        or not 1 <= page_size <= 1000
        or not isinstance(rows, list)
        or len(rows) >= page_size
        or len(rows) > 12
    ):
        raise ValueError("Unexpected or potentially truncated RTN page.")
    # This API always supplies next, even for a complete page. Bounded month count,
    # page metadata and duplicate checks establish completeness; never follow it.
    output = []
    seen = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or row.get("codigoTema") != "10"
            or row.get("nomeTema") != THEME_NAME
            or row.get("codigoSerie") != series
            or not isinstance(row.get("data"), str)
            or not _TIMESTAMP.fullmatch(row["data"])
        ):
            raise ValueError("RTN definition, scope or timestamp differs from catalog.")
        when = date.fromisoformat(row["data"][:10])
        if not start <= when <= end or when in seen:
            raise ValueError("Duplicate or out-of-period RTN observation.")
        raw = row.get("valor")
        if type(raw) not in (Decimal, int):
            raise ValueError("RTN money must be decoded without binary floats.")
        value = Decimal(raw)
        if not value.is_finite() or abs(value) >= Decimal("100000000"):
            raise ValueError("Nonfinite or out-of-storage-range RTN observation.")
        try:
            money = (value * SCALE).quantize(CENT, rounding=ROUND_HALF_EVEN)
        except InvalidOperation as exc:
            raise ValueError("Invalid RTN monetary precision.") from exc
        if abs(money) >= Decimal("100000000000000"):
            raise ValueError("RTN money exceeds indicator storage range.")
        if money == 0:
            money = Decimal("0.00")
        seen.add(when)
        output.append((when, money))
    return sorted(output)


def fetch_bundle(start: date, end: date):
    start, end = _interval(start, end)
    from app.integrations.http import read_json

    bundle = {}
    for code, entry in TREASURY_SERIES.items():
        query = urlencode(
            {
                "tema": "10",
                "codigo_da_serie": entry["series"],
                "data_inicio": start.strftime("%m/%Y"),
                "data_fim": end.strftime("%m/%Y"),
                "correcao_ipca": "false",
            }
        )
        url = f"{API_URL}?{query}"
        bundle[code] = {
            "observations": parse_series(
                read_json(url, decimal_numbers=True), entry["series"], start, end
            ),
            "request_url": url,
        }
    by_code = {code: dict(item["observations"]) for code, item in bundle.items()}
    months = set(by_code["rtn-receita-liquida"])
    if any(set(values) != months for values in by_code.values()):
        raise ValueError("RTN bundle has incompatible monthly coverage.")
    for when in months:
        difference = (
            by_code["rtn-receita-liquida"][when]
            - by_code["rtn-despesa-primaria"][when]
            - by_code["rtn-resultado-primario"][when]
        )
        if abs(difference) > RECONCILIATION_TOLERANCE:
            raise ValueError("RTN monthly accounting reconciliation failed.")
    return bundle


def period_fingerprint(when: date, values: dict[str, Decimal]) -> str:
    if when.day != 1 or set(values) != set(TREASURY_SERIES):
        raise ValueError("Fingerprint requires one complete RTN monthly triple.")
    if any(type(value) is not Decimal or not value.is_finite() for value in values.values()):
        raise ValueError("Fingerprint money must be finite Decimal.")
    payload = {
        "provider": "tesouro-rtn-v1",
        "period": when.isoformat(),
        "scope": SCOPE,
        "accounting_basis": ACCOUNTING_BASIS,
        "price_basis": PRICE_BASIS,
        "currency": "BRL",
        "original_unit": "R$ milhões",
        "scale": str(SCALE),
        "series": {
            code: {
                "id": TREASURY_SERIES[code]["series"],
                "value": format(
                    Decimal("0.00")
                    if values[code] == 0
                    else values[code].quantize(CENT, rounding=ROUND_HALF_EVEN),
                    ".2f",
                ),
            }
            for code in sorted(values)
        },
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
