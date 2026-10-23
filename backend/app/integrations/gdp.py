"""Reviewed SIDRA current-price national GDP; one bounded year per request."""

import hashlib
import json
import re
from datetime import UTC, date, datetime
from decimal import Decimal

from app.integrations.ibge import IBGE_TERMS

GDP_CODE = "pib-nominal-trimestral"
SOURCE_URL = "https://sidra.ibge.gov.br/tabela/1846"
LICENSE_NAME = "Termos do portal IBGE"
LICENSE_URL = IBGE_TERMS
SCOPE = "Brasil; Contas Nacionais Trimestrais, PIB a preços de mercado"
ORIGINAL_UNIT = "Milhões de Reais"
SCALE = Decimal("1000000")
SOURCE_PRECISION = "0.01_million_brl"
GDP_SERIES = {
    GDP_CODE: {
        "series": "585",
        "aggregate": 1846,
        "variable": 585,
        "name": "PIB nominal trimestral",
        "description": (
            "Valor do Produto Interno Bruto a preços de mercado no trimestre, "
            "em reais correntes, sem ajuste sazonal."
        ),
        "category": "ECONOMY",
        "unit": "R$",
        "frequency": "QUARTERLY",
        "scope": SCOPE,
        "methodology": (
            "IBGE/SIDRA 1846, variável 585 (valores a preços correntes), "
            "classificação 11255, categoria 90707 (PIB a preços de mercado), Brasil. "
            "Sem ajuste sazonal. Fluxos trimestrais, não índice de volume nem crescimento. "
            "Unidade original: Milhões de Reais. Consulta com duas casas decimais; "
            "multiplica-se por 1.000.000 para reais nominais. Resolução da fonte nesta "
            "consulta: R$ 10.000; centavos na apresentação não implicam maior precisão. "
            "O dia 01 do primeiro mês identifica o trimestre. Somar os quatro trimestres "
            "do mesmo ano para o denominador anual; não anualizar um trimestre parcial. "
            "Revisões oficiais geram novas observações."
        ),
    }
}
HEADER = {
    "NC": "Nível Territorial (Código)",
    "NN": "Nível Territorial",
    "MC": "Unidade de Medida (Código)",
    "MN": "Unidade de Medida",
    "V": "Valor",
    "D1C": "Brasil (Código)",
    "D1N": "Brasil",
    "D2C": "Variável (Código)",
    "D2N": "Variável",
    "D3C": "Trimestre (Código)",
    "D3N": "Trimestre",
    "D4C": "Setores e subsetores (Código)",
    "D4N": "Setores e subsetores",
}
_ROW_METADATA = {
    "NC": "1",
    "NN": "Brasil",
    "MC": "1550",
    "MN": ORIGINAL_UNIT,
    "D1C": "1",
    "D1N": "Brasil",
    "D2C": "585",
    "D2N": "Valores a preços correntes",
    "D4C": "90707",
    "D4N": "PIB a preços de mercado",
}
_MONEY = re.compile(r"\d+\.\d{2}\Z")


def _quarters(year: int, end: date) -> list[int]:
    if (
        type(year) is not int
        or not 1900 <= year <= 2200
        or not isinstance(end, date)
        or isinstance(end, datetime)
        or end > datetime.now(UTC).date()
        or year > end.year
    ):
        raise ValueError("Choose a past GDP year and a nonfuture end date.")
    last_quarter = 4 if year < end.year else (end.month - 1) // 3 + 1
    return list(range(1, last_quarter + 1))


def parse_year(payload, year: int, end: date):
    quarters = _quarters(year, end)
    if (
        not isinstance(payload, list)
        or not 1 <= len(payload) <= len(quarters) + 1
        or payload[0] != HEADER
    ):
        raise ValueError("SIDRA GDP header or bounded payload differs from catalog.")
    output = []
    seen = set()
    for row in payload[1:]:
        if (
            not isinstance(row, dict)
            or set(row) != set(HEADER)
            or any(row.get(key) != value for key, value in _ROW_METADATA.items())
        ):
            raise ValueError("GDP unit, variable, geography or category differs from catalog.")
        period = row["D3C"]
        if not isinstance(period, str) or not re.fullmatch(r"\d{6}", period):
            raise ValueError("Invalid GDP quarterly period.")
        quarter = int(period[4:])
        if (
            int(period[:4]) != year
            or quarter not in quarters
            or row["D3N"] != f"{quarter}º trimestre {year}"
            or quarter in seen
        ):
            raise ValueError("Duplicate, unexpected or out-of-period GDP quarter.")
        seen.add(quarter)
        raw = row["V"]
        if raw in ("-", "...", "..", "X"):
            continue
        if not isinstance(raw, str) or not _MONEY.fullmatch(raw):
            raise ValueError("GDP money must retain the source's decimal string precision.")
        value = Decimal(raw)
        if not value.is_finite() or not Decimal("0") < value < Decimal("100000000"):
            raise ValueError("GDP must be finite, positive and within indicator storage range.")
        output.append((date(year, (quarter - 1) * 3 + 1, 1), value * SCALE))
    return sorted(output)


def fetch_year(year: int, end: date):
    quarters = _quarters(year, end)
    periods = ",".join(f"{year}{quarter:02d}" for quarter in quarters)
    url = (
        f"https://apisidra.ibge.gov.br/values/t/1846/n1/1/v/585/p/{periods}/c11255/90707/d/v585%202"
    )
    from app.integrations.http import read_json

    return {"observations": parse_year(read_json(url), year, end), "request_url": url}


def year_fingerprint(year: int, values: dict[date, Decimal]) -> str:
    if type(year) is not int or not 1900 <= year <= 2200:
        raise ValueError("Invalid GDP fingerprint year.")
    for when, value in values.items():
        if (
            not isinstance(when, date)
            or isinstance(when, datetime)
            or when.year != year
            or when.month not in (1, 4, 7, 10)
            or when.day != 1
            or type(value) is not Decimal
            or not value.is_finite()
            or value <= 0
            or value != value.quantize(Decimal("0.01"))
        ):
            raise ValueError("GDP fingerprint requires valid quarterly Decimal observations.")
    payload = {
        "provider": "ibge-cnt-gdp-v1",
        "year": year,
        "scope": SCOPE,
        "price_basis": "nominal",
        "currency": "BRL",
        "original_unit": ORIGINAL_UNIT,
        "scale": str(SCALE),
        "table": "1846",
        "series": "585",
        "classification": "11255",
        "category": "90707",
        "aggregation": "sum_four_quarters_cnt",
        "source_precision": SOURCE_PRECISION,
        "values": {
            when.isoformat(): format(value, ".2f") for when, value in sorted(values.items())
        },
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
