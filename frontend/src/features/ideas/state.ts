import type { Funding, Impact, Source } from "../../lib/types";

export type IdeaContent = {
  title: string; summary: string; problem: string; proposal: string; category: string;
  implementation_start: number | null; implementation_end: number | null;
  financial_impact_status: string; impact_justification: string | null;
  change_summary: string | null; impacts: Impact[]; fundings: Funding[];
  sources: { source_id: string; usage_description: string }[];
};
export type IdeaInput = {
  title: string; summary: string; content: IdeaContent; beneficiaries: string;
  adversely_affected: string; risks: string; assisted_fields: string[];
};
export type Idea = IdeaInput & {
  id: string; status: "PRIVATE" | "SHARED" | "PROMOTED" | "ARCHIVED";
  author: { name: string; username: string }; created_at: string; updated_at: string;
  promoted_policy_id: string | null; checklist: { key: string; label: string; complete: boolean }[];
  source_snapshots: Source[];
  origin_attribution?: { idea_id: string; title: string; author: { name: string; username: string }; source_snapshots: Source[] } | null;
};
export type GuideStep = { id: string; field: string; question: string };
export type Guidance = { version: string; steps: GuideStep[]; ai_available: boolean; provider: string; privacy: { log_retention_days: number; notice: string } };
export type Organized = { step_id: string; question: string; organized_text: string; assisted_by_ai: boolean; unknown: boolean; script_version: string; original_text?: string; rewritten?: boolean; suggestions?: string[]; open_questions?: string[]; call_id?: string | null };
/** Send only bounded excerpts of confirmed answers, never unsaved suggestions or numeric fields. */
export function guidanceContext(input: IdeaInput): Record<string, string> {
  return Object.fromEntries(["title", "summary", "problem", "proposal", "beneficiaries", "adversely_affected", "risks", "impact_justification"]
    .map(field => [field, readAnswer(input, field).trim().slice(0, 1500)])
    .filter(([, value]) => value));
}
export function confirmedGuidanceText(result: Organized, selected: number[], field: string): string {
  const accepted = [...new Set(selected)].filter(index => Number.isInteger(index) && index >= 0 && index < (result.suggestions?.length ?? 0));
  const text = [result.organized_text, ...accepted.map(index => `Sugestão de IA a avaliar: ${result.suggestions![index]}`)].join("\n\n");
  const limit = field === "title" ? 200 : field === "summary" ? 5000 : 10000;
  if (text.length > limit) throw new Error("O texto ficou longo demais para esta etapa. Selecione menos sugestões ou revise a resposta.");
  return text;
}
/** Compare actual text rather than claiming a rewrite from provider metadata alone. */
export function reviewGuidance(result: Organized, answer: string) {
  const original = result.original_text ?? answer;
  const normalize = (value: string) => value.trim().replace(/\s+/g, " ");
  const changed = normalize(original) !== normalize(result.organized_text);
  const kind = result.unknown ? "unknown" : !result.assisted_by_ai ? "literal" : changed ? "rewritten" : "unchanged";
  return { original, suggestion: result.organized_text, kind };
}
export function emptyIdea(): IdeaInput {
  return { title: "", summary: "", beneficiaries: "", adversely_affected: "", risks: "", assisted_fields: [], content: {
    title: "", summary: "", problem: "", proposal: "", category: "OTHER", implementation_start: null,
    implementation_end: null, financial_impact_status: "NOT_ESTIMATED", impact_justification: null,
    change_summary: null, impacts: [], fundings: [], sources: [],
  } };
}
/** Both paths write the same value, and confirmation is the only guided write. */
export function confirmAnswer(input: IdeaInput, field: string, answer: string, assisted: boolean, unknown = false): IdeaInput {
  if (unknown) return input;
  const direct = ["title", "summary", "beneficiaries", "adversely_affected", "risks"];
  const nested = ["problem", "proposal", "impact_justification"];
  let next = input;
  if (direct.includes(field)) next = { ...input, [field]: answer };
  else if (nested.includes(field)) next = { ...input, content: { ...input.content, [field]: answer } };
  else if (field === "funding" || field === "fundings") next = { ...input, content: { ...input.content, fundings: [{ funding_type: "OTHER", amount: null, year: null, description: answer }] } };
  if (next === input) return input;
  return { ...next, assisted_fields: assisted ? [...new Set([...input.assisted_fields, field])] : input.assisted_fields };
}
export function normalizedIdea(input: IdeaInput): IdeaInput {
  return { ...input, title: input.title.trim(), summary: input.summary.trim(), content: {
    ...input.content, title: input.title.trim(), summary: input.summary.trim(),
    impacts: input.content.impacts.map((row) => ({ ...row, amount: normalizedMoney(row.amount) })),
    fundings: input.content.fundings.map((row) => ({ ...row, amount: row.amount ? normalizedMoney(row.amount) : null })),
  } };
}
export function normalizedMoney(value: string): string {
  const result = value.includes(",") ? value.replaceAll(".", "").replace(",", ".") : value;
  if (!/^\d+(\.\d{1,2})?$/.test(result)) throw new Error("Informe valores não negativos com até duas casas decimais. Campos de impacto incompletos precisam ser preenchidos ou removidos para salvar.");
  return result;
}
export function ideaInput(record: Idea): IdeaInput {
  return { title: record.title, summary: record.summary, content: record.content, beneficiaries: record.beneficiaries,
    adversely_affected: record.adversely_affected, risks: record.risks, assisted_fields: record.assisted_fields };
}
export function canSave(input: IdeaInput): boolean { return Boolean(input.title.trim() && input.summary.trim()); }
export function readAnswer(input: IdeaInput, field: string): string {
  if (field === "funding" || field === "fundings") return input.content.fundings.map((item) => item.description).join("\n");
  const value = field in input ? input[field as keyof IdeaInput] : input.content[field as keyof IdeaContent];
  return typeof value === "string" ? value : "";
}
