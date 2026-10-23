"use client";
import { useState } from "react";
import { useAuth } from "@/features/auth/provider";
import type { Baseline, Plan, Policy } from "@/lib/types";
export function DraftBaselineControl({
  kind,
  id,
  disabled,
  onUpdated,
}: {
  kind: "policies" | "plans";
  id?: string;
  disabled: boolean;
  onUpdated: (baseline: Baseline | null) => void;
}) {
  const { request } = useAuth();
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  if (!id) return null;
  return (
    <div className="draft-baseline-control">
      <button
        type="button"
        className="button secondary"
        disabled={disabled || busy}
        onClick={async () => {
          setBusy(true);
          setMessage("");
          try {
            const result = await request<Policy | Plan>(`${kind}/${id}`, {
              method: "PATCH",
              body: JSON.stringify({ refresh_baseline: true }),
            });
            onUpdated(result.data.version.baseline_snapshot ?? null);
            setMessage(
              "Base atual adotada neste rascunho. Revise suas premissas; versões publicadas continuam preservadas.",
            );
          } catch (e) {
            setMessage(
              e instanceof Error ? e.message : "Não deu para atualizar a base.",
            );
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Atualizando…" : "Adotar dados atuais neste rascunho"}
      </button>
      {message && <p role="status">{message}</p>}
    </div>
  );
}
