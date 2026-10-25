import type { IdeaInput } from "./state";

export type IdeaScreen = "quick" | "choice" | "manual" | "guided";
type IdeaQuery = Record<string, string | string[] | undefined>;

/** Old explicit mode links still resume preparation; a plain idea URL stays simple. */
export function ideaScreen(query: IdeaQuery): IdeaScreen {
  if (query.modo === "guiado") return "guided";
  if (query.modo === "manual") return "manual";
  return query.desenvolver === "proposta" ? "choice" : "quick";
}

export function ideaDevelopmentPath(id: string, mode?: "manual" | "guided"): string {
  const query = new URLSearchParams({ desenvolver: "proposta" });
  if (mode) query.set("modo", mode === "guided" ? "guiado" : "manual");
  return `/painel/ideias/${encodeURIComponent(id)}?${query}`;
}

/** Only the two quick fields change. Existing estimates, sources and provenance survive. */
export function updateQuickIdea(input: IdeaInput, title: string, summary: string): IdeaInput {
  return {
    ...input,
    title: title.trim(),
    summary: summary.trim(),
    content: { ...input.content, title: title.trim(), summary: summary.trim() },
  };
}


/** Skip the two saved quick fields only on the first entry into the guided path. */
export function guidedEntryQuestion({ current, started, saved, title, summary }: {
  current: number; started: boolean; saved: boolean; title: string; summary: string;
}): number {
  return !started && saved && current === 0 && Boolean(title.trim() && summary.trim()) ? 2 : current;
}
