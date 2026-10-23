"""Synthetic fiscal records only; never request official data in unit tests."""

from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest

from app.integrations.treasury import SOURCE_URL, TREASURY_SERIES, period_fingerprint
from app.modules.indicators.fiscal_baseline import assemble


def monthly_records(year, month, revenue="1000.10", expenditure="750.01", balance=None):
    when = date(year, month, 1)
    values = {
        "rtn-receita-liquida": Decimal(revenue),
        "rtn-despesa-primaria": Decimal(expenditure),
        "rtn-resultado-primario": (
            Decimal(balance) if balance is not None else Decimal(revenue) - Decimal(expenditure)
        ),
    }
    fingerprint = period_fingerprint(when, values)
    return [
        {
            "code": code,
            "id": f"synthetic-{year}-{month}-{code}-v1",
            "reference_date": when.isoformat(),
            "value": str(value),
            "revision": 1,
            "source": {
                "url": SOURCE_URL,
                "source_type": "OFFICIAL",
                "is_example": False,
            },
            "provenance": {
                "collector": "tesouro-rtn-v1",
                "accounting_basis": "cash",
                "price_basis": "nominal",
                "currency": "BRL",
                "original_unit": "R$ milhões",
                "scale": "1000000",
                "series": TREASURY_SERIES[code]["series"],
                "dataset_url": SOURCE_URL,
                "period_fingerprint": fingerprint,
                "definition": {
                    key: TREASURY_SERIES[code][key]
                    for key in ("unit", "scope", "frequency", "methodology")
                },
            },
        }
        for code, value in values.items()
    ]


def closed_year(year=2025, **amounts):
    return [row for month in range(1, 13) for row in monthly_records(year, month, **amounts)]


def test_twelve_compatible_months_preserve_sources_and_exact_observed_arithmetic():
    records = closed_year()
    original = deepcopy(records)
    result = assemble(records, date(2026, 10, 9))
    assert result["status"] == "AVAILABLE"
    assert result["year"] == 2025
    assert result["period_start"] == "2025-01-01"
    assert result["period_end"] == "2025-12-31"
    assert result["accounting_basis"] == "cash"
    assert result["price_basis"] == "nominal"
    assert result["currency"] == "BRL"
    assert result["amounts"] == {
        "net_revenue": "12001.20",
        "primary_expenditure": "9000.12",
        "published_primary_balance": "3001.08",
        "calculated_primary_balance": "3001.08",
        "reconciliation_difference": "0.00",
    }
    assert len(result["months"]) == 12
    assert all(len(month["observations"]) == 3 for month in result["months"])
    assert result["source"]["url"] == SOURCE_URL
    assert result["missing"] == []
    assert records == original


def test_missing_month_is_incomplete_and_does_not_become_zero():
    records = [row for row in closed_year() if row["reference_date"] != "2025-06-01"]
    result = assemble(records, date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE"
    assert result["amounts"] is None and result["year"] is None
    assert result["months"] == [] and result["missing"]


def test_receipts_and_expenses_from_different_years_are_not_combined():
    records = [row for row in closed_year(2025) if row["code"] != "rtn-despesa-primaria"] + [
        row for row in closed_year(2024) if row["code"] == "rtn-despesa-primaria"
    ]
    result = assemble(records, date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE" and result["amounts"] is None


@pytest.mark.parametrize(
    ("location", "field", "invalid"),
    [
        ("provenance", "accounting_basis", "accrual"),
        ("provenance", "price_basis", "real_2020"),
        ("provenance", "currency", "USD"),
        ("provenance", "original_unit", "R$ bilhões"),
        ("provenance", "scale", "1000"),
        ("provenance", "collector", "unverified-provider"),
        ("provenance", "series", "10.99.9"),
        ("provenance", "dataset_url", "https://example.com/unverified"),
        ("definition", "unit", "% do PIB"),
        ("definition", "scope", "Governo Geral"),
        ("definition", "frequency", "YEARLY"),
        ("definition", "methodology", "Outro critério contábil"),
        ("source", "source_type", "OTHER"),
        ("source", "url", "https://example.com/unverified"),
        ("source", "is_example", True),
    ],
)
def test_incompatible_definition_accounting_units_or_source_blocks_annual_reference(
    location, field, invalid
):
    records = closed_year()
    row = records[0]
    target = row["provenance"]["definition"] if location == "definition" else row[location]
    target[field] = invalid
    result = assemble(records, date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE" and result["amounts"] is None


def test_mixed_monthly_bundle_fingerprint_is_not_accepted():
    records = closed_year()
    records[1]["provenance"]["period_fingerprint"] = "different-cohort"
    result = assemble(records, date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE" and result["amounts"] is None


def test_large_reconciliation_difference_is_not_silently_adjusted():
    result = assemble(closed_year(balance="249.00"), date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE" and result["amounts"] is None


def test_independent_cent_rounding_difference_is_exposed_without_adjusting_source():
    result = assemble(closed_year(balance="250.08"), date(2026, 10, 9))
    assert result["status"] == "AVAILABLE"
    assert result["amounts"]["published_primary_balance"] == "3000.96"
    assert result["amounts"]["calculated_primary_balance"] == "3001.08"
    assert result["amounts"]["reconciliation_difference"] == "0.12"


def test_invalid_latest_revision_cannot_fall_back_to_valid_older_monthly_revision():
    records = closed_year()
    revised = deepcopy(records[0])
    revised["revision"] = 2
    revised["id"] = "synthetic-revised-v2"
    revised["provenance"]["period_fingerprint"] = "invalid-revision"
    result = assemble([revised, *records], date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE" and result["amounts"] is None


def test_last_complete_closed_year_fallback_is_explicit():
    records = closed_year(2024) + [
        row for row in closed_year(2025) if row["reference_date"] != "2025-12-01"
    ]
    result = assemble(records, date(2026, 10, 9))
    assert result["status"] == "AVAILABLE" and result["year"] == 2024
    assert any("mais recente" in limitation for limitation in result["limitations"])


def test_current_year_to_date_is_never_annualized_or_used_as_a_closed_year():
    current_year = [row for month in range(1, 10) for row in monthly_records(2026, month)]
    result = assemble(current_year, date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE" and result["amounts"] is None
    assert result["period_start"] is None and result["period_end"] is None


def test_large_nominal_amounts_and_cent_precision_are_exact():
    result = assemble(
        closed_year(revenue="12345678901234.56", expenditure="12345678901000.01"),
        date(2026, 10, 9),
    )
    assert result["status"] == "AVAILABLE"
    assert result["amounts"]["net_revenue"] == "148148146814814.72"
    assert result["amounts"]["primary_expenditure"] == "148148146812000.12"
    assert result["amounts"]["calculated_primary_balance"] == "2814.60"


@pytest.mark.parametrize("invalid", ["NaN", "Infinity", "1000.101"])
def test_nonfinite_or_subcent_values_cannot_enter_annual_reference(invalid):
    records = closed_year()
    records[0]["value"] = invalid
    result = assemble(records, date(2026, 10, 9))
    assert result["status"] == "INCOMPLETE" and result["amounts"] is None


def test_empty_records_have_no_amounts_or_implied_zero():
    result = assemble([], date(2026, 10, 9))
    assert result["status"] == "EMPTY" and result["amounts"] is None
    assert result["year"] is None and result["months"] == []
