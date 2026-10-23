"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/provider";
import type { Idea } from "@/features/ideas/state";
type Kind = "ideas" | "policies" | "plans" | "sources" | "contexts";
type Summary = { total: number | null; error: string };
type Overview = { summaries: Partial<Record<Kind, Summary>>; ideas: Idea[]; loading: boolean; refresh: () => void };
const PanelContext = createContext<Overview>({ summaries: {}, ideas: [], loading: true, refresh: () => {} });
export function PanelDataProvider({ children }: { children: ReactNode }) {
  const { user, request } = useAuth();
  const pathname = usePathname();
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState<{ owner: string; route: string; revision: number; summaries: Partial<Record<Kind, Summary>>; ideas: Idea[] } | null>(null);
  useEffect(() => {
    if (!user) return;
    let active = true;
    const controller = new AbortController();
    const kinds: Kind[] = ["ideas", "policies", "plans", "sources", "contexts"];
    Promise.all(kinds.map(async kind => {
      try {
        const response = await request<unknown[]>(`${kind}/mine?page=1&page_size=${kind === "ideas" ? 20 : 1}`, { signal: controller.signal });
        return { kind, total: response.pagination?.total ?? null, rows: response.data, error: "" };
      } catch (e) { return { kind, total: null, rows: [], error: e instanceof Error ? e.message : "Não foi possível consultar." }; }
    })).then(rows => {
      if (active) setResult({ owner: user.id, route: pathname, revision, summaries: Object.fromEntries(rows.map(r => [r.kind, { total: r.total, error: r.error }])), ideas: (rows.find(r => r.kind === "ideas")?.rows ?? []) as Idea[] });
    });
    return () => { active = false; controller.abort(); };
  }, [user, request, pathname, revision]);
  const current = result?.owner === user?.id && result?.route === pathname && result?.revision === revision ? result : null;
  return <PanelContext.Provider value={{ summaries: current?.summaries ?? {}, ideas: current?.ideas ?? [], loading: !current, refresh: () => setRevision(v => v + 1) }}>{children}</PanelContext.Provider>;
}
export function usePanelData() { return useContext(PanelContext); }
