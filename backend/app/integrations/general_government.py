"""Official annual GFSM modified-accrual cohort; never a handmade RTN consolidation."""

import hashlib
import json
import re
import time
import zipfile
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from html import unescape
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree.ElementTree import ParseError

from app.integrations.federal_spending import NS, PKG, REL, _small_xml, _strings, _zip

SOURCE_URL = (
    "https://www.tesourotransparente.gov.br/publicacoes/estatisticas-fiscais-do-governo-geral"
)
TERMS_URL = "https://www.tesourotransparente.gov.br/sobre/dados-abertos/termos-de-uso"
SOURCE = {
    "title": "Estatísticas Fiscais do Governo Geral — demonstrativo anual por esfera",
    "institution": "Secretaria do Tesouro Nacional",
    "url": SOURCE_URL,
    "license": "Termos de uso do Tesouro Transparente (atribuição)",
    "license_url": TERMS_URL,
}
PARSER_VERSION = "1.0.0"
PRECISION_VERSION = "million-cell-half-even-cent-v1"
MAX_DOWNLOAD = 3_000_000
MAX_EXPANDED = 20_000_000
TOLERANCE = Decimal("0.03")
METRICS = {
    "revenue": ("1", "Receita"),
    "interest_revenue": ("1411", "Juros"),
    "expense": ("2M", "Despesa (2+31)"),
    "spending": ("2", "Gasto"),
    "interest_expense": ("24", "Juros"),
    "net_investment": ("31", "Investimento líquido"),
    "net_lending": (None, "Capacidade (+)/Necessidade(-) líquida de financiamento (1-2M)"),
    "primary_net_lending": (
        None,
        "Capacidade (+)/Necessidade(-) líquida de financiamento primária",
    ),
}
SECTORS = {
    "CENTRAL_BUDGETARY": "Governo Central Orçamentário",
    "CENTRAL_EXTRA_BUDGETARY": "Governo Central Extraorçamentário",
    "CENTRAL_CONSOLIDATION": "Consolidação do Governo Central",
    "CENTRAL": "Governo Central (GFSM 2014)",
    "STATES": "Governos Estaduais e Distrito Federal",
    "MUNICIPALITIES": "Governos Municipais",
    "GENERAL_CONSOLIDATION": "Consolidação do Governo Geral",
    "GENERAL": "Governo Geral consolidado",
}
COVERAGE = {
    "states_units": 27,
    "municipal_units": 5570,
    "municipal_collection_approx_percent": "90",
    "municipal_extrapolated": True,
    "central_excludes_bcb": True,
}
_DECIMAL = re.compile(r"[+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d{1,2})?\Z")
_CELL = re.compile(r"([A-Z]{1,3})([1-9]\d{0,3})\Z")


def _year(year, as_of):
    if type(year) is not int or type(as_of) is not date or not 2010 <= year < as_of.year:
        raise ValueError("Select one closed year from the official annual series.")


def _approved(url, kind):
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or p.username
        or p.password
        or p.port not in (None, 443)
        or p.query
        or p.fragment
    ):
        raise ValueError("Unapproved fiscal publication URL.")
    if kind == "page":
        valid = p.hostname == "www.tesourotransparente.gov.br" and re.fullmatch(
            r"/publicacoes/estatisticas-fiscais-do-governo-geral(?:/\d{4}/\d+)?", p.path
        )
    else:
        valid = (
            p.hostname == "thot-arquivos.tesouro.gov.br"
            and re.fullmatch(r"/publicacao/[1-9]\d*", p.path)
        ) or (
            p.hostname == "cdn.tesouro.gov.br"
            and re.fullmatch(
                r"/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/"
                r"[1-9]\d*_[1-9]\d*/demonstrativos-governo-geral\.xlsx",
                p.path,
            )
        )
    if not valid:
        raise ValueError("Fiscal resource host or path differs from the reviewed publication.")


class _NoFollow(HTTPRedirectHandler):
    """Expose redirects as HTTPError for the explicit official-host checks below."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _request(url, kind, *, head=False):
    opener = build_opener(_NoFollow())
    limit = MAX_DOWNLOAD if kind == "file" else 500_000
    started = time.monotonic()
    for _ in range(4):
        if time.monotonic() - started > 120:
            raise ValueError("Fiscal request exceeded its total time budget.")
        _approved(url, kind)
        try:
            response = opener.open(
                Request(
                    url,
                    method="HEAD" if head else "GET",
                    headers={
                        "User-Agent": "BrasilPorTodos/0.1",
                        "Accept-Encoding": "identity",
                    },
                ),
                timeout=20,
            )
        except HTTPError as exc:
            if exc.code not in (301, 302, 303, 307, 308) or not exc.headers.get("Location"):
                raise
            url = urljoin(url, exc.headers["Location"])
            continue
        with response:
            if (
                response.geturl() != url
                or response.headers.get("Content-Encoding", "identity") != "identity"
            ):
                raise ValueError("Unexpected publication response.")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or not 0 < int(length) <= limit):
                raise ValueError("Fiscal download exceeds its bound.")
            chunks, size = [], 0
            if not head:
                while chunk := response.read(min(65536, limit - size + 1)):
                    size += len(chunk)
                    if size > limit or time.monotonic() - started > 120:
                        raise ValueError("Fiscal response exceeded bytes or total time budget.")
                    chunks.append(chunk)
            raw = b"".join(chunks)
            if len(raw) > limit or (not head and length and len(raw) != int(length)):
                raise ValueError("Truncated or oversized fiscal response.")
            return raw, {
                "url": url,
                "size": int(length) if length else None,
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    raise ValueError("Too many fiscal publication redirects.")


def _publication(raw):
    text = raw.decode("utf-8")
    urls = re.findall(r'<a\b[^>]*class="download"[^>]*href="([^"]+)"', text)
    if len(urls) != 1:
        raise ValueError("Exactly one principal annual publication is required.")
    download = unescape(urls[0])
    _approved(download, "file")
    if urlsplit(download).hostname != "thot-arquivos.tesouro.gov.br":
        raise ValueError("Principal publication identifier is missing.")
    updated = re.search(r"Dados atualizados em (\d{2}/\d{2}/\d{4})", text)
    published = re.search(r'<time datetime="(\d{4}/\d{2}/\d{2})[^\"]*">', text)
    if not updated or not published:
        raise ValueError("Missing publication revision metadata.")
    return {
        "publication_id": download.rsplit("/", 1)[-1],
        "download_url": download,
        "updated_at": datetime.strptime(updated[1], "%d/%m/%Y").date().isoformat(),
        "published_at": datetime.strptime(published[1], "%Y/%m/%d").date().isoformat(),
    }


def _column(number):
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _number(raw):
    if not isinstance(raw, str) or len(raw) > 60 or not _DECIMAL.fullmatch(raw):
        raise ValueError("Money must be a finite decimal from a cached source cell.")
    value = Decimal(raw)
    if not value.is_finite() or abs(value) >= Decimal("100000000"):
        raise ValueError("Fiscal aggregate exceeds its bound in millions.")
    return value


def _amount(raw):
    value = (_number(raw) * 1_000_000).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return format(value if value else Decimal(0), ".2f")


def _difference(value):
    return format(value if value else Decimal(0), ".2f")


def _sheet(z, path, strings):
    root = _small_xml(z, path, 1_500_000)
    if root.tag != NS + "worksheet":
        raise ValueError("Unexpected annual worksheet namespace.")
    result, previous, seen, numeric = {}, 0, set(), set()
    for row in root.findall(NS + "sheetData/" + NS + "row"):
        index = row.get("r", "")
        if not index.isdigit() or not previous < int(index) <= 200:
            raise ValueError("Unordered or duplicate annual rows.")
        previous = int(index)
        for cell in row.findall(NS + "c"):
            location = cell.get("r", "")
            match = _CELL.fullmatch(location)
            if not match or int(match[2]) != previous or location in seen:
                raise ValueError("Duplicate or invalid annual cell.")
            seen.add(location)
            if cell.find(NS + "f") is not None or len(cell.findall(NS + "v")) > 1:
                raise ValueError(
                    "Formulas and duplicate cached values are not reviewed observations."
                )
            kind, value = cell.get("t", "n"), cell.findtext(NS + "v")
            if kind == "s":
                if value is None or not value.isdigit() or int(value) >= len(strings):
                    raise ValueError("Invalid source string index.")
                value = strings[int(value)]
            elif kind == "inlineStr":
                value = "".join(t.text or "" for t in cell.iter(NS + "t"))
            elif kind != "n":
                raise ValueError("Unexpected cached annual cell type.")
            if value is not None:
                result[location] = value
                if kind == "n":
                    numeric.add(location)
    return result, numeric


def _locations(sheet):
    result = {}
    for key, (code, label) in METRICS.items():
        rows = []
        for location, value in sheet.items():
            if not re.fullmatch(r"B\d+", location):
                continue
            index = location[1:]
            if value.strip().startswith(label) and (code is None or sheet.get("A" + index) == code):
                rows.append(int(index))
        if len(rows) != 1:
            raise ValueError("Annual metric identity is missing or duplicated.")
        result[key] = rows[0]
    return result


def _reconciliation(sectors, references):
    by_sector = {
        row["sector"]: {k: Decimal(v) for k, v in row["amounts"].items()} for row in sectors
    }
    identities = []
    for sector, values in by_sector.items():
        identities.append(
            {
                "sector": sector,
                "expense_difference": _difference(
                    values["expense"] - values["spending"] - values["net_investment"]
                ),
                "net_lending_difference": _difference(
                    values["net_lending"] - values["revenue"] + values["expense"]
                ),
                "primary_difference": _difference(
                    values["primary_net_lending"]
                    - values["net_lending"]
                    - values["interest_expense"]
                    + values["interest_revenue"]
                ),
            }
        )
    consolidation = []
    for metric in METRICS:
        consolidation.append(
            {
                "metric": metric,
                "central_difference": _difference(
                    sum(by_sector[s][metric] for s in list(SECTORS)[:3])
                    - by_sector["CENTRAL"][metric]
                ),
                "general_difference": _difference(
                    sum(
                        by_sector[s][metric]
                        for s in ("CENTRAL", "STATES", "MUNICIPALITIES", "GENERAL_CONSOLIDATION")
                    )
                    - by_sector["GENERAL"][metric]
                ),
            }
        )
    reference = [
        {
            **row,
            "difference": _difference(by_sector["GENERAL"][row["metric"]] - Decimal(row["amount"])),
        }
        for row in references
    ]
    return {
        "tolerance": str(TOLERANCE),
        "identities": identities,
        "consolidation": consolidation,
        "general_reference": reference,
    }


def fingerprint(payload):
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in payload.items() if k != "fingerprint"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def parse_workbook(raw, year, resource):
    _year(year, date.today())
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_DOWNLOAD:
        raise ValueError("Unbounded general-government workbook.")
    try:
        with zipfile.ZipFile(BytesIO(raw)) as inspected:
            if sum(item.file_size for item in inspected.infolist()) > MAX_EXPANDED:
                raise ValueError("Expanded annual workbook exceeds its bound.")
        with _zip(raw) as z:
            workbook = _small_xml(z, "xl/workbook.xml", 100_000)
            relationships = _small_xml(z, "xl/_rels/workbook.xml.rels", 100_000)
            relations = {r.get("Id"): r for r in relationships.findall(PKG + "Relationship")}
            if len(relations) != len(relationships):
                raise ValueError("Duplicate annual workbook relationships.")
            paths = {}
            for item in workbook.findall(NS + "sheets/" + NS + "sheet"):
                name = item.get("name")
                if name not in ("2.1", "3.1", "Metadados"):
                    continue
                relation = relations.get(item.get(REL + "id"))
                if (
                    relation is None
                    or relation.get("TargetMode") == "External"
                    or not relation.get("Type", "").endswith("/worksheet")
                ):
                    raise ValueError("Unapproved annual worksheet relation.")
                target = relation.get("Target", "")
                if name in paths or not re.fullmatch(r"worksheets/sheet[1-9]\d*\.xml", target):
                    raise ValueError("Invalid annual worksheet target.")
                paths[name] = "xl/" + target
            if set(paths) != {"2.1", "3.1", "Metadados"}:
                raise ValueError("Annual partitions, independent total and coverage are required.")
            strings = _strings(z) if "xl/sharedStrings.xml" in z.namelist() else []
            loaded = {name: _sheet(z, path, strings) for name, path in paths.items()}
            sheets = {name: item[0] for name, item in loaded.items()}
            numeric = {name: item[1] for name, item in loaded.items()}
            for name in ("2.1", "3.1"):
                if sheets[name].get("A2", "").strip() != "R$ Milhões - Valores Correntes":
                    raise ValueError("Annual unit or price basis changed.")
            metadata = " ".join(sheets["Metadados"].values())
            for required in (
                "26 estados e do Distrito Federal",
                "5.570 municípios",
                "90%",
                "extrapolar",
                "exceto o Banco Central do Brasil",
                "competência modificada",
            ):
                if required not in metadata:
                    raise ValueError("Reviewed coverage or registration basis changed.")
            table, reference = sheets["2.1"], sheets["3.1"]
            starts = [
                key[:-1]
                for key, value in table.items()
                if key in numeric["2.1"] and re.fullmatch(r"[A-Z]+4", key) and value == str(year)
            ]
            expected_start = _column(3 + 8 * (year - 2010))
            if starts != [expected_start]:
                raise ValueError(
                    "The selected closed year is absent or ambiguous in annual partitions."
                )
            reference_columns = [
                key[:-1]
                for key, value in reference.items()
                if key in numeric["3.1"] and re.fullmatch(r"[A-Z]+4", key) and value == str(year)
            ]
            if len(reference_columns) != 1:
                raise ValueError("Independent annual total for selected year is missing.")
            rows, ref_rows = _locations(table), _locations(reference)
            sectors = []
            expected_headers = [
                "Orçamentário",
                "Extraorçamentário",
                "Coluna de Consolidação",
                "Governo Central",
                "Governos Estaduais",
                "Governos Municipais",
                "Coluna de Consolidação",
                "Governo Geral",
            ]
            for offset, (sector, label) in enumerate(SECTORS.items()):
                col = _column(3 + 8 * (year - 2010) + offset)
                header = table.get(col + ("6" if offset < 4 else "5"), "")
                if not header.startswith(expected_headers[offset]):
                    raise ValueError("Annual sector or consolidation order changed.")
                cells = {key: f"{col}{index}" for key, index in rows.items()}
                if any(cell not in numeric["2.1"] for cell in cells.values()):
                    raise ValueError("Selected annual amounts must be source numeric cells.")
                original = {key: table[cell] for key, cell in cells.items()}
                sectors.append(
                    {
                        "sector": sector,
                        "label": label,
                        "column": col,
                        "cells": cells,
                        "raw_millions": original,
                        "amounts": {key: _amount(value) for key, value in original.items()},
                    }
                )
            references = []
            for metric, row in ref_rows.items():
                cell = reference_columns[0] + str(row)
                if cell not in numeric["3.1"]:
                    raise ValueError("Independent annual total must be a source numeric cell.")
                original = reference[cell]
                references.append(
                    {
                        "metric": metric,
                        "cell": cell,
                        "raw_millions": original,
                        "amount": _amount(original),
                    }
                )
            p = {
                "year": year,
                "currency": "BRL",
                "price_basis": "CURRENT",
                "accounting_basis": "MODIFIED_ACCRUAL",
                "methodology_basis": "GFSM_2014",
                "period_basis": "FULL_YEAR",
                "parser_version": PARSER_VERSION,
                "precision_version": PRECISION_VERSION,
                "source": dict(SOURCE),
                "coverage": dict(COVERAGE),
                "resource": {
                    **resource,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "size": len(raw),
                },
                "sectors": sectors,
                "reconciliation": _reconciliation(sectors, references),
            }
            p["fingerprint"] = fingerprint(p)
            validate_payload(p)
            return p
    except (
        KeyError,
        TypeError,
        IndexError,
        InvalidOperation,
        zipfile.BadZipFile,
        ParseError,
        UnicodeDecodeError,
    ) as error:
        raise ValueError("Incomplete or incompatible general-government workbook.") from error


def validate_payload(p):
    try:
        _validate(p)
    except (KeyError, TypeError, AttributeError, InvalidOperation, OverflowError) as error:
        raise ValueError("Incomplete or incompatible general-government cohort.") from error


def _validate(p):
    expected = {
        "currency": "BRL",
        "price_basis": "CURRENT",
        "accounting_basis": "MODIFIED_ACCRUAL",
        "methodology_basis": "GFSM_2014",
        "period_basis": "FULL_YEAR",
        "parser_version": PARSER_VERSION,
        "precision_version": PRECISION_VERSION,
        "source": SOURCE,
        "coverage": COVERAGE,
    }
    if (
        not isinstance(p, dict)
        or set(p) != {*expected, "year", "resource", "sectors", "reconciliation", "fingerprint"}
        or any(p.get(k) != v for k, v in expected.items())
    ):
        raise ValueError("General-government cohort definitions changed.")
    if (
        type(p["coverage"]["municipal_extrapolated"]) is not bool
        or type(p["coverage"]["central_excludes_bcb"]) is not bool
    ):
        raise ValueError("Coverage flags cannot be inferred from numeric values.")
    if any(type(p["coverage"][key]) is not int for key in ("states_units", "municipal_units")):
        raise ValueError("Coverage unit counts must be explicit integers.")
    _year(p["year"], date.today())
    resource = p["resource"]
    if not isinstance(resource, dict) or set(resource) != {
        "publication_url",
        "publication_id",
        "download_url",
        "url",
        "published_at",
        "updated_at",
        "size",
        "sha256",
        "etag",
        "last_modified",
    }:
        raise ValueError("Resource revision metadata changed.")
    _approved(resource["publication_url"], "page")
    _approved(resource["download_url"], "file")
    _approved(resource["url"], "file")
    if (
        not re.fullmatch(r"[1-9]\d*", resource["publication_id"])
        or resource["download_url"]
        != f"https://thot-arquivos.tesouro.gov.br/publicacao/{resource['publication_id']}"
    ):
        raise ValueError("Publication identity is inconsistent.")
    if not resource["url"].startswith(
        f"https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/{resource['publication_id']}_"
    ):
        raise ValueError("Publication and CDN revision differ.")
    for key in ("published_at", "updated_at"):
        if (
            not isinstance(resource[key], str)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", resource[key])
            or date.fromisoformat(resource[key]) > date.today()
        ):
            raise ValueError("Invalid publication revision date.")
    for key in ("etag", "last_modified"):
        if resource[key] is not None and (
            not isinstance(resource[key], str) or len(resource[key]) > 200
        ):
            raise ValueError("Invalid resource header metadata.")
    if (
        type(resource["size"]) is not int
        or not 0 < resource["size"] <= MAX_DOWNLOAD
        or not isinstance(resource["sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", resource["sha256"])
    ):
        raise ValueError("Invalid source file size or SHA.")
    if p["fingerprint"] != fingerprint(p):
        raise ValueError("Canonical general-government fingerprint differs.")

    def cents(raw):
        if (
            not isinstance(raw, str)
            or not re.fullmatch(r"-?\d+\.\d{2}", raw)
            or abs(Decimal(raw)) >= Decimal("100000000000000")
        ):
            raise ValueError("Invalid monetary cent string.")
        return Decimal(raw)

    if not isinstance(p["sectors"], list) or [r["sector"] for r in p["sectors"]] != list(SECTORS):
        raise ValueError("All eight official sector and consolidation columns are required.")
    for offset, row in enumerate(p["sectors"]):
        if (
            set(row) != {"sector", "label", "column", "cells", "raw_millions", "amounts"}
            or row["label"] != SECTORS[row["sector"]]
            or row["column"] != _column(3 + 8 * (p["year"] - 2010) + offset)
        ):
            raise ValueError("Sector identity or annual column differs.")
        if any(
            not isinstance(row[k], dict) or set(row[k]) != set(METRICS)
            for k in ("cells", "raw_millions", "amounts")
        ):
            raise ValueError("All eight metric cells are required.")
        if len(set(row["cells"].values())) != len(METRICS):
            raise ValueError("Duplicate annual metric cells.")
        for metric in METRICS:
            if (
                not isinstance(row["cells"][metric], str)
                or not re.fullmatch(row["column"] + r"[1-9]\d{0,2}", row["cells"][metric])
                or row["amounts"][metric] != _amount(row["raw_millions"][metric])
            ):
                raise ValueError("Source locators or monetary normalization differ.")
            cents(row["amounts"][metric])
    recon = p["reconciliation"]
    if not isinstance(recon, dict) or set(recon) != {
        "tolerance",
        "identities",
        "consolidation",
        "general_reference",
    }:
        raise ValueError("Incomplete general-government reconciliations.")
    if not isinstance(recon["general_reference"], list) or [
        r["metric"] for r in recon["general_reference"]
    ] != list(METRICS):
        raise ValueError("Independent annual total coverage differs.")
    if len({row["cell"] for row in recon["general_reference"]}) != len(METRICS):
        raise ValueError("Independent annual metric cells must be distinct.")
    references = []
    ref_col = _column(3 + p["year"] - 2010)
    for row in recon["general_reference"]:
        if (
            set(row) != {"metric", "cell", "raw_millions", "amount", "difference"}
            or not re.fullmatch(ref_col + r"[1-9]\d{0,2}", row["cell"])
            or row["amount"] != _amount(row["raw_millions"])
        ):
            raise ValueError("Independent source amount or locator differs.")
        cents(row["amount"])
        references.append({k: v for k, v in row.items() if k != "difference"})
    if recon != _reconciliation(p["sectors"], references):
        raise ValueError("Source reconciliation evidence differs from amounts.")
    for group, excluded in (
        ("identities", "sector"),
        ("consolidation", "metric"),
        ("general_reference", None),
    ):
        for row in recon[group]:
            keys = [k for k in row if k != excluded] if excluded else ["difference"]
            if any(abs(cents(row[key])) > TOLERANCE for key in keys):
                raise ValueError(
                    "Published fiscal identities differ beyond cell rounding allowance."
                )


def fetch_year(year, as_of):
    _year(year, as_of)
    page, page_info = _request(SOURCE_URL, "page")
    before = _publication(page)
    # The reviewed thot origin does not support HEAD. Re-read its pointer with
    # bounded GETs and require the exact same file and semantic revision headers.
    raw, downloaded = _request(before["download_url"], "file")
    verified_raw, verified_headers = _request(before["download_url"], "file")
    after_page, _ = _request(SOURCE_URL, "page")
    if (
        downloaded != verified_headers
        or hashlib.sha256(raw).digest() != hashlib.sha256(verified_raw).digest()
        or before != _publication(after_page)
    ):
        raise ValueError("Official publication revision changed during collection.")
    return parse_workbook(raw, year, {**before, **downloaded, "publication_url": page_info["url"]})
