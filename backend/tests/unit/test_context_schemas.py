"""Transport inputs preserve strict authority boundaries and contract records."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.contexts.schemas import (
    ContextContentInput,
    ContextCreate,
    ContextPublishInput,
    ContextReviewInput,
    ContextUpdate,
)


def review_input():
    return {
        "expected_revision": 1,
        "decision": "ACCEPT",
        "rationale": "Conferência fictícia.",
        "references_checked": True,
        "scopes_checked": True,
        "alternatives_checked": True,
        "limitations_checked": True,
    }


@pytest.mark.parametrize(
    "name,value",
    [
        ("author_id", str(uuid4())),
        ("reviewer_id", str(uuid4())),
        ("content_hash", "a" * 64),
        ("approved", True),
        ("revision", 4),
        ("is_example", True),
        ("updated_at", "2026-10-13T12:00:00Z"),
    ],
)
def test_content_cannot_assign_server_authority(name, value):
    with pytest.raises(ValidationError):
        ContextCreate.model_validate({"content": {name: value}})


@pytest.mark.parametrize(
    "name,value",
    [
        ("reviewer_id", str(uuid4())),
        ("content_hash", "a" * 64),
        ("reviewed_at", "2026-10-13T12:00:00Z"),
        ("approved", True),
    ],
)
def test_review_cannot_supply_identity_or_approval(name, value):
    with pytest.raises(ValidationError):
        ContextReviewInput.model_validate({**review_input(), name: value})


@pytest.mark.parametrize("value", [True, 1.0, "1", 0, -1, 2147483648])
@pytest.mark.parametrize(
    "model,body",
    [
        (ContextUpdate, {"content": {}}),
        (ContextPublishInput, {}),
        (ContextReviewInput, review_input()),
    ],
)
def test_expected_revision_is_required_strict_bounded_integer(value, model, body):
    with pytest.raises(ValidationError):
        model.model_validate({**body, "expected_revision": value})


@pytest.mark.parametrize(
    "field", ["references_checked", "scopes_checked", "alternatives_checked", "limitations_checked"]
)
@pytest.mark.parametrize("value", [1, "true", "false", None])
def test_checklist_requires_real_booleans(field, value):
    with pytest.raises(ValidationError):
        ContextReviewInput.model_validate({**review_input(), field: value})


def test_json_nested_uuid_enum_and_tuple_transport():
    anchor, source, evidence = uuid4(), uuid4(), uuid4()
    data = ContextContentInput.model_validate(
        {
            "primary_observation_id": str(anchor),
            "observation_ids": [str(anchor)],
            "source_ids": [str(source)],
            "counterparts": [
                {
                    "indicator_code": "selic",
                    "why_read_together": "Recorte fictício.",
                    "availability": "NOT_COLLECTED",
                }
            ],
            "evidence": [
                {
                    "id": str(evidence),
                    "source_id": str(source),
                    "level": "DESCRIPTION",
                    "claim": "Teste",
                    "locator": "Tabela",
                    "excerpt": "Trecho",
                    "scope": "Brasil",
                    "period": "2025",
                    "limitations": "Exemplo",
                }
            ],
            "hypotheses": [
                {
                    "id": "alternativa",
                    "explanation": "Hipótese fictícia",
                    "uncertainty": "Não confirmada",
                    "evidence": [
                        {
                            "evidence_id": str(evidence),
                            "relation": "CONTEXT",
                            "justification": "Exemplo",
                        }
                    ],
                }
            ],
        }
    )
    assert data.primary_observation_id == anchor
    assert data.observation_ids == (anchor,)
    assert data.evidence[0].source_id == source
    assert data.hypotheses[0].evidence[0].evidence_id == evidence
    assert ContextContentInput.model_validate_json(data.model_dump_json()) == data


@pytest.mark.parametrize("field", ["source_ids", "observation_ids"])
def test_reference_duplicates_rejected(field):
    key = str(uuid4())
    with pytest.raises(ValidationError):
        ContextContentInput.model_validate({field: [key, key]})


def test_primary_observation_must_be_selected():
    with pytest.raises(ValidationError):
        ContextContentInput.model_validate({"primary_observation_id": str(uuid4())})


def test_nested_unknown_and_numeric_enum_rejected():
    for extra in ({"approved": True}, {"availability": 1}):
        with pytest.raises(ValidationError):
            ContextContentInput.model_validate(
                {
                    "counterparts": [
                        {
                            "indicator_code": "selic",
                            "why_read_together": "Teste",
                            "availability": "NOT_COLLECTED",
                            **extra,
                        }
                    ]
                }
            )


def test_empty_draft_and_explicit_unknown_are_valid():
    draft = ContextCreate.model_validate({"content": {"unknowns": ["Não sabemos ainda."]}})
    assert draft.content.title == ""
    assert draft.content.observation_ids == ()
    assert draft.content.unknowns == ("Não sabemos ainda.",)
