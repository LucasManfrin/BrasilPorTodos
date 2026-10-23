"""General-government parser, canonical cohort and bounded transport use invented fixtures."""

from copy import deepcopy
from datetime import date
from io import BytesIO
from urllib.error import HTTPError
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.integrations import general_government as provider
from tests.general_government_fixture import payload, resource, workbook


def rehash(p):
    p["fingerprint"] = provider.fingerprint(p)
    return p


@pytest.mark.parametrize("year", [2024, 2025])
@pytest.mark.parametrize("revenue", ["1000.10", "-1000.10", "0.00"])
def test_exact_year_signed_values_and_all_published_columns_are_preserved(year, revenue):
    raw = workbook(year, revenue)
    result = provider.parse_workbook(raw, year, resource())
    assert result["year"] == year and len(result["sectors"]) == 8
    assert list(result["sectors"][0]["amounts"]) == list(provider.METRICS)
    assert result["resource"]["size"] == len(raw)
    assert result["coverage"]["municipal_extrapolated"] is True
    assert result["source"]["license"] != "ODbL 1.0"
    assert result["sectors"][0]["amounts"]["revenue"] == revenue
    assert result["sectors"][6]["amounts"]["revenue"] == "-100.00"
    assert (
        result["sectors"][1]["amounts"]["revenue"] == "0.00"
    )  # Explicit source zero, not missing.
    assert result["fingerprint"] == provider.fingerprint(result)


@pytest.mark.parametrize("failure", ["unit", "year", "metric", "coverage", "order", "reference"])
def test_missing_or_changed_workbook_contract_never_becomes_zero_or_other_year(failure):
    def mutate(tables):
        if failure == "unit":
            tables["2.1"]["A2"] = "R$ correntes"
        if failure == "year":
            tables["2.1"]["DS4"] = "2024"
        if failure == "metric":
            del tables["2.1"]["DW7"]
        if failure == "coverage":
            tables["Metadados"]["B2"] = "100% observed"
        if failure == "order":
            tables["2.1"]["DW5"] = "Governos Municipais"
        if failure == "reference":
            del tables["3.1"]["R5"]

    with pytest.raises(ValueError):
        provider.parse_workbook(workbook(mutate=mutate), 2025, resource())


@pytest.mark.parametrize(
    "injection",
    [
        "<f>1+1</f><v>0.00100010</v>",
        "<v>0.00100010</v><v>0.00100010</v>",
        "<is><t>0.00100010</t></is>",
        "<v>#VALUE!</v>",
    ],
)
def test_formula_duplicate_cached_value_inline_money_and_error_cells_are_rejected(injection):
    raw = workbook()
    output = BytesIO()
    with ZipFile(BytesIO(raw)) as source, ZipFile(output, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            content = source.read(name)
            if name == "xl/worksheets/sheet1.xml":
                content = content.replace(
                    b'<c r="DS7"><v>0.00100010</v></c>',
                    (
                        '<c r="DS7"'
                        + (' t="inlineStr"' if injection.startswith("<is>") else "")
                        + ">"
                        + injection
                        + "</c>"
                    ).encode(),
                )
            target.writestr(name, content)
    with pytest.raises(ValueError):
        provider.parse_workbook(output.getvalue(), 2025, resource())


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("201.46320482703", "201463204.83"),
        ("1.234567895", "1234567.90"),
        ("-1.234567895", "-1234567.90"),
        ("0.000000005", "0.00"),
        ("0.000000015", "0.02"),
    ],
)
def test_millions_scale_and_cell_half_even_precision_are_explicit(raw, expected):
    assert provider._amount(raw) == expected


@pytest.mark.parametrize(
    "failure",
    [
        "currency",
        "basis",
        "precision",
        "terms",
        "extra_field",
        "missing_sector",
        "duplicate_sector",
        "amount",
        "raw",
        "locator",
        "reconciliation",
        "coverage_bool",
        "resource_id",
        "source_hash",
    ],
)
def test_tampered_snapshots_rejected_even_with_new_canonical_fingerprint(failure):
    p = payload()
    if failure == "currency":
        p["currency"] = "USD"
    if failure == "basis":
        p["accounting_basis"] = "CASH"
    if failure == "precision":
        p["precision_version"] = "changed"
    if failure == "terms":
        p["source"]["license"] = "ODbL 1.0"
    if failure == "extra_field":
        p["created_by"] = "private-author-id"
    if failure == "missing_sector":
        p["sectors"].pop()
    if failure == "duplicate_sector":
        p["sectors"][1] = deepcopy(p["sectors"][0])
    if failure == "amount":
        p["sectors"][0]["amounts"]["revenue"] = "1001.00"
    if failure == "raw":
        p["sectors"][0]["raw_millions"]["revenue"] = "NaN"
    if failure == "locator":
        p["sectors"][0]["cells"]["revenue"] = "DS36"
    if failure == "reconciliation":
        p["reconciliation"]["identities"][0]["expense_difference"] = "1.00"
    if failure == "coverage_bool":
        p["coverage"]["municipal_extrapolated"] = 1
    if failure == "resource_id":
        p["resource"]["publication_id"] = "999"
    if failure == "source_hash":
        p["resource"]["sha256"] = "bad"
    with pytest.raises(ValueError):
        provider.validate_payload(rehash(p))


def test_rounding_residual_is_exposed_and_never_forced_to_zero():
    p = payload()
    last = p["sectors"][-1]
    last["amounts"]["expense"] = "1077.01"
    last["raw_millions"]["expense"] = "0.00107701"
    references = [
        {k: v for k, v in row.items() if k != "difference"}
        for row in p["reconciliation"]["general_reference"]
    ]
    references[2]["amount"] = "1077.01"
    references[2]["raw_millions"] = "0.00107701"
    p["reconciliation"] = provider._reconciliation(p["sectors"], references)
    provider.validate_payload(rehash(p))
    assert p["reconciliation"]["identities"][-1]["expense_difference"] == "0.01"
    assert p["reconciliation"]["consolidation"][2]["general_difference"] == "-0.01"


@pytest.mark.parametrize(
    "url",
    [
        "http://thot-arquivos.tesouro.gov.br/publicacao/40185",
        "https://thot-arquivos.tesouro.gov.br.evil.test/publicacao/40185",
        "https://user:secret@thot-arquivos.tesouro.gov.br/publicacao/40185",
        "https://thot-arquivos.tesouro.gov.br/publicacao/40185?redirect=evil",
        "https://cdn.tesouro.gov.br/another.xlsx",
        "https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/40185_2097592/other.xlsx",
    ],
)
def test_arbitrary_or_changed_resource_urls_are_rejected(url):
    with pytest.raises(ValueError):
        provider._approved(url, "file")


PAGE = (
    b'<a class="download" href="https://thot-arquivos.tesouro.gov.br/publicacao/40185">'
    b'Download</a><time datetime="2026/10/01 00:00:00 GMT-3">01/10/2026</time>'
    b"<p>Dados atualizados em 30/09/2026</p>"
)


@pytest.mark.parametrize("change", [None, "etag", "page", "bytes"])
def test_fetch_rechecks_publication_and_resource_revision_before_return(monkeypatch, change):
    raw = workbook()
    calls = []
    file_info = {
        "url": resource()["url"],
        "size": len(raw),
        "etag": "revision-one",
        "last_modified": None,
    }

    def request(url, kind, *, head=False):
        calls.append((url, kind, head))
        if head:
            raise HTTPError(url, 405, "HEAD unsupported", {}, None)
        if kind == "page":
            page = (
                PAGE.replace(b"30/09/2026", b"01/10/2026")
                if len(calls) > 1 and change == "page"
                else PAGE
            )
            return page, {
                "url": resource()["publication_url"],
                "size": len(page),
                "etag": None,
                "last_modified": None,
            }
        metadata = dict(file_info)
        if change == "etag" and len(calls) == 3:
            metadata["etag"] = "revision-two"
        body = raw[:-1] + bytes([raw[-1] ^ 1]) if change == "bytes" and len(calls) == 3 else raw
        return body, metadata

    monkeypatch.setattr(provider, "_request", request)
    if change:
        with pytest.raises(ValueError):
            provider.fetch_year(2025, date(2026, 10, 11))
    else:
        p = provider.fetch_year(2025, date(2026, 10, 11))
        assert p["year"] == 2025 and p["resource"]["etag"] == "revision-one"
    assert len(calls) == 4 and not any(head for _, _, head in calls)


class Reply:
    def __init__(self, url, raw, headers):
        self.url, self.raw, self.headers = url, BytesIO(raw), headers

    def geturl(self):
        return self.url

    def read(self, size):
        return self.raw.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@pytest.mark.parametrize("failure", ["size", "truncated", "encoding", "redirect", "time"])
def test_bounded_http_rejects_limits_and_unapproved_redirect_before_following(monkeypatch, failure):
    url = resource()["download_url"]
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(request.full_url)
            if failure == "redirect":
                raise HTTPError(
                    url, 302, "redirect", {"Location": "https://example.com/secret"}, None
                )
            headers = {"Content-Length": "5000000" if failure == "size" else "3"}
            if failure == "encoding":
                headers["Content-Encoding"] = "gzip"
            return Reply(url, b"ab" if failure == "truncated" else b"abc", headers)

    monkeypatch.setattr(provider, "build_opener", lambda *args: Opener())
    if failure == "time":
        readings = iter([0, 0, 130])
        monkeypatch.setattr(provider.time, "monotonic", lambda: next(readings))
    with pytest.raises(ValueError):
        provider._request(url, "file")
    assert calls == [url]


@pytest.mark.parametrize("year", [True, 2026, 2009])
def test_open_year_or_boolean_never_calls_network(monkeypatch, year):
    monkeypatch.setattr(provider, "_request", lambda *args: pytest.fail("must not fetch"))
    with pytest.raises(ValueError):
        provider.fetch_year(year, date(2026, 10, 11))


def test_coverage_counts_cannot_be_floats_and_independent_locators_cannot_repeat():
    p = payload()
    p["coverage"]["states_units"] = 27.0
    with pytest.raises(ValueError):
        provider.validate_payload(rehash(p))
    p = payload()
    p["reconciliation"]["general_reference"][1]["cell"] = "R5"
    with pytest.raises(ValueError):
        provider.validate_payload(rehash(p))


def test_real_redirect_handler_surfaces_http_error_and_manual_chain_is_allowlisted(monkeypatch):
    from email.message import Message
    from urllib.request import BaseHandler, Request, build_opener
    from urllib.response import addinfourl

    url = resource()["download_url"]
    final = resource()["url"]
    headers = Message()
    headers["Location"] = final
    handler = provider._NoFollow()
    assert handler.redirect_request(None, None, 302, "Found", headers, final) is None
    assert handler.http_error_302(Request(url), BytesIO(), 302, "Found", headers) is None
    opened = []

    class Transport(BaseHandler):
        handler_order = 100

        def https_open(self, request):
            opened.append(request.full_url)
            if request.full_url == url:
                reply = addinfourl(BytesIO(), headers, url, 302)
                reply.msg = "Found"
            else:
                success = Message()
                success["Content-Length"] = "3"
                reply = addinfourl(BytesIO(b"abc"), success, final, 200)
                reply.msg = "OK"
            return reply

    # The real urllib error processor converts handler refusal into HTTPError;
    # the transport alone is synthetic, so no request can reach a real network.
    opener = build_opener(handler, Transport())
    with pytest.raises(HTTPError) as captured:
        opener.open(Request(url))
    assert captured.value.code == 302 and captured.value.headers["Location"] == final
    opened.clear()
    monkeypatch.setattr(
        provider, "build_opener", lambda handler: build_opener(handler, Transport())
    )
    raw, metadata = provider._request(url, "file")
    assert raw == b"abc" and metadata["url"] == final and opened == [url, final]
