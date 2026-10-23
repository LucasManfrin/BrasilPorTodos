"""Annual incremental fiscal aggregation; see docs/data/METHODOLOGY.md."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import StrEnum

from app.simulation.version import SIMULATION_ENGINE_VERSION


class ImpactType(StrEnum):
    NEW_EXPENSE = "NEW_EXPENSE"
    EXPENSE_REDUCTION = "EXPENSE_REDUCTION"
    NEW_REVENUE = "NEW_REVENUE"
    REVENUE_REDUCTION = "REVENUE_REDUCTION"


class EstimateStatus(StrEnum):
    ESTIMATED = "ESTIMATED"
    NOT_ESTIMATED = "NOT_ESTIMATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class Impact:
    year: int
    kind: ImpactType
    amount: Decimal

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            raise ValueError("Money must be Decimal.")
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError("Money must be finite and nonnegative.")
        if self.amount > Decimal("9999999999999999.99"):
            raise ValueError("Money exceeds NUMERIC(18,2).")
        if self.amount != self.amount.quantize(Decimal("0.01")):
            raise ValueError("Money must have at most two decimal places.")
        if type(self.year) is not int or not 1900 <= self.year <= 2200:
            raise ValueError("Year must be between 1900 and 2200.")
        if not isinstance(self.kind, ImpactType):
            raise ValueError("Unknown impact type.")


@dataclass(frozen=True)
class PolicyInput:
    version_id: str
    status: EstimateStatus
    impacts: tuple[Impact, ...] = ()
    enabled: bool = True
    unfunded: bool = False

    def __post_init__(self):
        if not self.version_id.strip():
            raise ValueError("A policy version identifier is required.")
        if not isinstance(self.status, EstimateStatus):
            raise ValueError("Unknown estimate status.")
        if not isinstance(self.impacts, tuple) or any(
            not isinstance(impact, Impact) for impact in self.impacts
        ):
            raise ValueError("Impacts must be an immutable tuple of Impact objects.")
        if self.status != EstimateStatus.ESTIMATED and self.impacts:
            raise ValueError("Only estimated policies can carry fiscal amounts.")


@dataclass(frozen=True)
class YearResult:
    year: int
    new_expenses: Decimal
    expense_reductions: Decimal
    new_revenues: Decimal
    revenue_reductions: Decimal
    net_impact: Decimal


@dataclass(frozen=True)
class Warning:
    code: str
    policy_version_id: str


@dataclass(frozen=True)
class SimulationResult:
    years: tuple[YearResult, ...]
    cumulative_impact: Decimal
    warnings: tuple[Warning, ...]
    is_partial: bool
    engine_version: str = SIMULATION_ENGINE_VERSION


def simulate(start_year: int, end_year: int, policies: tuple[PolicyInput, ...]) -> SimulationResult:
    if (
        type(start_year) is not int
        or type(end_year) is not int
        or not 1900 <= start_year <= end_year <= 2200
    ):
        raise ValueError("Invalid simulation period (supported range: 1900–2200).")
    identifiers = [policy.version_id for policy in policies]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("A policy version cannot appear twice in a plan.")

    totals = {
        year: {kind: Decimal("0.00") for kind in ImpactType}
        for year in range(start_year, end_year + 1)
    }
    warnings: list[Warning] = []
    partial = False
    # Extra precision prevents rounding while aggregating many valid NUMERIC inputs.
    with localcontext() as context:
        context.prec = 40
        for policy in policies:
            if not policy.enabled:
                continue
            if policy.status == EstimateStatus.NOT_ESTIMATED:
                partial = True
                warnings.append(Warning("NOT_ESTIMATED", policy.version_id))
            if policy.unfunded:
                warnings.append(Warning("UNFUNDED", policy.version_id))
            if any(not start_year <= impact.year <= end_year for impact in policy.impacts):
                warnings.append(Warning("OUTSIDE_PERIOD", policy.version_id))
            for impact in policy.impacts:
                if impact.year in totals:
                    totals[impact.year][impact.kind] += impact.amount

        years = tuple(
            YearResult(
                year=year,
                new_expenses=values[ImpactType.NEW_EXPENSE],
                expense_reductions=values[ImpactType.EXPENSE_REDUCTION],
                new_revenues=values[ImpactType.NEW_REVENUE],
                revenue_reductions=values[ImpactType.REVENUE_REDUCTION],
                net_impact=(
                    values[ImpactType.EXPENSE_REDUCTION]
                    + values[ImpactType.NEW_REVENUE]
                    - values[ImpactType.NEW_EXPENSE]
                    - values[ImpactType.REVENUE_REDUCTION]
                ),
            )
            for year, values in totals.items()
        )
        cumulative = sum((year.net_impact for year in years), Decimal("0.00"))
    return SimulationResult(years, cumulative, tuple(warnings), partial)
