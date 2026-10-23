"""Fictitious evidence fixtures: no reviewed analysis of Brazil is created by these tests."""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.modules.contexts.context import (
    Consequence,
    ConsequenceKind,
    ContextDraft,
    ContextReview,
    ContextStatus,
    Counterpart,
    CounterpartAvailability,
    Evidence,
    EvidenceLevel,
    EvidenceLink,
    EvidenceRelation,
    Hypothesis,
    ObservationAnchor,
    ReviewDecision,
    SourceReference,
    assess_context,
    fingerprint,
)

NOW = datetime(2026, 10, 13, 12, tzinfo=UTC)


def uid(number):
    return UUID(int=number)


def context():
    return ContextDraft(
        id=uid(1),
        author_id=uid(2),
        revision=1,
        updated_at=NOW - timedelta(hours=2),
        title="Contexto fictício para teste",
        observation_summary="Descrição de teste, sem causa.",
        primary_observation_id=uid(3),
        observations=(
            ObservationAnchor(
                observation_id=uid(3),
                indicator_code="indicador-teste",
                revision=1,
                source_id=uid(4),
                value="0.00",
                unit="%",
                scope="Universo fictício",
                frequency="mensal",
                methodology="Método fictício",
                reference_date=date(2025, 8, 1),
                period_start=date(2025, 8, 1),
                period_end=date(2025, 8, 31),
                collected_at=NOW - timedelta(days=1),
            ),
        ),
        sources=(
            SourceReference(
                id=uid(4),
                title="Fonte fictícia",
                institution="Instituição de teste",
                url="https://example.org/estudo",
                terms="Termos fictícios",
                terms_url="https://example.org/termos",
                consulted_at=NOW - timedelta(days=1),
            ),
        ),
        counterparts=(
            Counterpart(
                indicator_code="contrapartida-teste",
                why_read_together="Comparar outro recorte.",
                availability=CounterpartAvailability.NOT_COLLECTED,
            ),
        ),
        evidence=(
            Evidence(
                id=uid(5),
                source_id=uid(4),
                level=EvidenceLevel.ASSOCIATION,
                claim="Associação descrita no exemplo.",
                locator="Seção fictícia 2",
                excerpt="Trecho fictício, não extraído de estudo real.",
                scope="Amostra fictícia",
                period="2025",
                limitations="Associação não identifica causa.",
            ),
        ),
        hypotheses=(
            Hypothesis(
                id="hipotese-a",
                explanation="Uma explicação possível de teste.",
                evidence=(
                    EvidenceLink(
                        evidence_id=uid(5),
                        relation=EvidenceRelation.SUPPORTS,
                        justification="Sustenta a hipótese sem provar causa.",
                    ),
                ),
                uncertainty="Pode haver fatores não observados.",
            ),
            Hypothesis(
                id="hipotese-b",
                explanation="Outra explicação possível de teste.",
                uncertainty="Não há estimativa para esta alternativa.",
            ),
        ),
        limitations=("Dados fictícios; sem avaliação política.",),
        unknowns=("Não se sabe qual mecanismo explicaria o exemplo.",),
    )


def changed(draft=None, **updates):
    payload = (draft or context()).model_dump()
    payload.update(updates)
    return ContextDraft.model_validate(payload)


def review(draft=None, **updates):
    draft = draft or context()
    payload = dict(
        context_id=draft.id,
        context_revision=draft.revision,
        content_hash=fingerprint(draft),
        reviewer_id=uid(6),
        reviewed_at=NOW - timedelta(hours=1),
        decision=ReviewDecision.ACCEPT,
        rationale="Conferência fictícia do contrato, não validação de verdade.",
        references_checked=True,
        scopes_checked=True,
        alternatives_checked=True,
        limitations_checked=True,
    )
    payload.update(updates)
    return ContextReview(**payload)


def assess(draft=None, **kwargs):
    return assess_context(draft or context(), assessed_at=NOW, **kwargs)


def test_draft_and_matched_review_never_mean_publication_or_proof_of_causality():
    assert assess().status == ContextStatus.NEEDS_REVIEW
    result = assess(review=review())
    assert result.status == ContextStatus.REVIEW_MATCHES and not result.missing
    assert len(result.limitations) == 4
    assert set(result.model_dump()) == {
        "contract_version",
        "content_hash",
        "status",
        "missing",
        "limitations",
    }
    assert not hasattr(result, "publishable") and not hasattr(result, "coefficient")


def test_incomplete_draft_can_exist_but_cannot_use_a_review():
    draft = ContextDraft(id=uid(1), author_id=uid(2), revision=1, updated_at=NOW)
    result = assess(draft, review=review(draft))
    assert result.status == ContextStatus.INCOMPLETE
    assert set(result.missing) == {
        "TITLE_REQUIRED",
        "OBSERVATION_SUMMARY_REQUIRED",
        "PRIMARY_OBSERVATION_REQUIRED",
        "COUNTERPART_REQUIRED",
        "ALTERNATIVE_HYPOTHESIS_REQUIRED",
        "HYPOTHESIS_EVIDENCE_REQUIRED",
        "LIMITATIONS_REQUIRED",
        "UNKNOWNS_REQUIRED",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "Alterado"),
        ("observation_summary", "Outra descrição"),
        ("id", uid(100)),
        ("author_id", uid(101)),
        ("revision", 2),
        ("updated_at", NOW - timedelta(minutes=30)),
        ("limitations", ("Limite alterado",)),
        ("unknowns", ("Outra lacuna",)),
    ],
)
def test_content_edit_copy_or_new_revision_invalidates_prior_review(field, value):
    result = assess(changed(**{field: value}), review=review())
    assert result.status == ContextStatus.REVIEW_STALE


@pytest.mark.parametrize(
    "section,index,field,value",
    [
        ("observations", 0, "revision", 2),
        ("observations", 0, "value", "-0.01"),
        ("observations", 0, "unit", "índice"),
        ("observations", 0, "scope", "Outro universo"),
        ("observations", 0, "methodology", "Método revisado"),
        ("observations", 0, "period_end", date(2025, 8, 30)),
        ("observations", 0, "reference_date", date(2025, 8, 2)),
        ("observations", 0, "collected_at", NOW - timedelta(days=2)),
        ("sources", 0, "url", "https://example.org/revisao"),
        ("sources", 0, "terms", "Termos revisados"),
        ("sources", 0, "institution", "Outra instituição"),
        ("sources", 0, "published_date", date(2025, 9, 1)),
        ("evidence", 0, "level", EvidenceLevel.DESCRIPTION),
        ("evidence", 0, "locator", "Seção 3"),
        ("evidence", 0, "excerpt", "Trecho revisado"),
        ("hypotheses", 1, "explanation", "Alternativa revisada"),
        ("counterparts", 0, "why_read_together", "Outra justificativa"),
    ],
)
def test_nested_semantics_are_bound_to_the_review(section, index, field, value):
    payload = context().model_dump()
    payload[section][index][field] = value
    draft = ContextDraft.model_validate(payload)
    assert assess(draft, review=review()).status == ContextStatus.REVIEW_STALE


def test_observed_and_projected_consequences_have_distinct_requirements():
    observed = Consequence(
        id="observada",
        kind=ConsequenceKind.OBSERVED,
        description="Consequência fictícia",
        limitations="Limite",
    )
    projected = Consequence(
        id="projetada",
        kind=ConsequenceKind.PROJECTED,
        description="Possibilidade futura",
        limitations="Limite",
    )
    result = assess(changed(consequences=(observed, projected)))
    assert result.status == ContextStatus.INCOMPLETE
    assert set(result.missing) == {
        "OBSERVED_REFERENCE_REQUIRED:observada",
        "PROJECTED_PREMISES_REQUIRED:projetada",
    }
    complete = changed(
        consequences=(
            observed.model_copy(update={"observation_ids": (uid(3),)}),
            projected.model_copy(update={"premises": ("Premissa declarada, sem cálculo.",)}),
        )
    )
    assert assess(complete).status == ContextStatus.NEEDS_REVIEW
    assert assess(complete, review=review()).status == ContextStatus.REVIEW_STALE
    assert assess(complete, review=review(complete)).status == ContextStatus.REVIEW_MATCHES
    assert context().observations[0].value == "0.00"  # Zero is an observed string, never missing.


def test_projection_premises_are_not_accepted_as_an_observed_consequence():
    row = Consequence(
        id="efeito",
        kind=ConsequenceKind.OBSERVED,
        description="Teste",
        observation_ids=(uid(3),),
        premises=("Hipótese",),
        limitations="Limite",
    )
    assert "OBSERVED_HAS_PROJECTION_PREMISES:efeito" in assess(changed(consequences=(row,))).missing


@pytest.mark.parametrize(
    "field,value",
    [
        ("context_id", uid(10)),
        ("context_revision", 2),
        ("content_hash", "0" * 64),
        ("reviewed_at", NOW + timedelta(seconds=1)),
        ("reviewed_at", NOW - timedelta(days=2)),
    ],
)
def test_review_rejects_wrong_target_hash_or_temporal_binding(field, value):
    assert assess(review=review(**{field: value})).status == ContextStatus.REVIEW_STALE


@pytest.mark.parametrize(
    "field",
    [
        "references_checked",
        "scopes_checked",
        "alternatives_checked",
        "limitations_checked",
    ],
)
def test_each_review_check_is_required(field):
    assert assess(review=review(**{field: False})).status == ContextStatus.NEEDS_REVIEW


def test_request_changes_is_preserved_instead_of_becoming_acceptance():
    assert assess(review=review(decision=ReviewDecision.REQUEST_CHANGES)).status == (
        ContextStatus.CHANGES_REQUESTED
    )


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///tmp/x",
        "https://user:pass@example.org",
        "https:///missing",
        "https://example.org:bad",
        "https://example.org:0",
        "https://example.org\n/x",
        "https://example.org/x y",
        "https://example.org\\evil",
    ],
)
def test_reference_url_is_only_stored_http_without_credentials_or_ambiguous_input(url):
    data = context().sources[0].model_dump()
    with pytest.raises(ValidationError):
        SourceReference(**{**data, "url": url})


@pytest.mark.parametrize("section", ["sources", "observations", "evidence", "hypotheses"])
def test_duplicate_ids_rejected(section):
    with pytest.raises(ValidationError):
        changed(**{section: (getattr(context(), section)[0],) * 2})


@pytest.mark.parametrize(
    "section,field",
    [
        ("observations", "source_id"),
        ("evidence", "source_id"),
    ],
)
def test_orphan_source_rejected(section, field):
    payload = context().model_dump()
    payload[section][0][field] = uid(999)
    with pytest.raises(ValidationError):
        ContextDraft.model_validate(payload)


def test_orphan_hypothesis_or_consequence_evidence_rejected():
    payload = context().model_dump()
    payload["hypotheses"][0]["evidence"][0]["evidence_id"] = uid(999)
    with pytest.raises(ValidationError):
        ContextDraft.model_validate(payload)
    with pytest.raises(ValidationError):
        changed(
            consequences=(
                Consequence(
                    id="efeito",
                    kind=ConsequenceKind.OBSERVED,
                    description="Teste",
                    evidence_ids=(uid(999),),
                    limitations="Limite",
                ),
            )
        )


def test_available_counterpart_must_reference_its_own_indicator():
    with pytest.raises(ValidationError):
        changed(
            counterparts=(
                Counterpart(
                    indicator_code="contrapartida-teste",
                    why_read_together="Teste",
                    availability=CounterpartAvailability.REFERENCED,
                    observation_ids=(uid(3),),
                ),
            )
        )
    missing = context().counterparts[0].model_dump()
    with pytest.raises(ValidationError):
        Counterpart(**{**missing, "observation_ids": (uid(3),)})


def test_same_indicator_is_not_a_counterpart_and_duplicate_wording_is_not_an_alternative():
    payload = context().model_dump()
    payload["counterparts"][0]["indicator_code"] = "indicador-teste"
    payload["hypotheses"][1]["explanation"] = "UMA  EXPLICAÇÃO POSSÍVEL DE TESTE."
    result = assess(ContextDraft.model_validate(payload))
    assert "DISTINCT_COUNTERPART_REQUIRED" in result.missing
    assert "ALTERNATIVE_HYPOTHESIS_REQUIRED" in result.missing


def test_naive_timestamps_and_unknown_contract_fields_are_rejected():
    with pytest.raises(ValidationError):
        changed(updated_at=NOW.replace(tzinfo=None))
    with pytest.raises(ValidationError):
        changed(causal_coefficient="0.5")
    with pytest.raises(ValidationError):
        changed(contract_version="2.0.0")
    with pytest.raises(ValueError):
        assess_context(context(), assessed_at=NOW.replace(tzinfo=None))


@pytest.mark.parametrize("value", [0.1, True, "NaN", "Infinity", "1e5", "1,23"])
def test_observation_values_preserve_exact_decimal_strings_and_reject_float_or_nonfinite(value):
    payload = context().model_dump()
    payload["observations"][0]["value"] = value
    with pytest.raises(ValidationError):
        ContextDraft.model_validate(payload)


def test_json_roundtrip_retains_hash_unknown_date_and_immutable_nested_records():
    draft = context()
    restored = ContextDraft.model_validate_json(draft.model_dump_json())
    assert restored == draft and fingerprint(restored) == fingerprint(draft)
    assert restored.sources[0].published_date is None
    with pytest.raises(ValidationError):
        draft.observations[0].value = "1"
    with pytest.raises(ValidationError):
        draft.title = "Outro"
    assert isinstance(draft.hypotheses, tuple) and isinstance(draft.hypotheses[0].evidence, tuple)


def test_unvalidated_copy_cannot_bypass_integrity_checks():
    with pytest.raises(ValidationError):
        fingerprint(context().model_copy(update={"revision": True}))
    with pytest.raises(ValidationError):
        assess(review=review().model_copy(update={"references_checked": "yes"}))


def test_context_time_and_source_time_cannot_silently_be_future_data():
    assert "CONTEXT_DATE_IN_FUTURE" in assess(changed(updated_at=NOW + timedelta(days=1))).missing
    payload = context().model_dump()
    payload["sources"][0]["consulted_at"] = NOW
    payload["sources"][0]["published_date"] = date(2027, 1, 1)
    payload["observations"][0]["collected_at"] = NOW
    result = assess(ContextDraft.model_validate(payload))
    assert set(result.missing) == {
        "SOURCE_CONSULTED_AFTER_CONTEXT",
        "SOURCE_PUBLICATION_AFTER_CONSULTATION",
        "OBSERVATION_COLLECTED_AFTER_CONTEXT",
    }


@pytest.mark.parametrize(
    "level,expected",
    [
        (EvidenceLevel.HYPOTHESIS_SUPPORT, ContextStatus.INCOMPLETE),
        (EvidenceLevel.DESCRIPTION, ContextStatus.REVIEW_MATCHES),
        (EvidenceLevel.ASSOCIATION, ContextStatus.REVIEW_MATCHES),
    ],
)
def test_hypothesis_alone_does_not_support_an_observed_consequence(level, expected):
    payload = context().model_dump()
    payload["evidence"][0]["level"] = level
    payload["consequences"] = (
        Consequence(
            id="efeito",
            kind=ConsequenceKind.OBSERVED,
            description="Exemplo",
            evidence_ids=(uid(5),),
            limitations="Descrição não implica causa.",
        ),
    )
    draft = ContextDraft.model_validate(payload)
    assert assess(draft, review=review(draft)).status == expected


@pytest.mark.parametrize("code", ["taxa_desemprego", "123-indicador", "a" * 100])
def test_indicator_codes_match_existing_catalog_contract(code):
    payload = context().model_dump()
    payload["observations"][0]["indicator_code"] = code
    draft = ContextDraft.model_validate(payload)
    assert draft.observations[0].indicator_code == code


@pytest.mark.parametrize("value", ["１２３", "١٢٣", "0.１２"])
def test_observation_decimal_strings_require_ascii_digits(value):
    payload = context().model_dump()
    payload["observations"][0]["value"] = value
    with pytest.raises(ValidationError):
        ContextDraft.model_validate(payload)


def test_catalog_metadata_is_not_truncated_by_the_context_contract():
    payload = context().model_dump()
    payload["sources"][0]["title"] = "s" * 300
    payload["observations"][0]["scope"] = "s" * 10000
    payload["observations"][0]["methodology"] = "m" * 20000
    draft = ContextDraft.model_validate(payload)
    assert len(draft.observations[0].methodology) == 20000
    assert assess(draft).status == ContextStatus.NEEDS_REVIEW
