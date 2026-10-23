"""Functional spending wrappers validate immutable aggregates without a database/network."""

from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect

from app.integrations import federal_spending as provider
from app.modules.indicators import fiscal_spending as service
from app.modules.sources.schemas import SourceInput, SourceResponse
from tests.federal_spending_fixture import payload


def cohort(data=None):
    data = data or payload()
    return {
        "year": data["year"],
        "revision": 1,
        "source_hash": data["resource"]["sha256"],
        "parser_version": data["parser_version"],
        "precision_version": data["precision_version"],
        "cohort_fingerprint": data["fingerprint"],
        "source_snapshot": service.source_snapshot(data),
        "payload": data,
        "retrieved_at": "2026-01-01T00:00:00+00:00",
    }


@pytest.mark.parametrize("paid", ["100.10", "-100.10", "0.00"])
def test_signed_stages_and_exact_months_are_preserved_without_mutating_inputs(paid):
    row = cohort(payload(paid=paid))
    source = deepcopy(row["source_snapshot"])
    original = deepcopy(row)
    result = service.assemble(row, 2025, source)
    assert result["status"] == "AVAILABLE" and result["payload"] == row["payload"]
    assert result["period_start"] == "2025-01-01" and result["period_end"] == "2025-12-31"
    assert result["revision"] == 1 and result["cohort_fingerprint"] == row["cohort_fingerprint"]
    assert len(result["payload"]["months"]) == 12
    assert len(result["payload"]["natures"]) == 1  # Absent natures are never zero-imputed.
    result["payload"]["totals"]["PAID"] = "999.00"
    result["source"]["title"] = "Changed by caller"
    assert row == original and source == original["source_snapshot"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("year", 2024),
        ("source_hash", "a" * 64),
        ("parser_version", "changed"),
        ("precision_version", "changed"),
        ("cohort_fingerprint", "b" * 64),
        ("revision", 0),
        ("revision", True),
        ("retrieved_at", "2026-01-01T00:00:00"),
        ("retrieved_at", "not-a-date"),
    ],
)
def test_incompatible_persistence_provenance_never_exposes_amounts(field, value):
    row = cohort()
    source = deepcopy(row["source_snapshot"])
    row[field] = value
    result = service.assemble(row, 2025, source)
    assert result["status"] == "INCOMPLETE" and result["year"] == 2025
    assert result["payload"] is None and result["source"] is None
    assert result["revision"] is None and result["cohort_fingerprint"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "Private title"),
        ("institution", "Other institution"),
        ("url", "https://example.com"),
        ("source_type", "OTHER"),
        ("is_example", True),
        ("description", "Other terms"),
    ],
)
def test_source_collision_or_mutation_is_not_verified_by_url(field, value):
    row = cohort()
    source = deepcopy(row["source_snapshot"])
    source[field] = value
    assert service.assemble(row, 2025, source)["status"] == "INCOMPLETE"


@pytest.mark.parametrize("failure", ["missing_month", "totals", "stage", "definition", "license"])
def test_payload_coherence_is_validated_even_after_rehash(failure):
    row = cohort()
    p = row["payload"]
    if failure == "missing_month":
        p["months"].pop()
    elif failure == "totals":
        p["totals"]["PAID"] = "1234.00"
    elif failure == "stage":
        p["months"][0]["groups"][0]["amounts"]["TOTAL_PAID"] = "99.00"
    elif failure == "definition":
        p["accounting_basis"] = "cash"
    elif failure == "license":
        p["source"]["license"] = "MIT"
    p["fingerprint"] = provider.fingerprint(p)
    row["cohort_fingerprint"] = p["fingerprint"]
    assert service.assemble(row, 2025, row["source_snapshot"])["status"] == "INCOMPLETE"


def test_missing_reference_missing_source_future_retrieval_and_snapshot_mutation_are_unavailable():
    assert service.assemble(None, None)["payload"] is None
    assert service.assemble(None, None)["year"] is None
    assert service.assemble(None, 2025)["status"] == "EMPTY"
    row = cohort()
    source = deepcopy(row["source_snapshot"])
    assert service.assemble(row, 2025, None)["status"] == "INCOMPLETE"
    row["retrieved_at"] = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    assert service.assemble(row, 2025, source)["status"] == "INCOMPLETE"
    row = cohort()
    row["source_snapshot"]["license"] = "MIT"
    assert service.assemble(row, 2025, source)["status"] == "INCOMPLETE"


def test_public_cohort_and_source_views_omit_database_identity_and_actor():
    saved = cohort()
    saved["retrieved_at"] = datetime.fromisoformat(saved["retrieved_at"])
    row = SimpleNamespace(**saved, created_by=uuid4(), source_id=uuid4(), id=uuid4())
    exposed = service.cohort_view(row)
    assert not {"id", "source_id", "created_by"} & exposed.keys()
    assert exposed["retrieved_at"].endswith("+00:00")
    source = SimpleNamespace(**saved["source_snapshot"], id=uuid4(), created_by=uuid4())
    assert not {"id", "created_by"} & service.source_view(source).keys()


def test_latest_query_selects_revision_before_validation_no_fallback():
    class Capture:
        def scalar(self, statement):
            self.statement = statement
            return "newest-row"

    session = Capture()
    assert service.latest(session, 2025) == "newest-row"
    sql = str(session.statement.compile(dialect=dialect(), compile_kwargs={"literal_binds": True}))
    assert "ORDER BY fiscal_spending_cohorts.revision DESC" in sql
    assert "LIMIT 1" in sql and "source_hash =" not in sql and "parser_version =" not in sql


def test_collection_marker_is_output_only_and_legacy_serialization_is_unchanged():
    original = {
        "id": str(uuid4()),
        "title": "Existing source",
        "institution": "Institution",
        "url": "https://example.com",
        "source_type": "OFFICIAL",
        "publication_date": None,
        "accessed_at": "2025-01-01",
        "description": None,
        "is_example": False,
        "usage_count": 0,
        "license": None,
        "license_url": None,
    }
    assert SourceResponse.model_validate(original).model_dump(mode="json") == original
    marked = SourceResponse.model_validate({**original, "collection_code": "federal-spending"})
    assert marked.model_dump(mode="json")["collection_code"] == "federal-spending"
    with pytest.raises(ValidationError):
        SourceInput(
            title="Private",
            institution="Institution",
            url="https://example.com",
            accessed_at=date(2025, 1, 1),
            collection_code="federal-spending",
        )
