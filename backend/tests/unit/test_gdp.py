"""Synthetic SIDRA fixtures; no actual country amounts or network calls."""

from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest

from app.integrations.gdp import HEADER, fetch_year, parse_year, year_fingerprint

END = date(2025, 12, 31)


def payload(values=None):
    if values is None:
        values = {1: "1234567.89", 2: "2345678.90", 3: "3456789.01", 4: "4567890.12"}
    return [
        deepcopy(HEADER),
        *[
            {
                "NC": "1",
                "NN": "Brasil",
                "MC": "1550",
                "MN": "Milhões de Reais",
                "V": value,
                "D1C": "1",
                "D1N": "Brasil",
                "D2C": "585",
                "D2N": "Valores a preços correntes",
                "D3C": f"2025{quarter:02d}",
                "D3N": f"{quarter}º trimestre 2025",
                "D4C": "90707",
                "D4N": "PIB a preços de mercado",
            }
            for quarter, value in values.items()
        ],
    ]


def test_gdp_source_scale_and_quarter_starts_are_preserved_without_rounding():
    parsed = parse_year(payload({4: "4567890.12", 1: "1234567.89"}), 2025, END)
    assert parsed == [
        (date(2025, 1, 1), Decimal("1234567890000.00")),
        (date(2025, 10, 1), Decimal("4567890120000.00")),
    ]


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("MC", "14"),
        ("MN", "Reais"),
        ("D1C", "35"),
        ("D1N", "São Paulo"),
        ("D2C", "584"),
        ("D2N", "Índice de volume"),
        ("D4C", "90687"),
        ("D4N", "Indústria"),
        ("D3C", "202401"),
        ("D3N", "2º trimestre 2025"),
        ("V", 1.2),
        ("V", "NaN"),
        ("V", "1.234"),
        ("V", "-1.00"),
        ("V", "0.00"),
    ],
)
def test_rejects_definition_scope_period_and_money_drift(field, invalid):
    data = payload({1: "1234567.89"})
    data[1][field] = invalid
    with pytest.raises(ValueError):
        parse_year(data, 2025, END)


def test_metadata_header_drift_and_duplicate_quarters_are_rejected():
    data = payload({1: "1234567.89"})
    data[0]["D3N"] = "Ano"
    with pytest.raises(ValueError):
        parse_year(data, 2025, END)
    data = payload({1: "1234567.89"})
    data.append(deepcopy(data[1]))
    with pytest.raises(ValueError):
        parse_year(data, 2025, END)


def test_missing_values_and_header_only_response_do_not_fabricate_zeros():
    assert parse_year(payload({1: "..", 2: "-", 3: "X", 4: "..."}), 2025, END) == []
    assert parse_year([deepcopy(HEADER)], 2025, END) == []


def test_current_year_request_has_only_eligible_quarters_and_keeps_partial_observations(
    monkeypatch,
):
    calls = []

    def read(url):
        calls.append(url)
        assert "/p/202501,202502/" in url
        assert url.endswith("/c11255/90707/d/v585%202")
        return payload({1: "1234567.89", 2: ".."})

    monkeypatch.setattr("app.integrations.http.read_json", read)
    result = fetch_year(2025, date(2025, 5, 15))
    assert len(calls) == 1 and result["request_url"] == calls[0]
    assert result["observations"] == [(date(2025, 1, 1), Decimal("1234567890000.00"))]
    with pytest.raises(ValueError):
        parse_year(payload({3: "1234567.89"}), 2025, date(2025, 5, 15))


@pytest.mark.parametrize(
    ("year", "end"),
    [(True, END), (2026, END), (2999, date(2999, 1, 1)), (2025, date(2024, 12, 31))],
)
def test_invalid_or_future_requests_are_rejected_before_http(year, end):
    with pytest.raises(ValueError):
        fetch_year(year, end)


def test_complete_and_partial_fingerprints_pin_year_period_values_and_metadata():
    values = dict(parse_year(payload(), 2025, END))
    fingerprint = year_fingerprint(2025, values)
    assert len(fingerprint) == 64
    assert fingerprint == year_fingerprint(2025, dict(reversed(list(values.items()))))
    partial = {date(2025, 1, 1): values[date(2025, 1, 1)]}
    assert fingerprint != year_fingerprint(2025, partial)
    values[date(2025, 1, 1)] += Decimal("10000.00")
    assert fingerprint != year_fingerprint(2025, values)
    with pytest.raises(ValueError):
        year_fingerprint(2024, values)
    with pytest.raises(ValueError):
        year_fingerprint(2025, {date(2025, 2, 1): Decimal("10000.00")})
    with pytest.raises(ValueError):
        year_fingerprint(2025, {date(2025, 1, 1): Decimal("NaN")})
