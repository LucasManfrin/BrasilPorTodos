import type { GraphEdge, GraphNode, GraphRecord, NodeKind } from "./types";

// A local teaching scene, never a seed, public collection or researched claim.
// Reserved .invalid URLs cannot be mistaken for an official source.
const timestamp = "2026-10-15T12:00:00Z";
const author = "00000000-0000-4000-8000-000000000001";
const definitions: [string, string, NodeKind, string][] = [
  ["medida", "Medida de exemplo", "MEASURE", "Adoção de uma medida imaginária em um serviço que não existe."],
  ["capacidade", "Capacidade de atendimento", "MECHANISM", "Quantidade de atendimentos que o serviço imaginário consegue oferecer."],
  ["acesso", "Acesso ao serviço", "MECHANISM", "Possibilidade de chegar ao serviço imaginário."],
  ["tempo", "Tempo de espera", "INDICATOR", "Indicador didático do tempo aguardado no sistema imaginário; sem medição ou catálogo oficial."],
  ["equipe", "Equipe disponível", "MECHANISM", "Disponibilidade de equipe no exemplo."],
  ["preparo", "Preparo da equipe", "MECHANISM", "Preparação para as tarefas do exemplo."],
  ["qualidade", "Qualidade do atendimento", "MECHANISM", "Característica imaginária da entrega, sem medição real."],
  ["demanda", "Procura pelo serviço", "MECHANISM", "Volume de procura no cenário imaginário."],
  ["cobertura", "Cobertura do serviço", "INDICATOR", "Indicador didático de alcance no cenário fictício; sem medição ou catálogo oficial."],
  ["distancia", "Distância até o serviço", "MECHANISM", "Distância abstrata percorrida no exemplo."],
  ["informacao", "Informação disponível", "MECHANISM", "Disponibilidade de informação no cenário fictício."],
  ["coordenacao", "Coordenação das equipes", "MECHANISM", "Coordenação das atividades do exemplo."],
  ["continuidade", "Continuidade do serviço", "MECHANISM", "Continuidade imaginária do atendimento."],
  ["barreiras", "Barreiras de acesso", "MECHANISM", "Obstáculos abstratos dentro do cenário fictício."],
  ["grupo-a", "Acesso do grupo A", "AFFECTED_GROUP", "Condição de acesso do grupo A, inteiramente fictício."],
  ["grupo-b", "Acesso do grupo B", "AFFECTED_GROUP", "Condição de acesso do grupo B, inteiramente fictício."],
  ["grupo-c", "Acesso do grupo C", "AFFECTED_GROUP", "Condição de acesso do grupo C, inteiramente fictício."],
  ["lacuna", "O que ainda falta saber", "MECHANISM", "Conceito sem ligação: ilustra uma lacuna, sem inventar uma explicação."],
];
const nodes: GraphNode[] = definitions.map(([id, label, kind, definition]) => ({
  id: `demo-${id}`, revision: 1, label, kind, definition, dimension: definition,
  unit: null, indicator_code: kind === "INDICATOR" ? `demo-${id}` : null,
  policy_version_id: kind === "MEASURE" ? "00000000-0000-4000-8000-000000000002" : null,
  policy_version_number: kind === "MEASURE" ? 1 : null,
}));
const pairs: [number, number, GraphEdge["direction"]][] = [
  [0, 1, "INCREASES"], [0, 4, "UNCERTAIN"], [0, 8, "INCREASES"],
  [4, 1, "INCREASES"], [5, 6, "INCREASES"], [1, 3, "DECREASES"],
  [1, 2, "INCREASES"], [2, 7, "INCREASES"], [7, 3, "INCREASES"],
  [3, 14, "DECREASES"], [3, 15, "UNCERTAIN"], [8, 9, "DECREASES"],
  [9, 13, "INCREASES"], [13, 2, "DECREASES"], [10, 2, "INCREASES"],
  [11, 1, "INCREASES"], [11, 12, "INCREASES"], [12, 6, "UNCERTAIN"],
  [6, 7, "INCREASES"], [8, 16, "UNCERTAIN"], [2, 14, "INCREASES"],
  [2, 15, "INCREASES"], [10, 16, "UNCERTAIN"], [7, 4, "UNCERTAIN"],
];
const source = {
  id: "00000000-0000-4000-8000-000000000003", title: "Roteiro fictício desta demonstração",
  institution: "Demonstração local · não é instituição real", url: "https://example.invalid/demonstracao",
  terms: "Material autoral fictício, usado apenas para ensinar a navegação. Não constitui evidência real.",
  terms_url: "https://example.invalid/termos", published_date: null, consulted_at: timestamp,
};
const edges: GraphEdge[] = pairs.map(([from, to, direction], i) => {
  const evidenceId = `00000000-0000-4000-8000-${String(i + 10).padStart(12, "0")}`;
  return {
    contract_version: "1.0.0", id: `demo-ligacao-${i + 1}`, revision: 1,
    author_id: author, updated_at: timestamp, from_node: nodes[from], to_node: nodes[to],
    statement: `Hipótese fictícia: ${nodes[from].label.toLocaleLowerCase("pt-BR")} e ${nodes[to].label.toLocaleLowerCase("pt-BR")} estão ligados neste exemplo. Não é uma afirmação sobre o Brasil.`,
    trigger: nodes[from].kind === "MEASURE" ? "ADOPTION" : "INCREASE", direction,
    horizon: i % 3 === 0 ? "LONG" : i % 3 === 1 ? "SHORT" : "MEDIUM",
    effect: "QUALITATIVE", consensus: "SPECULATIVE", authorship: "AI_ASSISTED",
    sources: [{ ...source }],
    evidence: [{ id: evidenceId, source_id: source.id, level: "DESCRIPTION", claim: "Ligação inventada para demonstrar a interface.", locator: `Exemplo visual, ligação ${i + 1}`, excerpt: "Esta relação pertence a um cenário imaginário. Não há evidência empírica apresentada.", scope: "Serviço imaginário; nenhum recorte brasileiro.", period: "Sem período observado", limitations: "Trecho fictício: não sustenta uma hipótese real." }],
    links: [{ evidence_id: evidenceId, relation: "CONTEXT", justification: "Somente contexto didático; não é apoio científico nem revisão." }],
    premises: ["Todas as relações foram inventadas para demonstrar a navegação."],
    scope: "Cenário imaginário, sem correspondência com serviço real.", period: "Sem período observado",
    limitations: ["Não há pesquisa, magnitude, probabilidade nem efeito fiscal neste exemplo."],
    unknowns: ["Esta cena não permite concluir o que aconteceria no mundo real."],
    counterpoint_status: "NOT_RESEARCHED", counterpoint_search_notes: [], counterpoint_searched_at: null,
    counterargument_note: "Não pesquisado: demonstração fictícia, sem revisão humana.",
  };
});

export const DEMO_GRAPH: GraphRecord = {
  id: "demonstracao-local", revision: 1, version_id: "demonstracao-local-v1",
  content_hash: "demonstracao-sem-hash-de-publicacao", published_at: null, is_example: true,
  content: { contract_version: "1.0.0", id: "00000000-0000-4000-8000-000000000004", revision: 1, author_id: author, updated_at: timestamp, title: "Uma ideia. Muitas conexões.", nodes, edges },
  publications: [],
  topology: { duplicate_edges: [], conflicting_edges: [], cycle_components: [["demo-acesso", "demo-capacidade", "demo-demanda", "demo-equipe"]], isolated_nodes: ["demo-lacuna"], limitations: ["Cena fictícia e sem revisão humana. Ciclos visuais não comprovam realimentação econômica. Não soma efeitos nem calcula impacto fiscal."] },
};
