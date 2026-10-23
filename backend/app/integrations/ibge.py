"""Bounded, allowlisted national SIDRA series; no user-supplied URL."""

import hashlib
import json
import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

IBGE_TERMS = (
    "https://www.ibge.gov.br/acesso-informacao/acoes-e-programas/politica-de-privacidade.html"
)
INCOME_CODE = "renda-trabalho-real"
INCOME_REFERENCE_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6390/periodos/-1/variaveis/5933"
    "?localidades=N1[1]"
)
INCOME_PERIODS_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/6390/periodos"
INCOME_PRICE_METHOD_URL = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Mensal/Notas_tecnicas/"
    "nota_tecnica_02_pnadc_mensal.pdf"
)
IBGE_SERIES = {
    "ipca-mensal": {
        "aggregate": 1737,
        "variable": 63,
        "name": "Inflação no mês",
        "category": "ECONOMY",
        "unit": "%",
        "frequency": "MONTHLY",
        "scope": "Brasil; IPCA/IBGE",
        "description": "Variação mensal dos preços da cesta de consumo medida pelo IPCA.",
        "methodology": (
            "SIDRA 1737, variável 63. Variação mensal do IPCA. O dia 01 identifica o "
            "mês. Não somar percentuais para acumular inflação."
        ),
    },
    "ipca-12-meses": {
        "aggregate": 1737,
        "variable": 2265,
        "name": "Inflação em 12 meses",
        "category": "ECONOMY",
        "unit": "%",
        "frequency": "MONTHLY",
        "scope": "Brasil; IPCA/IBGE",
        "description": "Quanto os preços da cesta do IPCA variaram nos últimos 12 meses.",
        "methodology": (
            "SIDRA 1737, variável 2265. Acumulado em 12 meses calculado pelo IBGE. "
            "Janelas sucessivas se sobrepõem; o dia 01 identifica o mês."
        ),
    },
    "desocupacao": {
        "aggregate": 6381,
        "variable": 4099,
        "name": "Desemprego",
        "category": "SOCIAL",
        "unit": "%",
        "frequency": "MONTHLY",
        "scope": "Brasil; pessoas de 14 anos ou mais na força de trabalho",
        "description": (
            "Parcela da força de trabalho que está sem trabalho, procura e está "
            "disponível para trabalhar."
        ),
        "methodology": (
            "PNAD Contínua, SIDRA 6381, variável 4099. Trimestre móvel encerrado no mês; "
            "não é taxa mensal isolada. Janelas consecutivas compartilham dois meses. "
            "Preferir comparações com três meses antes e com o mesmo trimestre do ano "
            "anterior; não inferir causas nem significância apenas da diferença."
        ),
    },
}

IBGE_SERIES.update(
    {
        "renda-trabalho-real": {
            "aggregate": 6390,
            "variable": 5933,
            "api_unit": "Reais",
            "name": "Renda média real do trabalho",
            "category": "SOCIAL",
            "unit": "R$",
            "frequency": "MONTHLY",
            "scope": ("Brasil; pessoas ocupadas de 14 anos ou mais com rendimento de trabalho"),
            "description": (
                "Rendimento médio mensal real habitualmente recebido em todos os trabalhos. "
                "É uma média entre pessoas ocupadas com renda, não salário de toda a população."
            ),
            "methodology": (
                "PNAD Contínua, SIDRA 6390, variável 5933. Trimestre móvel encerrado no mês. "
                "Rendimento habitual de todos os trabalhos, em reais ajustados pela inflação; "
                "não é renda nominal nem rendimento efetivo de um mês isolado. A base de "
                "preços é a média do último trimestre móvel disponibilizado na consulta, "
                "usando IPCA conforme a nota técnica 02 do IBGE, e é preservada na "
                "proveniência de cada coleta. Revisões "
                "e atualização da base de preços podem alterar todo o histórico. Janelas "
                "consecutivas compartilham dois meses. Não inferir causas nem significância "
                "estatística somente da variação; esta série não é receita do governo."
            ),
        },
        "informalidade": {
            "aggregate": 8513,
            "variable": 12466,
            "name": "Taxa de informalidade",
            "category": "SOCIAL",
            "unit": "%",
            "frequency": "MONTHLY",
            "scope": "Brasil; pessoas ocupadas de 14 anos ou mais",
            "description": (
                "Parcela das pessoas ocupadas que trabalham em condições consideradas "
                "informais pela PNAD Contínua. Não é a taxa de desemprego."
            ),
            "methodology": (
                "PNAD Contínua, SIDRA 8513, variável 12466. Trimestre móvel encerrado no mês; "
                "percentual de trabalhadores informais na população ocupada. Definição "
                "oficial inclui empregados privados e domésticos sem carteira, empregadores "
                "e trabalhadores por conta própria sem CNPJ e trabalhadores familiares "
                "auxiliares. Janelas consecutivas compartilham dois meses. Preferir "
                "comparações com três meses antes ou o mesmo trimestre do ano anterior; "
                "não atribuir causas apenas pela diferença observada."
            ),
        },
        "participacao-forca-trabalho": {
            "aggregate": 5944,
            "variable": 4096,
            "name": "Participação na força de trabalho",
            "category": "SOCIAL",
            "unit": "%",
            "frequency": "MONTHLY",
            "scope": "Brasil; pessoas de 14 anos ou mais",
            "description": (
                "Parcela das pessoas de 14 anos ou mais que estão trabalhando ou "
                "procuram trabalho e estão disponíveis para trabalhar."
            ),
            "methodology": (
                "PNAD Contínua, SIDRA 5944, variável 4096. Trimestre móvel encerrado no mês. "
                "Percentual da força de trabalho na população de 14 anos ou mais; "
                "denominador diferente da taxa de desemprego. Janelas consecutivas "
                "compartilham dois meses. Preferir comparações com três meses antes "
                "e o mesmo trimestre do ano anterior; não inferir causas nem significância "
                "estatística somente da diferença."
            ),
        },
    }
)


def _interval(start, end):
    if (
        not isinstance(start, date)
        or not isinstance(end, date)
        or isinstance(start, datetime)
        or isinstance(end, datetime)
        or start > end
        or (end - start).days > 365
        or end > datetime.now(UTC).date()
    ):
        raise ValueError("Choose a past IBGE interval of up to one year.")
    return start.replace(day=1), end


def parse_series(payload, variable, start, end):
    start, end = _interval(start, end)
    entries = [entry for entry in IBGE_SERIES.values() if str(entry["variable"]) == str(variable)]
    if len(entries) != 1:
        raise ValueError("Unapproved IBGE variable.")
    entry = entries[0]
    if not isinstance(payload, list) or len(payload) != 1:
        raise ValueError("Unexpected IBGE payload.")
    item = payload[0]
    if str(item["id"]) != str(variable) or item["unidade"] != entry.get("api_unit", entry["unit"]):
        raise ValueError("IBGE definition differs from catalog.")
    results = item["resultados"]
    if (
        not isinstance(results, list)
        or len(results) != 1
        or results[0].get("classificacoes", []) != entry.get("classifications", [])
    ):
        raise ValueError("Unexpected IBGE breakdown.")
    series = results[0]["series"]
    if len(series) != 1 or series[0]["localidade"]["id"] != "1":
        raise ValueError("Only Brazil national totals are allowed.")
    values = series[0]["serie"]
    if not isinstance(values, dict) or len(values) > 13:
        raise ValueError("Unexpected or unbounded IBGE monthly values.")
    output = []
    for period, raw in values.items():
        if not isinstance(period, str) or not re.fullmatch(r"\d{6}", period):
            raise ValueError("Invalid IBGE monthly period.")
        when = date(int(period[:4]), int(period[4:]), 1)
        if not start <= when <= end or when > datetime.now(UTC).date():
            raise ValueError("IBGE observation outside requested interval.")
        if raw in ("-", "...", "..", "X"):
            continue
        if not isinstance(raw, str):
            raise ValueError("IBGE observations must be decimal strings.")
        try:
            value = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError("Invalid IBGE decimal observation.") from exc
        if not value.is_finite():
            raise ValueError("Nonfinite IBGE observation.")
        if entry["category"] == "SOCIAL" and (value < 0 or (entry["unit"] == "%" and value > 100)):
            raise ValueError("IBGE employment observation outside the reviewed measure range.")
        output.append((when, value))
    return sorted(output)


def fetch_series(code, start, end):
    start, end = _interval(start, end)
    if code not in IBGE_SERIES:
        raise ValueError("Choose approved series and a past interval of up to one year.")
    entry = IBGE_SERIES[code]
    periods = []
    cursor = start.replace(day=1)
    while cursor <= end:
        periods.append(cursor.strftime("%Y%m"))
        cursor = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{entry['aggregate']}/periodos/{'|'.join(periods)}/variaveis/{entry['variable']}?localidades=N1[1]"
    if entry.get("classification_query"):
        url += f"&classificacao={entry['classification_query']}"
    from app.integrations.http import read_json

    return parse_series(read_json(url), entry["variable"], start.replace(day=1), end), url


def income_price_reference():
    """Global source anchor, never inferred from the latest month in a history window."""
    from app.integrations.http import read_json

    metadata = read_json(INCOME_PERIODS_URL)
    if not isinstance(metadata, list) or not 1 <= len(metadata) <= 1000:
        raise ValueError("Unexpected or unbounded income release periods.")
    periods = {}
    for item in metadata:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not re.fullmatch(r"\d{6}", item["id"])
            or not isinstance(item.get("literals"), list)
            or not item["literals"]
            or any(not isinstance(label, str) for label in item["literals"])
            or not isinstance(item.get("modificacao"), str)
            or item["id"] in periods
        ):
            raise ValueError("Income release metadata differs from the reviewed contract.")
        period_date = date(int(item["id"][:4]), int(item["id"][4:]), 1)
        modified = datetime.strptime(item["modificacao"], "%d/%m/%Y").date()
        if period_date > datetime.now(UTC).date() or modified > datetime.now(UTC).date():
            raise ValueError("Income release metadata contains a future period or modification.")
        periods[item["id"]] = {
            "modified": modified.isoformat(),
            "labels": item["literals"],
        }
    payload = read_json(INCOME_REFERENCE_URL)
    try:
        values = payload[0]["resultados"][0]["series"][0]["serie"]
        if not isinstance(values, dict) or len(values) != 1:
            raise ValueError("Income price reference must contain exactly one latest period.")
        period = next(iter(values))
        if not isinstance(period, str) or not re.fullmatch(r"\d{6}", period):
            raise ValueError("Invalid income price reference period.")
        when = date(int(period[:4]), int(period[4:]), 1)
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Income price reference response differs from catalog.") from exc
    observations = parse_series(payload, 5933, when, when)
    if len(observations) != 1 or period != max(periods):
        raise ValueError("No usable latest income price reference.")
    months = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
    first_month = (when.month - 3) % 12 + 1
    first_year = when.year - (when.month < 3)
    period_label = (
        f"{months[first_month - 1]}–{months[when.month - 1]}/{when.year}"
        if first_year == when.year
        else f"{months[first_month - 1]}/{first_year}–{months[when.month - 1]}/{when.year}"
    )
    return {
        "income_price_reference": when.isoformat(),
        "income_price_period": period_label,
        "income_price_anchor_value": str(observations[0][1]),
        "income_price_reference_url": INCOME_REFERENCE_URL,
        "income_price_method_url": INCOME_PRICE_METHOD_URL,
        "price_basis": "real_latest_rolling_quarter",
        "original_unit": "Reais",
        "income_source_modified": periods[period]["modified"],
        "income_periods_url": INCOME_PERIODS_URL,
        "income_periods_fingerprint": hashlib.sha256(
            json.dumps(periods, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
    }
