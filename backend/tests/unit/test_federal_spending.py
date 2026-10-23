"""Reduced OFSS schemas from official XLSX2025; all monetary fixture values are invented.

Source headers/labels/metadata: Tesouro, ODbL1.0, resource f40d5431-058d-48b8-9ab6-065fb0fce5b3.
Real file SHA256:886f4e3266e99907f976c4815dfe8da99ebcf9c670a6ce331925913e88e64b88.
This generated tiny workbook is test evidence only, never a substitute for the official resource.
"""

import io
import json
import zipfile
from copy import deepcopy
from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest

from app.integrations import federal_spending as f

RESOURCE_ID = "f40d5431-058d-48b8-9ab6-065fb0fce5b3"
RESOURCE_URL = (
    f"https://www.tesourotransparente.gov.br/ckan/dataset/{f.DATASET_ID}"
    f"/resource/{RESOURCE_ID}/download/limite-gastos-lc200dez25.xlsx"
)
SUMMARY_LABEL = "2.4.2.1 - Saúde (Discricionárias)"
EXTRA_LABEL = "2.3.3 - Apoio Fin. Municípios / Estados"
COLS = [chr(65 + i) for i in range(26)] + ["A" + chr(65 + i) for i in range(11)]


def workbook(*, rows_change=None, xml_change=None, extra_entries=None, summary_delta="0"):
    strings, indices = [], {}

    def text(value):
        if value not in indices:
            indices[value] = len(strings)
            strings.append(value)
        return str(indices[value])

    sheet = ET.Element(f.NS + "worksheet")
    data = ET.SubElement(sheet, f.NS + "sheetData")
    records = []
    for month in range(1, 13):
        row = dict.fromkeys(COLS, "0")
        row.update(
            A="2025",
            B=str(month),
            C=str((date(2025, month, 1) - date(1899, 12, 30)).days),
            R="10",
            S="SAUDE",
            AI="Primária",
            AK=SUMMARY_LABEL,
            AE="100.25",
            AF="20.00",
            AG="120.25",
        )
        records.append(row)
        if month <= 3:
            records.append(
                {
                    **row,
                    "R": "12",
                    "S": "EDUCACAO",
                    "AI": "Despesa Financeira",
                    "AK": "N/A",
                    "AE": "-10.00",
                    "AF": "0",
                    "AG": "-10.00",
                }
            )
        if month == 1:
            records.append(
                {
                    **row,
                    "R": "99",
                    "S": "N/A",
                    "AI": "Extra-Siafi",
                    "AK": EXTRA_LABEL,
                    "AE": "-1.006",
                    "AF": "0",
                    "AG": "-1.006",
                }
            )
        if month == 2:
            records.append(
                {
                    **row,
                    "R": "99",
                    "S": "RESERVA DE CONTINGENCIA",
                    "AK": "N/A",
                    "AE": "0",
                    "AF": "0",
                    "AG": "0",
                }
            )
        if month == 12:
            records.append(
                {
                    **row,
                    "R": "99",
                    "S": "OUTRAS",
                    "AI": "Extra-Siafi",
                    "AK": "N/A",
                    "AE": "0",
                    "AF": "0",
                    "AG": "0",
                }
            )
    if rows_change:
        rows_change(records)
    ET.SubElement(sheet, f.NS + "dimension", ref=f"A1:AK{len(records) + 1}")

    def cell(parent, col, row, value, *, numeric=False):
        node = ET.SubElement(parent, f.NS + "c", r=f"{col}{row}", t="n" if numeric else "s")
        ET.SubElement(node, f.NS + "v").text = value if numeric else text(value)

    header = ET.SubElement(data, f.NS + "row", r="1")
    for col, value in zip(COLS, f.HEADERS, strict=True):
        cell(header, col, 1, value)
    for index, record in enumerate(records, 2):
        row = ET.SubElement(data, f.NS + "row", r=str(index))
        for col, value in record.items():
            cell(row, col, index, value, numeric=col in ("A", "B", "C", "R", "AE", "AF", "AG"))
    summary = ET.Element(f.NS + "worksheet")
    summary_data = ET.SubElement(summary, f.NS + "sheetData")
    cols = ["P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA"]
    header = ET.SubElement(summary_data, f.NS + "row", r="4")
    cell(header, "O", 4, "Rótulos de Linha")
    for month, col in enumerate(cols, 1):
        cell(header, col, 4, str(month), numeric=True)
    for index, label in enumerate((SUMMARY_LABEL, EXTRA_LABEL), 5):
        row = ET.SubElement(summary_data, f.NS + "row", r=str(index))
        cell(row, "O", index, label)
    total = ET.SubElement(summary_data, f.NS + "row", r="7")
    cell(total, "O", 7, "Total Geral")
    amounts = []
    for month, col in enumerate(cols, 1):
        amount = sum(
            (
                Decimal(r["AG"])
                for r in records
                if r["B"] == str(month) and r["AK"] in (SUMMARY_LABEL, EXTRA_LABEL)
            ),
            Decimal(0),
        )
        amounts.append(amount)
        cell(
            total,
            col,
            7,
            str(amount + Decimal(summary_delta) if month == 1 else amount),
            numeric=True,
        )
    cell(total, "AB", 7, str(sum(amounts, Decimal(0))), numeric=True)
    book = ET.Element(f.NS + "workbook")
    sheets = ET.SubElement(book, f.NS + "sheets")
    ET.SubElement(sheets, f.NS + "sheet", name="2025", attrib={f.REL + "id": "rId1"})
    ET.SubElement(
        sheets, f.NS + "sheet", name="Resumo Pagamento Total", attrib={f.REL + "id": "rId2"}
    )
    relations = ET.Element(f.PKG + "Relationships")
    for number in (1, 2):
        ET.SubElement(
            relations,
            f.PKG + "Relationship",
            Id=f"rId{number}",
            Target=f"worksheets/sheet{number}.xml",
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
        )
    shared = ET.Element(f.NS + "sst")
    for value in strings:
        ET.SubElement(ET.SubElement(shared, f.NS + "si"), f.NS + "t").text = value
    entries = {
        "xl/workbook.xml": ET.tostring(book),
        "xl/_rels/workbook.xml.rels": ET.tostring(relations),
        "xl/sharedStrings.xml": ET.tostring(shared),
        "xl/worksheets/sheet1.xml": ET.tostring(sheet),
        "xl/worksheets/sheet2.xml": ET.tostring(summary),
    }
    if xml_change:
        xml_change(entries)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as z:
        for name, value in [*entries.items(), *(extra_entries or [])]:
            info = zipfile.ZipInfo(name)
            info.filename = name  # Preserve unsafe raw names that Windows ZipInfo normalizes.
            z.writestr(info, value)
    raw = output.getvalue()
    return raw, {
        "id": RESOURCE_ID,
        "url": RESOURCE_URL,
        "size": len(raw),
        "last_modified": "2026-02-25T14:41:36.873214",
    }


def parsed(**kwargs):
    raw, resource = workbook(**kwargs)
    return f.parse_workbook(raw, 2025, resource)


def rehash(payload):
    payload["fingerprint"] = f.fingerprint(payload)
    return payload


def test_complete_cohort_keeps_signed_stages_sparse_coverage_and_distinct_99_groups():
    p = parsed()
    assert p["row_count"] == 18 and len(p["months"]) == 12
    assert p["totals"] == {"PAID": "1171.99", "RAP_PAID": "240.00", "TOTAL_PAID": "1411.99"}
    assert p["reconciliation"]["published_subset"]["annual_difference"] == "0.00"
    keys = {(g["nature"], g["function_key"]): g for g in p["functions"]}
    assert keys[("FINANCIAL", "FUNCTION_12")]["observed_months"] == [1, 2, 3]
    assert keys[("EXTRA_SIAFI", "UNCLASSIFIED_NA")]["amounts"]["TOTAL_PAID"] == "-1.01"
    assert keys[("EXTRA_SIAFI", "UNCLASSIFIED_OTHER")]["function_label"] == "OUTRAS"
    assert keys[("PRIMARY", "FUNCTION_99")]["function_label"] == "RESERVA DE CONTINGENCIA"
    assert f.ABSENCE_POLICY == p["absence_policy"]
    assert not any(g["nature"] == "FINANCIAL" for g in p["months"][3]["groups"])
    f.validate_payload(p)
    assert p["fingerprint"] == f.fingerprint(p)
    json.dumps(p, allow_nan=False)


def test_raw_fraction_audit_and_half_even_precision_are_preserved():
    p = parsed()
    assert Decimal(p["reconciliation"]["raw_minus_rounded_totals"]["TOTAL_PAID"]) == Decimal(
        "0.004"
    )
    assert f._money("-1.005") == Decimal("-1.00")
    assert f._money("1.015") == Decimal("1.02")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p["months"][0].update(month=True),
        lambda p: p["months"][0].update(row_count=True),
        lambda p: p["months"][0]["groups"][0].update(row_count=True),
        lambda p: p["functions"][0].update(observed_months=[True]),
        lambda p: p["natures"][0].update(row_count=True),
        lambda p: p["reconciliation"]["published_subset"]["months"][0].update(month=True),
        lambda p: p["reconciliation"]["published_subset"]["months"][0].update(
            published_total="119.2401"
        ),
        lambda p: p["reconciliation"]["published_subset"].update(annual_difference="0.001"),
        lambda p: p.update(year=True),
        lambda p: p.update(private_notes="Do not expose arbitrary snapshot fields"),
        lambda p: p["source"].update(institution="Other private source"),
        lambda p: p["resource"].update(url="https://example.org/private.xlsx"),
        lambda p: p["months"][0]["groups"][0]["amounts"].update(PAID="100.001"),
        lambda p: p["totals"].update(TOTAL_PAID="1412.00"),
        lambda p: p["functions"][0].update(observed_months=[]),
        lambda p: p["functions"].pop(),
        lambda p: p["natures"].pop(),
        lambda p: p.update(months={}),
    ],
)
def test_rehashed_malformed_snapshot_never_becomes_available(mutation):
    p = parsed()
    mutation(p)
    with pytest.raises(ValueError):
        f.validate_payload(rehash(p))


def test_hash_detects_amount_revision_and_source_file_revision():
    p = parsed()
    changed = deepcopy(p)
    changed["resource"]["sha256"] = "a" * 64
    assert f.fingerprint(changed) != p["fingerprint"]
    with pytest.raises(ValueError):
        f.validate_payload(changed)


@pytest.mark.parametrize(
    "change",
    [
        lambda rows: rows[0].update(A="2024"),
        lambda rows: rows[0].update(B="0"),
        lambda rows: rows[0].update(B="13"),
        lambda rows: rows[0].update(AI="Other nature"),
        lambda rows: rows[0].update(R="99", S="SAUDE"),
        lambda rows: rows[0].update(AE="NaN"),
        lambda rows: rows[0].update(AG="120.24"),
        lambda rows: rows[0].pop("AE"),
        lambda rows: rows.__setitem__(slice(None), [r for r in rows if r["B"] != "6"]),
    ],
)
def test_wrong_period_missing_money_and_inconsistent_source_are_rejected(change):
    with pytest.raises(ValueError):
        parsed(rows_change=change)


@pytest.mark.parametrize(
    "kind", ["formula", "bool", "text_money", "duplicate", "header", "dimension", "entity"]
)
def test_bad_xml_cells_headers_dimensions_and_entities_are_rejected(kind):
    def edit(entries):
        name = "xl/worksheets/sheet1.xml"
        root = ET.fromstring(entries[name])
        cell = root.find(f".//{f.NS}c[@r='AE2']")
        if kind == "formula":
            ET.SubElement(cell, f.NS + "f").text = "1+1"
        if kind == "bool":
            cell.set("t", "b")
        if kind == "text_money":
            cell.set("t", "s")
            cell.find(f.NS + "v").text = "0"
        if kind == "duplicate":
            root.find(f".//{f.NS}row[@r='2']").append(deepcopy(cell))
        if kind == "header":
            root.find(f".//{f.NS}c[@r='AK1']/{f.NS}v").text = "0"
        if kind == "dimension":
            root.find(f.NS + "dimension").set("ref", "A1:AK2")
        entries[name] = ET.tostring(root)
        if kind == "entity":
            entries[name] = b'<!DOCTYPE worksheet [<!ENTITY attack "boom">]>' + entries[name]

    with pytest.raises(ValueError):
        parsed(xml_change=edit)


def test_published_summary_difference_is_not_absorbed_as_other_spending():
    with pytest.raises(ValueError, match="summary"):
        parsed(summary_delta="1")


def test_unused_xml_entities_are_rejected_without_executing_external_connections():
    with pytest.raises(ValueError, match="entities"):
        parsed(extra_entries=[("xl/connections.xml", b"<!DOCTYPE connection><connection/>")])


def test_ignored_utf16_source_metadata_is_scanned_safely_without_parsing_or_execution():
    parsed(extra_entries=[("customXml/item1.xml", "<metadata/>".encode("utf-16"))])
    with pytest.raises(ValueError, match="entities"):
        parsed(
            extra_entries=[
                ("customXml/item1.xml", "<!DOCTYPE metadata><metadata/>".encode("utf-16"))
            ]
        )


@pytest.mark.parametrize(
    "bound", ["MAX_DOWNLOAD", "MAX_EXPANDED", "MAX_SHEET", "MAX_STRINGS", "MAX_ROWS"]
)
def test_zip_and_xml_limits_fail_before_returning_a_cohort(monkeypatch, bound):
    monkeypatch.setattr(f, bound, 10)
    with pytest.raises(ValueError):
        parsed()


@pytest.mark.parametrize(
    "path",
    [
        "../escape.xml",
        "/escape.xml",
        "xl/../escape.xml",
        "xl/./escape.xml",
        "C:/escape.xml",
        "xl\\escape.xml",
    ],
)
def test_zip_paths_are_never_extracted_or_followed(path):
    with pytest.raises(ValueError):
        parsed(extra_entries=[(path, b"safe test bytes")])


def test_duplicate_zip_members_truncation_and_crc_corruption_are_rejected():
    with pytest.warns(UserWarning):
        raw, resource = workbook(extra_entries=[("xl/workbook.xml", b"duplicate")])
    with pytest.raises(ValueError):
        f.parse_workbook(raw, 2025, resource)
    raw, resource = workbook()
    corrupt = bytearray(raw)
    offset = raw.index(b"100.25")
    corrupt[offset] = ord("9")
    with pytest.raises(ValueError):
        f.parse_workbook(bytes(corrupt), 2025, resource)
    with pytest.raises(ValueError):
        f.parse_workbook(raw[:-10], 2025, {**resource, "size": len(raw) - 10})


def catalog(size="34500062", **updates):
    resource = {
        "id": RESOURCE_ID,
        "url": RESOURCE_URL,
        "size": size,
        "format": "XLSX",
        "name": "Despesas e Transferências da União - 2025",
        "last_modified": "2026-02-25T14:41:36.873214",
    }
    resource.update(updates)
    return {
        "success": True,
        "result": {
            "id": f.DATASET_ID,
            "name": "despesas-e-transferencias-totais",
            "license_id": "odc-odbl",
            "resources": [resource],
        },
    }


def test_catalog_accepts_real_ckan_integer_string_size_and_rejects_ambiguous_license():
    assert f._metadata(catalog(), 2025)["size"] == 34500062
    data = catalog()
    data["result"]["license_id"] = "MIT"
    with pytest.raises(ValueError):
        f._metadata(data, 2025)
    data = catalog()
    data["result"]["resources"] *= 2
    with pytest.raises(ValueError):
        f._metadata(data, 2025)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.tesourotransparente.gov.br/a.xlsx",
        "https://example.org/a.xlsx",
        RESOURCE_URL + "?url=https://example.org",
        RESOURCE_URL.replace("/download/", "/download/../"),
        RESOURCE_URL.replace(".xlsx", ".xlsm"),
        RESOURCE_URL.replace(
            "www.tesourotransparente.gov.br", "user:password@www.tesourotransparente.gov.br"
        ),
    ],
)
def test_catalog_cannot_trigger_arbitrary_url_downloads(url):
    with pytest.raises(ValueError):
        f._metadata(catalog(url=url), 2025)


def test_fetch_uses_only_catalog_then_reviewed_annual_resource(monkeypatch):
    raw, resource = workbook()
    calls = []
    data = catalog(size=str(len(raw)))

    def download(url, limit):
        calls.append((url, limit))
        return json.dumps(data).encode() if url == f.CATALOG_URL else raw

    monkeypatch.setattr(f, "_download", download)
    result = f.fetch_year(2025, date(2026, 10, 11))
    assert result["row_count"] == 18
    assert calls == [(f.CATALOG_URL, 1_000_000), (resource["url"], f.MAX_DOWNLOAD)]
    with pytest.raises(ValueError):
        f.fetch_year(2026, date(2026, 10, 11))
    with pytest.raises(ValueError):
        f.fetch_year(True, date(2026, 10, 11))


def test_download_rejects_redirects_encoding_large_body_and_truncation(monkeypatch):
    class Response(io.BytesIO):
        headers = {}
        url = f.CATALOG_URL

        def geturl(self):
            return self.url

    class Opener:
        response = None

        def open(self, request, timeout):
            assert request.full_url == f.CATALOG_URL and timeout == 20
            return self.response

    opener = Opener()
    monkeypatch.setattr(f, "build_opener", lambda handler: opener)
    for headers, url, body in [
        ({"Content-Length": "11"}, f.CATALOG_URL, b"x"),
        ({"Content-Length": "2"}, f.CATALOG_URL, b"x"),
        ({"Content-Encoding": "gzip"}, f.CATALOG_URL, b"x"),
        ({}, "https://example.org/redirect", b"x"),
        ({}, f.CATALOG_URL, b"x" * 11),
    ]:
        response = Response(body)
        response.headers = headers
        response.url = url
        opener.response = response
        with pytest.raises(ValueError):
            f._download(f.CATALOG_URL, 10)
