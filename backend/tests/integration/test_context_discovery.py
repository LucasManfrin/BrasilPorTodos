"""Discovery uses latest publications and readable, unrevised stored references.

All data here is explicitly fictitious and rolled back by the integration fixture.
"""

from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.core.config import get_settings
from app.modules.contexts.resolver import KNOWN_SERIES
from app.modules.indicators.models import Indicator, IndicatorValue

from .test_contexts import (
    ENDPOINT,
    accepted,
    account,
    extra_observation,
    fixture,
    observation,
    publish,
    review,
    source,
)
from .test_policies import headers

pytestmark = pytest.mark.database


def choices(client, owner, code="selic-meta", **params):
    return client.get(f"{ENDPOINT}/references/{code}", headers=headers(owner), params=params)


def test_references_require_active_session_and_cannot_match_uuid_route(auth_client, db_session):
    assert auth_client.get(f"{ENDPOINT}/references/selic-meta").status_code == 401
    owner, row = account(auth_client, db_session)
    observation(db_session, row, "selic-meta")
    assert choices(auth_client, owner).status_code == 200
    row.is_active = False
    db_session.commit()
    assert choices(auth_client, owner).status_code == 401


@pytest.mark.parametrize("code", ["unknown", "rtn-juros-nominais", "federal-spending"])
def test_unknown_auxiliary_reference_codes_not_exposed(auth_client, db_session, code):
    owner, _ = account(auth_client, db_session)
    assert choices(auth_client, owner, code).status_code == 404


def test_inactive_known_reference_not_exposed(auth_client, db_session):
    owner, row = account(auth_client, db_session)
    observed, _ = observation(db_session, row, "selic-meta")
    db_session.get(Indicator, observed.indicator_id).is_active = False
    db_session.commit()
    assert choices(auth_client, owner).status_code == 404


def test_choices_latest_revision_per_period_history_exact_source_and_pagination(
    auth_client,
    db_session,
):
    owner, row = account(auth_client, db_session)
    old, reference = observation(db_session, row, "selic-meta", value="13.000001")
    newer = IndicatorValue(
        indicator_id=old.indicator_id,
        source_id=old.source_id,
        reference_date=old.reference_date,
        value=Decimal("14.123456"),
        revision=2,
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
        provenance=deepcopy(old.provenance),
    )
    db_session.add(newer)
    db_session.commit()
    august = extra_observation(
        db_session,
        old,
        license_name="Termos agosto fictício",
        license_url="https://example.org/terms-august",
    )
    response = choices(auth_client, owner, page_size=1)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["pagination"] == {"page": 1, "page_size": 1, "total": 2}
    assert result["data"]["observations"][0]["observation_id"] == str(august.id)
    assert result["data"]["observations"][0]["source"]["terms"] == "Termos agosto fictício"
    second = choices(auth_client, owner, page=2, page_size=1).json()["data"]["observations"]
    assert len(second) == 1 and second[0]["observation_id"] == str(newer.id)
    assert second[0]["value"] == "14.123456" and second[0]["revision"] == 2
    assert second[0]["source"]["id"] == str(reference.id)
    assert second[0]["source"]["terms"] == "ODbL 1.0"
    assert "description" not in second[0]["source"] and "created_by" not in second[0]["source"]
    assert choices(auth_client, owner, page=3, page_size=1).json()["data"]["observations"] == []


@pytest.mark.parametrize("page,page_size", [(0, 20), (1, 101), (1, 0)])
def test_reference_pagination_bounds(auth_client, db_session, page, page_size):
    owner, _ = account(auth_client, db_session)
    assert choices(auth_client, owner, page=page, page_size=page_size).status_code == 422


def test_reference_historical_definition_never_live_fallback(auth_client, db_session):
    owner, row = account(auth_client, db_session)
    old, _ = observation(db_session, row, "selic-meta")
    indicator = db_session.get(Indicator, old.indicator_id)
    indicator.unit = "Nova unidade fictícia"
    indicator.scope = "Novo recorte fictício"
    indicator.frequency = "YEARLY"
    indicator.methodology = "Nova metodologia fictícia"
    db_session.commit()
    item = choices(auth_client, owner).json()["data"]["observations"][0]
    for key, value in old.provenance["definition"].items():
        assert item[key] == value
    corrupt = IndicatorValue(
        indicator_id=old.indicator_id,
        source_id=old.source_id,
        reference_date=old.reference_date,
        value=old.value,
        revision=2,
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
        provenance={"license": "ODbL 1.0", "license_url": "https://example.org/terms"},
    )
    db_session.add(corrupt)
    db_session.commit()
    failed = choices(auth_client, owner)
    assert failed.status_code == 422
    assert failed.json()["error"]["code"] == "CONTEXT_OBSERVATION_DEFINITION"


@pytest.mark.parametrize(
    "code,reference,start,end",
    [
        ("desocupacao", date(2025, 7, 1), "2025-05-01", "2025-07-31"),
        ("ipca-12-meses", date(2025, 7, 1), "2024-08-01", "2025-07-31"),
        ("pib-nominal-trimestral", date(2025, 7, 1), "2025-07-01", "2025-09-30"),
    ],
)
def test_reference_choices_preserve_measurement_windows(
    auth_client,
    db_session,
    code,
    reference,
    start,
    end,
):
    owner, row = account(auth_client, db_session)
    meta = KNOWN_SERIES[code]
    indicator = Indicator(
        code=code,
        is_active=True,
        **{
            key: meta[key]
            for key in (
                "name",
                "description",
                "category",
                "unit",
                "frequency",
                "scope",
                "methodology",
            )
        },
    )
    db_session.add(indicator)
    db_session.flush()
    ref = source(db_session, row)
    ref.source_type = "OFFICIAL"
    observed = IndicatorValue(
        indicator_id=indicator.id,
        source_id=ref.id,
        reference_date=reference,
        value=Decimal("5.5"),
        revision=1,
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
        provenance={
            "license": "Termos fictícios",
            "license_url": "https://example.org/terms",
            "definition": {key: meta[key] for key in ("unit", "scope", "frequency", "methodology")},
        },
    )
    db_session.add(observed)
    db_session.commit()
    response = choices(auth_client, owner, code)
    assert response.status_code == 200, response.text
    item = response.json()["data"]["observations"][0]
    assert item["period_start"] == start and item["period_end"] == end


def test_reference_examples_hidden_in_production_without_fallback(
    auth_client, db_session, monkeypatch
):
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    owner, row = account(auth_client, db_session)
    observed, ref = observation(db_session, row, "selic-meta", example=True)
    assert choices(auth_client, owner).json()["pagination"]["total"] == 1
    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    result = choices(auth_client, owner)
    assert result.status_code == 200 and result.json()["data"]["observations"] == []
    assert result.json()["pagination"]["total"] == 0


def test_primary_filter_latest_publication_not_draft_or_counterpart(auth_client, db_session):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    first_title = "Publicado antigo " + uuid4().hex
    data["title"] = first_title
    draft, _ = accepted(auth_client, owner, reviewer, data)

    def query(code):
        return auth_client.get(ENDPOINT, params={"indicator_code": code}).json()

    assert query("selic-meta")["pagination"]["total"] == 1
    assert query("divida-bruta-pib")["data"] == []  # counterpart is not primary
    changed = deepcopy(data)
    changed["title"] = "Rascunho secreto " + uuid4().hex
    changed["primary_observation_id"] = data["observation_ids"][1]
    changed["counterparts"][0].update(
        indicator_code="selic-meta", observation_ids=[data["observation_ids"][0]]
    )
    response = auth_client.patch(
        f"{ENDPOINT}/{draft['id']}",
        headers=headers(owner),
        json={"content": changed, "expected_revision": 1},
    )
    assert response.status_code == 200, response.text
    second = response.json()["data"]
    assert query("selic-meta")["data"][0]["revision"] == 1
    assert query("divida-bruta-pib")["data"] == []
    assert auth_client.get(ENDPOINT, params={"q": changed["title"]}).json()["data"] == []
    assert review(auth_client, reviewer, second).status_code == 200
    assert publish(auth_client, owner, second).status_code == 200
    assert query("selic-meta")["data"] == []
    assert query("divida-bruta-pib")["data"][0]["revision"] == 2
    assert auth_client.get(ENDPOINT, params={"q": first_title}).json()["data"] == []
    assert auth_client.get(f"{ENDPOINT}/{draft['id']}/versions/1").status_code == 200


def test_primary_filter_count_and_pagination_agree(auth_client, db_session):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    first, _ = accepted(auth_client, owner, reviewer, data)
    second, _ = accepted(auth_client, owner, reviewer, data)
    result = auth_client.get(
        ENDPOINT, params={"indicator_code": "selic-meta", "page_size": 1}
    ).json()
    assert result["pagination"] == {"page": 1, "page_size": 1, "total": 2}
    assert len(result["data"]) == 1
    last = auth_client.get(
        ENDPOINT, params={"indicator_code": "selic-meta", "page_size": 1, "page": 2}
    ).json()
    assert last["data"][0]["id"] != result["data"][0]["id"]
    assert {result["data"][0]["id"], last["data"][0]["id"]} == {first["id"], second["id"]}


def test_reference_visible_real_link_not_matching_foreign_private_url(auth_client, db_session):
    owner, row = account(auth_client, db_session)
    _, other = account(auth_client, db_session, role="ADMIN")
    observed, visible = observation(db_session, row, "selic-meta")
    private = source(db_session, other, url=visible.url)
    private.title = "Segredo privado coincidente"
    db_session.commit()
    response = choices(auth_client, owner)
    assert response.status_code == 200, response.text
    items = response.json()["data"]["observations"]
    assert len(items) == 1 and items[0]["source"]["id"] == str(visible.id)
    assert "Segredo privado" not in response.text and str(private.id) not in response.text


@pytest.mark.parametrize("excluded", ["example", "not-official"])
def test_latest_unselectable_revision_never_falls_back_to_old_public_value(
    auth_client, db_session, monkeypatch, excluded
):
    owner, row = account(auth_client, db_session)
    old, _ = observation(db_session, row, "selic-meta")
    replacement = source(db_session, row, example=excluded == "example")
    replacement.source_type = "OFFICIAL" if excluded == "example" else "TECHNICAL_REPORT"
    db_session.add(
        IndicatorValue(
            indicator_id=old.indicator_id,
            source_id=replacement.id,
            reference_date=old.reference_date,
            revision=2,
            value=Decimal("15"),
            retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
            provenance=deepcopy(old.provenance),
        )
    )
    db_session.commit()
    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    response = choices(auth_client, owner)
    assert response.status_code == 200
    assert response.json()["data"]["observations"] == []
    assert response.json()["pagination"]["total"] == 0


@pytest.mark.parametrize("malformed", [{"private": "bad terms"}, [], None])
def test_malformed_current_terms_fail_safely_instead_of_using_old_terms(
    auth_client, db_session, malformed
):
    owner, row = account(auth_client, db_session)
    old, _ = observation(db_session, row, "selic-meta")
    provenance = deepcopy(old.provenance)
    provenance["license"] = malformed
    db_session.add(
        IndicatorValue(
            indicator_id=old.indicator_id,
            source_id=old.source_id,
            reference_date=old.reference_date,
            revision=2,
            value=old.value,
            retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
            provenance=provenance,
        )
    )
    db_session.commit()
    response = choices(auth_client, owner)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CONTEXT_REFERENCE_INVALID"
    assert "bad terms" not in response.text


def test_empty_active_reviewed_catalog_is_explicitly_empty(auth_client, db_session):
    owner, _ = account(auth_client, db_session)
    meta = KNOWN_SERIES["selic-meta"]
    db_session.add(
        Indicator(
            code="selic-meta",
            is_active=True,
            **{
                key: meta[key]
                for key in (
                    "name",
                    "description",
                    "category",
                    "unit",
                    "scope",
                    "frequency",
                    "methodology",
                )
            },
        )
    )
    db_session.commit()
    response = choices(auth_client, owner)
    assert response.status_code == 200
    assert response.json()["data"]["observations"] == []
    assert response.json()["data"]["frequency"] == "DAILY"
    assert response.json()["pagination"]["total"] == 0


def test_equal_revision_different_source_yields_one_current_period(auth_client, db_session):
    owner, row = account(auth_client, db_session)
    old, _ = observation(db_session, row, "selic-meta")
    latest_source = source(db_session, row)
    latest_source.source_type = "OFFICIAL"
    latest = IndicatorValue(
        indicator_id=old.indicator_id,
        source_id=latest_source.id,
        reference_date=old.reference_date,
        revision=old.revision,
        value=Decimal("14.5"),
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
        provenance=deepcopy(old.provenance),
    )
    db_session.add(latest)
    db_session.commit()
    response = choices(auth_client, owner)
    assert response.status_code == 200, response.text
    assert response.json()["pagination"]["total"] == 1
    items = response.json()["data"]["observations"]
    assert len(items) == 1 and items[0]["observation_id"] == str(latest.id)


def test_list_freezes_selected_publication_when_new_version_publishes_during_render(
    auth_client, db_session, monkeypatch
):
    from app.modules.contexts import service
    from app.modules.contexts.schemas import ContextPublishInput, ContextReviewInput, ContextUpdate

    owner, owner_row, reviewer, reviewer_row, data = fixture(auth_client, db_session)
    data["title"] = "Publicação selecionada " + uuid4().hex
    first, _ = accepted(auth_client, owner, reviewer, data)
    changed = deepcopy(data)
    changed["title"] = "Outra publicação " + uuid4().hex
    changed["primary_observation_id"] = data["observation_ids"][1]
    changed["counterparts"][0].update(
        indicator_code="selic-meta", observation_ids=[data["observation_ids"][0]]
    )
    original_view, original_public = service.context_view, service.public_context
    advanced = False

    def advance_publication():
        nonlocal advanced
        if advanced:
            return
        advanced = True
        context_id = UUID(first["id"])
        service.update_context(
            db_session,
            context_id,
            ContextUpdate.model_validate({"content": changed, "expected_revision": 1}),
            owner_row,
        )
        service.review_context(
            db_session,
            context_id,
            ContextReviewInput.model_validate(
                {
                    "expected_revision": 2,
                    "decision": "ACCEPT",
                    "rationale": "Revisão fictícia",
                    "references_checked": True,
                    "scopes_checked": True,
                    "alternatives_checked": True,
                    "limitations_checked": True,
                }
            ),
            reviewer_row,
        )
        service.publish_context(
            db_session,
            context_id,
            ContextPublishInput(expected_revision=2),
            owner_row,
        )

    def racing_view(*args, **kwargs):
        advance_publication()
        return original_view(*args, **kwargs)

    def racing_public(*args, **kwargs):
        advance_publication()
        return original_public(*args, **kwargs)

    # The hook models a new publication after list selection but before rendering.
    # It also covers the former latest-lookup path, which returned version 2 wrongly.
    monkeypatch.setattr(service, "context_view", racing_view)
    monkeypatch.setattr(service, "public_context", racing_public)
    result = service.list_contexts(db_session, 1, 20, data["title"], indicator_code="selic-meta")
    assert advanced
    assert len(result["data"]) == 1
    assert result["data"][0]["revision"] == 1
    assert result["data"][0]["content"]["title"] == data["title"]
    assert original_public(db_session, UUID(first["id"]))["revision"] == 2
    assert service.list_contexts(db_session, 1, 20, indicator_code="selic-meta")["data"] == []
