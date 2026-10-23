"""Synthetic RTN fixtures; amounts are invented for parser/accounting tests."""

from copy import deepcopy
from datetime import date
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest

from app.integrations.treasury import (
    TREASURY_SERIES,
    fetch_bundle,
    parse_series,
    period_fingerprint,
)

START = date(2025, 1, 1)
END = date(2025, 12, 31)


def payload(series="10.01.2", values=None):
    if values is None:
        values = {"2025-01-01T00:00:00.000Z": Decimal("10.000000015")}
    return {
        "status": "ok",
        "page": 1,
        "pageSize": 1000,
        "next": "https://untrusted.example/not-followed",
        "registros": [
            {
                "nomeTema": "Resultado Fiscal do Governo Central - Valores Mensais",
                "codigoTema": "10",
                "data": when,
                "codigoSerie": series,
                "nomeSerie": "Synthetic test label",
                "valor": value,
            }
            for when, value in values.items()
        ],
    }


def test_money_scale_half_even_and_utc_timestamp_variants():
    data = payload(
        values={
            "2025-02-01T00:00:00Z": Decimal("-0.000000005"),
            "2025-01-01T00:00:00.000Z": Decimal("10.000000015"),
        }
    )
    assert parse_series(data, "10.01.2", START, END) == [
        (date(2025, 1, 1), Decimal("10000000.02")),
        (date(2025, 2, 1), Decimal("0.00")),
    ]


@pytest.mark.parametrize(
    "change",
    [
        "status",
        "page",
        "page_size",
        "truncated",
        "row_count",
        "theme",
        "scope",
        "series",
        "timestamp",
        "duplicate",
        "outside",
        "float",
        "string",
        "bool",
        "nonfinite",
        "large",
    ],
)
def test_rejects_drift_truncation_and_invalid_money(change):
    data = payload()
    row = data["registros"][0]
    if change == "status":
        data["status"] = "error"
    if change == "page":
        data["page"] = 2
    if change == "page_size":
        data["pageSize"] = True
    if change == "truncated":
        data["pageSize"] = 1
    if change == "row_count":
        data["registros"] *= 13
    if change == "theme":
        row["codigoTema"] = "11"
    if change == "scope":
        row["nomeTema"] = "Governo Geral"
    if change == "series":
        row["codigoSerie"] = "10.03.1"
    if change == "timestamp":
        row["data"] = "2025-01-02T00:00:00.000Z"
    if change == "duplicate":
        data["registros"].append(deepcopy(row))
    if change == "outside":
        row["data"] = "2024-01-01T00:00:00.000Z"
    if change == "float":
        row["valor"] = 10.1
    if change == "string":
        row["valor"] = "10.1"
    if change == "bool":
        row["valor"] = True
    if change == "nonfinite":
        row["valor"] = Decimal("NaN")
    if change == "large":
        row["valor"] = Decimal("100000000")
    with pytest.raises(ValueError):
        parse_series(data, "10.01.2", START, END)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (date(2024, 12, 1), date(2025, 1, 1)),
        (date(2025, 2, 1), date(2025, 1, 1)),
        (date(2999, 1, 1), date(2999, 1, 2)),
    ],
)
def test_interval_is_bounded_to_past_calendar_year(start, end):
    with pytest.raises(ValueError):
        fetch_bundle(start, end)


def mock_reader(monkeypatch, *, extra_month=False, wrong_balance=False, empty=False):
    calls = []
    amounts = {
        "10.01.2": Decimal("10"),
        "10.03.1": Decimal("7"),
        "10.04.1": Decimal("3"),
    }

    def read_json(url, *, decimal_numbers):
        assert decimal_numbers is True
        parts = urlsplit(url)
        assert parts.scheme == "https" and parts.hostname == "apiapex.tesouro.gov.br"
        query = parse_qs(parts.query)
        assert query["tema"] == ["10"]
        assert query["correcao_ipca"] == ["false"]
        assert query["data_inicio"] == ["01/2025"]
        assert query["data_fim"] == ["12/2025"]
        series = query["codigo_da_serie"][0]
        calls.append(url)
        values = {} if empty else {"2025-01-01T00:00:00Z": amounts[series]}
        if extra_month and series == "10.03.1":
            values["2025-02-01T00:00:00Z"] = Decimal("1")
        if wrong_balance and series == "10.04.1":
            values["2025-01-01T00:00:00Z"] += Decimal("0.000001")
        return payload(series, values)

    monkeypatch.setattr("app.integrations.http.read_json", read_json)
    return calls


def test_bundle_checks_all_three_before_returning_and_does_not_follow_next(monkeypatch):
    calls = mock_reader(monkeypatch)
    bundle = fetch_bundle(START, END)
    assert len(calls) == 3
    assert set(bundle) == set(TREASURY_SERIES)
    assert bundle["rtn-resultado-primario"]["observations"] == [(START, Decimal("3000000.00"))]
    assert all(item["request_url"] in calls for item in bundle.values())


@pytest.mark.parametrize("failure", ["extra_month", "wrong_balance"])
def test_bundle_rejects_coverage_mismatch_and_accounting_failure(monkeypatch, failure):
    calls = mock_reader(monkeypatch, **{failure: True})
    with pytest.raises(ValueError):
        fetch_bundle(START, END)
    assert len(calls) == 3


def test_empty_bundle_does_not_fabricate_months(monkeypatch):
    mock_reader(monkeypatch, empty=True)
    bundle = fetch_bundle(START, END)
    assert all(item["observations"] == [] for item in bundle.values())


def test_bundle_network_failure_never_returns_a_partial_bundle(monkeypatch):
    calls = []

    def fail_after_first(url, *, decimal_numbers):
        calls.append(url)
        if len(calls) == 2:
            raise TimeoutError("Synthetic source failure")
        return payload(values={"2025-01-01T00:00:00Z": Decimal("10")})

    monkeypatch.setattr("app.integrations.http.read_json", fail_after_first)
    with pytest.raises(TimeoutError):
        fetch_bundle(START, END)
    assert len(calls) == 2


def test_fingerprint_uses_fixed_scope_period_and_decimal_money_independent_of_order():
    values = {
        "rtn-receita-liquida": Decimal("10.0"),
        "rtn-despesa-primaria": Decimal("7"),
        "rtn-resultado-primario": Decimal("3.00"),
    }
    fingerprint = period_fingerprint(START, values)
    assert len(fingerprint) == 64
    assert fingerprint == period_fingerprint(START, dict(reversed(list(values.items()))))
    assert fingerprint != period_fingerprint(date(2025, 2, 1), values)
    values["rtn-receita-liquida"] += Decimal("0.01")
    assert fingerprint != period_fingerprint(START, values)
    with pytest.raises(ValueError):
        period_fingerprint(START, {"rtn-receita-liquida": Decimal("10")})


def test_zero_sign_is_not_a_revision():
    values = dict.fromkeys(TREASURY_SERIES, Decimal("0.00"))
    fingerprint = period_fingerprint(START, values)
    values["rtn-resultado-primario"] = Decimal("-0.00")
    assert fingerprint == period_fingerprint(START, values)
