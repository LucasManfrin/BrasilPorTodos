from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.ideas.models import Idea
from app.modules.policies.models import PolicyVersion
from app.modules.sources.models import Source
from app.modules.users.models import User

from .test_auth import signup
from .test_policies import headers, policy_input
from .test_sources import source_data

pytestmark = pytest.mark.database


def new_idea(client, user, **values):
    response = client.post(
        "/api/v1/ideas",
        headers=headers(user),
        json={"title": "Ideia de teste", "summary": "Uma frase.", **values},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_private_share_withdraw_and_owner_authorization(auth_client):
    owner, _ = signup(auth_client)
    other, _ = signup(auth_client)
    idea = new_idea(auth_client, owner)
    path = f"/api/v1/ideas/{idea['id']}"
    assert idea["status"] == "PRIVATE"
    assert auth_client.get("/api/v1/ideas").json()["data"] == []
    assert auth_client.get(path + "/shared").status_code == 404
    assert auth_client.get(path).status_code == 401
    assert auth_client.get(path, headers=headers(other)).status_code == 404
    assert (
        auth_client.patch(path, json={"title": "Invasão"}, headers=headers(other)).status_code
        == 404
    )
    shared = auth_client.post(path + "/share", headers=headers(owner))
    assert shared.status_code == 200, shared.text
    assert shared.json()["data"]["status"] == "SHARED"
    public = auth_client.get(path + "/shared").json()["data"]
    assert "email" not in str(public) and "author_id" not in public
    assert auth_client.get("/api/v1/ideas").json()["data"][0] == public
    edited = auth_client.patch(path, json={"summary": "Nova frase"}, headers=headers(owner))
    assert edited.status_code == 200, edited.text
    assert edited.json()["data"]["status"] == "PRIVATE"
    assert auth_client.get(path + "/shared").status_code == 404
    assert public["summary"] == "Uma frase."
    auth_client.post(path + "/share", headers=headers(owner))
    assert auth_client.get(path + "/shared").json()["data"]["summary"] == "Nova frase"
    assert auth_client.post(path + "/unshare", headers=headers(owner)).status_code == 200
    assert auth_client.get(path + "/shared").status_code == 404


def test_checklist_blocks_calculation_and_incomplete_promotion(auth_client):
    owner, _ = signup(auth_client)
    idea = new_idea(auth_client, owner)
    path = f"/api/v1/ideas/{idea['id']}"
    assert sum(item["complete"] for item in idea["checklist"]) == 1
    result = auth_client.post(path + "/promote", headers=headers(owner))
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "INCOMPLETE_IDEA"
    assert auth_client.get("/api/v1/policies/mine", headers=headers(owner)).json()["data"] == []
    assert auth_client.get("/api/v1/policies").json()["data"] == []
    # An idea UUID is not accepted as a policy/version by plans or simulation.
    assert auth_client.get(f"/api/v1/policies/{idea['id']}").status_code == 404


def test_share_snapshots_sources_and_duplicate_preserves_attribution(auth_client, db_session):
    owner, _ = signup(auth_client)
    other, _ = signup(auth_client)
    source = auth_client.post("/api/v1/sources", json=source_data(), headers=headers(owner)).json()[
        "data"
    ]
    idea = new_idea(
        auth_client,
        owner,
        content={
            "sources": [
                {"source_id": source["id"], "usage_description": "Referência fornecida pelo autor"}
            ]
        },
    )
    path = f"/api/v1/ideas/{idea['id']}"
    snap = auth_client.post(path + "/share", headers=headers(owner)).json()["data"]
    row = db_session.get(Source, UUID(source["id"]))
    row.title = "Cadastro alterado"
    db_session.commit()
    assert auth_client.get(path + "/shared").json()["data"] == snap
    assert snap["source_snapshots"][0]["title"] == source["title"]
    copied = auth_client.post(path + "/duplicate", headers=headers(other))
    assert copied.status_code == 201, copied.text
    clone = copied.json()["data"]
    assert clone["status"] == "PRIVATE"
    assert clone["content"]["sources"] == []
    assert clone["origin_attribution"]["author"] == idea["author"]
    assert clone["origin_attribution"]["source_snapshots"][0]["title"] == source["title"]
    assert clone["id"] != idea["id"]


def test_private_source_cannot_be_attached_by_other_author(auth_client):
    owner, _ = signup(auth_client)
    other, _ = signup(auth_client)
    source = auth_client.post("/api/v1/sources", json=source_data(), headers=headers(owner)).json()[
        "data"
    ]
    response = auth_client.post(
        "/api/v1/ideas",
        headers=headers(other),
        json={
            "title": "Teste",
            "summary": "Teste",
            "content": {"sources": [{"source_id": source["id"], "usage_description": "Privada"}]},
        },
    )
    assert response.status_code == 404


def complete_idea(client, owner, *, estimated=True):
    source = client.post("/api/v1/sources", json=source_data(), headers=headers(owner)).json()[
        "data"
    ]
    content = policy_input(source["id"])
    content["fundings"] = [
        {
            "funding_type": "SPENDING_CUT",
            "year": 2027,
            "amount": "100.10",
            "description": "Hipótese de corte explícita",
        }
    ]
    if not estimated:
        content.update(
            financial_impact_status="NOT_APPLICABLE",
            impacts=[],
            impact_justification="Medida organizacional sem efeito fiscal direto.",
        )
    return new_idea(
        client,
        owner,
        content=content,
        beneficiaries="Pessoas beneficiadas",
        adversely_affected="Grupos sujeitos à redução",
        risks="Execução pode falhar",
        assisted_fields=["problem"],
    )


@pytest.mark.parametrize("estimated", [True, False])
def test_promotion_is_atomic_idempotent_and_freezes_details(auth_client, db_session, estimated):
    owner, _ = signup(auth_client)
    idea = complete_idea(auth_client, owner, estimated=estimated)
    assert all(item["complete"] for item in idea["checklist"])
    path = f"/api/v1/ideas/{idea['id']}"
    promoted = auth_client.post(path + "/promote", headers=headers(owner))
    assert promoted.status_code == 200, promoted.text
    policy = promoted.json()["data"]
    details = policy["version"]["proposal_details"]
    assert policy["status"] == "PUBLISHED"
    assert details["beneficiaries"] == idea["beneficiaries"]
    assert details["assisted_fields"] == ["problem"]
    assert details["idea_id"] == idea["id"]
    second = auth_client.post(path + "/promote", headers=headers(owner))
    assert second.status_code == 200, second.text
    assert second.json()["data"]["id"] == policy["id"]
    assert len(auth_client.get("/api/v1/policies/mine", headers=headers(owner)).json()["data"]) == 1
    assert (
        auth_client.patch(path, json={"title": "Outra"}, headers=headers(owner)).status_code == 409
    )
    updated = auth_client.patch(
        f"/api/v1/policies/{policy['id']}", json={"title": "Revisão"}, headers=headers(owner)
    ).json()["data"]
    assert updated["version"]["proposal_details"] == details
    assert (
        auth_client.get(f"/api/v1/policies/{policy['slug']}").json()["data"]["version"][
            "proposal_details"
        ]
        == details
    )
    version = db_session.get(PolicyVersion, UUID(policy["version"]["id"]))
    with pytest.raises(IntegrityError), db_session.begin_nested():
        version.proposal_details = {"risks": "Mudança indevida"}
        db_session.flush()


def test_failed_promotion_rolls_back_new_policy(auth_client, db_session, monkeypatch):
    owner, _ = signup(auth_client)
    idea = complete_idea(auth_client, owner)
    source_id = idea["content"]["sources"][0]["source_id"]
    # Publication validation rejects contradictory fiscal status without committing a draft.
    data = idea["content"]
    data["implementation_end"] = 2027
    data["impacts"][0]["year"] = 2028
    # Force the service's final publication to fail after draft creation.
    from app.core.errors import DomainError
    from app.modules.ideas import service

    def fail(*args, **kwargs):
        raise DomainError(422, "TEST_PUBLICATION_FAILURE", "Falha controlada")

    monkeypatch.setattr(service.policies, "publish_policy", fail)
    response = auth_client.post(f"/api/v1/ideas/{idea['id']}/promote", headers=headers(owner))
    assert response.status_code == 422
    # Nested transaction already rolled back the draft, even with the outer session alive.
    assert db_session.scalar(select(Idea.status).where(Idea.id == UUID(idea["id"]))) == "PRIVATE"
    assert auth_client.get("/api/v1/policies/mine", headers=headers(owner)).json()["data"] == []
    assert source_id


def test_limits_invalid_fields_and_null_patch(auth_client, monkeypatch):
    owner, _ = signup(auth_client)
    monkeypatch.setenv("IDEAS_DAILY_LIMIT", "1")
    idea = new_idea(auth_client, owner)
    response = auth_client.post(
        "/api/v1/ideas", headers=headers(owner), json={"title": "Outra", "summary": "Frase"}
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    path = f"/api/v1/ideas/{idea['id']}"
    assert (
        auth_client.patch(path, json={"summary": None}, headers=headers(owner)).status_code == 422
    )
    assert (
        auth_client.patch(
            path, json={"assisted_fields": ["email"]}, headers=headers(owner)
        ).status_code
        == 422
    )


def test_suggestions_never_edit_original_and_require_owner_approval(auth_client):
    owner, _ = signup(auth_client)
    helper, _ = signup(auth_client)
    idea = new_idea(auth_client, owner)
    path = f"/api/v1/ideas/{idea['id']}"
    suggestion = {"url": "https://ibge.gov.br/", "note": "Uma fonte para conferir"}
    assert (
        auth_client.post(
            path + "/suggestions", json=suggestion, headers=headers(helper)
        ).status_code
        == 404
    )
    auth_client.post(path + "/share", headers=headers(owner))
    created = auth_client.post(path + "/suggestions", json=suggestion, headers=headers(helper))
    assert created.status_code == 201, created.text
    item = created.json()["data"]
    assert auth_client.get(path + "/suggestions", headers=headers(helper)).status_code == 404
    assert (
        auth_client.get(path + "/suggestions", headers=headers(owner)).json()["data"][0]["status"]
        == "PENDING"
    )
    resolved = auth_client.post(
        path + f"/suggestions/{item['id']}/resolve",
        json={"action": "ACCEPT"},
        headers=headers(owner),
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["data"]["status"] == "ACCEPTED"
    assert auth_client.get(path, headers=headers(owner)).json()["data"]["content"]["sources"] == []
    assert (
        auth_client.post(
            path + "/suggestions",
            headers=headers(helper),
            json={"url": "https://user:secret@example.com", "note": "Credenciais"},
        ).status_code
        == 422
    )


def test_reports_admin_resolution_and_reporter_privacy(auth_client, db_session):
    owner, _ = signup(auth_client)
    reporter, _ = signup(auth_client)
    admin, _ = signup(auth_client)
    admin_row = db_session.scalar(select(User).where(User.username == admin["user"]["username"]))
    admin_row.role = "ADMIN"
    db_session.commit()
    idea = new_idea(auth_client, owner)
    path = f"/api/v1/ideas/{idea['id']}"
    auth_client.post(path + "/share", headers=headers(owner))
    payload = {"reason": "Conteúdo de teste a moderar"}
    report = auth_client.post(path + "/report", json=payload, headers=headers(reporter))
    assert report.status_code == 201, report.text
    assert (
        auth_client.post(path + "/report", json=payload, headers=headers(reporter)).status_code
        == 409
    )
    assert auth_client.get("/api/v1/ideas/moderation", headers=headers(owner)).status_code == 403
    reports = auth_client.get("/api/v1/ideas/moderation", headers=headers(admin)).json()["data"]
    assert len(reports) == 1
    assert "reporter_id" not in reports[0]
    result = auth_client.post(
        f"/api/v1/ideas/moderation/{reports[0]['id']}/resolve",
        headers=headers(admin),
        json={"action": "ARCHIVE", "note": "Arquivamento de teste"},
    )
    assert result.status_code == 200, result.text
    assert auth_client.get(path + "/shared").status_code == 404
    assert auth_client.get(path, headers=headers(owner)).json()["data"]["status"] == "ARCHIVED"


def test_promotion_retry_keeps_original_version_after_new_publication(auth_client):
    owner, _ = signup(auth_client)
    idea = complete_idea(auth_client, owner)
    path = f"/api/v1/ideas/{idea['id']}/promote"
    original = auth_client.post(path, headers=headers(owner)).json()["data"]
    policy_path = f"/api/v1/policies/{original['id']}"
    assert (
        auth_client.patch(
            policy_path, json={"title": "Nova versão completa"}, headers=headers(owner)
        ).status_code
        == 200
    )
    assert auth_client.post(policy_path + "/publish", headers=headers(owner)).status_code == 200
    retry = auth_client.post(path, headers=headers(owner))
    assert retry.status_code == 200, retry.text
    assert retry.json()["data"]["version"]["id"] == original["version"]["id"]


def test_daily_limit_serializes_concurrent_accounts(monkeypatch):
    import os
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from uuid import uuid4

    from sqlalchemy import create_engine, delete
    from sqlalchemy.orm import Session

    from app.core.config import get_settings
    from app.core.errors import DomainError
    from app.modules.ideas import service
    from app.modules.ideas.schemas import IdeaInput

    assert os.getenv("RUN_DATABASE_TESTS") == "1"
    engine = create_engine(get_settings().database_url, connect_args={"options": "-c timezone=UTC"})
    monkeypatch.setenv("IDEAS_DAILY_LIMIT", "1")
    key = uuid4().hex
    with Session(engine) as session:
        user = User(
            name="Concorrência fictícia",
            username=key,
            email=f"{key}@example.com",
            password_hash="test-only",
            role="USER",
            is_active=True,
        )
        session.add(user)
        session.commit()
        user_id = user.id
    barrier = Barrier(2)

    def attempt():
        with Session(engine) as session:
            user = session.get(User, user_id)
            barrier.wait(timeout=10)
            try:
                service.create(
                    session, IdeaInput(title="Teste simultâneo", summary="Uma frase"), user
                )
                return 201
            except DomainError as exc:
                session.rollback()
                return exc.status

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        assert sorted(results) == [201, 429]
    finally:
        with Session(engine) as session:
            session.execute(delete(Idea).where(Idea.author_id == user_id))
            session.execute(delete(User).where(User.id == user_id))
            session.commit()
        engine.dispose()


def test_complete_proposal_cannot_drop_or_clear_details_on_next_version(auth_client):
    owner, _ = signup(auth_client)
    idea = complete_idea(auth_client, owner)
    policy = auth_client.post(f"/api/v1/ideas/{idea['id']}/promote", headers=headers(owner)).json()[
        "data"
    ]
    path = f"/api/v1/policies/{policy['id']}"
    assert (
        auth_client.patch(path, json={"proposal_details": None}, headers=headers(owner)).status_code
        == 422
    )
    result = auth_client.patch(
        path, json={"proposal_details": {"risks": "Somente risco"}}, headers=headers(owner)
    )
    assert result.status_code == 200, result.text
    # Metadata cannot erase server origin or previous AI disclosure.
    details = result.json()["data"]["version"]["proposal_details"]
    assert details["level"] == "COMPLETE"
    assert details["idea_id"] == idea["id"]
    assert details["assisted_fields"] == ["problem"]
    publish = auth_client.post(path + "/publish", headers=headers(owner))
    assert publish.status_code == 422, publish.text
    assert (
        auth_client.get(f"/api/v1/policies/{policy['slug']}").json()["data"]["version"]["id"]
        == policy["version"]["id"]
    )


def test_documentary_order_global_pagination_and_legacy_kept(auth_client):
    from .test_policies import draft

    owner, _ = signup(auth_client)
    idea = complete_idea(auth_client, owner)
    complete = auth_client.post(
        f"/api/v1/ideas/{idea['id']}/promote", headers=headers(owner)
    ).json()["data"]
    # Legacy API has its historical rules; existing content is never reclassified.
    legacy, _ = draft(auth_client, owner)
    assert (
        auth_client.post(
            f"/api/v1/policies/{legacy['id']}/publish", headers=headers(owner)
        ).status_code
        == 200
    )
    first = auth_client.get("/api/v1/policies?page=1&page_size=1").json()
    second = auth_client.get("/api/v1/policies?page=2&page_size=1").json()
    assert first["pagination"]["total"] == 2
    assert first["data"][0]["id"] == complete["id"]
    solidity = first["data"][0]["solidity"]
    assert solidity == {
        "method": "DOC_COMPLETENESS1",
        "level": "COMPLETE",
        "score": 2,
        "max_score": 3,
        "has_sources": True,
        "funding_defined": True,
        "reviewed": False,
        "review_status": "NOT_ASSESSED",
    }
    assert second["data"][0]["id"] == legacy["id"]
    assert second["data"][0]["solidity"]["level"] == "LEGACY"
    assert second["data"][0]["solidity"]["score"] is None


def test_new_details_on_legacy_draft_opt_into_complete_checks(auth_client):
    from .test_policies import draft

    owner, _ = signup(auth_client)
    legacy, _ = draft(auth_client, owner)
    path = f"/api/v1/policies/{legacy['id']}"
    assert (
        auth_client.patch(
            path, json={"proposal_details": {"risks": "Só isso"}}, headers=headers(owner)
        ).status_code
        == 200
    )
    assert auth_client.post(path + "/publish", headers=headers(owner)).status_code == 422


def test_legacy_publication_keeps_its_level_when_new_draft_becomes_complete(auth_client):
    from .test_policies import draft

    owner, _ = signup(auth_client)
    for _ in range(2):
        policy, _ = draft(auth_client, owner)
        response = auth_client.post(
            f"/api/v1/policies/{policy['id']}/publish", headers=headers(owner)
        )
        assert response.status_code == 200, response.text
    before = auth_client.get("/api/v1/policies").json()["data"]
    assert len(before) == 2
    # Pick the second item so changing only the identity marker would incorrectly reorder it.
    target = before[1]
    assert target["solidity"]["level"] == "LEGACY"
    path = f"/api/v1/policies/{target['id']}"
    patch = {
        "proposal_details": {
            "beneficiaries": "Beneficiários descritos",
            "adversely_affected": "Possíveis perdas descritas",
            "risks": "Riscos descritos",
        },
        "fundings": [
            {
                "funding_type": "SPENDING_CUT",
                "year": 2027,
                "amount": "100.10",
                "description": "Financiamento hipotético declarado",
            }
        ],
    }
    edited = auth_client.patch(path, json=patch, headers=headers(owner))
    assert edited.status_code == 200, edited.text
    assert edited.json()["data"]["version"]["version_number"] == 2
    # The private draft opted into the strict checks; the previous public photograph did not.
    old = auth_client.get(f"/api/v1/policies/{target['slug']}/versions/1").json()["data"]
    assert old["version"]["proposal_details"] is None
    assert old["solidity"]["level"] == "LEGACY"
    assert old["solidity"]["score"] is None
    during = auth_client.get("/api/v1/policies").json()["data"]
    assert [row["id"] for row in during] == [row["id"] for row in before]
    published = auth_client.post(path + "/publish", headers=headers(owner))
    assert published.status_code == 200, published.text
    assert published.json()["data"]["solidity"]["level"] == "COMPLETE"
    assert published.json()["data"]["solidity"]["score"] == 2
    after = auth_client.get("/api/v1/policies").json()["data"]
    assert after[0]["id"] == target["id"]
    assert after[0]["version"]["version_number"] == 2
    historical = auth_client.get(f"/api/v1/policies/{target['slug']}/versions/1").json()["data"]
    assert historical["version"]["id"] == target["version"]["id"]
    assert historical["solidity"]["level"] == "LEGACY"
    assert historical["solidity"]["score"] is None
