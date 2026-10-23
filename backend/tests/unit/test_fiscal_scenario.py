import copy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext

import pytest

from app.simulation.compatibility import EXPECTED
from app.simulation.fiscal import EstimateStatus, ImpactType
from app.simulation.scenario import (
    MAX_MONEY,
    FiscalScenario,
    ScenarioImpact,
    ScenarioPolicy,
    ScenarioStatus,
    ScenarioYear,
    simulate_scenario,
)
from tests.unit.test_fiscal_compatibility import baseline as fiscal_baseline


def baseline():
    return {"id": "reviewed-frozen-baseline", **fiscal_baseline()}


def scenario(**overrides):
    return FiscalScenario(
        id="manual-future",
        title="Cenário fictício",
        explanation="Premissas de teste, sem previsão oficial.",
        reference_baseline_id="reviewed-frozen-baseline",
        start_year=2027,
        end_year=2028,
        years=(
            ScenarioYear(2027, Decimal("1000.00"), Decimal("1100.00"), "Premissa explícita"),
            ScenarioYear(2028, Decimal("2000.00"), Decimal("1800.00"), "Outra premissa explícita"),
        ),
        excludes_plan_impacts=True,
        **overrides,
    )


def impact(kind=ImpactType.NEW_EXPENSE, amount="100.10", **overrides):
    data = {
        "id": "i",
        "year": 2027,
        "kind": kind,
        "amount": Decimal(amount),
        **EXPECTED,
        **overrides,
    }
    return ScenarioImpact(**data)


def policy(*impacts, **overrides):
    return ScenarioPolicy("published-v1", EstimateStatus.ESTIMATED, tuple(impacts), **overrides)


def run(*policies, premise=None, context=None):
    return simulate_scenario(
        baseline() if context is None else context,
        scenario() if premise is None else premise,
        tuple(policies),
    )


def test_future_year_uses_manual_premises_never_repeats_historical_accounts():
    result = run(policy(impact()))
    assert result.status == ScenarioStatus.COMPATIBLE
    assert result.historical_year == 2025
    assert result.scenario_method_version == result.aggregation_engine_version == "1.0.0"
    assert result.years[0].declared.primary_balance == Decimal("-100.00")
    assert result.years[0].incremental.net_impact == Decimal("-100.10")
    assert result.years[0].combined.net_revenue == Decimal("1000.00")
    assert result.years[0].combined.primary_expenditure == Decimal("1200.10")
    assert result.years[0].combined.primary_balance == Decimal("-200.10")
    assert result.years[1].combined.net_revenue == Decimal("2000.00")
    assert result.cumulative_incremental == Decimal("-100.10")
    assert result.aggregate_basis == "HOMOGENEOUS" and result.price_basis == "NOMINAL"


def test_all_four_impact_components_preserve_cent_identity_once():
    rows = (
        impact(ImpactType.NEW_REVENUE, "50.03", id="r"),
        impact(ImpactType.REVENUE_REDUCTION, "20.02", id="rr"),
        impact(ImpactType.NEW_EXPENSE, "10.01", id="e"),
        impact(ImpactType.EXPENSE_REDUCTION, "5.02", id="er"),
    )
    result = run(policy(*rows, unfunded=True))
    year = result.years[0]
    assert year.combined.net_revenue == Decimal("1030.01")
    assert year.combined.primary_expenditure == Decimal("1104.99")
    assert year.combined.primary_balance == Decimal("-74.98")
    assert year.incremental.net_impact == Decimal("25.02")
    assert (
        year.combined.primary_balance - year.declared.primary_balance == year.incremental.net_impact
    )
    assert "UNFUNDED" in {w.code for w in result.warnings}


@pytest.mark.parametrize(
    "field,value",
    [
        ("fiscal_scope", "STATE"),
        ("fiscal_scope", "GENERAL_GOVERNMENT"),
        ("fiscal_scope", "MUNICIPAL"),
        ("accounting_basis", "ACCRUAL"),
        ("component", "INTEREST"),
        ("period_basis", "PARTIAL_YEAR"),
        ("price_basis", "CONSTANT"),
    ],
)
def test_one_mismatching_parcel_blocks_all_years_without_discarding_its_increment(field, value):
    metadata = {field: value}
    if field == "price_basis":
        metadata["price_base_year"] = 2020
    result = run(
        policy(impact(id="valid"), impact(id="mismatch", amount="50.00", year=2028, **metadata))
    )
    assert result.status == ScenarioStatus.NOT_COMPARABLE
    assert all(year.combined is None for year in result.years)
    assert result.years[0].incremental.net_impact == Decimal("-100.10")
    assert result.years[1].incremental.net_impact == Decimal("-50.00")
    assert result.impacts[0].status == ScenarioStatus.COMPATIBLE
    assert result.impacts[1].issues[0].field == field
    assert result.aggregate_basis == "MIXED"
    assert "FISCAL_AGGREGATE_HETEROGENEOUS" in {w.code for w in result.warnings}


@pytest.mark.parametrize("field", list(EXPECTED))
def test_absent_metadata_blocks_combination_and_remains_unknown(field):
    result = run(policy(impact(**{field: "UNSPECIFIED"})))
    assert result.status == ScenarioStatus.INCOMPLETE
    assert result.aggregate_basis == "UNSPECIFIED"
    assert result.years[0].combined is None
    assert result.impacts[0].issues[0].code == "METADATA_UNSPECIFIED"
    if field == "price_basis":
        assert result.price_basis == "UNSPECIFIED"


def test_all_unknown_defaults_and_all_mismatch_reasons_are_retained():
    row = ScenarioImpact("unknown", 2027, ImpactType.NEW_EXPENSE, Decimal("100.00"))
    result = run(policy(row))
    assert len(result.impacts[0].issues) == 5 and result.status == ScenarioStatus.INCOMPLETE
    result = run(policy(replace(row, fiscal_scope="STATE")))
    assert len(result.impacts[0].issues) == 5 and result.status == ScenarioStatus.NOT_COMPARABLE


def test_unconfirmed_exclusion_blocks_combination():
    premise = replace(scenario(), excludes_plan_impacts=False)
    result = run(policy(impact()), premise=premise)
    assert result.status == ScenarioStatus.NOT_COMPARABLE
    assert all(row.combined is None for row in result.years)
    assert result.issues[0].code == "DOUBLE_COUNTING_UNCHECKED"
    assert "DOUBLE_COUNTING_UNCHECKED" in {warning.code for warning in result.warnings}
    assert any("declaração do autor" in limit for limit in result.limitations)
    assert (
        FiscalScenario(
            "s",
            "t",
            "e",
            "ref",
            2027,
            2027,
            (ScenarioYear(2027, Decimal("0"), Decimal("0"), "Zero explícito"),),
        ).excludes_plan_impacts
        is False
    )


@pytest.mark.parametrize(
    "kind,amount,field",
    [
        (ImpactType.REVENUE_REDUCTION, "2000.01", "net_revenue"),
        (ImpactType.EXPENSE_REDUCTION, "1800.01", "primary_expenditure"),
    ],
)
def test_negative_component_in_last_year_blocks_every_year_without_clamp(kind, amount, field):
    result = run(policy(impact(id="normal"), impact(kind, amount, id="negative", year=2028)))
    assert result.status == ScenarioStatus.NOT_COMPARABLE
    assert all(row.combined is None for row in result.years)
    assert result.issues[-1].code == "NEGATIVE_PROJECTED_COMPONENT"
    assert result.issues[-1].field == field and result.issues[-1].year == 2028
    assert (
        result.years[1].incremental.net_impact == Decimal(amount) * -1
        if kind == ImpactType.REVENUE_REDUCTION
        else result.years[1].incremental.net_impact == Decimal(amount)
    )


@pytest.mark.parametrize(
    "kind,field",
    [(ImpactType.NEW_REVENUE, "net_revenue"), (ImpactType.NEW_EXPENSE, "primary_expenditure")],
)
def test_projected_component_overflow_blocks_combination_preserving_exact_separate_sums(
    kind, field
):
    premise = replace(
        scenario(),
        years=(
            replace(scenario().years[0], net_revenue=MAX_MONEY, primary_expenditure=MAX_MONEY),
            scenario().years[1],
        ),
    )
    result = run(policy(impact(kind, "0.01")), premise=premise)
    assert result.status == ScenarioStatus.NOT_COMPARABLE
    assert result.issues[0].code == "PROJECTED_AMOUNT_OVERFLOW" and result.issues[0].field == field
    assert result.years[0].declared.net_revenue == MAX_MONEY
    assert result.years[0].combined is None and result.years[1].combined is None
    assert abs(result.cumulative_incremental) == Decimal("0.01")


def test_disabled_and_outside_period_incompatible_amounts_do_not_block_active_ones():
    disabled = replace(
        policy(impact(id="disabled", fiscal_scope="STATE")), version_id="disabled-v", enabled=False
    )
    result = run(
        policy(impact(id="inside"), impact(id="outside", year=2026, fiscal_scope="STATE")), disabled
    )
    assert result.status == ScenarioStatus.COMPATIBLE
    assert len(result.impacts) == 1
    assert result.cumulative_incremental == Decimal("-100.10")
    assert {"OUTSIDE_PERIOD", "POLICY_DISABLED"}.issubset({w.code for w in result.warnings})


def test_no_impacts_and_not_applicable_never_claim_combination():
    for policies in (
        (),
        (ScenarioPolicy("none", EstimateStatus.NOT_APPLICABLE),),
        (policy(),),
        (policy(impact(year=2026)),),
        (policy(impact(), enabled=False),),
    ):
        result = run(*policies)
        assert result.status == ScenarioStatus.NO_IMPACTS
        assert all(row.combined is None for row in result.years)
        assert result.cumulative_incremental == Decimal("0.00")


def test_unestimated_active_policy_precedes_no_impacts_or_absent_confirmation():
    unknown = ScenarioPolicy("unknown", EstimateStatus.NOT_ESTIMATED)
    for policies in ((unknown,), (unknown, policy(impact()))):
        result = run(*policies)
        assert result.status == ScenarioStatus.INCOMPLETE and result.incremental_is_partial
        assert all(row.combined is None for row in result.years)
        assert "NOT_ESTIMATED" in {issue.code for issue in result.issues}
    result = run(unknown, premise=replace(scenario(), excludes_plan_impacts=False))
    assert result.status == ScenarioStatus.INCOMPLETE


def test_immutable_inputs_readonly_baseline_and_determinism():
    base = baseline()
    before = copy.deepcopy(base)
    premise = scenario()
    proposals = (policy(impact()),)
    first = simulate_scenario(base, premise, proposals)
    assert simulate_scenario(base, premise, proposals) == first
    assert base == before
    with pytest.raises(FrozenInstanceError):
        premise.title = "Changed"
    with pytest.raises(FrozenInstanceError):
        proposals[0].impacts[0].amount = Decimal("1.00")
    with pytest.raises(FrozenInstanceError):
        first.years[0].declared.net_revenue = Decimal("0")


def test_reference_identity_and_historical_year_validation():
    with pytest.raises(ValueError, match="reference_baseline_id"):
        run(premise=replace(scenario(), reference_baseline_id="another"))
    for year in (2024, 2025):
        premise = replace(
            scenario(),
            start_year=year,
            end_year=year,
            years=(ScenarioYear(year, Decimal("1.00"), Decimal("2.00"), "Fictício"),),
        )
        with pytest.raises(ValueError, match="posteriores"):
            run(premise=premise)
    for source in (
        {},
        [],
        {"id": "reviewed-frozen-baseline", "fiscal": {"status": "AVAILABLE"}},
        replace_baseline_id(""),
    ):
        with pytest.raises(ValueError):
            run(context=source)


def replace_baseline_id(value):
    source = baseline()
    source["id"] = value
    return source


@pytest.mark.parametrize(
    "field,value",
    [
        ("year", True),
        ("year", 2027.0),
        ("year", 1899),
        ("year", 2201),
        ("net_revenue", True),
        ("net_revenue", 1.0),
        ("net_revenue", None),
        ("net_revenue", Decimal("NaN")),
        ("net_revenue", Decimal("Infinity")),
        ("net_revenue", Decimal("-0.01")),
        ("net_revenue", Decimal("10000000000000000.00")),
        ("net_revenue", Decimal("1.001")),
        ("net_revenue", Decimal("1.000")),
        ("primary_expenditure", None),
        ("primary_expenditure", Decimal("-1.00")),
        ("justification", " "),
        ("justification", None),
    ],
)
def test_invalid_annual_premises_fail_before_arithmetic(field, value):
    with pytest.raises(ValueError):
        replace(scenario().years[0], **{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("start_year", True),
        ("end_year", 2028.0),
        ("id", None),
        ("title", " "),
        ("explanation", []),
        ("reference_baseline_id", ""),
        ("excludes_plan_impacts", 1),
        ("excludes_plan_impacts", "true"),
        ("fiscal_scope", "STATE"),
        ("accounting_basis", "ACCRUAL"),
        ("price_basis", "CONSTANT"),
        ("price_base_year", 2020),
        ("component", "INTEREST"),
        ("period_basis", "PARTIAL_YEAR"),
        ("currency", "USD"),
    ],
)
def test_invalid_scenario_contract_is_rejected(field, value):
    with pytest.raises(ValueError):
        replace(scenario(), **{field: value})


def test_year_gaps_duplicates_order_horizon_and_explicit_zero():
    one = scenario().years[0]
    for rows in ((one,), (one, one), (one, replace(one, year=2029)), [one, scenario().years[1]]):
        with pytest.raises(ValueError):
            replace(scenario(), years=rows)
    with pytest.raises(ValueError):
        replace(scenario(), start_year=2029)
    years = tuple(
        ScenarioYear(year, Decimal("0.00"), Decimal("0.00"), "Zero explícito")
        for year in range(2027, 2057)
    )
    premise = replace(scenario(), end_year=2056, years=years)
    assert len(run(premise=premise).years) == 30
    with pytest.raises(ValueError, match="30 anos"):
        replace(premise, end_year=2057, years=(*years, replace(years[0], year=2057)))
    assert (
        run(premise=replace(scenario(), years=tuple(reversed(scenario().years)))).years[0].year
        == 2027
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", None),
        ("year", True),
        ("kind", "NEW_EXPENSE"),
        ("amount", 1.0),
        ("amount", Decimal("NaN")),
        ("fiscal_scope", None),
        ("fiscal_scope", "UNKNOWN"),
        ("accounting_basis", []),
        ("price_basis", "UNKNOWN"),
        ("price_base_year", 2020),
        ("component", "TOTAL"),
        ("period_basis", "MONTH"),
    ],
)
def test_invalid_impact_shape_or_unknown_enum_is_rejected(field, value):
    with pytest.raises(ValueError):
        replace(impact(), **{field: value})


def test_constant_price_reference_and_policy_shapes():
    with pytest.raises(ValueError):
        replace(impact(), price_basis="CONSTANT")
    with pytest.raises(ValueError):
        replace(impact(), price_basis="CONSTANT", price_base_year=True)
    for field, value in (
        ("version_id", None),
        ("status", "ESTIMATED"),
        ("enabled", 1),
        ("unfunded", "false"),
        ("impacts", []),
    ):
        with pytest.raises(ValueError):
            replace(policy(), **{field: value})
    for status in (EstimateStatus.NOT_ESTIMATED, EstimateStatus.NOT_APPLICABLE):
        with pytest.raises(ValueError):
            ScenarioPolicy("p", status, (impact(),))
    with pytest.raises(ValueError):
        simulate_scenario(baseline(), scenario(), [])
    with pytest.raises(ValueError):
        simulate_scenario(baseline(), {}, ())
    with pytest.raises(ValueError):
        run(policy(), policy())
    with pytest.raises(ValueError):
        run(policy(impact()), replace(policy(impact()), version_id="other"))


@pytest.mark.parametrize(
    "url",
    [
        "https://ibge.gov.br/table?id=1",
        "http://example.test/report",
        "https://example.test:443/x#part",
    ],
)
def test_reference_urls_are_retained_without_network(url, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network is forbidden")

    monkeypatch.setattr("socket.socket", forbidden)
    premise = replace(
        scenario(), years=(replace(scenario().years[0], source_urls=(url,)), scenario().years[1])
    )
    assert run(premise=premise).scenario.years[0].source_urls == (url,)


@pytest.mark.parametrize(
    "urls",
    [
        ["https://example.test"],
        ("file:///etc/secret",),
        ("javascript:alert(1)",),
        ("https://",),
        ("https://example.test:bad",),
        ("https://example.test:99999",),
        ("https://user:pass@example.test",),
        ("https://example.test/has space",),
        ("https://example.test/\n",),
        (None,),
    ],
)
def test_invalid_reference_urls_are_rejected(urls):
    with pytest.raises(ValueError):
        replace(scenario().years[0], source_urls=urls)


def test_exact_large_decimal_aggregation_is_independent_of_caller_precision():
    rows = tuple(
        impact(ImpactType.NEW_REVENUE, str(MAX_MONEY), id=f"i{index}") for index in range(100)
    )
    with localcontext() as context:
        context.prec = 6
        result = run(policy(*rows))
        assert context.prec == 6
    assert result.cumulative_incremental == Decimal("999999999999999999.00")
    assert result.years[0].incremental.new_revenues == Decimal("999999999999999999.00")
    assert result.status == ScenarioStatus.NOT_COMPARABLE
    assert result.years[0].combined is None
    assert "PROJECTED_AMOUNT_OVERFLOW" in {issue.code for issue in result.issues}


def test_exact_numeric_boundary_and_explicit_zero_can_be_combined():
    premise = replace(
        scenario(),
        years=(
            replace(scenario().years[0], net_revenue=MAX_MONEY, primary_expenditure=MAX_MONEY),
            scenario().years[1],
        ),
    )
    result = run(policy(impact(amount="0.00")), premise=premise)
    assert result.status == ScenarioStatus.COMPATIBLE
    assert result.years[0].combined.net_revenue == MAX_MONEY
    assert result.years[0].combined.primary_expenditure == MAX_MONEY
    assert result.years[0].combined.primary_balance == Decimal("0.00")


def test_different_constant_price_years_remain_mixed_and_are_never_converted():
    first = impact(price_basis="CONSTANT", price_base_year=2020)
    second = impact(id="j", price_basis="CONSTANT", price_base_year=2021)
    result = run(policy(first, second))
    assert result.status == ScenarioStatus.NOT_COMPARABLE
    assert result.price_basis == result.aggregate_basis == "MIXED"
    assert result.cumulative_incremental == Decimal("-200.20")
    assert all(row.combined is None for row in result.years)
