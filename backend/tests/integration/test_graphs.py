"""Fictitious graph curation; all rows roll back in exclusive PostgreSQL tests."""

from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.modules.graphs.models import (
    GraphCollection,
    GraphCollectionPublication,
    GraphCollectionVersion,
    GraphEdge,
    GraphEdgePublication,
    GraphEdgeReview,
    GraphEdgeVersion,
    GraphNode,
    GraphNodeVersion,
)
from app.modules.indicators.catalog import BCB_SERIES

from .test_contexts import account, observation, source
from .test_policies import draft as policy_draft
from .test_policies import headers

pytestmark = pytest.mark.database
ROOT = "/api/v1/graphs"
NODES = ROOT + "/nodes"
EDGES = ROOT + "/edges"
MODELS = (
    GraphNode,
    GraphNodeVersion,
    GraphEdge,
    GraphEdgeVersion,
    GraphEdgeReview,
    GraphEdgePublication,
    GraphCollection,
    GraphCollectionVersion,
    GraphCollectionPublication,
)


def counts(session):
    return tuple(session.scalar(select(func.count()).select_from(model)) for model in MODELS)


def node_content(label="Mecanismo fictício de teste"):
    return {
        "kind": "MECHANISM",
        "label": label,
        "definition": "Conceito inventado exclusivamente para testar permissões e versões.",
        "dimension": "Intensidade fictícia, sem coeficiente nem aplicação fiscal.",
        "unit": None,
        "indicator_code": None,
        "policy_version_id": None,
    }


def create(client, actor, path, content):
    response = client.post(path, headers=headers(actor), json={"content": content})
    assert response.status_code == 201, response.text
    return response.json()["data"]


def edge_content(first, second, reference):
    evidence_id = str(uuid4())
    return {
        "from_node_version_id": first["version_id"],
        "to_node_version_id": second["version_id"],
        "statement": "Relação fictícia, não uma afirmação sobre o Brasil.",
        "trigger": "INCREASE",
        "direction": "INCREASES",
        "horizon": "SHORT",
        "effect": "QUALITATIVE",
        "consensus": "SPECULATIVE",
        "authorship": "HUMAN",
        "source_ids": [str(reference.id)],
        "evidence": [
            {
                "id": evidence_id,
                "source_id": str(reference.id),
                "level": "ASSOCIATION",
                "claim": "Alegação explicitamente inventada para integração.",
                "locator": "Tabela fictícia 1",
                "excerpt": "Trecho inventado, sem evidência real.",
                "scope": "Universo fictício de teste",
                "period": "2025",
                "limitations": "Não demonstra causalidade nem quantifica qualquer efeito.",
            }
        ],
        "links": [
            {
                "evidence_id": evidence_id,
                "relation": "SUPPORTS",
                "justification": "Ligação fictícia para validar o fluxo de revisão.",
            }
        ],
        "premises": ["Premissa inventada e explícita."],
        "scope": "Universo fictício de teste",
        "period": "2025",
        "limitations": ["Teste sem validade substantiva ou causal."],
        "unknowns": ["Magnitude e causalidade não foram investigadas."],
        "counterpoint_status": "NOT_RESEARCHED",
        "counterargument_note": "",
        "counterpoint_search_notes": [],
        "counterpoint_searched_at": None,
    }


def fixture(client, session, *, example=False):
    owner, owner_row = account(client, session)
    reviewer, reviewer_row = account(client, session, role="ADMIN")
    first = create(client, owner, NODES, node_content())
    second = create(client, owner, NODES, node_content("Destino fictício de teste"))
    reference = source(session, owner_row, example=example)
    session.commit()
    data = edge_content(first, second, reference)
    return owner, owner_row, reviewer, reviewer_row, first, second, reference, data


def review(client, actor, record, *, decision="ACCEPT", **overrides):
    return client.post(
        f"{EDGES}/{record['id']}/review",
        headers=headers(actor),
        json={
            "expected_revision": record["revision"],
            "decision": decision,
            "rationale": "Conferência fictícia de referências, recortes, contrapontos e limites.",
            "references_checked": True,
            "scopes_checked": True,
            "counterpoints_checked": True,
            "limitations_checked": True,
            **overrides,
        },
    )


def publish_edge(client, actor, record, *, state="REVIEWED"):
    return client.post(
        f"{EDGES}/{record['id']}/publish",
        headers=headers(actor),
        json={"expected_revision": record["revision"], "publication_state": state},
    )


def publish_graph(client, actor, record):
    return client.post(
        f"{ROOT}/{record['id']}/publish",
        headers=headers(actor),
        json={"expected_revision": record["revision"]},
    )


def accepted(client, owner, reviewer, data):
    record = create(client, owner, EDGES, data)
    response = review(client, reviewer, record)
    assert response.status_code == 200, response.text
    response = publish_edge(client, owner, record)
    assert response.status_code == 200, response.text
    return record, response.json()["data"]


def collection_content(first, second, edge):
    return {
        "title": "Conjunto fictício para teste, sem interpretação real",
        "node_version_ids": [first["version_id"], second["version_id"]],
        "edge_version_ids": [edge["version_id"]],
    }


def test_drafts_are_private_and_publication_exposes_only_exact_referenced_nodes(
    auth_client, db_session
):
    owner, _, reviewer, _, first, second, reference, data = fixture(auth_client, db_session)
    unused = create(auth_client, owner, NODES, node_content("Nó privado sem ligação"))
    edge = create(auth_client, owner, EDGES, data)
    for path, record in ((NODES, first), (NODES, second), (EDGES, edge)):
        assert auth_client.get(f"{path}/{record['id']}").status_code == 404
        assert auth_client.get(f"{path}/{record['id']}/draft").status_code == 401
        assert auth_client.get(path).json()["data"] == []
        assert (
            auth_client.get(f"{path}/{record['id']}/draft", headers=headers(reviewer)).status_code
            == 200
        )
    assert publish_edge(auth_client, owner, edge).status_code == 422
    assert review(auth_client, reviewer, edge).status_code == 200
    assert publish_edge(auth_client, owner, edge).status_code == 200
    public = auth_client.get(f"{EDGES}/{edge['id']}").json()["data"]
    assert public["content"] == edge["content"]
    assert public["publication_state"] == "REVIEWED"
    assert public["published_at"] is not None
    assert auth_client.get(f"{NODES}/{first['id']}/versions/1").status_code == 200
    assert auth_client.get(f"{NODES}/{unused['id']}").status_code == 404
    assert auth_client.get(f"/api/v1/sources/{reference.id}").status_code == 404
    assert "password_hash" not in str(public) and "@example.com" not in str(public)


@pytest.mark.parametrize("resource", ["node", "edge", "graph"])
@pytest.mark.parametrize("actor_name", ["anonymous", "other", "reviewer"])
def test_only_author_mutates_and_lists_private_resources(
    auth_client, db_session, resource, actor_name
):
    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    graph_data = collection_content(first, second, edge)
    graph = create(auth_client, owner, ROOT, graph_data)
    other, _ = account(auth_client, db_session)
    actor = {"anonymous": None, "other": other, "reviewer": reviewer}[actor_name]
    path, record, content = {
        "node": (NODES, first, node_content()),
        "edge": (EDGES, edge, data),
        "graph": (ROOT, graph, graph_data),
    }[resource]
    kwargs = {} if actor is None else {"headers": headers(actor)}
    before = counts(db_session)
    response = auth_client.patch(
        f"{path}/{record['id']}",
        json={"expected_revision": record["revision"], "content": content},
        **kwargs,
    )
    assert response.status_code == (401 if actor is None else 403), response.text
    if resource != "node":
        payload = {"expected_revision": 1}
        if resource == "edge":
            payload["publication_state"] = "REVIEWED"
        response = auth_client.post(f"{path}/{record['id']}/publish", json=payload, **kwargs)
        assert response.status_code == (401 if actor is None else 403), response.text
    assert counts(db_session) == before
    if actor is not None:
        assert auth_client.get(path + "/mine", **kwargs).json()["data"] == []


def test_only_distinct_active_admin_can_review_and_admin_cannot_publish_for_author(
    auth_client, db_session
):
    owner, owner_row, reviewer, reviewer_row, _, _, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    assert auth_client.post(f"{EDGES}/{edge['id']}/review", json={}).status_code == 401
    assert review(auth_client, owner, edge).status_code == 403
    owner_row.role = "ADMIN"
    db_session.commit()
    assert review(auth_client, owner, edge).status_code == 403
    assert review(auth_client, reviewer, edge).status_code == 200
    assert publish_edge(auth_client, reviewer, edge).status_code == 403
    reviewer_row.is_active = False
    db_session.commit()
    assert review(auth_client, reviewer, edge).status_code == 401
    assert publish_edge(auth_client, owner, edge).status_code == 422
    assert auth_client.get(f"{EDGES}/{edge['id']}").status_code == 404


@pytest.mark.parametrize("decision", ["ACCEPT", "DISPUTE"])
@pytest.mark.parametrize(
    "check",
    ["references_checked", "scopes_checked", "counterpoints_checked", "limitations_checked"],
)
def test_acceptance_and_dispute_require_every_check(auth_client, db_session, decision, check):
    owner, _, reviewer, _, _, _, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    before = counts(db_session)
    response = review(auth_client, reviewer, edge, decision=decision, **{check: False})
    assert response.status_code == 422, response.text
    assert counts(db_session) == before


@pytest.mark.parametrize("decision", ["REQUEST_CHANGES", "REJECT"])
def test_latest_negative_review_blocks_previous_acceptance(auth_client, db_session, decision):
    owner, _, reviewer, _, _, _, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    assert review(auth_client, reviewer, edge).status_code == 200
    assert review(auth_client, reviewer, edge, decision=decision).status_code == 200
    before = counts(db_session)
    assert publish_edge(auth_client, owner, edge).status_code == 422
    assert publish_edge(auth_client, owner, edge, state="DISPUTED").status_code == 422
    assert counts(db_session) == before
    assert auth_client.get(f"{EDGES}/{edge['id']}").status_code == 404


def test_dispute_is_private_until_owner_explicitly_publishes_disputed_state(
    auth_client, db_session
):
    owner, _, reviewer, _, _, _, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    assert review(auth_client, reviewer, edge, decision="DISPUTE").status_code == 200
    assert auth_client.get(f"{EDGES}/{edge['id']}").status_code == 404
    assert publish_edge(auth_client, owner, edge).status_code == 422
    response = publish_edge(auth_client, owner, edge, state="DISPUTED")
    assert response.status_code == 200, response.text
    assert response.json()["data"]["publication_state"] == "DISPUTED"
    assert review(auth_client, reviewer, edge).status_code == 409
    assert publish_edge(auth_client, owner, edge, state="DISPUTED").status_code == 409


def test_assisted_authorship_never_bypasses_review_or_transfers_review_to_copy(
    auth_client, db_session
):
    owner, _, reviewer, _, _, _, _, data = fixture(auth_client, db_session)
    data["authorship"] = "AI_ASSISTED"
    edge = create(auth_client, owner, EDGES, data)
    assert publish_edge(auth_client, owner, edge).status_code == 422
    assert review(auth_client, reviewer, edge).status_code == 200
    copied = create(auth_client, owner, EDGES, data)
    assert copied["content_hash"] != edge["content_hash"]
    assert publish_edge(auth_client, owner, copied).status_code == 422
    assert publish_edge(auth_client, owner, edge).status_code == 200


@pytest.mark.parametrize(
    "field", ["id", "revision", "author_id", "updated_at", "content_hash", "approved"]
)
def test_client_cannot_set_server_managed_edge_fields(auth_client, db_session, field):
    owner, _, _, _, _, _, _, data = fixture(auth_client, db_session)
    data[field] = 1 if field == "revision" else str(uuid4())
    before = counts(db_session)
    response = auth_client.post(EDGES, json={"content": data}, headers=headers(owner))
    assert response.status_code == 422, response.text
    assert counts(db_session) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer_id", str(uuid4())),
        ("content_hash", "0" * 64),
        ("reviewed_at", "2026-01-01T00:00:00Z"),
        ("references_checked", "true"),
        ("expected_revision", True),
        ("expected_revision", "1"),
    ],
)
def test_review_rejects_forged_metadata_and_coerced_fields(auth_client, db_session, field, value):
    owner, _, reviewer, _, _, _, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    before = counts(db_session)
    response = review(auth_client, reviewer, edge, **{field: value})
    assert response.status_code == 422, response.text
    assert counts(db_session) == before


@pytest.mark.parametrize(
    "invalid", ["source", "node", "duplicate-source", "orphan-evidence", "same-node"]
)
def test_invalid_references_roll_back_identity_and_revision(auth_client, db_session, invalid):
    owner, _, _, _, _, _, _, data = fixture(auth_client, db_session)
    if invalid == "source":
        data["source_ids"] = [str(uuid4())]
        data["evidence"][0]["source_id"] = data["source_ids"][0]
    elif invalid == "node":
        data["from_node_version_id"] = str(uuid4())
    elif invalid == "duplicate-source":
        data["source_ids"].append(data["source_ids"][0])
    elif invalid == "orphan-evidence":
        data["links"][0]["evidence_id"] = str(uuid4())
    else:
        data["to_node_version_id"] = data["from_node_version_id"]
    before = counts(db_session)
    response = auth_client.post(EDGES, json={"content": data}, headers=headers(owner))
    assert response.status_code in (404, 422), response.text
    assert counts(db_session) == before


def test_foreign_private_sources_with_equal_url_do_not_gain_visibility_even_for_admin(
    auth_client, db_session
):
    owner, _, reviewer, reviewer_row, first, second, reference, data = fixture(
        auth_client, db_session
    )
    foreign = source(db_session, reviewer_row, url=reference.url)
    db_session.commit()
    data["source_ids"] = [str(foreign.id)]
    data["evidence"][0]["source_id"] = str(foreign.id)
    before = counts(db_session)
    response = auth_client.post(EDGES, json={"content": data}, headers=headers(owner))
    assert response.status_code == 404, response.text
    assert foreign.title not in response.text
    # Admin owns these nodes; foreign-source privacy is checked independently of node privacy.
    admin_first = create(auth_client, reviewer, NODES, node_content("Origem privada do admin"))
    admin_second = create(auth_client, reviewer, NODES, node_content("Destino privado do admin"))
    data = edge_content(admin_first, admin_second, reference)
    before = counts(db_session)
    response = auth_client.post(EDGES, json={"content": data}, headers=headers(reviewer))
    assert response.status_code == 404, response.text
    assert counts(db_session) == before


def test_public_source_ids_can_be_reused_without_promoting_private_alias(auth_client, db_session):
    owner, _, reviewer, reviewer_row, first, second, _, data = fixture(auth_client, db_session)
    observed, public_reference = observation(db_session, reviewer_row, "selic-meta")
    assert observed.source_id == public_reference.id
    data["source_ids"] = [str(public_reference.id)]
    data["evidence"][0]["source_id"] = str(public_reference.id)
    edge = create(auth_client, owner, EDGES, data)
    assert edge["content"]["sources"][0]["id"] == str(public_reference.id)
    assert auth_client.get(f"{NODES}/{first['id']}").status_code == 404
    assert auth_client.get(f"{NODES}/{second['id']}").status_code == 404


def test_published_nodes_reusable_by_other_author_but_private_new_revision_is_not(
    auth_client, db_session
):
    owner, _, reviewer, reviewer_row, first, second, _, data = fixture(auth_client, db_session)
    accepted(auth_client, owner, reviewer, data)
    own_reference = source(db_session, reviewer_row)
    db_session.commit()
    borrowed = edge_content(first, second, own_reference)
    create(auth_client, reviewer, EDGES, borrowed)
    changed = node_content("Nome privado posterior")
    response = auth_client.patch(
        f"{NODES}/{first['id']}",
        headers=headers(owner),
        json={"expected_revision": 1, "content": changed},
    )
    assert response.status_code == 200, response.text
    borrowed["from_node_version_id"] = response.json()["data"]["version_id"]
    before = counts(db_session)
    response = auth_client.post(EDGES, headers=headers(reviewer), json={"content": borrowed})
    assert response.status_code == 404, response.text
    assert counts(db_session) == before


def test_source_changes_after_review_block_publication_without_rewriting_draft(
    auth_client, db_session
):
    owner, _, reviewer, _, _, _, reference, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    assert review(auth_client, reviewer, edge).status_code == 200
    before = counts(db_session)
    reference.title = "Correção fictícia do cadastro posterior à revisão"
    db_session.commit()
    assert publish_edge(auth_client, owner, edge).status_code == 409
    assert counts(db_session) == before
    draft = auth_client.get(f"{EDGES}/{edge['id']}/draft", headers=headers(owner)).json()["data"]
    assert draft["content"] == edge["content"]
    assert auth_client.get(f"{EDGES}/{edge['id']}").status_code == 404


def test_immutable_edge_and_graph_history_survive_source_and_node_changes(auth_client, db_session):
    owner, _, reviewer, _, first, second, reference, data = fixture(auth_client, db_session)
    edge, _ = accepted(auth_client, owner, reviewer, data)
    collection_data = collection_content(first, second, edge)
    graph = create(auth_client, owner, ROOT, collection_data)
    response = publish_graph(auth_client, owner, graph)
    assert response.status_code == 200, response.text
    edge_path = f"{EDGES}/{edge['id']}"
    graph_path = f"{ROOT}/{graph['id']}"
    frozen_edge = deepcopy(auth_client.get(edge_path).json())
    frozen_graph = deepcopy(auth_client.get(graph_path).json())
    reference.title = "Fonte fictícia alterada depois da publicação"
    db_session.commit()
    response = auth_client.patch(
        f"{NODES}/{first['id']}",
        headers=headers(owner),
        json={"expected_revision": 1, "content": node_content("Nome novo privado")},
    )
    assert response.status_code == 200, response.text
    new_node = response.json()["data"]
    data["from_node_version_id"] = new_node["version_id"]
    data["statement"] = "Relação nova privada " + uuid4().hex
    response = auth_client.patch(
        edge_path, headers=headers(owner), json={"expected_revision": 1, "content": data}
    )
    assert response.status_code == 200, response.text
    new_edge = response.json()["data"]
    assert new_edge["revision"] == 2 and new_edge["review"] is None
    assert new_edge["content_hash"] != edge["content_hash"]
    assert publish_edge(auth_client, owner, new_edge).status_code == 422
    assert auth_client.get(edge_path).json() == frozen_edge
    assert auth_client.get(edge_path + "/versions/1").json() == frozen_edge
    assert auth_client.get(edge_path + "/versions/2").status_code == 404
    assert auth_client.get(graph_path).json() == frozen_graph
    assert auth_client.get(graph_path + "/versions/1").json() == frozen_graph
    assert auth_client.get(EDGES, params={"q": data["statement"]}).json()["data"] == []
    # The old published edge version remains explicitly selectable after a new private revision.
    another = create(auth_client, owner, ROOT, collection_data)
    assert publish_graph(auth_client, owner, another).status_code == 200
    assert review(auth_client, reviewer, new_edge).status_code == 200
    assert publish_edge(auth_client, owner, new_edge).status_code == 200
    assert auth_client.get(graph_path).json() == frozen_graph
    assert auth_client.get(edge_path + "/versions/1").json() == frozen_edge


def test_revision_conflicts_and_failed_updates_preserve_draft_and_review(auth_client, db_session):
    owner, _, reviewer, _, _, _, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    assert review(auth_client, reviewer, edge).status_code == 200
    path = f"{EDGES}/{edge['id']}"
    before = deepcopy(auth_client.get(path + "/draft", headers=headers(owner)).json())
    original_counts = counts(db_session)
    invalid = deepcopy(data)
    invalid["source_ids"].append(str(uuid4()))
    response = auth_client.patch(
        path, headers=headers(owner), json={"expected_revision": 1, "content": invalid}
    )
    assert response.status_code in (404, 422), response.text
    assert counts(db_session) == original_counts
    assert auth_client.get(path + "/draft", headers=headers(owner)).json() == before
    response = auth_client.patch(
        path, headers=headers(owner), json={"expected_revision": 1, "content": data}
    )
    assert response.status_code == 200, response.text
    original_counts = counts(db_session)
    assert review(auth_client, reviewer, edge).status_code == 409
    assert publish_edge(auth_client, owner, edge).status_code == 409
    assert (
        auth_client.patch(
            path, headers=headers(owner), json={"expected_revision": 1, "content": data}
        ).status_code
        == 409
    )
    assert counts(db_session) == original_counts


@pytest.mark.parametrize("failure", ["unpublished-edge", "no-edges", "isolated-private-node"])
def test_graph_publication_never_implicitly_publishes_private_references(
    auth_client, db_session, failure
):
    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    content = collection_content(first, second, edge)
    if failure != "unpublished-edge":
        assert review(auth_client, reviewer, edge).status_code == 200
        assert publish_edge(auth_client, owner, edge).status_code == 200
    if failure == "no-edges":
        content["edge_version_ids"] = []
    elif failure == "isolated-private-node":
        isolated = create(auth_client, owner, NODES, node_content("Isolado privado"))
        content["node_version_ids"].append(isolated["version_id"])
    graph = create(auth_client, owner, ROOT, content)
    before = counts(db_session)
    response = publish_graph(auth_client, owner, graph)
    assert response.status_code == 422, response.text
    assert counts(db_session) == before
    assert auth_client.get(f"{ROOT}/{graph['id']}").status_code == 404


def test_graph_exact_node_version_required_not_merely_same_identity(auth_client, db_session):
    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge, _ = accepted(auth_client, owner, reviewer, data)
    response = auth_client.patch(
        f"{NODES}/{first['id']}",
        headers=headers(owner),
        json={"expected_revision": 1, "content": node_content("Outra revisão do nó")},
    )
    assert response.status_code == 200, response.text
    mismatched = collection_content(response.json()["data"], second, edge)
    before = counts(db_session)
    response = auth_client.post(ROOT, headers=headers(owner), json={"content": mismatched})
    assert response.status_code == 422, response.text
    assert counts(db_session) == before


@pytest.mark.parametrize("case", ["unknown", "inactive", "auxiliary", "forged-unit"])
def test_indicator_node_uses_active_reviewed_catalog_and_server_unit(auth_client, db_session, case):
    owner, owner_row = account(auth_client, db_session)
    observed, _ = observation(db_session, owner_row, "selic-meta")
    content = node_content()
    content.update(kind="INDICATOR", indicator_code="selic-meta")
    if case == "unknown":
        content["indicator_code"] = "invented-indicator"
    elif case == "inactive":
        from app.modules.indicators.models import Indicator

        db_session.get(Indicator, observed.indicator_id).is_active = False
        db_session.commit()
    elif case == "auxiliary":
        content["indicator_code"] = "rtn-receita-total"
    else:
        content["unit"] = "Unidade inventada pelo cliente"
    before = counts(db_session)
    response = auth_client.post(NODES, headers=headers(owner), json={"content": content})
    if case == "forged-unit":
        # The catalogue owns the unit: reject mismatches or resolve the trusted unit.
        if response.status_code == 201:
            assert response.json()["data"]["content"]["unit"] == BCB_SERIES["selic-meta"]["unit"]
        else:
            assert response.status_code == 422, response.text
            assert counts(db_session) == before
    else:
        assert response.status_code in (404, 422), response.text
        assert counts(db_session) == before


def test_measure_node_accepts_only_exact_published_policy_version(auth_client, db_session):
    owner, _ = account(auth_client, db_session)
    proposal, _ = policy_draft(auth_client, owner)
    content = node_content()
    content.update(kind="MEASURE", policy_version_id=proposal["version"]["id"])
    before = counts(db_session)
    response = auth_client.post(NODES, headers=headers(owner), json={"content": content})
    assert response.status_code in (404, 422), response.text
    assert counts(db_session) == before
    published = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(owner)
    )
    assert published.status_code == 200, published.text
    version = published.json()["data"]["version"]
    content["policy_version_id"] = version["id"]
    node = create(auth_client, owner, NODES, content)
    assert node["content"]["policy_version_id"] == version["id"]
    assert node["content"]["policy_version_number"] == version["version_number"]


def test_example_graphs_and_their_nodes_are_hidden_outside_development(
    auth_client, db_session, monkeypatch
):
    from app.core.config import get_settings

    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session, example=True)
    edge, published = accepted(auth_client, owner, reviewer, data)
    assert published["is_example"] is True
    graph = create(auth_client, owner, ROOT, collection_content(first, second, edge))
    response = publish_graph(auth_client, owner, graph)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["is_example"] is True
    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    for endpoint, record in ((EDGES, edge), (ROOT, graph), (NODES, first), (NODES, second)):
        assert auth_client.get(f"{endpoint}/{record['id']}").status_code == 404
        assert auth_client.get(f"{endpoint}/{record['id']}/versions/1").status_code == 404
        assert auth_client.get(endpoint).json()["data"] == []


def test_source_later_marked_example_cannot_publish_real_edge_even_in_development(
    auth_client, db_session, monkeypatch
):
    from app.core.config import get_settings

    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    owner, _, reviewer, _, _, _, reference, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    assert edge["is_example"] is False
    assert review(auth_client, reviewer, edge).status_code == 200
    reference.is_example = True
    db_session.commit()
    before = counts(db_session)
    assert publish_edge(auth_client, owner, edge).status_code == 422
    assert counts(db_session) == before


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__tablename__)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_graph_records_append_only_even_through_sql(auth_client, db_session, model, operation):
    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge, _ = accepted(auth_client, owner, reviewer, data)
    graph = create(auth_client, owner, ROOT, collection_content(first, second, edge))
    response = publish_graph(auth_client, owner, graph)
    assert response.status_code == 200, response.text
    frozen = deepcopy(auth_client.get(f"{ROOT}/{graph['id']}").json())
    assert db_session.scalar(select(func.count()).select_from(model)) > 0
    table = model.__tablename__
    command = f"UPDATE {table} SET id=id" if operation == "UPDATE" else f"DELETE FROM {table}"
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(text(command))
    assert auth_client.get(f"{ROOT}/{graph['id']}").json() == frozen


@pytest.mark.parametrize(
    "wrong", ["other-version-review", "wrong-hash", "other-publisher", "wrong-state"]
)
def test_sql_cannot_publish_edge_with_mismatched_review_hash_author_or_state(
    auth_client, db_session, wrong
):
    owner, _, reviewer, _, _, _, _, data = fixture(auth_client, db_session)
    first = create(auth_client, owner, EDGES, data)
    second = create(auth_client, owner, EDGES, data)
    assert review(auth_client, reviewer, first).status_code == 200
    assert review(auth_client, reviewer, second).status_code == 200
    saved_review = db_session.scalar(
        select(GraphEdgeReview).where(GraphEdgeReview.edge_version_id == UUID(first["version_id"]))
    )
    published_at = datetime.now(UTC)
    fields = {
        "edge_version_id": UUID(first["version_id"]),
        "review_id": saved_review.id,
        "content_hash": first["content_hash"],
        "published_by": UUID(owner["user"]["id"]),
        "published_state": "REVIEWED",
        "published_at": published_at,
        "created_at": published_at,
    }
    if wrong == "other-version-review":
        fields["edge_version_id"] = UUID(second["version_id"])
        fields["content_hash"] = second["content_hash"]
    elif wrong == "wrong-hash":
        fields["content_hash"] = "0" * 64
    elif wrong == "other-publisher":
        fields["published_by"] = UUID(reviewer["user"]["id"])
    else:
        fields["published_state"] = "DISPUTED"
    before = counts(db_session)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(GraphEdgePublication(**fields))
        db_session.flush()
    assert counts(db_session) == before
    assert auth_client.get(f"{EDGES}/{first['id']}").status_code == 404


@pytest.mark.parametrize(
    "operation", ["create", "update", "review", "publish-edge", "publish-graph"]
)
def test_failed_response_construction_rolls_back_pending_graph_mutation(
    auth_client, db_session, monkeypatch, operation
):
    from app.modules.graphs import service

    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    graph = None
    if operation in ("publish-edge", "publish-graph"):
        assert review(auth_client, reviewer, edge).status_code == 200
    if operation == "publish-graph":
        assert publish_edge(auth_client, owner, edge).status_code == 200
        graph = create(auth_client, owner, ROOT, collection_content(first, second, edge))
    before = counts(db_session)

    def broken_view(*args, **kwargs):
        raise RuntimeError("Explicit fictitious response construction failure")

    with monkeypatch.context() as scoped:
        scoped.setattr(service, "_view", broken_view)
        with pytest.raises(RuntimeError, match="response construction failure"):
            if operation == "create":
                auth_client.post(NODES, headers=headers(owner), json={"content": node_content()})
            elif operation == "update":
                auth_client.patch(
                    f"{EDGES}/{edge['id']}",
                    headers=headers(owner),
                    json={"expected_revision": 1, "content": data},
                )
            elif operation == "review":
                review(auth_client, reviewer, edge)
            elif operation == "publish-edge":
                publish_edge(auth_client, owner, edge)
            else:
                publish_graph(auth_client, owner, graph)
    assert counts(db_session) == before
    if operation != "publish-graph":
        assert auth_client.get(f"{EDGES}/{edge['id']}").status_code == 404


def test_latest_public_graph_title_search_ignores_old_public_and_new_private_titles(
    auth_client, db_session
):
    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge, _ = accepted(auth_client, owner, reviewer, data)
    content = collection_content(first, second, edge)
    first_title = "Antigo título público fictício " + uuid4().hex
    content["title"] = first_title
    graph = create(auth_client, owner, ROOT, content)
    assert publish_graph(auth_client, owner, graph).status_code == 200
    path = f"{ROOT}/{graph['id']}"
    frozen = deepcopy(auth_client.get(path + "/versions/1").json())
    content["title"] = "Título público atual fictício " + uuid4().hex
    response = auth_client.patch(
        path, headers=headers(owner), json={"expected_revision": 1, "content": content}
    )
    assert response.status_code == 200, response.text
    assert publish_graph(auth_client, owner, response.json()["data"]).status_code == 200
    assert auth_client.get(ROOT, params={"q": first_title}).json()["data"] == []
    current = auth_client.get(ROOT, params={"q": content["title"]}).json()
    assert current["pagination"]["total"] == 1 and current["data"][0]["revision"] == 2
    private_title = "Título ainda privado fictício " + uuid4().hex
    content["title"] = private_title
    response = auth_client.patch(
        path, headers=headers(owner), json={"expected_revision": 2, "content": content}
    )
    assert response.status_code == 200, response.text
    assert auth_client.get(ROOT, params={"q": private_title}).json()["data"] == []
    assert auth_client.get(path + "/versions/1").json() == frozen
    assert auth_client.get(path + "/versions/3").status_code == 404


@pytest.mark.parametrize("resource", ["node", "edge", "graph"])
def test_payload_byte_limits_reject_mutations_without_leaking_partial_rows(
    auth_client, db_session, monkeypatch, resource
):
    from app.modules.graphs import service

    owner, _, _, _, first, second, _, data = fixture(auth_client, db_session)
    edge = create(auth_client, owner, EDGES, data)
    endpoint, content = {
        "node": (NODES, node_content()),
        "edge": (EDGES, data),
        "graph": (ROOT, collection_content(first, second, edge)),
    }[resource]
    constant = {
        "node": "MAX_NODE_PAYLOAD_BYTES",
        "edge": "MAX_EDGE_PAYLOAD_BYTES",
        "graph": "MAX_GRAPH_PAYLOAD_BYTES",
    }[resource]
    monkeypatch.setattr(service, constant, 16)
    before = counts(db_session)
    response = auth_client.post(endpoint, headers=headers(owner), json={"content": content})
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "GRAPH_CONTENT_TOO_LARGE"
    assert counts(db_session) == before


def test_historical_graph_read_does_not_apply_new_mutation_payload_limit(
    auth_client, db_session, monkeypatch
):
    from app.modules.graphs import service

    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge, _ = accepted(auth_client, owner, reviewer, data)
    graph = create(auth_client, owner, ROOT, collection_content(first, second, edge))
    assert publish_graph(auth_client, owner, graph).status_code == 200
    path = f"{ROOT}/{graph['id']}"
    frozen = deepcopy(auth_client.get(path).json())
    monkeypatch.setattr(service, "MAX_GRAPH_PAYLOAD_BYTES", 16)
    assert auth_client.get(path).json() == frozen
    assert auth_client.get(path + "/versions/1").json() == frozen


def test_third_author_can_publish_collection_of_public_edge_with_original_private_source(
    auth_client, db_session
):
    owner, _, reviewer, _, first, second, reference, data = fixture(auth_client, db_session)
    edge, published = accepted(auth_client, owner, reviewer, data)
    source_path = f"/api/v1/sources/{reference.id}"
    assert auth_client.get(source_path).status_code == 404
    collector, _ = account(auth_client, db_session)
    graph = create(auth_client, collector, ROOT, collection_content(first, second, edge))
    response = publish_graph(auth_client, collector, graph)
    assert response.status_code == 200, response.text
    public = auth_client.get(f"{ROOT}/{graph['id']}").json()["data"]
    assert public["content"]["author_id"] == collector["user"]["id"]
    assert public["content"]["edges"][0] == published["content"]
    assert public["content"]["edges"][0]["sources"][0]["id"] == str(reference.id)
    assert public["content"]["edges"][0]["author_id"] == owner["user"]["id"]
    assert auth_client.get(source_path).status_code == 404
    assert auth_client.get("/api/v1/sources").json()["data"] == []


def test_real_collection_cannot_use_node_witnessed_only_by_example_edge_in_development(
    auth_client, db_session, monkeypatch
):
    from app.core.config import get_settings

    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    owner, owner_row, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    real_edge, _ = accepted(auth_client, owner, reviewer, data)
    isolated = create(
        auth_client, owner, NODES, node_content("Nó com testemunha apenas de exemplo")
    )
    assert isolated["is_example"] is False
    example_reference = source(db_session, owner_row, example=True)
    db_session.commit()
    example_edge, published_example = accepted(
        auth_client, owner, reviewer, edge_content(isolated, first, example_reference)
    )
    assert published_example["is_example"] is True
    content = collection_content(first, second, real_edge)
    content["node_version_ids"].append(isolated["version_id"])
    graph = create(auth_client, owner, ROOT, content)
    assert graph["is_example"] is False
    before = counts(db_session)
    response = publish_graph(auth_client, owner, graph)
    assert response.status_code == 422, response.text
    assert counts(db_session) == before
    assert auth_client.get(f"{ROOT}/{graph['id']}").status_code == 404
    # A direct insert must not bypass the real-witness gate enforced by the service.
    published_at = datetime.now(UTC)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            GraphCollectionPublication(
                graph_version_id=UUID(graph["version_id"]),
                content_hash=graph["content_hash"],
                published_by=UUID(owner["user"]["id"]),
                published_at=published_at,
                created_at=published_at,
            )
        )
        db_session.flush()
    assert counts(db_session) == before
    # Including the example relation explicitly derives an example collection and permits it in DEV.
    content["edge_version_ids"].append(example_edge["version_id"])
    example_graph = create(auth_client, owner, ROOT, content)
    assert example_graph["is_example"] is True
    response = publish_graph(auth_client, owner, example_graph)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["is_example"] is True


@pytest.mark.parametrize("resource", ["node", "edge", "graph"])
def test_public_lists_are_compact_while_detail_preserves_complete_frozen_content(
    auth_client, db_session, resource
):
    owner, _, reviewer, _, first, second, _, data = fixture(auth_client, db_session)
    edge, _ = accepted(auth_client, owner, reviewer, data)
    graph = create(auth_client, owner, ROOT, collection_content(first, second, edge))
    assert publish_graph(auth_client, owner, graph).status_code == 200
    endpoint, record, field = {
        "node": (NODES, first, "label"),
        "edge": (EDGES, edge, "statement"),
        "graph": (ROOT, graph, "title"),
    }[resource]
    full = auth_client.get(f"{endpoint}/{record['id']}").json()["data"]
    listed = auth_client.get(endpoint, params={"q": full["content"][field]}).json()["data"]
    summary = next(row for row in listed if row["id"] == record["id"])
    assert summary["content"] == {field: full["content"][field]}
    assert summary["version_id"] == full["version_id"]
    assert summary["content_hash"] == full["content_hash"]
    assert "evidence" not in str(summary) and "topology" not in summary
    assert "review" not in summary and "publications" not in summary
    assert len(full["content"]) > len(summary["content"])
