import copy

import pytest
from pydantic import ValidationError

from app.modules.policies.schemas import ImpactInput
from app.simulation.compatibility import CENTRAL_SCOPE, EXPECTED, assess


def baseline():
    return {
        "fiscal": {
            "status": "AVAILABLE",
            "year": 2025,
            "scope": CENTRAL_SCOPE,
            "accounting_basis": "cash",
            "price_basis": "nominal",
            "currency": "BRL",
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "source": {
                "url": "https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional"
            },
            "months": [{"reference_date": f"2025-{month:02d}-01"} for month in range(1, 13)],
            "amounts": {
                "net_revenue": "1000.00",
                "primary_expenditure": "1100.00",
                "published_primary_balance": "-100.00",
                "calculated_primary_balance": "-100.00",
                "reconciliation_difference": "0.00",
            },
        }
    }


def impact(**overrides):
    return {
        "id": "i",
        "year": 2025,
        "type": "NEW_EXPENSE",
        "amount": "100.00",
        "description": "Fictício",
        **EXPECTED,
        "price_base_year": None,
        **overrides,
    }


def policy(*impacts, **overrides):
    return {
        "version_id": "p",
        "enabled": True,
        "estimate_status": "ESTIMATED",
        "impacts": list(impacts),
        **overrides,
    }


def review(*policies, base=None):
    return assess(baseline() if base is None else base, list(policies), 2025, 2027)


def test_only_matching_observed_year_is_compatible_without_combining_baseline():
    source = baseline()
    before = copy.deepcopy(source)
    report, interpretation, warnings = review(policy(impact()), base=source)
    assert report["status"] == "COMPATIBLE"
    assert report["version"] == "1.0.0" and report["baseline_year"] == 2025
    assert report["coverage"] == {
        "considered": 1,
        "compatible": 1,
        "not_comparable": 0,
        "incomplete": 0,
    }
    assert report["baseline_combined"] is False
    assert interpretation["price_basis"] == "NOMINAL" and not warnings
    assert source == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("fiscal_scope", "GENERAL_GOVERNMENT"),
        ("fiscal_scope", "STATE"),
        ("fiscal_scope", "MUNICIPAL"),
        ("accounting_basis", "ACCRUAL"),
        ("price_basis", "CONSTANT"),
        ("component", "INTEREST"),
        ("period_basis", "PARTIAL_YEAR"),
        ("year", 2027),
    ],
)
def test_incompatible_declarations_and_future_year_are_not_converted(field, value):
    report, _, _ = review(policy(impact(**{field: value})))
    assert report["status"] == "NOT_COMPARABLE"
    assert any(i["field"] == field for i in report["impacts"][0]["issues"])
    if field == "year":
        assert report["impacts"][0]["issues"][0]["code"] == "FUTURE_ASSUMPTIONS_REQUIRED"


@pytest.mark.parametrize("field", list(EXPECTED))
def test_missing_metadata_never_inferred(field):
    row = impact()
    row.pop(field)
    report, interpretation, warnings = review(policy(row))
    assert report["status"] == "INCOMPLETE"
    assert report["coverage"]["incomplete"] == 1
    assert interpretation["aggregate_basis"] == "UNSPECIFIED"
    assert "FISCAL_METADATA_MISSING" in {w["code"] for w in warnings}
    if field == "price_basis":
        assert interpretation["price_basis"] == "UNSPECIFIED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("scope", "Governo Central"),
        ("currency", "USD"),
        ("period_end", "2025-08-31"),
        ("status", "INCOMPLETE"),
        ("year", True),
        ("months", []),
        ("amounts", {}),
    ],
)
def test_invalid_frozen_base_fails_closed(field, value):
    source = baseline()
    source["fiscal"][field] = value
    assert review(policy(impact()), base=source)[0]["status"] == "NOT_COMPARABLE"


@pytest.mark.parametrize(
    "field,value",
    [
        ("fiscal_scope", "STATE"),
        ("accounting_basis", "ACCRUAL"),
        ("component", "INTEREST"),
        ("period_basis", "PARTIAL_YEAR"),
        ("price_basis", "UNSPECIFIED"),
    ],
)
def test_heterogeneous_aggregate_has_explicit_warning(field, value):
    report, interpretation, warnings = review(policy(impact(), impact(id="j", **{field: value})))
    assert "FISCAL_AGGREGATE_HETEROGENEOUS" in {w["code"] for w in warnings}
    assert any(i["code"] == "AGGREGATE_HETEROGENEOUS" for i in report["issues"])
    assert interpretation["aggregate_basis"] in {"MIXED", "UNSPECIFIED"}


def test_constant_price_bases_are_preserved_and_different_bases_are_mixed():
    first = impact(price_basis="CONSTANT", price_base_year=2020)
    second = impact(id="j", price_basis="CONSTANT", price_base_year=2021)
    assert review(policy(first))[1]["price_base_year"] == 2020
    assert review(policy(first, second))[1]["price_basis"] == "MIXED"
    assert review(policy(first, second))[1]["price_base_year"] is None


def test_disabled_and_outside_period_impacts_do_not_taint_active_coverage():
    report, _, warnings = review(
        policy(impact()),
        policy(impact(year=2024)),
        policy(impact(fiscal_scope="STATE"), enabled=False),
    )
    assert report["status"] == "COMPATIBLE" and len(report["impacts"]) == 1 and not warnings


def test_no_impacts_is_not_comparability_by_vacuity_and_not_estimated_is_incomplete():
    assert review(policy())[0]["status"] == "NO_IMPACTS"
    assert review(policy(estimate_status="NOT_ESTIMATED"))[0]["status"] == "INCOMPLETE"
    assert (
        review(policy(impact()), policy(estimate_status="NOT_ESTIMATED"))[0]["status"]
        == "INCOMPLETE"
    )


def test_schema_legacy_defaults_and_constant_validation():
    data = {
        "year": 2025,
        "impact_type": "NEW_EXPENSE",
        "amount": "100.00",
        "description": "Fictício",
    }
    legacy = ImpactInput.model_validate(data)
    assert all(getattr(legacy, f) == "UNSPECIFIED" for f in EXPECTED)
    assert legacy.price_base_year is None
    actual = ImpactInput.model_validate(
        {**data, "price_basis": "CONSTANT", "price_base_year": 2020}
    )
    assert actual.price_base_year == 2020
    for invalid in (
        {"price_basis": "CONSTANT"},
        {"price_basis": "NOMINAL", "price_base_year": 2020},
        {"price_base_year": 2020},
        {"price_basis": "CONSTANT", "price_base_year": 1800},
        {"fiscal_scope": "FEDERAL"},
    ):
        with pytest.raises(ValidationError):
            ImpactInput.model_validate({**data, **invalid})


@pytest.mark.parametrize("source", [[], "invalid", {"fiscal": []}, {"fiscal": "invalid"}])
def test_non_object_baseline_fails_closed(source):
    assert assess(source, [policy(impact())], 2025, 2027)[0]["status"] == "NOT_COMPARABLE"


@pytest.mark.parametrize("source", [[], "invalid"])
def test_non_object_fiscal_source_fails_closed(source):
    context = baseline()
    context["fiscal"]["source"] = source
    assert review(policy(impact()), base=context)[0]["status"] == "NOT_COMPARABLE"


@pytest.mark.parametrize("field", ["net_revenue", "primary_expenditure"])
def test_negative_gross_fiscal_amounts_fail_closed(field):
    context = baseline()
    context["fiscal"]["amounts"][field] = "-1.00"
    assert review(policy(impact()), base=context)[0]["status"] == "NOT_COMPARABLE"
