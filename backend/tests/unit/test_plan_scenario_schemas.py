from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.plans.schemas import FiscalScenarioDraft, FiscalScenarioYearDraft, PlanUpdate


def test_draft_allows_missing_fields_and_nullable_annual_premises():
    assert FiscalScenarioDraft().years == []
    row = FiscalScenarioYearDraft(year=2027)
    assert row.net_revenue is None and row.primary_expenditure is None
    assert PlanUpdate.model_validate({"fiscal_scenario": None}).fiscal_scenario is None
    assert (
        FiscalScenarioYearDraft(year=2027, net_revenue="1000").model_dump(mode="json")[
            "net_revenue"
        ]
        == "1000.00"
    )


@pytest.mark.parametrize(
    "value",
    [
        True,
        1,
        1.0,
        "NaN",
        "Infinity",
        "-0.01",
        "1.001",
        "1.000",
        "10000000000000000.00",
        "not money",
    ],
)
def test_money_never_coerces_float_or_nonfinite_or_bad_precision(value):
    with pytest.raises(ValidationError):
        FiscalScenarioYearDraft(year=2027, net_revenue=value)


@pytest.mark.parametrize("value", [True, 2027.0, "2027", 1899, 2201])
def test_scenario_years_are_strict(value):
    with pytest.raises(ValidationError):
        FiscalScenarioYearDraft(year=value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("excludes_plan_impacts", True),
        ("review_input_hash", "a" * 64),
        ("reviewed_input_hash", "a" * 64),
        ("reviewed_at", "2026-01-01"),
        ("currency", "USD"),
    ],
)
def test_readonly_or_recuts_cannot_be_injected(field, value):
    with pytest.raises(ValidationError):
        FiscalScenarioDraft.model_validate({field: value})


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/secret",
        "javascript:alert(1)",
        "https://user:pass@example.test",
        "https://example.test:99999",
        "https://example.test:bad",
    ],
)
def test_reference_urls_are_http_and_without_credentials(url):
    with pytest.raises(ValidationError):
        FiscalScenarioYearDraft(year=2027, source_urls=[url])


def test_explicit_zero_exact_boundary_and_maximum_lengths():
    row = FiscalScenarioYearDraft(
        year=2027, net_revenue="9999999999999999.99", primary_expenditure="0"
    )
    assert row.net_revenue == Decimal("9999999999999999.99") and row.primary_expenditure == 0
    with pytest.raises(ValidationError):
        FiscalScenarioDraft(years=[{"year": 2027}] * 31)
    with pytest.raises(ValidationError):
        FiscalScenarioYearDraft(year=2027, source_urls=["https://example.test"] * 21)
