"""Storage/review adapter for optional plan scenarios; no external source fetching."""

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from enum import Enum

from pydantic import ValidationError
from sqlalchemy import select

from app.core.errors import DomainError
from app.modules.plans.models import PlanPolicy
from app.modules.plans.schemas import FiscalScenarioDraft
from app.simulation.compatibility import METADATA_FIELDS
from app.simulation.fiscal import EstimateStatus, ImpactType
from app.simulation.scenario import (
    SCENARIO_METHOD_VERSION,
    FiscalScenario,
    ScenarioImpact,
    ScenarioPolicy,
    ScenarioYear,
    simulate_scenario,
)

PAYLOAD_FIELDS = ("title", "explanation", "reference_baseline_id", "years")


def payload(config):
    """Readonly review state never belongs to a client-editable scenario payload."""
    if not isinstance(config, dict):
        raise DomainError(422, "SCENARIO_INVALID", "O cenário salvo deve ser um objeto.")
    return {
        field: deepcopy(config.get(field, [] if field == "years" else ""))
        for field in PAYLOAD_FIELDS
    }


def clear_review(config):
    if config is None:
        return None
    return {
        **payload(config),
        "excludes_plan_impacts": False,
        "reviewed_input_hash": None,
        "reviewed_at": None,
    }


def review_input_hash(session, version):
    if version.fiscal_scenario is None:
        return None
    items = session.scalars(
        select(PlanPolicy)
        .where(PlanPolicy.plan_version_id == version.id)
        .order_by(PlanPolicy.position)
    ).all()
    inputs = {
        "scenario_method_version": SCENARIO_METHOD_VERSION,
        "scenario": payload(version.fiscal_scenario),
        "baseline_snapshot": version.baseline_snapshot,
        "start_year": version.start_year,
        "end_year": version.end_year,
        "policies": [
            {
                "policy_version_id": str(item.policy_version_id),
                "is_enabled": item.is_enabled,
                "position": item.position,
            }
            for item in items
        ],
    }
    canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def scenario_view(session, version):
    config = version.fiscal_scenario
    if config is None:
        return None
    current_hash = review_input_hash(session, version)
    confirmed = (
        config.get("excludes_plan_impacts") is True
        and config.get("reviewed_input_hash") == current_hash
        and bool(config.get("reviewed_at"))
    )
    return {
        **payload(config),
        "excludes_plan_impacts": confirmed,
        "review_input_hash": current_hash,
        "reviewed_input_hash": config.get("reviewed_input_hash"),
        "reviewed_at": config.get("reviewed_at"),
    }


def domain_scenario(session, version):
    if version.fiscal_scenario is None:
        raise DomainError(422, "SCENARIO_INCOMPLETE", "Este plano não tem cenário futuro ativo.")
    try:
        draft = FiscalScenarioDraft.model_validate(payload(version.fiscal_scenario))
    except ValidationError as error:
        raise DomainError(
            422, "SCENARIO_INVALID", "O cenário salvo contém campos inválidos."
        ) from error
    if (
        not draft.title
        or not draft.explanation
        or not draft.reference_baseline_id
        or not draft.years
        or any(
            row.net_revenue is None or row.primary_expenditure is None or not row.justification
            for row in draft.years
        )
    ):
        raise DomainError(
            422,
            "SCENARIO_INCOMPLETE",
            "Preencha título, explicação, referência e premissas justificadas de todos os anos.",
        )
    try:
        scenario = FiscalScenario(
            id=f"plan-version:{version.id}",
            title=draft.title,
            explanation=draft.explanation,
            reference_baseline_id=draft.reference_baseline_id,
            start_year=version.start_year,
            end_year=version.end_year,
            years=tuple(
                ScenarioYear(
                    row.year,
                    row.net_revenue,
                    row.primary_expenditure,
                    row.justification,
                    tuple(row.source_urls),
                )
                for row in draft.years
            ),
            excludes_plan_impacts=scenario_view(session, version)["excludes_plan_impacts"],
        )
        # Validate historical provenance/year/identity before evaluating selected policy amounts.
        simulate_scenario(version.baseline_snapshot, scenario, ())
        return scenario
    except ValueError as error:
        raise DomainError(422, "SCENARIO_INVALID", str(error)) from error


def scenario_result(session, version, policies):
    scenario = domain_scenario(session, version)
    try:
        declared = tuple(
            ScenarioPolicy(
                policy["version_id"],
                EstimateStatus(policy["estimate_status"]),
                tuple(
                    ScenarioImpact(
                        row["id"],
                        row["year"],
                        ImpactType(row["type"]),
                        Decimal(row["amount"]),
                        **{field: row[field] for field in METADATA_FIELDS},
                    )
                    for row in policy["impacts"]
                ),
                enabled=policy["enabled"],
                unfunded=policy["unfunded"],
            )
            for policy in policies
        )
        return simulate_scenario(version.baseline_snapshot, scenario, declared)
    except ValueError as error:
        raise DomainError(422, "SCENARIO_INVALID", str(error)) from error


def json_result(value):
    """Dataclass/Decimal/enum serialization retains exact money as strings in JSON."""
    if is_dataclass(value):
        return json_result(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: json_result(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_result(item) for item in value]
    return value
