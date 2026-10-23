from datetime import date
from uuid import uuid4

import pytest

from app.modules.indicators.models import Indicator, IndicatorValue

from .test_auth import signup

pytestmark = pytest.mark.database


def source_data():
    return {
        "title": "Fonte fictícia de teste",
        "institution": "Instituição teste",
        "url": "https://example.org/reference",
        "source_type": "TECHNICAL_REPORT",
        "accessed_at": "2026-10-06",
    }


def test_source_creation_requires_login_and_is_private_until_cited(auth_client):
    assert auth_client.post("/api/v1/sources", json=source_data()).status_code == 401
    result, _ = signup(auth_client)
    headers = {"Authorization": f"Bearer {result['access_token']}"}
    created = auth_client.post("/api/v1/sources", json=source_data(), headers=headers)
    assert created.status_code == 201
    source_id = created.json()["data"]["id"]
    assert auth_client.get("/api/v1/sources").json()["data"] == []
    assert auth_client.get(f"/api/v1/sources/{source_id}").status_code == 404
    mine = auth_client.get("/api/v1/sources/mine", headers=headers)
    assert mine.json()["data"][0]["id"] == source_id
    other, _ = signup(auth_client)
    assert (
        auth_client.get(
            "/api/v1/sources/mine", headers={"Authorization": f"Bearer {other['access_token']}"}
        ).json()["data"]
        == []
    )


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///private",
        "https://user:password@example.org/",
        "data:text/html,anything",
    ],
)
def test_invalid_or_credential_bearing_urls_are_rejected(auth_client, url):
    result, _ = signup(auth_client)
    response = auth_client.post(
        "/api/v1/sources",
        json={**source_data(), "url": url},
        headers={"Authorization": f"Bearer {result['access_token']}"},
    )
    assert response.status_code == 422


def test_observed_source_is_public_and_list_is_paginated(auth_client, db_session):
    from datetime import UTC, datetime
    from uuid import UUID

    result, _ = signup(auth_client)
    created = auth_client.post(
        "/api/v1/sources",
        json=source_data(),
        headers={"Authorization": f"Bearer {result['access_token']}"},
    )
    source_id = UUID(created.json()["data"]["id"])
    indicator = Indicator(
        code=uuid4().hex,
        name="Fictitious",
        description="Test only",
        category="ECONOMY",
        unit="BRL",
        frequency="YEARLY",
        scope="Test",
        methodology="Test",
    )
    db_session.add(indicator)
    db_session.flush()
    db_session.add(
        IndicatorValue(
            indicator_id=indicator.id,
            reference_date=date(2025, 1, 1),
            value=1,
            source_id=source_id,
            retrieved_at=datetime.now(UTC),
            provenance={"fictitious": True},
        )
    )
    db_session.commit()
    public = auth_client.get("/api/v1/sources?page_size=1&q=fictícia")
    assert public.status_code == 200
    assert public.json()["pagination"]["total"] == 1
    assert len(public.json()["data"]) == 1
    assert auth_client.get(f"/api/v1/sources/{source_id}").status_code == 200
    assert auth_client.get("/api/v1/sources?page_size=101").status_code == 422
