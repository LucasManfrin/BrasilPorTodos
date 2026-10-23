"""Fictitious contexts and evidence in the exclusive PostgreSQL rollback transaction."""

from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.modules.contexts.models import Context, ContextPublication, ContextReview, ContextVersion
from app.modules.indicators.catalog import BCB_SERIES, LICENSE_URL
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.sources.models import Source
from app.modules.users.models import User

from .test_auth import signup
from .test_policies import headers

pytestmark = pytest.mark.database
ENDPOINT = "/api/v1/contexts"


def account(client, session, *, role="USER"):
    result, _ = signup(client)
    user = session.get(User, UUID(result["user"]["id"]))
    user.role = role
    session.commit()
    return result, user


def source(session, user, *, example=False, url=None):
    row = Source(
        created_by=user.id,
        title="Referência explicitamente fictícia para teste de contextos",
        institution="Instituição fictícia de teste",
        url=url or f"https://example.org/context/{uuid4().hex}",
        source_type="TECHNICAL_REPORT",
        publication_date=date(2025, 2, 1),
        accessed_at=date(2026, 1, 2),
        description="Citação inventada para testar a persistência, não análise do Brasil.",
        is_example=example,
    )
    session.add(row)
    session.flush()
    return row


def observation(session, user, code, *, example=False, value="13.75"):
    meta = BCB_SERIES[code]
    indicator = session.scalar(select(Indicator).where(Indicator.code == code))
    if indicator is None:
        indicator = Indicator(
            code=code,
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
            is_active=True,
        )
        session.add(indicator)
        session.flush()
    reference = source(session, user, example=example)
    reference.source_type = "OFFICIAL"
    row = IndicatorValue(
        indicator_id=indicator.id,
        source_id=reference.id,
        reference_date=date(2025, 7, 1),
        retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
        value=Decimal(value),
        revision=1,
        provenance={
            "license": "ODbL 1.0",
            "license_url": LICENSE_URL,
            "fixture": "Fictitious context integration observation",
            "definition": {
                key: getattr(indicator, key)
                for key in ("unit", "scope", "methodology", "frequency")
            },
        },
    )
    session.add(row)
    session.commit()
    return row, reference


def content(primary, counterpart, reference):
    evidence_id = str(uuid4())
    return {
        "title": "Contexto fictício: números não demonstram uma causa",
        "observation_summary": "Duas observações inventadas com recortes próprios.",
        "primary_observation_id": str(primary.id),
        "observation_ids": [str(primary.id), str(counterpart.id)],
        "source_ids": [str(reference.id)],
        "counterparts": [
            {
                "indicator_code": "divida-bruta-pib",
                "why_read_together": "Distinguir juros e estoque, sem inferir causalidade.",
                "availability": "REFERENCED",
                "observation_ids": [str(counterpart.id)],
            }
        ],
        "evidence": [
            {
                "id": evidence_id,
                "source_id": str(reference.id),
                "level": "ASSOCIATION",
                "claim": "Associação fictícia, sem conclusão causal.",
                "locator": "Tabela inventada 1",
                "excerpt": "Trecho fictício",
                "scope": "Recorte fictício",
                "period": "2025",
                "limitations": "Exemplo sem valor de evidência real.",
            }
        ],
        "hypotheses": [
            {
                "id": "primeira-explicacao",
                "explanation": "Primeira explicação fictícia.",
                "evidence": [
                    {
                        "evidence_id": evidence_id,
                        "relation": "CONTEXT",
                        "justification": "Exemplo de contexto, não prova.",
                    }
                ],
                "uncertainty": "Não identificamos um efeito causal.",
            },
            {
                "id": "alternativa",
                "explanation": "Explicação alternativa fictícia.",
                "evidence": [],
                "uncertainty": "Sem evidência suficiente para escolher.",
            },
        ],
        "consequences": [
            {
                "id": "projecao",
                "kind": "PROJECTED",
                "description": "Possibilidade declarada, não observação.",
                "premises": ["Premissa fictícia explicitamente declarada."],
                "limitations": "Não é resultado do motor fiscal.",
            }
        ],
        "limitations": ["Teste não demonstra causa nem valida conteúdo real."],
        "unknowns": ["Não sabemos o mecanismo que explicaria a associação."],
    }


def fixture(client, session, *, example=False):
    owner, owner_row = account(client, session)
    reviewer, reviewer_row = account(client, session, role="ADMIN")
    primary, _ = observation(session, owner_row, "selic-meta", example=example)
    counterpart, _ = observation(session, owner_row, "divida-bruta-pib", value="82.86")
    private_reference = source(session, owner_row)
    session.commit()
    return (
        owner,
        owner_row,
        reviewer,
        reviewer_row,
        content(primary, counterpart, private_reference),
    )


def create(client, owner, data):
    response = client.post(ENDPOINT, json={"content": data}, headers=headers(owner))
    assert response.status_code == 201, response.text
    return response.json()["data"]


def review(client, reviewer, draft, *, decision="ACCEPT", **overrides):
    response = client.post(
        f"{ENDPOINT}/{draft['id']}/review",
        headers=headers(reviewer),
        json={
            "expected_revision": draft["revision"],
            "decision": decision,
            "rationale": "Revisão fictícia de referências, recortes, alternativas e limites.",
            "references_checked": True,
            "scopes_checked": True,
            "alternatives_checked": True,
            "limitations_checked": True,
            **overrides,
        },
    )
    return response


def publish(client, owner, draft):
    return client.post(
        f"{ENDPOINT}/{draft['id']}/publish",
        headers=headers(owner),
        json={"expected_revision": draft["revision"]},
    )


def accepted(client, owner, reviewer, data):
    draft = create(client, owner, data)
    response = review(client, reviewer, draft)
    assert response.status_code == 200, response.text
    response = publish(client, owner, draft)
    assert response.status_code == 200, response.text
    return draft, response.json()["data"]


def counts(session):
    return [
        session.scalar(select(func.count()).select_from(model))
        for model in (Context, ContextVersion, ContextReview, ContextPublication)
    ]


def test_drafts_private_publication_public_and_resolves_frozen_references(auth_client, db_session):
    owner, owner_row, reviewer, reviewer_row, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    path = f"{ENDPOINT}/{draft['id']}"
    assert auth_client.get(path).status_code == 404
    assert auth_client.get(path + "/draft").status_code == 401
    assert auth_client.get(ENDPOINT).json()["data"] == []
    assert draft["content"]["author_id"] == str(owner_row.id)
    assert draft["content"]["revision"] == 1
    anchors = {row["indicator_code"]: row for row in draft["content"]["observations"]}
    assert Decimal(anchors["selic-meta"]["value"]) == Decimal("13.75")
    assert anchors["selic-meta"]["period_start"] == "2025-07-01"
    assert anchors["selic-meta"]["period_end"] == "2025-07-01"
    assert anchors["divida-bruta-pib"]["period_end"] == "2025-07-31"
    assert anchors["divida-bruta-pib"]["unit"] == BCB_SERIES["divida-bruta-pib"]["unit"]
    assert anchors["divida-bruta-pib"]["scope"] == BCB_SERIES["divida-bruta-pib"]["scope"]
    assert all(row["revision"] == 1 for row in anchors.values())
    assert len(draft["content_hash"]) == 64
    assert draft["assessment"]["status"] == "NEEDS_REVIEW"
    response = review(auth_client, reviewer, draft)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["review"]["reviewer_id"] == str(reviewer_row.id)
    response = publish(auth_client, owner, draft)
    assert response.status_code == 200, response.text
    public = auth_client.get(path).json()["data"]
    assert public["content"] == draft["content"]
    assert public["published_at"] is not None
    assert auth_client.get(path + "/versions/1").json()["data"] == public
    assert [row["revision"] for row in auth_client.get(path + "/versions").json()["data"]] == [1]
    private_source = str(data["source_ids"][0])
    assert auth_client.get(f"/api/v1/sources/{private_source}").status_code == 404
    assert "password_hash" not in response.text and "@example.com" not in response.text


def test_author_only_mutations_and_distinct_admin_review(auth_client, db_session):
    owner, owner_row, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    path = f"{ENDPOINT}/{draft['id']}"
    other, _ = account(auth_client, db_session)
    for actor in (None, other, reviewer):
        kwargs = {} if actor is None else {"headers": headers(actor)}
        expected = 401 if actor is None else 403
        assert (
            auth_client.patch(
                path, json={"content": data, "expected_revision": 1}, **kwargs
            ).status_code
            == expected
        )
        assert (
            auth_client.post(path + "/publish", json={"expected_revision": 1}, **kwargs).status_code
            == expected
        )
    assert review(auth_client, other, draft).status_code == 403
    assert review(auth_client, owner, draft).status_code == 403
    owner_row.role = "ADMIN"
    db_session.commit()
    assert review(auth_client, owner, draft).status_code == 403
    assert auth_client.get(path + "/draft", headers=headers(other)).status_code == 403
    assert auth_client.get(ENDPOINT + "/review-queue", headers=headers(other)).status_code == 403
    assert auth_client.get(ENDPOINT + "/mine").status_code == 401
    assert auth_client.get(ENDPOINT + "/mine", headers=headers(other)).json()["data"] == []
    assert auth_client.post(ENDPOINT, json={"content": data}).status_code == 401


@pytest.mark.parametrize(
    "field,value",
    [
        ("author_id", str(uuid4())),
        ("revision", 1),
        ("updated_at", "2026-01-02T00:00:00Z"),
        ("content_hash", "0" * 64),
        ("approved", True),
    ],
)
def test_client_cannot_forge_content_identity_dates_hash_or_approval(
    auth_client, db_session, field, value
):
    owner, _, _, _, data = fixture(auth_client, db_session)
    data[field] = value
    before = counts(db_session)
    response = auth_client.post(ENDPOINT, json={"content": data}, headers=headers(owner))
    assert response.status_code == 422, response.text
    assert counts(db_session) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer_id", str(uuid4())),
        ("content_hash", "0" * 64),
        ("reviewed_at", "2026-01-02T00:00:00Z"),
        ("references_checked", "true"),
    ],
)
def test_review_rejects_forged_fields_and_non_boolean_checklist(
    auth_client, db_session, field, value
):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    before = counts(db_session)
    response = review(auth_client, reviewer, draft, **{field: value})
    assert response.status_code == 422, response.text
    assert counts(db_session) == before


def test_private_foreign_source_same_url_is_not_visible_even_to_admin(auth_client, db_session):
    owner, _, reviewer, reviewer_row, data = fixture(auth_client, db_session)
    own = db_session.get(Source, UUID(data["source_ids"][0]))
    foreign = source(db_session, reviewer_row, url=own.url)
    db_session.commit()
    assert auth_client.get(f"/api/v1/sources/{foreign.id}").status_code == 404
    data["source_ids"] = [str(foreign.id)]
    data["evidence"][0]["source_id"] = str(foreign.id)
    before = counts(db_session)
    response = auth_client.post(ENDPOINT, json={"content": data}, headers=headers(owner))
    assert response.status_code == 404, response.text
    assert "Referência explicitamente" not in response.text
    data["source_ids"] = [str(own.id)]
    data["evidence"][0]["source_id"] = str(own.id)
    response = auth_client.post(ENDPOINT, json={"content": data}, headers=headers(reviewer))
    assert response.status_code == 404, response.text
    assert counts(db_session) == before


def test_published_v1_stable_after_source_edit_and_unreviewed_v2(auth_client, db_session):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    first, _ = accepted(auth_client, owner, reviewer, data)
    path = f"{ENDPOINT}/{first['id']}"
    before = deepcopy(auth_client.get(path).json())
    reference = db_session.get(Source, UUID(data["source_ids"][0]))
    reference.title = "Fonte alterada depois, título também fictício"
    db_session.commit()
    data["observation_summary"] = "Nova leitura fictícia, exige nova revisão."
    response = auth_client.patch(
        path, json={"content": data, "expected_revision": 1}, headers=headers(owner)
    )
    assert response.status_code == 200, response.text
    edited = response.json()["data"]
    assert edited["revision"] == 2 and edited["content_hash"] != first["content_hash"]
    assert edited["review"] is None
    assert publish(auth_client, owner, edited).status_code == 422
    assert auth_client.get(path).json() == before
    assert auth_client.get(path + "/versions/1").json() == before
    assert auth_client.get(path + "/versions/2").status_code == 404
    assert review(auth_client, reviewer, edited).status_code == 200
    assert publish(auth_client, owner, edited).status_code == 200
    assert [row["revision"] for row in auth_client.get(path + "/versions").json()["data"]] == [2, 1]
    assert auth_client.get(path + "/versions/1").json() == before


def test_latest_changes_request_blocks_earlier_accept_and_incomplete_checklist(
    auth_client, db_session
):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    assert review(auth_client, reviewer, draft, limitations_checked=False).status_code == 422
    assert publish(auth_client, owner, draft).status_code == 422
    assert review(auth_client, reviewer, draft).status_code == 200
    assert review(auth_client, reviewer, draft, decision="REQUEST_CHANGES").status_code == 200
    assert publish(auth_client, owner, draft).status_code == 422
    assert (
        auth_client.get(f"{ENDPOINT}/{draft['id']}/draft", headers=headers(owner)).json()["data"][
            "assessment"
        ]["status"]
        == "CHANGES_REQUESTED"
    )
    assert auth_client.get(f"{ENDPOINT}/{draft['id']}").status_code == 404


def test_optimistic_revision_conflicts_and_copy_cannot_reuse_review(auth_client, db_session):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    assert review(auth_client, reviewer, draft).status_code == 200
    copied = create(auth_client, owner, data)
    assert copied["content_hash"] != draft["content_hash"]
    assert publish(auth_client, owner, copied).status_code == 422
    edited = auth_client.patch(
        f"{ENDPOINT}/{draft['id']}",
        json={"content": data, "expected_revision": 1},
        headers=headers(owner),
    )
    assert edited.status_code == 200
    before = counts(db_session)
    assert review(auth_client, reviewer, draft).status_code == 409
    assert publish(auth_client, owner, draft).status_code == 409
    assert (
        auth_client.patch(
            f"{ENDPOINT}/{draft['id']}",
            json={"content": data, "expected_revision": 1},
            headers=headers(owner),
        ).status_code
        == 409
    )
    assert counts(db_session) == before


@pytest.mark.parametrize(
    "invalid", ["observation", "source", "counterpart-code", "duplicate", "orphan-evidence"]
)
def test_unknown_and_duplicate_references_rollback_whole_creation(auth_client, db_session, invalid):
    owner, _, _, _, data = fixture(auth_client, db_session)
    if invalid == "observation":
        data["observation_ids"].append(str(uuid4()))
    elif invalid == "source":
        data["source_ids"].append(str(uuid4()))
    elif invalid == "counterpart-code":
        data["counterparts"] = [
            {
                "indicator_code": "not-in-reviewed-catalog",
                "why_read_together": "Fictício",
                "availability": "NOT_COLLECTED",
                "observation_ids": [],
            }
        ]
    elif invalid == "duplicate":
        data["observation_ids"].append(data["observation_ids"][0])
    else:
        data["hypotheses"][0]["evidence"][0]["evidence_id"] = str(uuid4())
    before = counts(db_session)
    response = auth_client.post(ENDPOINT, json={"content": data}, headers=headers(owner))
    assert response.status_code in (404, 422), response.text
    assert counts(db_session) == before


def test_new_official_revision_blocks_actions_but_not_historical_read(auth_client, db_session):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft, _ = accepted(auth_client, owner, reviewer, data)
    path = f"{ENDPOINT}/{draft['id']}"
    frozen = deepcopy(auth_client.get(path).json())
    response = auth_client.patch(
        path, json={"content": data, "expected_revision": 1}, headers=headers(owner)
    )
    edited = response.json()["data"]
    assert review(auth_client, reviewer, edited).status_code == 200
    previous = db_session.get(IndicatorValue, UUID(data["primary_observation_id"]))
    newer = IndicatorValue(
        indicator_id=previous.indicator_id,
        source_id=previous.source_id,
        reference_date=previous.reference_date,
        value=Decimal("14.00"),
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
        revision=2,
        revision_reason="Correção fictícia de teste",
        provenance=previous.provenance,
    )
    db_session.add(newer)
    db_session.commit()
    assert review(auth_client, reviewer, edited).status_code == 409
    assert publish(auth_client, owner, edited).status_code == 409
    assert auth_client.get(path).json() == frozen
    data["primary_observation_id"] = str(newer.id)
    data["observation_ids"][0] = str(newer.id)
    revised = auth_client.patch(
        path, json={"content": data, "expected_revision": 2}, headers=headers(owner)
    )
    assert revised.status_code == 200, revised.text
    revised = revised.json()["data"]
    assert revised["content"]["observations"][0]["revision"] == 2
    assert review(auth_client, reviewer, revised).status_code == 200
    assert publish(auth_client, owner, revised).status_code == 200
    assert auth_client.get(path + "/versions/1").json() == frozen


@pytest.mark.parametrize(
    "table", ["contexts", "context_versions", "context_reviews", "context_publications"]
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_version_review_and_publication_append_only_even_by_sql(
    auth_client, db_session, table, operation
):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft, _ = accepted(auth_client, owner, reviewer, data)
    public = deepcopy(auth_client.get(f"{ENDPOINT}/{draft['id']}").json())
    command = f"UPDATE {table} SET id=id" if operation == "UPDATE" else f"DELETE FROM {table}"
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(text(command))
    assert auth_client.get(f"{ENDPOINT}/{draft['id']}").json() == public


def test_publication_cannot_bind_review_of_another_version_by_sql(auth_client, db_session):
    owner, _, reviewer, reviewer_row, data = fixture(auth_client, db_session)
    first = create(auth_client, owner, data)
    second = create(auth_client, owner, data)
    assert review(auth_client, reviewer, first).status_code == 200
    saved_review = db_session.scalar(
        select(ContextReview).where(ContextReview.context_version_id == UUID(first["version_id"]))
    )
    recorded_at = datetime.now(UTC)
    with (
        pytest.raises(IntegrityError, match="Context publication requires"),
        db_session.begin_nested(),
    ):
        db_session.add(
            ContextPublication(
                context_version_id=UUID(second["version_id"]),
                review_id=saved_review.id,
                content_hash=second["content_hash"],
                published_by=UUID(owner["user"]["id"]),
                published_at=recorded_at,
                created_at=recorded_at,
            )
        )
        db_session.flush()
    assert counts(db_session)[-1] == 0
    assert reviewer_row.id == saved_review.reviewer_id


def test_examples_hidden_in_production(auth_client, db_session, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    owner, _, reviewer, _, data = fixture(auth_client, db_session, example=True)
    draft, _ = accepted(auth_client, owner, reviewer, data)
    assert draft["is_example"] is True
    path = f"{ENDPOINT}/{draft['id']}"
    assert auth_client.get(path).status_code == 200
    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    assert auth_client.get(path).status_code == 404
    assert auth_client.get(path + "/versions/1").status_code == 404
    assert auth_client.get(ENDPOINT).json()["data"] == []


def test_zero_observed_is_preserved_and_missing_counterpart_stays_explicit(auth_client, db_session):
    owner, owner_row, reviewer, _, data = fixture(auth_client, db_session)
    zero, _ = observation(db_session, owner_row, "selic-meta", value="0")
    data["primary_observation_id"] = str(zero.id)
    data["observation_ids"] = [str(zero.id)]
    meta = BCB_SERIES["atividade-ibc-br"]
    missing_indicator = Indicator(
        code="atividade-ibc-br",
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
        is_active=True,
    )
    db_session.add(missing_indicator)
    db_session.commit()
    data["counterparts"][0].update(
        indicator_code="atividade-ibc-br", availability="NOT_COLLECTED", observation_ids=[]
    )
    draft, _ = accepted(auth_client, owner, reviewer, data)
    frozen = auth_client.get(f"{ENDPOINT}/{draft['id']}").json()["data"]["content"]
    assert Decimal(frozen["observations"][0]["value"]) == 0
    assert frozen["counterparts"][0]["availability"] == "NOT_COLLECTED"
    assert frozen["counterparts"][0]["observation_ids"] == []
    assert len(frozen["observations"]) == 1


@pytest.mark.parametrize("change", ["inactive", "not-admin"])
def test_reviewer_authorization_is_rechecked_at_publication(auth_client, db_session, change):
    owner, _, reviewer, reviewer_row, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    assert review(auth_client, reviewer, draft).status_code == 200
    if change == "inactive":
        reviewer_row.is_active = False
    else:
        reviewer_row.role = "USER"
    db_session.commit()
    before = counts(db_session)
    response = publish(auth_client, owner, draft)
    assert response.status_code == 422, response.text
    assert counts(db_session) == before
    assert auth_client.get(f"{ENDPOINT}/{draft['id']}").status_code == 404


def test_failed_update_preserves_whole_draft_and_version_count(auth_client, db_session):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    path = f"{ENDPOINT}/{draft['id']}"
    assert review(auth_client, reviewer, draft).status_code == 200
    before = deepcopy(auth_client.get(path + "/draft", headers=headers(owner)).json())
    before_counts = counts(db_session)
    data["source_ids"].append(str(uuid4()))
    response = auth_client.patch(
        path, json={"content": data, "expected_revision": 1}, headers=headers(owner)
    )
    assert response.status_code == 404, response.text
    assert counts(db_session) == before_counts
    assert auth_client.get(path + "/draft", headers=headers(owner)).json() == before


def test_public_search_cannot_find_unpublished_title_or_return_latest_private_draft(
    auth_client, db_session
):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft, published = accepted(auth_client, owner, reviewer, data)
    unique_title = "Rascunho privado " + uuid4().hex
    data["title"] = unique_title
    response = auth_client.patch(
        f"{ENDPOINT}/{draft['id']}",
        json={"content": data, "expected_revision": 1},
        headers=headers(owner),
    )
    assert response.status_code == 200, response.text
    assert auth_client.get(ENDPOINT, params={"q": unique_title}).json()["data"] == []
    public_list = auth_client.get(ENDPOINT).json()["data"]
    assert len(public_list) == 1 and public_list[0] == published
    assert (
        auth_client.get(ENDPOINT + "/mine", headers=headers(owner)).json()["data"][0]["revision"]
        == 2
    )
    assert (
        auth_client.get(ENDPOINT + "/review-queue", headers=headers(reviewer)).json()["data"][0][
            "revision"
        ]
        == 2
    )


def test_source_changed_after_acceptance_requires_new_saved_and_reviewed_content(
    auth_client, db_session
):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    assert review(auth_client, reviewer, draft).status_code == 200
    reference = db_session.get(Source, UUID(data["source_ids"][0]))
    reference.title = "Metadados fictícios corrigidos entre aceitação e publicação"
    db_session.commit()
    before = counts(db_session)
    response = publish(auth_client, owner, draft)
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "CONTEXT_REFERENCE_CHANGED"
    assert counts(db_session) == before
    assert auth_client.get(f"{ENDPOINT}/{draft['id']}").status_code == 404


def test_inactive_author_cannot_update_or_publish(auth_client, db_session):
    owner, owner_row, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    assert review(auth_client, reviewer, draft).status_code == 200
    owner_row.is_active = False
    db_session.commit()
    before = counts(db_session)
    assert publish(auth_client, owner, draft).status_code == 401
    response = auth_client.patch(
        f"{ENDPOINT}/{draft['id']}",
        headers=headers(owner),
        json={"content": data, "expected_revision": 1},
    )
    assert response.status_code == 401
    assert counts(db_session) == before


def extra_observation(session, primary, *, license_name, license_url):
    # An independent immutable row, rather than editing an existing observation.
    provenance = deepcopy(primary.provenance)
    provenance.update(license=license_name, license_url=license_url)
    row = IndicatorValue(
        indicator_id=primary.indicator_id,
        source_id=primary.source_id,
        reference_date=date(2025, 8, 1),
        value=Decimal("14.00"),
        retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
        revision=1,
        provenance=provenance,
    )
    session.add(row)
    session.commit()
    return row


def test_shared_source_conflicting_observation_terms_rejected_with_rollback(
    auth_client, db_session
):
    owner, _, _, _, data = fixture(auth_client, db_session)
    primary = db_session.get(IndicatorValue, UUID(data["primary_observation_id"]))
    conflicting = extra_observation(
        db_session,
        primary,
        license_name="Termos fictícios incompatíveis",
        license_url="https://example.org/incompatible-fixture-terms",
    )
    data["observation_ids"].append(str(conflicting.id))
    before = counts(db_session)
    response = auth_client.post(ENDPOINT, json={"content": data}, headers=headers(owner))
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "CONTEXT_TERMS_CONFLICT"
    assert counts(db_session) == before
    assert auth_client.get(f"/api/v1/sources/{primary.source_id}").status_code == 200


@pytest.mark.parametrize(
    "key,malformed",
    [
        ("license", {"forged": "term"}),
        ("license", ["ODbL 1.0"]),
        ("license_url", {"forged": "url"}),
        ("license_url", [LICENSE_URL]),
    ],
)
def test_malformed_observation_terms_return_safe_error_and_rollback(
    auth_client, db_session, key, malformed
):
    owner, _, _, _, data = fixture(auth_client, db_session)
    primary = db_session.get(IndicatorValue, UUID(data["primary_observation_id"]))
    values = {"license_name": "ODbL 1.0", "license_url": LICENSE_URL}
    values["license_name" if key == "license" else key] = malformed
    invalid = extra_observation(db_session, primary, **values)
    data["observation_ids"].append(str(invalid.id))
    before = counts(db_session)
    response = auth_client.post(ENDPOINT, json={"content": data}, headers=headers(owner))
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "CONTEXT_REFERENCE_INVALID"
    assert counts(db_session) == before
    assert "TypeError" not in response.text and "forged" not in response.text


def test_historical_definition_wins_over_changed_live_indicator(auth_client, db_session):
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    primary = db_session.get(IndicatorValue, UUID(data["primary_observation_id"]))
    historical = deepcopy(primary.provenance["definition"])
    indicator = db_session.get(Indicator, primary.indicator_id)
    indicator.unit = "Unidade fictícia posterior"
    indicator.scope = "Abrangência fictícia posterior"
    indicator.methodology = "Metodologia fictícia posterior"
    indicator.frequency = "YEARLY"
    db_session.commit()
    draft, published = accepted(auth_client, owner, reviewer, data)
    anchor = next(
        row
        for row in published["content"]["observations"]
        if row["observation_id"] == str(primary.id)
    )
    for key in ("unit", "scope", "methodology", "frequency"):
        assert anchor[key] == historical[key]
    assert anchor["period_start"] == anchor["period_end"] == "2025-07-01"
    assert auth_client.get(f"{ENDPOINT}/{draft['id']}").json()["data"] == published


def test_real_income_preserves_rolling_period_and_observation_price_base(auth_client, db_session):
    from app.integrations.ibge import IBGE_SERIES, IBGE_TERMS, INCOME_PRICE_METHOD_URL

    owner, owner_row, reviewer, _, data = fixture(auth_client, db_session)
    meta = IBGE_SERIES["renda-trabalho-real"]
    indicator = Indicator(
        code="renda-trabalho-real",
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
        is_active=True,
    )
    db_session.add(indicator)
    db_session.flush()
    reference = source(db_session, owner_row)
    reference.source_type = "OFFICIAL"
    provenance = {
        "definition": {key: meta[key] for key in ("unit", "scope", "methodology", "frequency")},
        "license": "Termos IBGE",
        "license_url": IBGE_TERMS,
        "income_price_reference": "2025-07-01",
        "income_price_period": "Maio-junho-julho de 2025 (fixture fictício)",
        "income_price_method_url": INCOME_PRICE_METHOD_URL,
        "fixture": "Invented income for persistence integration, not actual Brazilian data",
    }
    income = IndicatorValue(
        indicator_id=indicator.id,
        source_id=reference.id,
        reference_date=date(2025, 7, 1),
        retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
        value=Decimal("999.99"),
        revision=1,
        provenance=provenance,
    )
    db_session.add(income)
    db_session.commit()
    data["primary_observation_id"] = str(income.id)
    data["observation_ids"][0] = str(income.id)
    _, published = accepted(auth_client, owner, reviewer, data)
    anchor = published["content"]["observations"][0]
    assert Decimal(anchor["value"]) == Decimal("999.99")
    assert anchor["period_start"] == "2025-05-01" and anchor["period_end"] == "2025-07-31"
    for key in ("income_price_reference", "income_price_period", "income_price_method_url"):
        assert provenance[key] in anchor["methodology"]
    assert "Não comparar bases de preços diferentes" in anchor["methodology"]


def test_reference_later_marked_example_cannot_publish_real_context_in_development(
    auth_client, db_session, monkeypatch
):
    from app.core.config import get_settings

    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    owner, _, reviewer, _, data = fixture(auth_client, db_session)
    draft = create(auth_client, owner, data)
    assert draft["is_example"] is False
    assert review(auth_client, reviewer, draft).status_code == 200
    reference = db_session.get(Source, UUID(data["source_ids"][0]))
    reference.is_example = True
    db_session.commit()
    before = counts(db_session)
    response = publish(auth_client, owner, draft)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "EXAMPLE_CONTEXT_REQUIRED"
    assert counts(db_session) == before
    identity = db_session.get(Context, UUID(draft["id"]))
    assert identity.is_example is False
    assert auth_client.get(f"{ENDPOINT}/{draft['id']}").status_code == 404
