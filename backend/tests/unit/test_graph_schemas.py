"""Transport preserves authority boundaries before domain reference resolution."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.graphs.schemas import (
    EdgeContentInput,
    EdgeCreate,
    EdgePublishInput,
    EdgeReviewInput,
    EdgeUpdate,
    GraphContentInput,
    GraphCreate,
    GraphPublishInput,
    GraphUpdate,
    NodeContentInput,
    NodeCreate,
    NodeUpdate,
)


def node_input():
    return {
        "kind": "MECHANISM",
        "label": "Acesso",
        "definition": "Exemplo fictício de definição.",
        "dimension": "Oferta disponível",
    }


def edge_input():
    source_id, evidence_id = uuid4(), uuid4()
    return {
        "from_node_version_id": str(uuid4()),
        "to_node_version_id": str(uuid4()),
        "statement": "Relação fictícia.",
        "trigger": "INCREASE",
        "direction": "UNCERTAIN",
        "horizon": "SHORT",
        "effect": "QUALITATIVE",
        "consensus": "SPECULATIVE",
        "authorship": "HUMAN",
        "source_ids": [str(source_id)],
        "evidence": [
            {
                "id": str(evidence_id),
                "source_id": str(source_id),
                "level": "DESCRIPTION",
                "claim": "Descrição fictícia",
                "locator": "Página 1",
                "excerpt": "Trecho fictício",
                "scope": "Exemplo",
                "period": "2025",
                "limitations": "Não causal",
            }
        ],
        "links": [
            {
                "evidence_id": str(evidence_id),
                "relation": "SUPPORTS",
                "justification": "Exemplo para teste",
            }
        ],
        "scope": "Exemplo",
        "period": "2025",
    }


def review_input():
    return {
        "expected_revision": 1,
        "decision": "ACCEPT",
        "rationale": "Conferência fictícia.",
        "references_checked": True,
        "scopes_checked": True,
        "counterpoints_checked": True,
        "limitations_checked": True,
    }


@pytest.mark.parametrize(
    "name,value",
    [
        ("author_id", str(uuid4())),
        ("reviewer_id", str(uuid4())),
        ("id", "example"),
        ("revision", 1),
        ("content_hash", "a" * 64),
        ("is_example", True),
        ("updated_at", "2026-10-14T12:00:00Z"),
        ("approved", True),
        ("publication_state", "REVIEWED"),
    ],
)
@pytest.mark.parametrize(
    "model,factory",
    [
        (NodeCreate, node_input),
        (EdgeCreate, edge_input),
        (GraphCreate, lambda: {"title": "Exemplo"}),
    ],
)
def test_managed_content_fields_rejected(model, factory, name, value):
    with pytest.raises(ValidationError):
        model.model_validate({"content": {**factory(), name: value}})


@pytest.mark.parametrize(
    "name,value",
    [
        ("reviewer_id", str(uuid4())),
        ("reviewed_at", "2026-10-14T12:00:00Z"),
        ("content_hash", "a" * 64),
        ("edge_id", "example"),
        ("approved", True),
    ],
)
def test_review_identity_and_binding_are_server_owned(name, value):
    with pytest.raises(ValidationError):
        EdgeReviewInput.model_validate({**review_input(), name: value})


@pytest.mark.parametrize("value", [True, 1.0, "1", 0, -1, 2147483648])
@pytest.mark.parametrize(
    "model,factory",
    [
        (NodeUpdate, lambda: {"content": node_input()}),
        (EdgeUpdate, lambda: {"content": edge_input()}),
        (GraphUpdate, lambda: {"content": {"title": "Exemplo"}}),
        (EdgeReviewInput, review_input),
        (EdgePublishInput, lambda: {"publication_state": "REVIEWED"}),
        (GraphPublishInput, dict),
    ],
)
def test_expected_revision_is_strict_positive_bounded_integer(value, model, factory):
    with pytest.raises(ValidationError):
        model.model_validate({**factory(), "expected_revision": value})


@pytest.mark.parametrize(
    "field",
    ["references_checked", "scopes_checked", "counterpoints_checked", "limitations_checked"],
)
@pytest.mark.parametrize("value", [1, "true", "false", None])
def test_checklist_only_accepts_booleans(field, value):
    with pytest.raises(ValidationError):
        EdgeReviewInput.model_validate({**review_input(), field: value})


@pytest.mark.parametrize(
    "extra",
    [
        {"sources": []},
        {"from_node": node_input()},
        {"coefficient": "1.2"},
        {"probability": "0.8"},
        {"magnitude": "5"},
    ],
)
def test_edge_rejects_embedded_references_and_numeric_effects(extra):
    with pytest.raises(ValidationError):
        EdgeContentInput.model_validate({**edge_input(), **extra})


def test_node_reference_types_and_managed_policy_number():
    invalid = [
        {**node_input(), "indicator_code": "selic"},
        {**node_input(), "policy_version_id": str(uuid4())},
        {**node_input(), "kind": "INDICATOR"},
        {**node_input(), "kind": "MEASURE"},
        {
            **node_input(),
            "kind": "MEASURE",
            "policy_version_id": str(uuid4()),
            "policy_version_number": 1,
        },
    ]
    for content in invalid:
        with pytest.raises(ValidationError):
            NodeContentInput.model_validate(content)
    assert (
        NodeContentInput.model_validate(
            {**node_input(), "kind": "INDICATOR", "indicator_code": "selic"}
        ).unit
        is None
    )


def test_nested_json_transport_preserves_uuid_and_enum_values():
    data = EdgeContentInput.model_validate(edge_input())
    assert data.evidence[0].source_id == data.source_ids[0]
    assert data.links[0].evidence_id == data.evidence[0].id
    assert EdgeContentInput.model_validate_json(data.model_dump_json()) == data


@pytest.mark.parametrize("change", [{"level": 1}, {"approved": True}, {"claim": 12}])
def test_nested_evidence_contract_remains_strict(change):
    content = edge_input()
    content["evidence"][0].update(change)
    with pytest.raises(ValidationError):
        EdgeContentInput.model_validate(content)


def test_duplicate_references_and_self_reference_rejected():
    content = edge_input()
    content["source_ids"] *= 2
    with pytest.raises(ValidationError):
        EdgeContentInput.model_validate(content)
    content = edge_input()
    content["to_node_version_id"] = content["from_node_version_id"]
    with pytest.raises(ValidationError):
        EdgeContentInput.model_validate(content)
    key = str(uuid4())
    for field in ("node_version_ids", "edge_version_ids"):
        with pytest.raises(ValidationError):
            GraphContentInput.model_validate({"title": "Exemplo", field: [key, key]})


@pytest.mark.parametrize("value", [None, "ACCEPT", "PUBLIC", True])
def test_publication_state_must_be_explicit_reviewed_or_disputed(value):
    with pytest.raises(ValidationError):
        EdgePublishInput.model_validate({"expected_revision": 1, "publication_state": value})


@pytest.mark.parametrize("field,count", [("node_version_ids", 201), ("edge_version_ids", 401)])
def test_graph_selection_limits(field, count):
    with pytest.raises(ValidationError):
        GraphContentInput.model_validate(
            {"title": "Exemplo", field: [str(uuid4()) for _ in range(count)]}
        )


def test_empty_graph_can_be_private_draft_and_decisions_preserve_dispute():
    assert (
        GraphCreate.model_validate(
            {"content": {"title": "Pesquisa em construção"}}
        ).content.edge_version_ids
        == ()
    )
    assert (
        EdgeReviewInput.model_validate({**review_input(), "decision": "DISPUTE"}).decision.value
        == "DISPUTE"
    )


def test_counterpoint_timestamp_requires_timezone():
    with pytest.raises(ValidationError):
        EdgeContentInput.model_validate(
            {**edge_input(), "counterpoint_searched_at": "2026-10-14T12:00:00"}
        )


@pytest.mark.parametrize("value", [True, False, 1, 1.5])
def test_counterpoint_timestamp_does_not_coerce_numeric_values(value):
    with pytest.raises(ValidationError):
        EdgeContentInput.model_validate({**edge_input(), "counterpoint_searched_at": value})
