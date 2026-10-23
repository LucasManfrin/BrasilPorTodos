from uuid import UUID

import pytest

from app.modules.sources.models import Source

from .test_auth import signup
from .test_sources import source_data

pytestmark = pytest.mark.database


def headers(result):
    return {"Authorization": f"Bearer {result['access_token']}"}


def policy_input(source_id):
    return {
        "title": "Proposta fictícia",
        "summary": "Resumo de teste",
        "problem": "Problema de teste",
        "proposal": "Solução de teste",
        "category": "EDUCATION",
        "implementation_start": 2027,
        "implementation_end": 2030,
        "financial_impact_status": "ESTIMATED",
        "impacts": [
            {
                "year": 2027,
                "impact_type": "NEW_EXPENSE",
                "amount": "100.10",
                "description": "Hipótese fictícia",
            }
        ],
        "fundings": [
            {"funding_type": "UNFUNDED", "description": "Financiamento ainda não definido"}
        ],
        "sources": [{"source_id": source_id, "usage_description": "Justificativa de teste"}],
    }


def draft(client, result):
    source = client.post("/api/v1/sources", json=source_data(), headers=headers(result)).json()[
        "data"
    ]
    response = client.post(
        "/api/v1/policies", json=policy_input(source["id"]), headers=headers(result)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"], source


def test_publication_and_new_draft_keep_public_version_and_source_snapshot(auth_client, db_session):
    user, _ = signup(auth_client)
    proposal, source = draft(auth_client, user)
    assert auth_client.get("/api/v1/policies").json()["data"] == []
    assert auth_client.get(f"/api/v1/policies/{proposal['slug']}").status_code == 404
    published = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
    )
    assert published.status_code == 200, published.text
    v1 = published.json()["data"]["version"]
    assert v1["status"] == "PUBLISHED"
    assert v1["impacts"][0]["amount"] == "100.10"
    assert auth_client.get(f"/api/v1/sources/{source['id']}").status_code == 200
    source_row = db_session.get(Source, UUID(source["id"]))
    source_row.title = "Cadastro corrigido após publicação"
    db_session.commit()
    edited = auth_client.patch(
        f"/api/v1/policies/{proposal['id']}", json={"title": "Título da v2"}, headers=headers(user)
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["data"]["version"]["version_number"] == 2
    assert edited.json()["data"]["version"]["status"] == "DRAFT"
    public = auth_client.get(f"/api/v1/policies/{proposal['slug']}").json()["data"]
    assert public["version"]["id"] == v1["id"]
    assert public["version"]["title"] == "Proposta fictícia"
    assert public["version"]["sources"][0]["source"]["title"] == source["title"]
    assert auth_client.get(f"/api/v1/policies/{proposal['slug']}/versions/2").status_code == 404
    published_v2 = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
    )
    assert published_v2.status_code == 200
    history = auth_client.get(f"/api/v1/policies/{proposal['slug']}/versions").json()["data"]
    assert [row["version_number"] for row in history] == [1, 2]
    assert (
        auth_client.get(f"/api/v1/policies/{proposal['slug']}/versions/1").json()["data"][
            "version"
        ]["title"]
        == "Proposta fictícia"
    )


def test_edit_and_publish_require_owner_and_authenticated_user(auth_client):
    owner, _ = signup(auth_client)
    proposal, _ = draft(auth_client, owner)
    assert (
        auth_client.patch(f"/api/v1/policies/{proposal['id']}", json={"title": "x"}).status_code
        == 401
    )
    assert auth_client.post(f"/api/v1/policies/{proposal['id']}/publish").status_code == 401
    other, _ = signup(auth_client)
    assert (
        auth_client.patch(
            f"/api/v1/policies/{proposal['id']}", json={"title": "x"}, headers=headers(other)
        ).status_code
        == 403
    )
    assert (
        auth_client.get(
            f"/api/v1/policies/{proposal['id']}/draft", headers=headers(other)
        ).status_code
        == 403
    )
    assert (
        auth_client.post(
            f"/api/v1/policies/{proposal['id']}/publish", headers=headers(other)
        ).status_code
        == 403
    )
    assert auth_client.get("/api/v1/policies/mine", headers=headers(other)).json()["data"] == []


def test_publication_checks_completeness_funding_and_sources(auth_client):
    user, _ = signup(auth_client)
    incomplete = auth_client.post("/api/v1/policies", json={}, headers=headers(user)).json()["data"]
    assert (
        auth_client.post(
            f"/api/v1/policies/{incomplete['id']}/publish", headers=headers(user)
        ).status_code
        == 422
    )
    proposal, _ = draft(auth_client, user)
    auth_client.patch(
        f"/api/v1/policies/{proposal['id']}", json={"fundings": []}, headers=headers(user)
    )
    response = auth_client.post(f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user))
    assert response.json()["error"]["code"] == "FUNDING_REQUIRED"
    auth_client.patch(
        f"/api/v1/policies/{proposal['id']}",
        json={
            "fundings": [{"funding_type": "UNFUNDED", "description": "Ainda não financiado"}],
            "sources": [],
        },
        headers=headers(user),
    )
    response = auth_client.post(f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user))
    assert response.json()["error"]["code"] == "SOURCE_REQUIRED"


def test_unestimated_does_not_mean_zero_and_not_applicable_needs_reason(auth_client):
    user, _ = signup(auth_client)
    proposal, _ = draft(auth_client, user)
    update = auth_client.patch(
        f"/api/v1/policies/{proposal['id']}",
        json={"financial_impact_status": "NOT_ESTIMATED", "impacts": []},
        headers=headers(user),
    )
    assert update.status_code == 200
    assert (
        auth_client.post(
            f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
        ).status_code
        == 200
    )
    public = auth_client.get(f"/api/v1/policies/{proposal['slug']}").json()["data"]["version"]
    assert public["financial_impact_status"] == "NOT_ESTIMATED" and public["impacts"] == []
    auth_client.patch(
        f"/api/v1/policies/{proposal['id']}",
        json={"financial_impact_status": "NOT_APPLICABLE"},
        headers=headers(user),
    )
    assert (
        auth_client.post(
            f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
        ).status_code
        == 422
    )


@pytest.mark.parametrize("amount", [10.1, "-1", "NaN", "0.001"])
def test_money_requires_finite_nonnegative_decimal_strings(auth_client, amount):
    user, _ = signup(auth_client)
    source = auth_client.post("/api/v1/sources", json=source_data(), headers=headers(user)).json()[
        "data"
    ]
    data = policy_input(source["id"])
    data["impacts"][0]["amount"] = amount
    assert auth_client.post("/api/v1/policies", json=data, headers=headers(user)).status_code == 422


def test_archive_preserves_history_and_excludes_catalog(auth_client):
    user, _ = signup(auth_client)
    proposal, _ = draft(auth_client, user)
    auth_client.post(f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user))
    archived = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/archive",
        json={"reason": "Exemplo encerrado"},
        headers=headers(user),
    )
    assert archived.status_code == 200
    assert auth_client.get("/api/v1/policies").json()["data"] == []
    public = auth_client.get(f"/api/v1/policies/{proposal['slug']}")
    assert public.status_code == 200 and public.json()["data"]["status"] == "ARCHIVED"
    assert (
        auth_client.patch(
            f"/api/v1/policies/{proposal['id']}", json={"title": "x"}, headers=headers(user)
        ).status_code
        == 409
    )


def test_deleting_a_draft_preserves_its_published_history(auth_client):
    user, _ = signup(auth_client)
    proposal, _ = draft(auth_client, user)
    auth_client.post(f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user))
    auth_client.patch(
        f"/api/v1/policies/{proposal['id']}", json={"title": "Private edit"}, headers=headers(user)
    )
    assert (
        auth_client.delete(
            f"/api/v1/policies/{proposal['id']}/draft", headers=headers(user)
        ).status_code
        == 200
    )
    public = auth_client.get(f"/api/v1/policies/{proposal['slug']}")
    assert public.status_code == 200
    assert public.json()["data"]["version"]["version_number"] == 1
    assert (
        auth_client.delete(
            f"/api/v1/policies/{proposal['id']}/draft", headers=headers(user)
        ).status_code
        == 409
    )
