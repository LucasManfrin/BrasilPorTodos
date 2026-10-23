from decimal import Decimal

import pytest

from app.simulation.fiscal import EstimateStatus, Impact, ImpactType, PolicyInput, simulate


def test_methodology_example_and_years_without_entries():
    policy = PolicyInput(
        "v1",
        EstimateStatus.ESTIMATED,
        (
            Impact(2030, ImpactType.EXPENSE_REDUCTION, Decimal("30000000000.00")),
            Impact(2030, ImpactType.NEW_REVENUE, Decimal("20000000000.00")),
            Impact(2030, ImpactType.NEW_EXPENSE, Decimal("40000000000.00")),
            Impact(2030, ImpactType.REVENUE_REDUCTION, Decimal("5000000000.00")),
        ),
    )
    result = simulate(2030, 2031, (policy,))
    assert result.years[0].net_impact == Decimal("5000000000.00")
    assert result.years[1].net_impact == Decimal("0.00")
    assert result.cumulative_impact == Decimal("5000000000.00")
    assert not result.is_partial
    assert result.engine_version == "1.0.0"


def test_decimal_precision_and_negative_balance():
    policy = PolicyInput(
        "v1",
        EstimateStatus.ESTIMATED,
        (
            Impact(2030, ImpactType.NEW_EXPENSE, Decimal("0.10")),
            Impact(2030, ImpactType.NEW_EXPENSE, Decimal("0.20")),
        ),
    )
    assert simulate(2030, 2030, (policy,)).cumulative_impact == Decimal("-0.30")


def test_unknown_impact_is_partial_and_unfunded_has_warning():
    result = simulate(
        2030, 2030, (PolicyInput("unknown", EstimateStatus.NOT_ESTIMATED, unfunded=True),)
    )
    assert result.is_partial
    assert {warning.code for warning in result.warnings} == {"NOT_ESTIMATED", "UNFUNDED"}


def test_disabled_policy_does_not_contribute_or_raise_unknown_warning():
    policy = PolicyInput("disabled", EstimateStatus.NOT_ESTIMATED, enabled=False)
    result = simulate(2030, 2030, (policy,))
    assert result.cumulative_impact == Decimal("0.00")
    assert not result.is_partial
    assert not result.warnings


def test_outside_period_is_excluded_with_warning():
    policy = PolicyInput(
        "v1", EstimateStatus.ESTIMATED, (Impact(2029, ImpactType.NEW_REVENUE, Decimal("10")),)
    )
    result = simulate(2030, 2030, (policy,))
    assert result.cumulative_impact == Decimal("0.00")
    assert result.warnings[0].code == "OUTSIDE_PERIOD"


def test_duplicate_version_is_rejected():
    policy = PolicyInput("v1", EstimateStatus.NOT_APPLICABLE)
    with pytest.raises(ValueError, match="twice"):
        simulate(2030, 2030, (policy, policy))


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("0.001"),
        Decimal("10000000000000000"),
        0.1,
    ],
)
def test_invalid_money_is_rejected(amount):
    with pytest.raises(ValueError):
        Impact(2030, ImpactType.NEW_EXPENSE, amount)


@pytest.mark.parametrize("period", [(2031, 2030), (True, 2030), (1800, 2030), (2030, 2300)])
def test_invalid_period_is_rejected(period):
    with pytest.raises(ValueError):
        simulate(*period, ())


def test_not_estimated_cannot_carry_amounts():
    with pytest.raises(ValueError, match="Only estimated"):
        PolicyInput(
            "v1",
            EstimateStatus.NOT_ESTIMATED,
            (Impact(2030, ImpactType.NEW_EXPENSE, Decimal("1")),),
        )
