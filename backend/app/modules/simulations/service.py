import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal, localcontext

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.plans.models import PlanPolicy, PlanVersion
from app.modules.plans.scenario import domain_scenario, json_result, scenario_result, scenario_view
from app.modules.policies.models import FinancialImpact, PolicyFunding, PolicyVersion
from app.modules.simulations.models import Simulation
from app.modules.simulations.models import SimulationResult as ResultRow
from app.simulation.compatibility import METADATA_FIELDS, assess
from app.simulation.fiscal import EstimateStatus, Impact, ImpactType, PolicyInput, simulate
from app.simulation.scenario import SCENARIO_METHOD_VERSION


def execution_view(session: Session, execution: Simulation):
    rows = session.scalars(
        select(ResultRow).where(ResultRow.simulation_id == execution.id).order_by(ResultRow.year)
    ).all()
    with localcontext() as context:
        context.prec = 40
        cumulative = sum((row.net_impact for row in rows), start=Decimal("0.00"))
    return {
        "id": str(execution.id),
        "status": execution.status,
        "plan_version_id": str(execution.plan_version_id),
        "engine_version": execution.calculation_version,
        "input_hash": execution.input_hash,
        "input_snapshot": execution.input_snapshot,
        "assumptions": execution.assumptions,
        "warnings": execution.warnings,
        "is_partial": execution.is_partial,
        "created_at": execution.created_at.isoformat(),
        "cumulative_impact": str(cumulative),
        "years": [
            {
                "year": row.year,
                "new_expenses": str(row.new_expenses),
                "expense_reductions": str(row.expense_reductions),
                "new_revenues": str(row.new_revenues),
                "revenue_reductions": str(row.revenue_reductions),
                "net_impact": str(row.net_impact),
            }
            for row in rows
        ],
    }


def run_simulation(session: Session, version: PlanVersion):
    if version.fiscal_scenario is not None:
        domain_scenario(session, version)
    items = session.scalars(
        select(PlanPolicy)
        .where(PlanPolicy.plan_version_id == version.id)
        .order_by(PlanPolicy.position)
    ).all()
    snapshot = {
        "plan_version_id": str(version.id),
        "baseline_snapshot": version.baseline_snapshot,
        "start_year": version.start_year,
        "end_year": version.end_year,
        "policies": [],
    }
    inputs = []
    warnings = []
    for item in items:
        proposal = session.get(PolicyVersion, item.policy_version_id)
        impacts = session.scalars(
            select(FinancialImpact)
            .where(FinancialImpact.policy_version_id == proposal.id)
            .order_by(FinancialImpact.year, FinancialImpact.id)
        ).all()
        fundings = session.scalars(
            select(PolicyFunding).where(PolicyFunding.policy_version_id == proposal.id)
        ).all()
        unfunded = any(row.funding_type == "UNFUNDED" for row in fundings)
        inputs.append(
            PolicyInput(
                str(proposal.id),
                EstimateStatus(proposal.financial_impact_status),
                tuple(Impact(row.year, ImpactType(row.impact_type), row.amount) for row in impacts),
                enabled=item.is_enabled,
                unfunded=unfunded,
            )
        )
        snapshot["policies"].append(
            {
                "version_id": str(proposal.id),
                "baseline_id": (proposal.baseline_snapshot or {}).get("id"),
                "version_number": proposal.version_number,
                "title": proposal.title,
                "estimate_status": proposal.financial_impact_status,
                "enabled": item.is_enabled,
                "position": item.position,
                "unfunded": unfunded,
                "impacts": [
                    {
                        "id": str(row.id),
                        "year": row.year,
                        "type": row.impact_type,
                        "amount": str(row.amount),
                        "description": row.description,
                        **{field: getattr(row, field) for field in METADATA_FIELDS},
                    }
                    for row in impacts
                ],
            }
        )
    result = simulate(version.start_year, version.end_year, tuple(inputs))
    maximum = Decimal("9999999999999999.99")
    for year in result.years:
        if any(
            abs(getattr(year, field)) > maximum
            for field in (
                "new_expenses",
                "expense_reductions",
                "new_revenues",
                "revenue_reductions",
                "net_impact",
            )
        ):
            raise DomainError(
                422,
                "SIMULATION_AMOUNT_OVERFLOW",
                "O resultado anual excede o limite de valor suportado.",
            )
    if sum(item.is_enabled for item in items) > 1:
        warnings.append({"code": "INTERACTIONS_NOT_MODELED"})
    warnings.extend(
        {"code": warning.code, "policy_version_id": warning.policy_version_id}
        for warning in result.warnings
    )
    if not version.baseline_snapshot or version.baseline_snapshot.get("status") == "EMPTY":
        warnings.append({"code": "BASELINE_MISSING"})
    if any(
        item["enabled"] and item["baseline_id"] != (version.baseline_snapshot or {}).get("id")
        for item in snapshot["policies"]
    ):
        warnings.append({"code": "BASELINE_DIFFERS"})
    assessment, interpretation, fiscal_warnings = assess(
        version.baseline_snapshot, snapshot["policies"], version.start_year, version.end_year
    )
    snapshot["fiscal_compatibility"] = assessment
    warnings.extend(fiscal_warnings)
    scenario_assumptions = {}
    if version.fiscal_scenario is not None:
        future = json_result(scenario_result(session, version, snapshot["policies"]))
        snapshot["fiscal_scenario"] = {
            **scenario_view(session, version),
            "scenario_method_version": SCENARIO_METHOD_VERSION,
        }
        scenario_assumptions["fiscal_scenario"] = future
        existing = {(warning["code"], warning.get("policy_version_id")) for warning in warnings}
        warnings.extend(
            warning
            for warning in future["warnings"]
            if (warning["code"], warning.get("policy_version_id")) not in existing
        )
    # Economic interactions are a stated limitation, never a detected overlap claim.
    canonical = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    execution = Simulation(
        plan_version_id=version.id,
        calculation_version=result.engine_version,
        input_snapshot=snapshot,
        input_hash=hashlib.sha256(canonical.encode()).hexdigest(),
        assumptions={
            "currency": "BRL",
            **interpretation,
            "fiscal_compatibility": assessment,
            "additive": True,
            "funding_not_added": True,
            "overlap_detection": "review_only",
            **scenario_assumptions,
        },
        warnings=warnings,
        is_partial=result.is_partial,
    )
    session.add(execution)
    session.flush()
    for year in result.years:
        session.add(
            ResultRow(
                simulation_id=execution.id,
                year=year.year,
                new_expenses=year.new_expenses,
                expense_reductions=year.expense_reductions,
                new_revenues=year.new_revenues,
                revenue_reductions=year.revenue_reductions,
                net_impact=year.net_impact,
            )
        )
    session.flush()
    execution.status = "COMPLETED"
    execution.completed_at = datetime.now(UTC)
    session.flush()
    return execution
