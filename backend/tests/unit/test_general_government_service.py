"""Annual official-statistics wrappers: exact provenance, separation and safe failure."""

from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect

from app.integrations import general_government as provider
from app.modules.indicators import collection, fiscal_baseline
from app.modules.indicators import general_government as service
from app.modules.sources.schemas import SourceInput, SourceResponse
from tests.general_government_fixture import payload


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


def test_full_year_all_sectors_signed_values_and_coverage_are_preserved_without_mutation():
    saved = cohort()
    original = deepcopy(saved)
    source = deepcopy(saved["source_snapshot"])
    result = service.assemble(saved, saved["year"], source)
    assert result["status"] == "AVAILABLE"
    assert result["period_start"] == f"{saved['year']}-01-01"
    assert result["period_end"] == f"{saved['year']}-12-31"
    assert result["payload"] == saved["payload"]
    assert result["revision"] == 1
    assert len(result["payload"]["sectors"]) == 8
    assert result["payload"]["coverage"]["municipal_extrapolated"] is True
    assert result["source"]["license"] != "ODbL 1.0"
    assert "RTN" in result["methodology"]
    result["payload"]["sectors"][0]["amounts"]["revenue"] = "999.00"
    result["source"]["title"] = "Modified by caller"
    assert saved == original and source == original["source_snapshot"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("year", 2024),
        ("year", 2025.0),
        ("source_hash", "a" * 64),
        ("parser_version", "changed"),
        ("precision_version", "changed"),
        ("cohort_fingerprint", "b" * 64),
        ("revision", 0),
        ("revision", True),
        ("retrieved_at", "2026-01-01T00:00:00"),
        ("retrieved_at", "bad-date"),
    ],
)
def test_incompatible_saved_provenance_never_exposes_amounts(field, value):
    saved = cohort()
    source = deepcopy(saved["source_snapshot"])
    saved[field] = value
    result = service.assemble(saved, 2025, source)
    assert result["status"] == "INCOMPLETE" and result["year"] == 2025
    assert result["payload"] is None and result["source"] is None
    assert result["revision"] is None and result["cohort_fingerprint"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "Private title"),
        ("institution", "Private institution"),
        ("url", "https://example.com"),
        ("source_type", "OTHER"),
        ("is_example", True),
        ("description", "Private unpublished description"),
    ],
)
def test_matching_url_does_not_override_source_identity_or_terms(field, value):
    saved = cohort()
    source = deepcopy(saved["source_snapshot"])
    source[field] = value
    assert service.assemble(saved, 2025, source)["status"] == "INCOMPLETE"


@pytest.mark.parametrize(
    "failure", ["missing_sector", "amount", "definition", "license", "coverage", "float"]
)
def test_provider_semantics_revalidated_even_when_fingerprint_recomputed(failure):
    saved = cohort()
    data = saved["payload"]
    if failure == "missing_sector":
        data["sectors"].pop()
    elif failure == "amount":
        data["sectors"][0]["amounts"]["revenue"] = "999999.00"
    elif failure == "definition":
        data["accounting_basis"] = "cash"
    elif failure == "license":
        data["source"]["license"] = "MIT"
    elif failure == "coverage":
        data["coverage"]["municipal_extrapolated"] = False
    elif failure == "float":
        data["sectors"][0]["amounts"]["revenue"] = 100.25
    if failure != "float":
        data["fingerprint"] = provider.fingerprint(data)
        saved["cohort_fingerprint"] = data["fingerprint"]
    result = service.assemble(saved, 2025, saved["source_snapshot"])
    assert result["status"] == "INCOMPLETE" and result["payload"] is None


def test_missing_reference_source_or_future_retrieval_does_not_expose_data():
    assert service.assemble(None, None)["year"] is None
    assert service.assemble(None, 2025)["status"] == "EMPTY"
    saved = cohort()
    source = deepcopy(saved["source_snapshot"])
    assert service.assemble(saved, 2025, None)["status"] == "INCOMPLETE"
    saved["retrieved_at"] = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    assert service.assemble(saved, 2025, source)["status"] == "INCOMPLETE"
    saved = cohort()
    saved["source_snapshot"]["license"] = "MIT"
    assert service.assemble(saved, 2025, source)["status"] == "INCOMPLETE"


@pytest.mark.parametrize("year", [True, 2025.0, "2025", 2000, 10000, datetime.now(UTC).year])
def test_invalid_reference_year_does_not_construct_dates_or_expose_data(year):
    result = service.assemble(cohort(), year)
    assert result["payload"] is None
    assert result["period_start"] is None and result["period_end"] is None


def test_public_views_omit_database_ids_actor_and_private_metadata():
    saved = cohort()
    saved["retrieved_at"] = datetime.fromisoformat(saved["retrieved_at"])
    row = SimpleNamespace(**saved, created_by=uuid4(), source_id=uuid4(), id=uuid4())
    assert not {"id", "source_id", "created_by"} & service.cohort_view(row).keys()
    source = SimpleNamespace(**saved["source_snapshot"], created_by=uuid4(), id=uuid4())
    assert not {"id", "created_by"} & service.source_view(source).keys()


def test_latest_selects_revision_before_validating_without_old_valid_fallback():
    class Capture:
        def scalar(self, statement):
            self.statement = statement
            return "latest"

    session = Capture()
    assert service.latest(session, 2025) == "latest"
    sql = str(session.statement.compile(dialect=dialect(), compile_kwargs={"literal_binds": True}))
    assert "ORDER BY general_government_cohorts.revision DESC" in sql
    assert "LIMIT 1" in sql and "source_hash =" not in sql and "parser_version =" not in sql


def test_output_marker_is_not_a_contributor_input():
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
    marked = SourceResponse.model_validate({**original, "collection_code": "general-government"})
    assert marked.model_dump(mode="json")["collection_code"] == "general-government"
    with pytest.raises(ValidationError):
        SourceInput(
            title="Private",
            institution="Institution",
            url="https://example.com",
            accessed_at=date(2025, 1, 1),
            collection_code="general-government",
        )


def test_missing_reference_skips_external_fetch_and_all_writes(monkeypatch):
    monkeypatch.setattr(
        fiscal_baseline, "current", lambda session: {"status": "EMPTY", "year": None}
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("No reference; no provider or save calls allowed")

    monkeypatch.setattr(provider, "fetch_year", forbidden)
    monkeypatch.setattr(service, "save_cohort", forbidden)
    result = collection.collect_general_government(None, None, date(2026, 1, 1))
    assert result["general-government"]["status"] == "NO_DATA"


def test_failed_download_rolls_back_and_hides_exception_payload(monkeypatch, caplog):
    monkeypatch.setattr(
        fiscal_baseline, "current", lambda session: {"status": "AVAILABLE", "year": 2025}
    )

    def failed(*args):
        raise TimeoutError("secret-token-private-url")

    monkeypatch.setattr(provider, "fetch_year", failed)
    rollbacks = []
    session = SimpleNamespace(rollback=lambda: rollbacks.append(True))
    result = collection.collect_general_government(session, None, date(2026, 1, 1))
    assert result["general-government"]["status"] == "FAILED"
    assert rollbacks == [True]
    assert "secret-token" not in str(result) and "secret-token" not in caplog.text


def test_current_rejects_source_owned_by_a_different_actor_even_with_matching_metadata(monkeypatch):
    saved = cohort()
    saved["retrieved_at"] = datetime.fromisoformat(saved["retrieved_at"])
    row = SimpleNamespace(**saved, created_by=uuid4(), source_id=uuid4(), id=uuid4())
    source = SimpleNamespace(**saved["source_snapshot"], created_by=uuid4(), id=row.source_id)
    session = SimpleNamespace(get=lambda model, identity: source)
    monkeypatch.setattr(
        service, "current_fiscal", lambda session: {"status": "AVAILABLE", "year": 2025}
    )
    monkeypatch.setattr(service, "latest", lambda session, year: row)
    assert service.current(session)["status"] == "INCOMPLETE"
