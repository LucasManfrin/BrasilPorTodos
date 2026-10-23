import type { ContextContentInput, ContextRecord, ContextStatus } from "./types.ts";

export function blankContent(): ContextContentInput {
  return { title: "", observation_summary: "", primary_observation_id: null, observation_ids: [], source_ids: [], counterparts: [], evidence: [], hypotheses: [], consequences: [], limitations: [], unknowns: [] };
}
/** Return only editable fields. Server-resolved values, identities and review never enter input. */
export function recordToContent(record: ContextRecord): ContextContentInput {
  const c = record.content;
  return structuredClone({ title: c.title, observation_summary: c.observation_summary, primary_observation_id: c.primary_observation_id, observation_ids: c.observations.map(o => o.observation_id), source_ids: c.sources.map(s => s.id), counterparts: c.counterparts, evidence: c.evidence, hypotheses: c.hypotheses, consequences: c.consequences, limitations: c.limitations, unknowns: c.unknowns });
}
export function safeReferenceUrl(value: string): string | null {
  if (/[\\\s\u0000-\u0020\u007f]/.test(value)) return null;
  try { const u = new URL(value); return ["http:", "https:"].includes(u.protocol) && !!u.hostname && !u.username && !u.password ? value : null; } catch { return null; }
}
export function contextPath(id: string, revision?: number) {
  return `/contextos/${encodeURIComponent(id)}${revision ? `/versoes/${revision}` : ""}`;
}
export function anchorMismatch(record: ContextRecord, code: string, latestId?: string | null) {
  if (!latestId) return false;
  const anchor = record.content.observations.find(o => o.observation_id === record.content.primary_observation_id && o.indicator_code === code);
  return !!anchor && anchor.observation_id !== latestId;
}
const statuses: Record<ContextStatus, string> = { INCOMPLETE: "Incompleto", NEEDS_REVIEW: "Aguarda revisão", REVIEW_STALE: "Revisão de outra versão", CHANGES_REQUESTED: "Ajustes pedidos", REVIEW_MATCHES: "Revisão correspondente" };
export const statusLabel = (status: ContextStatus) => statuses[status] ?? "Estado não reconhecido";
const missing: Record<string, string> = {
 TITLE_REQUIRED: "Título", OBSERVATION_SUMMARY_REQUIRED: "Resumo do dado", PRIMARY_OBSERVATION_REQUIRED: "Observação principal", COUNTERPART_REQUIRED: "Contrapartida", DISTINCT_COUNTERPART_REQUIRED: "Contrapartida de outro indicador", ALTERNATIVE_HYPOTHESIS_REQUIRED: "Duas explicações diferentes", HYPOTHESIS_EVIDENCE_REQUIRED: "Evidência vinculada a uma hipótese", LIMITATIONS_REQUIRED: "Limitações", UNKNOWNS_REQUIRED: "O que ainda não se sabe", HUMAN_REVIEW_REQUIRED: "Revisão humana", REVIEW_NOT_BOUND_TO_CURRENT_CONTENT: "Nova revisão para o conteúdo atual", REVIEW_REQUESTED_CHANGES: "Ajustes solicitados na revisão", REVIEW_CHECKLIST_INCOMPLETE: "Conferências da revisão", OBSERVED_REFERENCE_REQUIRED: "Referência para a consequência observada", OBSERVED_HAS_PROJECTION_PREMISES: "Separar premissas da consequência observada", PROJECTED_PREMISES_REQUIRED: "Premissas da projeção", CONSEQUENCE_LIMITATIONS_REQUIRED: "Limites da consequência", CONTEXT_DATE_IN_FUTURE: "Conferir data do contexto", SOURCE_CONSULTED_AFTER_CONTEXT: "Conferir data de consulta", OBSERVATION_COLLECTED_AFTER_CONTEXT: "Conferir data de coleta", SOURCE_PUBLICATION_AFTER_CONSULTATION: "Conferir data de publicação da fonte", OBSERVED_PERIOD_AFTER_COLLECTION: "Conferir período da observação"
};
export const missingLabel = (code: string) => missing[code.split(":")[0]] ?? "Conferência adicional necessária";
export const relationLabel = (value: string) => ({ SUPPORTS: "Apoia a hipótese", CHALLENGES: "Contesta a hipótese", CONTEXT: "Ajuda a contextualizar" })[value] ?? "Relação não informada";
export const evidenceLevelLabel = (value: string) => ({ DESCRIPTION: "Descrição", ASSOCIATION: "Associação", HYPOTHESIS_SUPPORT: "Suporte à hipótese" })[value] ?? "Nível não informado";
export function positivePage(raw: string | undefined): number { const n = Number(raw); return Number.isInteger(n) && n > 0 && n <= 2147483647 ? n : 1; }
