import copy
import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.simulations.models import Simulation
from app.modules.simulations.service import execution_view
from app.simulation.compatibility import EXPECTED, METADATA_FIELDS
from tests.unit.test_fiscal_compatibility import baseline

from .test_auth import signup
from .test_plans import plan_input
from .test_policies import draft, headers

pytestmark = pytest.mark.database


@pytest.fixture
def frozen_base(monkeypatch):
    context = {"id": "frozen-reviewed-2025", "status": "PARTIAL", "fiscal": baseline()["fiscal"]}
    monkeypatch.setattr(
        "app.modules.policies.service.current_baseline", lambda _: copy.deepcopy(context)
    )
    monkeypatch.setattr(
        "app.modules.plans.service.current_baseline", lambda _: copy.deepcopy(context)
    )
    return context


def publish(client, user, metadata=None, year=2025):
    proposal, _ = draft(client, user)
    response = client.patch(
        f"/api/v1/policies/{proposal['id']}",
        headers=headers(user),
        json={
            "implementation_start": 2025,
            "implementation_end": 2027,
            "impacts": [
                {
                    "year": year,
                    "impact_type": "NEW_EXPENSE",
                    "amount": "100.10",
                    "description": "Fictício",
                    **(metadata or {}),
                }
            ],
        },
    )
    assert response.status_code == 200, response.text
    response = client.post(f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def plan(client, user, proposals):
    data = plan_input(proposals)
    data.update(start_year=2025, end_year=2027)
    response = client.post("/api/v1/plans", headers=headers(user), json=data)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def run(client, user, item):
    response = client.post(f"/api/v1/plans/{item['id']}/simulate", headers=headers(user))
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.parametrize(
    "metadata", [EXPECTED, {**EXPECTED, "price_basis": "CONSTANT", "price_base_year": 2020}]
)
def test_metadata_roundtrip_plan_view_and_new_draft_preserve_published_metadata(
    auth_client, db_session, frozen_base, metadata
):
    user, _ = signup(auth_client)
    proposal = publish(auth_client, user, metadata)
    original = copy.deepcopy(proposal["version"])
    for field, value in metadata.items():
        assert original["impacts"][0][field] == value
    item = plan(auth_client, user, [proposal])
    assert item["version"]["policies"][0]["impacts"][0]["fiscal_scope"] == "CENTRAL_GOVERNMENT"
    updated = auth_client.patch(
        f"/api/v1/policies/{proposal['id']}", headers=headers(user), json={"title": "Novo rascunho"}
    )
    assert updated.status_code == 200, updated.text
    new = updated.json()["data"]["version"]["impacts"][0]
    for field in METADATA_FIELDS:
        assert new[field] == original["impacts"][0][field]
    assert (
        auth_client.get(f"/api/v1/policies/{proposal['slug']}").json()["data"]["version"]
        == original
    )
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text("UPDATE financial_impacts SET fiscal_scope='STATE' WHERE id=:id"),
            {"id": original["impacts"][0]["id"]},
        )


def test_matching_metadata_snapshot_hash_and_frozen_baseline_repeated_execution(
    auth_client, frozen_base
):
    user, _ = signup(auth_client)
    item = plan(auth_client, user, [publish(auth_client, user, EXPECTED)])
    first = run(auth_client, user, item)
    report = first["assumptions"]["fiscal_compatibility"]
    assert report["status"] == "COMPATIBLE" and not report["baseline_combined"]
    assert first["assumptions"]["price_basis"] == "NOMINAL"
    assert first["input_snapshot"]["fiscal_compatibility"] == report
    assert first["input_snapshot"]["policies"][0]["impacts"][0]["accounting_basis"] == "CASH"
    assert first["input_snapshot"]["baseline_snapshot"] == frozen_base
    assert first["years"][0]["net_impact"] == "-100.10"
    assert first["engine_version"] == "1.0.0"
    canonical = json.dumps(
        first["input_snapshot"], sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    assert hashlib.sha256(canonical.encode()).hexdigest() == first["input_hash"]
    changed = copy.deepcopy(first["input_snapshot"])
    changed["policies"][0]["impacts"][0]["fiscal_scope"] = "STATE"
    assert (
        hashlib.sha256(
            json.dumps(changed, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        ).hexdigest()
        != first["input_hash"]
    )
    assert run(auth_client, user, item)["input_hash"] == first["input_hash"]


def test_legacy_unknown_metadata_does_not_infer_nominal_and_new_simulation_does_not_rewrite_old(
    auth_client, db_session, frozen_base
):
    user, _ = signup(auth_client)
    proposal = publish(auth_client, user)
    assert proposal["version"]["impacts"][0]["price_basis"] == "UNSPECIFIED"
    item = plan(auth_client, user, [proposal])
    old = Simulation(
        plan_version_id=UUID(item["version"]["id"]),
        calculation_version="1.0.0",
        input_snapshot={"historical": True},
        input_hash="a" * 64,
        assumptions={"price_basis": "nominal_by_year"},
        warnings=[],
        is_partial=False,
    )
    db_session.add(old)
    db_session.flush()
    old.status = "COMPLETED"
    old.completed_at = datetime.now(UTC)
    db_session.flush()
    before = execution_view(db_session, old)
    fresh = run(auth_client, user, item)
    assert fresh["assumptions"]["price_basis"] == "UNSPECIFIED"
    assert fresh["assumptions"]["aggregate_basis"] == "UNSPECIFIED"
    assert fresh["assumptions"]["fiscal_compatibility"]["status"] == "INCOMPLETE"
    assert "FISCAL_METADATA_MISSING" in {w["code"] for w in fresh["warnings"]}
    assert execution_view(db_session, old) == before


def test_heterogeneous_declarations_keep_incremental_total_but_warn_about_interpretation(
    auth_client, frozen_base
):
    user, _ = signup(auth_client)
    first = publish(auth_client, user, EXPECTED)
    second = publish(
        auth_client,
        user,
        {**EXPECTED, "price_basis": "CONSTANT", "price_base_year": 2020, "fiscal_scope": "STATE"},
    )
    item = plan(auth_client, user, [first, second])
    result = run(auth_client, user, item)
    assert result["cumulative_impact"] == "-200.20"
    assert result["assumptions"]["price_basis"] == "MIXED"
    assert result["assumptions"]["aggregate_basis"] == "MIXED"
    assert result["assumptions"]["fiscal_compatibility"]["status"] == "NOT_COMPARABLE"
    assert result["assumptions"]["fiscal_compatibility"]["coverage"]["compatible"] == 1
    assert "FISCAL_AGGREGATE_HETEROGENEOUS" in {w["code"] for w in result["warnings"]}


def test_future_nominal_same_scope_still_requires_scenario(auth_client, frozen_base):
    user, _ = signup(auth_client)
    result = run(
        auth_client,
        user,
        plan(auth_client, user, [publish(auth_client, user, EXPECTED, year=2027)]),
    )
    report = result["assumptions"]["fiscal_compatibility"]
    assert report["status"] == "NOT_COMPARABLE"
    assert report["impacts"][0]["issues"][0]["code"] == "FUTURE_ASSUMPTIONS_REQUIRED"


@pytest.mark.parametrize(
    "sql",
    [
        "price_basis='CONSTANT',price_base_year=NULL",
        "price_basis='NOMINAL',price_base_year=2020",
        "fiscal_scope='INVALID'",
        "accounting_basis='OTHER'",
        "component='TOTAL'",
        "period_basis='MONTH'",
    ],
)
def test_database_constraints_reject_invalid_metadata_on_drafts(auth_client, db_session, sql):
    user, _ = signup(auth_client)
    proposal, _ = draft(auth_client, user)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text(f"UPDATE financial_impacts SET {sql} WHERE id=:id"),
            {"id": proposal["version"]["impacts"][0]["id"]},
        )


def test_replacing_draft_impacts_without_metadata_resets_to_unknown_not_previous_defaults(
    auth_client, frozen_base
):
    user, _ = signup(auth_client)
    proposal = publish(
        auth_client, user, {**EXPECTED, "price_basis": "CONSTANT", "price_base_year": 2020}
    )
    response = auth_client.patch(
        f"/api/v1/policies/{proposal['id']}",
        headers=headers(user),
        json={
            "impacts": [
                {
                    "year": 2025,
                    "impact_type": "NEW_EXPENSE",
                    "amount": "100.10",
                    "description": "Fictício",
                }
            ]
        },
    )
    assert response.status_code == 200, response.text
    row = response.json()["data"]["version"]["impacts"][0]
    assert all(row[field] == "UNSPECIFIED" for field in EXPECTED)
    assert row["price_base_year"] is None
    assert (
        auth_client.get(f"/api/v1/policies/{proposal['slug']}").json()["data"]["version"][
            "impacts"
        ][0]["price_basis"]
        == "CONSTANT"
    )
