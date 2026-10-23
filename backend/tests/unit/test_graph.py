"""Fictitious, isolated qualitative contracts; no claims about real policies/data."""

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.modules.contexts.context import EvidenceRelation
from app.modules.graphs.graph import (
    CounterpointStatus,
    EdgeAuthorship,
    EdgeReview,
    EdgeReviewDecision,
    EdgeStatus,
    GraphEdgeDraft,
    GraphNodeVersion,
    GraphSnapshot,
    assess_edge,
    edge_fingerprint,
    graph_fingerprint,
    inspect_topology,
)

NOW = datetime(2026, 10, 14, 12, tzinfo=UTC)
AUTHOR = UUID(int=1)
REVIEWER = UUID(int=2)


def node(key="origem", **changes):
    data = {
        "id": key,
        "revision": 1,
        "kind": "MECHANISM",
        "label": f"Exemplo fictício {key}",
        "definition": "Mecanismo didático sem relação com dado real.",
        "dimension": "Intensidade declarada do mecanismo fictício.",
    }
    data.update(changes)
    return GraphNodeVersion.model_validate_json(json.dumps(data))


def edge_data(**changes):
    data = {
        "id": "aresta-exemplo",
        "revision": 1,
        "author_id": str(AUTHOR),
        "updated_at": NOW.isoformat(),
        "from_node": node().model_dump(mode="json"),
        "to_node": node("destino").model_dump(mode="json"),
        "statement": "Aumento na dimensão de origem pode elevar a dimensão de destino.",
        "trigger": "INCREASE",
        "direction": "INCREASES",
        "horizon": "MEDIUM",
        "effect": "QUALITATIVE",
        "consensus": "SPECULATIVE",
        "authorship": "HUMAN",
        "sources": [
            {
                "id": str(UUID(int=3)),
                "title": "Documento integralmente fictício",
                "institution": "Instituição fictícia",
                "url": "https://example.invalid/documento",
                "terms": "Exemplo fictício; nenhum termo de instituição real inferido.",
                "terms_url": "https://example.invalid/termos",
                "published_date": "2026-01-01",
                "consulted_at": (NOW - timedelta(days=1)).isoformat(),
            }
        ],
        "evidence": [
            {
                "id": str(UUID(int=4)),
                "source_id": str(UUID(int=3)),
                "level": "HYPOTHESIS_SUPPORT",
                "claim": "Suporte hipotético sem validação causal.",
                "locator": "Seção fictícia A",
                "excerpt": "Trecho inteiramente inventado para teste.",
                "scope": "Universo fictício",
                "period": "Período didático",
                "limitations": "Sem validade empírica.",
            }
        ],
        "links": [
            {
                "evidence_id": str(UUID(int=4)),
                "relation": "SUPPORTS",
                "justification": "Justificativa declarada de exemplo.",
            }
        ],
        "premises": ["As demais condições fictícias são mantidas."],
        "scope": "Universo fictício",
        "period": "Período didático",
        "limitations": ["Não é evidência de relação real."],
        "unknowns": ["Não investigado: estabilidade do mecanismo."],
    }
    data.update(changes)
    return data


def edge(**changes):
    return GraphEdgeDraft.model_validate_json(json.dumps(edge_data(**changes)))


def review(row=None, **changes):
    row = row or edge()
    data = {
        "edge_id": row.id,
        "edge_revision": row.revision,
        "content_hash": edge_fingerprint(row),
        "reviewer_id": REVIEWER,
        "reviewed_at": NOW,
        "decision": EdgeReviewDecision.ACCEPT,
        "rationale": "Revisão declarada de exemplo, sem autenticação.",
        "references_checked": True,
        "scopes_checked": True,
        "counterpoints_checked": True,
        "limitations_checked": True,
    }
    data.update(changes)
    return EdgeReview(**data)


def graph(nodes=None, edges=(), **changes):
    data = {
        "id": UUID(int=5),
        "revision": 1,
        "author_id": AUTHOR,
        "updated_at": NOW,
        "title": "Grafo inteiramente fictício",
        "nodes": nodes if nodes is not None else (node(), node("destino")),
        "edges": edges,
    }
    data.update(changes)
    return GraphSnapshot(**data)


def test_typed_nodes_and_explicit_dimensions():
    for kind in ("MECHANISM", "AFFECTED_GROUP"):
        assert node(kind=kind).dimension
    assert node(kind="INDICATOR", indicator_code="indicador-ficticio").indicator_code
    assert (
        node(
            kind="MEASURE", policy_version_id=str(UUID(int=6)), policy_version_number=2
        ).policy_version_number
        == 2
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "INDICATOR"},
        {"kind": "MEASURE"},
        {"kind": "MEASURE", "policy_version_id": str(UUID(int=6))},
        {"kind": "MEASURE", "policy_version_number": 2},
        {"indicator_code": "indicador-ficticio"},
        {"policy_version_id": str(UUID(int=6))},
        {"policy_version_number": 2},
        {"dimension": " "},
        {"revision": True},
        {"revision": "1"},
        {"coefficient": 0.7},
    ],
)
def test_invalid_node_references_or_coercion(changes):
    with pytest.raises(ValidationError):
        node(**changes)


@pytest.mark.parametrize("field", ["sources", "evidence", "links"])
def test_evidence_minimum_is_structural(field):
    with pytest.raises(ValidationError):
        edge(**{field: []})


@pytest.mark.parametrize(
    "changes",
    [
        {"coefficient": "0.1"},
        {"magnitude": "10"},
        {"probability": 0.5},
        {"published": True},
        {"revision": True},
        {"revision": "1"},
        {"updated_at": "2026-10-14T12:00:00"},
        {"trigger": "ADOPTION"},
        {"direction": "POSITIVE"},
        {"statement": " "},
        {"contract_version": "9.0.0"},
        {"to_node": node().model_dump(mode="json")},
    ],
)
def test_rejects_quantification_coercion_and_ambiguous_inputs(changes):
    with pytest.raises(ValidationError):
        edge(**changes)


def test_measure_requires_adoption_and_indicator_is_declared_only():
    measure = node(kind="MEASURE", policy_version_id=str(UUID(int=6)), policy_version_number=2)
    with pytest.raises(ValidationError):
        edge(from_node=measure.model_dump(mode="json"))
    adopted = edge(from_node=measure.model_dump(mode="json"), trigger="ADOPTION")
    assert adopted.from_node.policy_version_number == 2
    hypothetical = node(kind="INDICATOR", indicator_code="ainda-nao-resolvido")
    assert edge(from_node=hypothetical.model_dump(mode="json")).from_node == hypothetical


@pytest.mark.parametrize("field", ["sources", "evidence", "links"])
def test_rejects_duplicate_ids(field):
    data = edge_data()
    data[field].append(dict(data[field][0]))
    with pytest.raises(ValidationError):
        edge(**data)


def test_rejects_missing_and_unused_sources_or_evidence():
    for field, key in (("evidence", "source_id"), ("links", "evidence_id")):
        data = edge_data()
        data[field][0][key] = str(UUID(int=999))
        with pytest.raises(ValidationError):
            edge(**data)
    for field in ("sources", "evidence"):
        data = edge_data()
        data[field].append(dict(data[field][0], id=str(UUID(int=888))))
        with pytest.raises(ValidationError):
            edge(**data)


def test_records_are_deeply_frozen_and_python_lists_not_coerced():
    row = edge()
    for obj, field, value in (
        (row, "statement", "Alterado"),
        (row.from_node, "dimension", "Alterado"),
        (row.sources[0], "title", "Alterado"),
        (row.evidence[0], "claim", "Alterado"),
        (row.links[0], "justification", "Alterado"),
    ):
        with pytest.raises(ValidationError):
            setattr(obj, field, value)
    with pytest.raises(ValidationError):
        GraphEdgeDraft.model_validate(row.model_copy(update={"premises": ["Mutável"]}))


def test_fingerprints_are_canonical_reproducible_and_bind_all_data():
    row = edge()
    assert edge_fingerprint(row) == edge_fingerprint(
        GraphEdgeDraft.model_validate_json(row.model_dump_json())
    )
    assert len(edge_fingerprint(row)) == 64
    original = edge_fingerprint(row)
    for update in (
        {"statement": "Outro enunciado fictício."},
        {"revision": 2},
        {"from_node": row.from_node.model_copy(update={"definition": "Definição alterada"})},
        {"sources": (row.sources[0].model_copy(update={"terms": "Outros termos"}),)},
        {"evidence": (row.evidence[0].model_copy(update={"locator": "Outra seção"}),)},
        {"links": (row.links[0].model_copy(update={"justification": "Outra justificativa"}),)},
        {"authorship": EdgeAuthorship.AI_ASSISTED},
    ):
        assert edge_fingerprint(row.model_copy(update=update)) != original


@pytest.mark.parametrize("operation", [edge_fingerprint, assess_edge])
def test_revalidates_model_copy_and_construct(operation):
    row = edge()
    malformed = row.model_copy(update={"revision": "2"})
    kwargs = {"assessed_at": NOW} if operation == assess_edge else {}
    with pytest.raises(ValidationError):
        operation(malformed, **kwargs)
    forged_node = row.from_node.model_copy(update={"policy_version_number": 2})
    with pytest.raises(ValidationError):
        operation(row.model_copy(update={"from_node": forged_node}), **kwargs)
    with pytest.raises(ValidationError):
        operation(GraphEdgeDraft.model_construct(**dict(row.model_dump(), revision="7")), **kwargs)


def test_assessment_never_certifies_or_publishes():
    result = assess_edge(edge(), assessed_at=NOW)
    assert result.status == EdgeStatus.NEEDS_REVIEW
    assert result.limitations
    assert not {"ready", "published", "publishable", "authorized"} & result.model_dump().keys()


@pytest.mark.parametrize(
    "field,code",
    [
        ("premises", "PREMISES_REQUIRED"),
        ("limitations", "LIMITATIONS_REQUIRED"),
        ("unknowns", "UNKNOWNS_REQUIRED"),
    ],
)
def test_missing_disclosures_block_even_matching_review(field, code):
    row = edge(**{field: []})
    result = assess_edge(row, assessed_at=NOW, review=review(row))
    assert result.status == EdgeStatus.INCOMPLETE
    assert code in result.missing


@pytest.mark.parametrize("relation", [EvidenceRelation.CONTEXT, EvidenceRelation.CHALLENGES])
def test_context_or_challenges_alone_never_count_as_support(relation):
    data = edge_data()
    data["links"][0]["relation"] = relation.value
    if relation == EvidenceRelation.CHALLENGES:
        data["counterpoint_status"] = "DOCUMENTED"
    assert "SUPPORTING_EVIDENCE_REQUIRED" in assess_edge(edge(**data), assessed_at=NOW).missing


@pytest.mark.parametrize("consensus", ["ESTABLISHED", "DEBATED"])
def test_counterpoint_is_required_for_stronger_consensus(consensus):
    row = edge(consensus=consensus)
    assert "COUNTERPOINT_REQUIRED" in assess_edge(row, assessed_at=NOW).missing
    human_note = edge(
        consensus=consensus, counterargument_note="Não investigado; revisão necessária."
    )
    assert (
        assess_edge(human_note, assessed_at=NOW, review=review(human_note)).status
        == EdgeStatus.INCOMPLETE
    )
    not_found = edge(
        consensus=consensus,
        counterpoint_status="NOT_FOUND",
        counterargument_note="Nenhum contraponto encontrado na busca declarada.",
        counterpoint_search_notes=["Consulta fictícia da seção B, sem resultados."],
        counterpoint_searched_at=NOW.isoformat(),
    )
    assert assess_edge(not_found, assessed_at=NOW).status == EdgeStatus.NEEDS_REVIEW
    data = edge_data(consensus=consensus)
    data["counterpoint_status"] = "DOCUMENTED"
    data["evidence"].append(dict(data["evidence"][0], id=str(UUID(int=77))))
    data["links"].append(
        dict(data["links"][0], evidence_id=str(UUID(int=77)), relation="CHALLENGES")
    )
    assert assess_edge(edge(**data), assessed_at=NOW).status == EdgeStatus.NEEDS_REVIEW


@pytest.mark.parametrize("case", ["edge_future", "source_after_edge", "publication_after_consult"])
def test_temporal_inconsistency_is_incomplete(case):
    data = edge_data()
    if case == "edge_future":
        data["updated_at"] = (NOW + timedelta(seconds=1)).isoformat()
        expected = "EDGE_DATE_IN_FUTURE"
    elif case == "source_after_edge":
        data["sources"][0]["consulted_at"] = (NOW + timedelta(seconds=1)).isoformat()
        expected = "SOURCE_CONSULTED_AFTER_EDGE"
    else:
        data["sources"][0]["published_date"] = "2026-10-14"
        expected = "SOURCE_PUBLICATION_AFTER_CONSULTATION"
    result = assess_edge(edge(**data), assessed_at=NOW)
    assert result.status == EdgeStatus.INCOMPLETE
    assert expected in result.missing


def test_explicit_timezone_required_and_normalized():
    with pytest.raises(ValidationError):
        assess_edge(edge(), assessed_at=NOW.replace(tzinfo=None))
    row = edge(updated_at="2026-10-14T09:00:00-03:00")
    assert row.updated_at == NOW
    assert edge_fingerprint(row) == edge_fingerprint(edge())


@pytest.mark.parametrize("authorship", ["HUMAN", "AI_ASSISTED"])
def test_both_authorships_require_distinct_review(authorship):
    row = edge(authorship=authorship)
    assert assess_edge(row, assessed_at=NOW).status == EdgeStatus.NEEDS_REVIEW
    assert assess_edge(row, assessed_at=NOW, review=review(row)).status == EdgeStatus.REVIEW_MATCHES
    assert (
        assess_edge(row, assessed_at=NOW, review=review(row, reviewer_id=AUTHOR)).status
        == EdgeStatus.REVIEW_STALE
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"edge_id": "outra-aresta"},
        {"edge_revision": 2},
        {"content_hash": "0" * 64},
        {"reviewed_at": NOW - timedelta(seconds=1)},
        {"reviewed_at": NOW + timedelta(seconds=1)},
    ],
)
def test_review_binding_rejects_wrong_identity_revision_hash_and_time(changes):
    assert (
        assess_edge(edge(), assessed_at=NOW, review=review(**changes)).status
        == EdgeStatus.REVIEW_STALE
    )


@pytest.mark.parametrize(
    "decision,status",
    [
        (EdgeReviewDecision.REQUEST_CHANGES, EdgeStatus.CHANGES_REQUESTED),
        (EdgeReviewDecision.DISPUTE, EdgeStatus.DISPUTE_MATCHES),
        (EdgeReviewDecision.REJECT, EdgeStatus.REJECTION_MATCHES),
    ],
)
def test_adverse_decisions_remain_distinct(decision, status):
    assert (
        assess_edge(
            edge(), assessed_at=NOW, review=review(decision=decision, references_checked=False)
        ).status
        == status
    )


@pytest.mark.parametrize(
    "check",
    ["references_checked", "scopes_checked", "counterpoints_checked", "limitations_checked"],
)
def test_all_checks_required_for_accept(check):
    assert (
        assess_edge(edge(), assessed_at=NOW, review=review(**{check: False})).status
        == EdgeStatus.NEEDS_REVIEW
    )


def test_reviews_revalidated_even_when_content_incomplete():
    row = edge(unknowns=[])
    invalid = review(row).model_copy(update={"references_checked": "true"})
    with pytest.raises(ValidationError):
        assess_edge(row, assessed_at=NOW, review=invalid)
    with pytest.raises(ValidationError):
        review(references_checked=1)
    with pytest.raises(ValidationError):
        review(role="ADMIN")


def test_edit_invalidates_review_even_without_revision_bump():
    row = edge()
    changed = row.model_copy(update={"from_node": node(definition="Outro conteúdo fictício")})
    assert (
        assess_edge(changed, assessed_at=NOW, review=review(row)).status == EdgeStatus.REVIEW_STALE
    )


def test_empty_graph_and_isolated_nodes_are_valid():
    assert inspect_topology(graph(nodes=())).isolated_nodes == ()
    assert inspect_topology(graph()).isolated_nodes == ("destino", "origem")


def test_graph_requires_exact_node_snapshots_and_unique_identities():
    row = edge()
    with pytest.raises(ValidationError):
        graph(nodes=(node(),), edges=(row,))
    for altered in (node(revision=2), node(definition="Mesmo ID e revisão, outro conteúdo")):
        with pytest.raises(ValidationError):
            graph(nodes=(altered, node("destino")), edges=(row,))
    with pytest.raises(ValidationError):
        graph(nodes=(node(), node(revision=2)))
    with pytest.raises(ValidationError):
        graph(edges=(row, row.model_copy(update={"revision": 2})))
    with pytest.raises(ValidationError):
        graph(edges=(row,), updated_at=NOW - timedelta(seconds=1))


@pytest.mark.parametrize("operation", [graph_fingerprint, inspect_topology])
def test_graph_operations_revalidate_forged_nested_data(operation):
    row = edge().model_copy(update={"magnitude": "10"})
    with pytest.raises(ValidationError):
        operation(graph().model_copy(update={"edges": (row,)}))


def test_graph_hash_includes_node_metadata_and_edge_full_content():
    original = graph(edges=(edge(),))
    assert graph_fingerprint(original) == graph_fingerprint(
        GraphSnapshot.model_validate_json(original.model_dump_json())
    )
    changed = graph(edges=(edge(statement="Texto alterado sem troca de IDs"),))
    assert graph_fingerprint(original) != graph_fingerprint(changed)
    assert graph_fingerprint(graph(nodes=(node(),))) != graph_fingerprint(
        graph(nodes=(node(definition="Definição alterada"),))
    )


def test_duplicates_conflicts_and_scope_normalization_are_deterministic():
    rows = (
        edge(id="b", scope="Universo  Fictício", period="Período  DIDÁTICO"),
        edge(id="a", scope="universo fictício"),
        edge(id="c", direction="DECREASES"),
        edge(id="d", direction="UNCERTAIN"),
        edge(id="e", scope="Outro universo"),
    )
    result = inspect_topology(graph(edges=rows))
    assert result.duplicate_edges == (("a", "b"),)
    assert result.conflicting_edges == (("a", "b", "c"),)
    assert result.cycle_components == ()
    assert result.isolated_nodes == ()
    assert inspect_topology(graph(edges=tuple(reversed(rows)))) == result


def test_cycle_components_use_identity_without_rejecting_feedback():
    rows = (
        edge(id="a"),
        edge(
            id="b",
            from_node=node("destino").model_dump(mode="json"),
            to_node=node().model_dump(mode="json"),
            direction="DECREASES",
        ),
    )
    assert inspect_topology(graph(edges=rows)).cycle_components == (("destino", "origem"),)
    newer_nodes = tuple(node(key, revision=2) for key in ("origem", "destino"))
    newer_rows = tuple(
        row.model_copy(
            update={
                "revision": 2,
                "from_node": row.from_node.model_copy(update={"revision": 2}),
                "to_node": row.to_node.model_copy(update={"revision": 2}),
            }
        )
        for row in rows
    )
    assert inspect_topology(graph(nodes=newer_nodes, edges=newer_rows)).cycle_components == (
        ("destino", "origem"),
    )


def test_long_dag_and_cycle_are_bounded_iterative_and_keep_isolated_nodes():
    nodes = tuple(node(f"n-{index}") for index in range(199)) + (node("isolado"),)
    rows = tuple(
        edge(
            id=f"e-{index}",
            from_node=nodes[index].model_dump(mode="json"),
            to_node=nodes[index + 1].model_dump(mode="json"),
        )
        for index in range(198)
    )
    result = inspect_topology(graph(nodes=nodes, edges=rows))
    assert result.cycle_components == ()
    assert result.isolated_nodes == ("isolado",)
    feedback = edge(
        id="feedback",
        from_node=nodes[198].model_dump(mode="json"),
        to_node=nodes[0].model_dump(mode="json"),
    )
    assert (
        len(inspect_topology(graph(nodes=nodes, edges=(*rows, feedback))).cycle_components[0])
        == 199
    )
    with pytest.raises(ValidationError):
        graph(nodes=(*nodes, node("excedente")))


def test_edge_count_cap_and_diagnostic_no_propagation():
    rows = tuple(edge(id=f"e-{index}") for index in range(400))
    diagnostics = inspect_topology(graph(edges=rows))
    assert len(diagnostics.duplicate_edges[0]) == 400
    assert not {"total", "result", "coefficient", "propagation"} & diagnostics.model_dump().keys()
    with pytest.raises(ValidationError):
        graph(edges=(*rows, edge(id="excedente")))


def test_source_snapshot_may_differ_between_edges_with_same_source_id():
    first = edge(id="a")
    later_source = first.sources[0].model_copy(
        update={"terms": "Metadados de outra consulta preservados na outra aresta."}
    )
    second = first.model_copy(update={"id": "b", "sources": (later_source,)})
    snapshot = graph(edges=(first, second))
    assert snapshot.edges[0].sources[0].id == snapshot.edges[1].sources[0].id
    assert edge_fingerprint(first) != edge_fingerprint(second)
    assert inspect_topology(snapshot).duplicate_edges == (("a", "b"),)


def test_disjoint_cycles_and_one_way_bridge_are_distinct_components():
    nodes = tuple(node(key) for key in ("a", "b", "c", "d", "isolado"))
    by_id = {item.id: item for item in nodes}
    edges = tuple(
        edge(
            id=f"e-{index}",
            from_node=by_id[start].model_dump(mode="json"),
            to_node=by_id[end].model_dump(mode="json"),
        )
        for index, (start, end) in enumerate(
            (("a", "b"), ("b", "a"), ("b", "c"), ("c", "d"), ("d", "c"))
        )
    )
    diagnostics = inspect_topology(graph(nodes=nodes, edges=edges))
    assert diagnostics.cycle_components == (("a", "b"), ("c", "d"))
    assert diagnostics.isolated_nodes == ("isolado",)


@pytest.mark.parametrize("field,cap", [("sources", 32), ("evidence", 64), ("links", 64)])
def test_reference_collection_limits_before_graph_traversal(field, cap):
    data = edge_data()
    data[field] = [data[field][0]] * (cap + 1)
    with pytest.raises(ValidationError):
        edge(**data)


@pytest.mark.parametrize(
    "changes",
    [
        {"counterpoint_status": "DOCUMENTED"},
        {"counterpoint_status": "NOT_RESEARCHED", "counterpoint_search_notes": ["Busca"]},
        {"counterpoint_status": "NOT_RESEARCHED", "counterpoint_searched_at": NOW.isoformat()},
        {"counterpoint_status": "UNKNOWN"},
        {"counterpoint_search_notes": ["Busca"] * 17},
        {"counterpoint_status": "NOT_FOUND", "counterpoint_searched_at": "2026-10-14T12:00:00"},
    ],
)
def test_counterpoint_declarations_must_be_structurally_consistent(changes):
    with pytest.raises(ValidationError):
        edge(**changes)


@pytest.mark.parametrize("status", ["NOT_RESEARCHED", "NOT_FOUND"])
def test_challenges_requires_documented_counterpoint_status(status):
    data = edge_data(counterpoint_status=status)
    data["links"][0]["relation"] = "CHALLENGES"
    with pytest.raises(ValidationError):
        edge(**data)


@pytest.mark.parametrize(
    "field,empty,code",
    [
        ("counterargument_note", "", "COUNTERPOINT_NOT_FOUND_NOTE_REQUIRED"),
        ("counterpoint_search_notes", [], "COUNTERPOINT_SEARCH_NOTES_REQUIRED"),
        ("counterpoint_searched_at", None, "COUNTERPOINT_SEARCH_DATE_REQUIRED"),
    ],
)
def test_not_found_requires_declared_search_and_note_even_with_matching_review(field, empty, code):
    data = {
        "counterpoint_status": "NOT_FOUND",
        "counterargument_note": "Não encontrado na busca declarada.",
        "counterpoint_search_notes": ["Consulta fictícia da seção B."],
        "counterpoint_searched_at": NOW.isoformat(),
    }
    data[field] = empty
    row = edge(**data)
    result = assess_edge(row, assessed_at=NOW, review=review(row))
    assert result.status == EdgeStatus.INCOMPLETE
    assert code in result.missing


def test_counterpoint_search_date_is_bound_to_edge_and_assessment():
    row = edge(
        counterpoint_status="NOT_FOUND",
        counterargument_note="Não encontrado na busca declarada.",
        counterpoint_search_notes=["Consulta fictícia da seção B."],
        counterpoint_searched_at=(NOW + timedelta(seconds=1)).isoformat(),
    )
    result = assess_edge(row, assessed_at=NOW, review=review(row))
    assert "COUNTERPOINT_SEARCH_AFTER_EDGE" in result.missing
    assert "COUNTERPOINT_SEARCH_IN_FUTURE" in result.missing
    result = assess_edge(row, assessed_at=NOW + timedelta(days=1), review=review(row))
    assert "COUNTERPOINT_SEARCH_AFTER_EDGE" in result.missing
    assert "COUNTERPOINT_SEARCH_IN_FUTURE" not in result.missing


def test_counterpoint_metadata_is_in_fingerprint_and_invalidates_prior_review():
    original = edge()
    changed = original.model_copy(update={"counterpoint_status": CounterpointStatus.NOT_FOUND})
    assert edge_fingerprint(original) != edge_fingerprint(changed)
    searched = edge(
        counterpoint_status="NOT_FOUND",
        counterargument_note="Não encontrado na busca declarada.",
        counterpoint_search_notes=["Consulta fictícia da seção B."],
        counterpoint_searched_at=NOW.isoformat(),
    )
    for update in (
        {"counterpoint_search_notes": ("Outra busca declarada.",)},
        {"counterpoint_searched_at": NOW - timedelta(minutes=1)},
        {"counterargument_note": "Nota alterada."},
    ):
        revised = searched.model_copy(update=update)
        assert edge_fingerprint(revised) != edge_fingerprint(searched)
        assert (
            assess_edge(revised, assessed_at=NOW, review=review(searched)).status
            == EdgeStatus.REVIEW_STALE
        )


def test_speculative_relation_may_explicitly_remain_unresearched():
    row = edge()
    assert row.counterpoint_status == CounterpointStatus.NOT_RESEARCHED
    assert assess_edge(row, assessed_at=NOW, review=review(row)).status == EdgeStatus.REVIEW_MATCHES


def test_cycle_is_only_structural_across_distinct_scopes_and_periods():
    first = edge(id="a", scope="Universo fictício A", period="2020")
    second = edge(
        id="b",
        from_node=node("destino").model_dump(mode="json"),
        to_node=node().model_dump(mode="json"),
        scope="Outro universo fictício B",
        period="2030",
    )
    result = inspect_topology(graph(edges=(first, second)))
    assert result.cycle_components == (("destino", "origem"),)
    assert any("ignoram escopo/período" in text for text in result.limitations)
