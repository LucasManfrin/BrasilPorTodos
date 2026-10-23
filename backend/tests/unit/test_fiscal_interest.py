"""Synthetic below-line records: invented amounts and no network."""

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest
from test_treasury import payload

from app.integrations import treasury
from app.integrations import treasury_interest as provider
from app.modules.indicators.fiscal_interest import SOURCE, assemble


def values(primary="100.10", interest="-70.01", residual="0.00"):
    primary, interest, residual = map(Decimal, (primary, interest, residual))
    return {
        "rtn-primario-abaixo-linha": primary,
        "rtn-juros-nominais": interest,
        "rtn-resultado-nominal": primary + interest - residual,
    }


def records(year=2025, **amounts):
    output = []
    for month in range(1, 13):
        when, money = date(year, month, 1), values(**amounts)
        fingerprint = provider.period_fingerprint(when, money)
        for code, entry in provider.INTEREST_SERIES.items():
            output.append(
                {
                    "code": code,
                    "reference_date": when.isoformat(),
                    "value": str(money[code]),
                    "revision": 1,
                    "retrieved_at": "2026-01-01T00:00:00+00:00",
                    "source": {
                        **SOURCE,
                        "source_type": "OFFICIAL",
                        "is_example": False,
                        "description": (
                            f"Dados oficiais de {SOURCE['institution']}. "
                            f"Termos: {treasury.LICENSE_NAME}. {treasury.LICENSE_URL}"
                        ),
                    },
                    "provenance": {
                        "collector": provider.COLLECTOR,
                        "method_version": provider.METHOD_VERSION,
                        "accounting_basis": entry["accounting_basis"],
                        "component": entry["component"],
                        "methodology_basis": "below_line",
                        "currency": "BRL",
                        "price_basis": "nominal",
                        "original_unit": "R$ milhões",
                        "scale": "1000000",
                        "series": entry["series"],
                        "institution": SOURCE["institution"],
                        "dataset_url": treasury.SOURCE_URL,
                        "license": treasury.LICENSE_NAME,
                        "license_url": treasury.LICENSE_URL,
                        "method": entry["methodology"],
                        "statistical_authority": "Banco Central do Brasil",
                        "methodology_url": provider.METHOD_URL,
                        "period_fingerprint": fingerprint,
                        "definition": {
                            key: entry[key] for key in ("unit", "scope", "frequency", "methodology")
                        },
                    },
                }
            )
    return output


@pytest.mark.parametrize("interest", ["-70.01", "70.01", "0.00"])
def test_signed_interest_uses_below_line_primary_and_mixed_basis(interest):
    rows = records(interest=interest)
    original = deepcopy(rows)
    result = assemble(rows, 2025)
    assert result["status"] == "AVAILABLE"
    assert result["totals"]["primary_balance"] == "1201.20"
    assert result["totals"]["interest"] == format(Decimal(interest) * 12, ".2f")
    assert (
        Decimal(result["totals"]["nominal_balance"]) == Decimal("1201.20") + Decimal(interest) * 12
    )
    assert result["accounting_basis"] == "mixed"
    assert result["component_bases"] == {"primary": "cash", "interest": "accrual"}
    assert result["methodology_basis"] == "below_line" and len(result["months"]) == 12
    assert result["reconciliation"] == {"monthly_tolerance": "0.03", "annual_difference": "0.00"}
    assert rows == original


def test_actual_rounding_difference_is_exposed_not_forced_to_zero():
    result = assemble(records(residual="0.01"), 2025)
    assert result["status"] == "AVAILABLE"
    assert result["reconciliation"]["annual_difference"] == "0.12"
    assert result["totals"]["nominal_balance"] == "360.96"


@pytest.mark.parametrize(
    "change",
    [
        "missing_month",
        "missing_series",
        "wrong_year",
        "bad_fingerprint",
        "invalid_latest",
        "bad_basis",
        "above_method",
        "wrong_authority",
        "bad_license",
        "bad_source",
        "private_description",
        "bad_definition",
        "nonfinite",
        "subcent",
        "out_of_range",
    ],
)
def test_missing_or_incompatible_latest_data_never_returns_partial_amounts(change):
    rows = records()
    if change == "missing_month":
        rows = [row for row in rows if row["reference_date"] != "2025-06-01"]
    if change == "missing_series":
        rows = rows[1:]
    if change == "wrong_year":
        rows = records(2024)
    if change == "bad_fingerprint":
        rows[0]["provenance"]["period_fingerprint"] = "another-cohort"
    if change == "invalid_latest":
        newer = deepcopy(rows[0])
        newer["revision"] = 2
        newer["value"] = "100.00"
        rows.append(newer)
    if change == "bad_basis":
        rows[1]["provenance"]["accounting_basis"] = "cash"
    if change == "above_method":
        rows[0]["provenance"]["methodology_basis"] = "above_line"
    if change == "wrong_authority":
        rows[0]["provenance"]["statistical_authority"] = "Unknown"
    if change == "bad_license":
        rows[0]["provenance"]["license"] = "MIT"
    if change == "bad_source":
        rows[0]["source"]["source_type"] = "OTHER"
    if change == "private_description":
        rows[0]["source"]["description"] = "Unpublished confidential description"
    if change == "bad_definition":
        rows[0]["provenance"]["definition"]["scope"] = "Governo Geral"
    if change == "nonfinite":
        rows[0]["value"] = "NaN"
    if change == "subcent":
        rows[0]["value"] = "100.101"
    if change == "out_of_range":
        rows[0]["value"] = "100000000000000"
    result = assemble(rows, 2025)
    assert result["status"] == "INCOMPLETE" and result["totals"] is None
    assert (
        result["months"] == []
        and result["collected_at"] is None
        and result["reconciliation"] is None
    )


def test_unavailable_year_does_not_fallback_to_another_year_or_imply_zero():
    result = assemble(records(), None)
    assert result["status"] == "INCOMPLETE" and result["year"] is None and result["totals"] is None
    assert assemble([], 2025)["status"] == "EMPTY"


@pytest.mark.parametrize(
    "bad", [Decimal("NaN"), Decimal("Infinity"), 1.1, True, "1", Decimal("100000000")]
)
def test_parser_never_accepts_binary_float_nonfinite_or_unbounded_money(bad):
    with pytest.raises(ValueError):
        provider.parse_series(
            payload("10.08.1", {"2025-01-01T00:00:00Z": bad}),
            "10.08.1",
            date(2025, 1, 1),
            date(2025, 12, 1),
        )


@pytest.mark.parametrize("wrong_id", ["10.04.1", "10.03.1", "10.99.1"])
def test_interest_parser_does_not_expand_above_line_or_unreviewed_allowlist(wrong_id):
    with pytest.raises(ValueError):
        provider.parse_series(payload(wrong_id), wrong_id, date(2025, 1, 1), date(2025, 12, 1))


def test_closed_year_fetch_checks_all_series_and_exact_months(monkeypatch):
    calls = []

    def read(url, *, decimal_numbers):
        assert decimal_numbers and urlsplit(url).hostname == "apiapex.tesouro.gov.br"
        query = parse_qs(urlsplit(url).query)
        assert query["tema"] == ["10"] and query["correcao_ipca"] == ["false"]
        series = query["codigo_da_serie"][0]
        calls.append(series)
        code = next(
            code for code, entry in provider.INTEREST_SERIES.items() if entry["series"] == series
        )
        return payload(
            series,
            {
                f"2025-{month:02}-01T00:00:00Z": values()[code] / treasury.SCALE
                for month in range(1, 13)
            },
        )

    monkeypatch.setattr("app.integrations.http.read_json", read)
    result = provider.fetch_year(2025, date(2026, 10, 11))
    assert len(calls) == len(result) == 3
    assert result["rtn-juros-nominais"]["observations"][0][1] == Decimal("-70.01")


def test_truncated_fetch_is_rejected_before_returning_a_cohort(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.http.read_json",
        lambda url, **kwargs: payload(parse_qs(urlsplit(url).query)["codigo_da_serie"][0], {}),
    )
    with pytest.raises(ValueError, match="omitted"):
        provider.fetch_year(2025, date(2026, 10, 11))


def test_reconciliation_and_fingerprint_cover_signed_values_and_precise_period():
    money = values()
    fingerprint = provider.period_fingerprint(date(2025, 1, 1), money)
    assert fingerprint == provider.period_fingerprint(
        date(2025, 1, 1), dict(reversed(list(money.items())))
    )
    assert fingerprint != provider.period_fingerprint(date(2025, 2, 1), money)
    money["rtn-resultado-nominal"] += Decimal("0.10")
    with pytest.raises(ValueError, match="reconcile"):
        provider.period_fingerprint(date(2025, 1, 1), money)
    with pytest.raises(ValueError):
        provider.period_fingerprint(datetime(2025, 1, 1), values())


@pytest.mark.parametrize("year", [2026, 2999, 1996, True])
def test_unclosed_or_unreviewed_year_never_fetches(year):
    with pytest.raises(ValueError):
        provider.fetch_year(year, date(2026, 10, 11))
