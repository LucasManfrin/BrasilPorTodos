"""Synthetic CNT quarterly records: no network calls or annualization."""

from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest

from app.integrations.gdp import GDP_CODE, GDP_SERIES, SOURCE_URL, year_fingerprint
from app.modules.indicators.gdp_baseline import assemble


def year_records(year=2025, amounts=None):
    values = {
        date(year, month, 1): Decimal(value)
        for month, value in zip(
            (1, 4, 7, 10),
            amounts or ("250000.00", "250000.00", "250000.00", "250000.00"),
            strict=True,
        )
    }
    fingerprint = year_fingerprint(year, values)
    return [
        {
            "id": f"synthetic-gdp-{when.isoformat()}-v1",
            "reference_date": when.isoformat(),
            "revision": 1,
            "value": str(value),
            "source": {
                "url": SOURCE_URL,
                "source_type": "OFFICIAL",
                "is_example": False,
            },
            "provenance": {
                "collector": "ibge-cnt-gdp-v1",
                "original_unit": "Milhões de Reais",
                "scale": "1000000",
                "series": "585",
                "aggregation": "sum_four_quarters_cnt",
                "source_precision": "0.01_million_brl",
                "dataset_url": SOURCE_URL,
                "annual_fingerprint": fingerprint,
                "definition": {
                    key: GDP_SERIES[GDP_CODE][key]
                    for key in ("unit", "scope", "frequency", "methodology")
                },
            },
        }
        for when, value in values.items()
    ]


def test_four_same_year_quarters_sum_exactly_and_preserve_precision_and_provenance():
    records = year_records()
    before = deepcopy(records)
    result = assemble(records, 2025)
    assert result["status"] == "AVAILABLE"
    assert result["year"] == 2025 and result["nominal_gdp"] == "1000000.00"
    assert result["aggregation"] == "sum_four_quarters_cnt"
    assert result["source_precision"] == "0.01_million_brl"
    assert result["source"]["url"] == SOURCE_URL
    assert result["missing"] == []
    assert len(result["quarters"]) == 4
    assert result["quarters"][0]["observation"]["id"] == records[0]["id"]
    assert any("10.000" in note for note in result["limitations"])
    assert any("definitiva" in note for note in result["limitations"])
    assert records == before


def test_missing_quarter_has_no_annual_total_or_implied_zero():
    result = assemble(year_records()[:3], 2025)
    assert result["status"] == "INCOMPLETE" and result["nominal_gdp"] is None
    assert result["quarters"] == [] and result["missing"]


def test_other_year_cannot_be_substituted_for_requested_fiscal_year():
    result = assemble(year_records(2024), 2025)
    assert result["status"] == "INCOMPLETE" and result["nominal_gdp"] is None


def test_mixed_year_quarters_are_not_combined():
    result = assemble(year_records(2025)[:3] + year_records(2024)[3:], 2025)
    assert result["status"] == "INCOMPLETE" and result["nominal_gdp"] is None


@pytest.mark.parametrize(
    ("location", "field", "invalid"),
    [
        ("provenance", "collector", "unverified-source"),
        ("provenance", "original_unit", "Percentual"),
        ("provenance", "scale", "1000"),
        ("provenance", "series", "584"),
        ("provenance", "aggregation", "annualize_current_quarter"),
        ("provenance", "source_precision", "cent_brl"),
        ("provenance", "dataset_url", "https://example.com/unverified"),
        ("definition", "unit", "%"),
        ("definition", "scope", "Estado de São Paulo"),
        ("definition", "frequency", "YEARLY"),
        ("definition", "methodology", "Índice de volume ajustado sazonalmente"),
        ("source", "url", "https://example.com/unverified"),
        ("source", "source_type", "OTHER"),
        ("source", "is_example", True),
    ],
)
def test_unverified_definition_unit_precision_or_source_is_not_a_valid_denominator(
    location, field, invalid
):
    records = year_records()
    target = (
        records[0]["provenance"]["definition"] if location == "definition" else records[0][location]
    )
    target[field] = invalid
    result = assemble(records, 2025)
    assert result["status"] == "INCOMPLETE" and result["nominal_gdp"] is None


def test_mixed_annual_cohort_is_blocked_even_when_values_reconcile():
    records = year_records()
    records[1]["provenance"]["annual_fingerprint"] = "another-release"
    result = assemble(records, 2025)
    assert result["status"] == "INCOMPLETE" and result["nominal_gdp"] is None


def test_invalid_latest_revision_cannot_reuse_old_valid_quarter():
    records = year_records()
    revised = deepcopy(records[0])
    revised["revision"] = 2
    revised["id"] = "synthetic-gdp-revised-v2"
    revised["provenance"]["annual_fingerprint"] = "invalid-release"
    result = assemble([revised, *records], 2025)
    assert result["status"] == "INCOMPLETE" and result["nominal_gdp"] is None


def test_large_nominal_quarter_sums_keep_decimal_precision():
    result = assemble(
        year_records(
            amounts=(
                "2500000010000.00",
                "2500000020000.00",
                "2500000030000.00",
                "2500000040000.00",
            )
        ),
        2025,
    )
    assert result["status"] == "AVAILABLE"
    assert result["nominal_gdp"] == "10000000100000.00"


@pytest.mark.parametrize("invalid", ["0", "-1", "NaN", "Infinity", "250000.001"])
def test_zero_negative_nonfinite_or_subcent_denominator_is_blocked(invalid):
    records = year_records()
    records[0]["value"] = invalid
    result = assemble(records, 2025)
    assert result["status"] == "INCOMPLETE" and result["nominal_gdp"] is None


def test_empty_records_have_no_denominator():
    result = assemble([], 2025)
    assert result["status"] == "EMPTY" and result["nominal_gdp"] is None
    assert result["quarters"] == [] and result["year"] == 2025
