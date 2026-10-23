"""Invented GFSM amounts for isolated tests, not actual public accounts."""

from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from app.integrations import general_government as provider

ROWS = dict(zip(provider.METRICS, (7, 18, 20, 21, 25, 30, 35, 36), strict=True))
REF_ROWS = dict(zip(provider.METRICS, (5, 16, 18, 19, 23, 28, 33, 34), strict=True))


def resource(tag="synthetic-file"):
    return {
        "publication_url": provider.SOURCE_URL + "/2021/22",
        "publication_id": "40185",
        "download_url": "https://thot-arquivos.tesouro.gov.br/publicacao/40185",
        "url": "https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/"
        "publicacoes/40185_2097592/demonstrativos-governo-geral.xlsx",
        "published_at": "2026-10-01",
        "updated_at": "2026-09-30",
        "size": 1024,
        "sha256": sha256(tag.encode()).hexdigest(),
        "etag": None,
        "last_modified": None,
    }


def payload(year=2025, tag="synthetic-file", revenue="1000.10"):
    def amounts(revenue, spending, investment, ir, ie):
        r, s, n, ir, ie = map(Decimal, (revenue, spending, investment, ir, ie))
        return dict(
            zip(
                provider.METRICS,
                (r, ir, s + n, s, ie, n, r - s - n, r - s - n + ie - ir),
                strict=True,
            )
        )

    zero = amounts("0", "0", "0", "0", "0")
    base = amounts(revenue, "900.00", "10.00", "20.00", "30.00")
    states = amounts("200.00", "180.00", "5.00", "4.00", "6.00")
    mun = amounts("100.00", "80.00", "2.00", "1.00", "3.00")
    cons = amounts("-100.00", "-100.00", "0", "0", "0")
    general = {key: base[key] + states[key] + mun[key] + cons[key] for key in provider.METRICS}
    data = [base, zero, zero, base, states, mun, cons, general]
    sectors = []
    for offset, (sector, label) in enumerate(provider.SECTORS.items()):
        col = provider._column(3 + 8 * (year - 2010) + offset)
        sectors.append(
            {
                "sector": sector,
                "label": label,
                "column": col,
                "amounts": {k: format(v, ".2f") for k, v in data[offset].items()},
                "raw_millions": {k: format(v / 1_000_000, ".8f") for k, v in data[offset].items()},
                "cells": {k: f"{col}{row}" for k, row in ROWS.items()},
            }
        )
    ref_col = provider._column(3 + year - 2010)
    references = [
        {
            "metric": k,
            "cell": f"{ref_col}{REF_ROWS[k]}",
            "raw_millions": format(v / 1_000_000, ".8f"),
            "amount": format(v, ".2f"),
        }
        for k, v in general.items()
    ]
    result = {
        "year": year,
        "currency": "BRL",
        "price_basis": "CURRENT",
        "accounting_basis": "MODIFIED_ACCRUAL",
        "methodology_basis": "GFSM_2014",
        "period_basis": "FULL_YEAR",
        "parser_version": provider.PARSER_VERSION,
        "precision_version": provider.PRECISION_VERSION,
        "source": dict(provider.SOURCE),
        "coverage": dict(provider.COVERAGE),
        "resource": resource(tag),
        "sectors": sectors,
        "reconciliation": provider._reconciliation(sectors, references),
    }
    result["fingerprint"] = provider.fingerprint(result)
    provider.validate_payload(result)
    return result


def workbook(year=2025, revenue="1000.10", mutate=None):
    p = payload(year, revenue=revenue)
    tables = {"2.1": {}, "3.1": {}, "Metadados": {}}

    def put(table, coord, value):
        tables[table][coord] = value

    for table in ("2.1", "3.1"):
        put(table, "A1", f"Tabela {table}. Demonstrativo de Operações do Governo Geral - Anual")
        put(table, "A2", "R$ Milhões - Valores Correntes ")
    start = p["sectors"][0]["column"]
    put("2.1", start + "4", str(year))
    headers = (
        "Orçamentário 1/",
        "Extraorçamentário",
        "Coluna de Consolidação 2/",
        "Governo Central",
        "Governos Estaduais 3/",
        "Governos Municipais 4/",
        "Coluna de Consolidação 2/",
        "Governo Geral 5/",
    )
    for offset, row in enumerate(p["sectors"]):
        put("2.1", row["column"] + ("6" if offset < 4 else "5"), headers[offset])
        for metric, cell in row["cells"].items():
            put("2.1", cell, row["raw_millions"][metric])
    ref_col = provider._column(3 + year - 2010)
    put("3.1", ref_col + "4", str(year))
    for metric, (code, label) in provider.METRICS.items():
        for table, row in [("2.1", ROWS[metric]), ("3.1", REF_ROWS[metric])]:
            if code:
                put(table, f"A{row}", code)
            put(table, f"B{row}", label)
    for row in p["reconciliation"]["general_reference"]:
        put("3.1", row["cell"], row["raw_millions"])
    put("Metadados", "A1", "Estatísticas de Finanças Públicas do Governo Geral")
    put(
        "Metadados",
        "B2",
        "26 estados e do Distrito Federal; 5.570 municípios; 90%; extrapolar; "
        "exceto o Banco Central do Brasil; competência modificada",
    )
    if mutate:
        mutate(tables)

    def sheet(cells):
        grouped = {}
        for coord, value in cells.items():
            number = int("".join(c for c in coord if c.isdigit()))
            numeric = provider._DECIMAL.fullmatch(value)
            cell = (
                f'<c r="{coord}"><v>{value}</v></c>'
                if numeric
                else f'<c r="{coord}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            )
            grouped.setdefault(number, []).append(cell)
        return (
            '<worksheet xmlns="'
            + provider.NS[1:-1]
            + '"><sheetData>'
            + "".join(
                f'<row r="{n}">' + "".join(cells) + "</row>" for n, cells in sorted(grouped.items())
            )
            + "</sheetData></worksheet>"
        ).encode()

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        names = list(tables)
        z.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="'
            + provider.NS[1:-1]
            + '" xmlns:r="'
            + provider.REL[1:-1]
            + '"><sheets>'
            + "".join(
                f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>'
                for i, name in enumerate(names, 1)
            )
            + "</sheets></workbook>",
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="'
            + provider.PKG[1:-1]
            + '">'
            + "".join(
                f'<Relationship Id="rId{i}" Type="{provider.REL[1:-1]}/worksheet" '
                f'Target="worksheets/sheet{i}.xml"/>'
                for i in range(1, 4)
            )
            + "</Relationships>",
        )
        for i, name in enumerate(names, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet(tables[name]))
    return output.getvalue()
