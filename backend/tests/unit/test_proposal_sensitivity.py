from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.modules.guidance import impact


def row(kind, amount):
    return SimpleNamespace(
        year=2028,
        impact_type=kind,
        amount=Decimal(amount),
        fiscal_scope="CENTRAL_GOVERNMENT",
        accounting_basis="CASH",
        price_basis="NOMINAL",
        price_base_year=None,
        component="PRIMARY",
        period_basis="FULL_YEAR",
    )


def version():
    return SimpleNamespace(
        id="published-version",
        proposal_details=SimpleNamespace(level="COMPLETE"),
        financial_impact_status="ESTIMATED",
        implementation_start=2028,
        implementation_end=2028,
        impacts=[row("NEW_EXPENSE", "100.00"), row("NEW_REVENUE", "40.00")],
    )


def test_defaults_do_not_invent_a_range_or_count_funding_twice():
    result = impact.analyze(version(), impact.Sensitivity())
    assert result["available"]
    assert {entry["cumulative_impact"] for entry in result["scenarios"]} == {"-60.00"}
    assert result["classification"] == "ESTIMATIVA_DECLARADA"


def test_declared_cost_and_gain_assumptions_are_computed_by_existing_engine():
    assumptions = impact.Sensitivity(
        cost_low="0.80", cost_high="1.20", gain_low="0.50", gain_high="1.50"
    )
    result = impact.analyze(version(), assumptions)
    assert [entry["cumulative_impact"] for entry in result["scenarios"]] == [
        "-100.00",
        "-60.00",
        "-20.00",
    ]
    assert result["scenarios"][0]["years"] == [{"year": 2028, "net_impact": "-100.00"}]


@pytest.mark.parametrize(
    "state", ["idea", "legacy", "missing", "mixed", "NOT_ESTIMATED", "NOT_APPLICABLE", "outside"]
)
def test_incomplete_or_incomparable_inputs_never_reach_the_motor(state, monkeypatch):
    value = version()
    if state in {"idea", "legacy"}:
        value.proposal_details = None
    elif state == "missing":
        value.impacts[0].accounting_basis = "UNSPECIFIED"
    elif state == "mixed":
        value.impacts[0].fiscal_scope = "STATE"
    elif state == "outside":
        value.impacts[0].year = 2029
    else:
        value.financial_impact_status = state
    monkeypatch.setattr(impact, "simulate", lambda *_: pytest.fail("Invalid level reached motor"))
    result = impact.analyze(value, impact.Sensitivity())
    assert result["available"] is False and result["scenarios"] == [] and result["reason"]


def test_constant_prices_require_one_base_year():
    value = version()
    for entry in value.impacts:
        entry.price_basis = "CONSTANT"
    value.impacts[0].price_base_year = 2026
    value.impacts[1].price_base_year = 2027
    assert impact.analyze(value, impact.Sensitivity())["available"] is False


def test_scaled_money_is_decimal_rounded_to_cents():
    value = version()
    value.impacts = [row("NEW_EXPENSE", "0.01")]
    result = impact.analyze(value, impact.Sensitivity(cost_high="1.50"))
    assert result["scenarios"][0]["cumulative_impact"] == "-0.02"


def test_amount_overflow_is_a_gap_not_an_unbounded_result():
    value = version()
    value.impacts = [row("NEW_EXPENSE", "9999999999999999.99")]
    result = impact.analyze(value, impact.Sensitivity(cost_high="2.00"))
    assert result["available"] is False and result["scenarios"] == []


@pytest.mark.parametrize(
    "values",
    [
        {"cost_low": "1.01"},
        {"cost_high": "0.99"},
        {"gain_high": "2.01"},
        {"gain_low": "-0.1"},
        {"cost_low": 0.8},
        {"cost_high": "NaN"},
    ],
)
def test_bounded_decimal_string_assumptions(values):
    with pytest.raises(ValidationError):
        impact.Sensitivity(**values)


def test_percentage_precision_survives_real_http_parameter_contract():
    from app.modules.guidance.router import sensitivity_parameters

    assumptions = sensitivity_parameters(
        cost_low="0.9999", cost_high="1.2000", gain_low="0.5000", gain_high="1.5000"
    )
    assert assumptions.cost_low == Decimal("0.9999")
    result = impact.analyze(version(), assumptions)
    assert result["available"]
    assert result["scenarios"][0]["cumulative_impact"] == "-100.00"
