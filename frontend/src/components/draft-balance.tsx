"use client";
import type { PlanItem } from "@/lib/types";
import { cents, decimal, ImpactMeter } from "./impact-meter";
import { money } from "@/lib/format";
import { fiscalAggregateState, aggregateMessages } from "@/lib/fiscal-compatibility";
export function DraftBalance({
  items,
  start,
  end,
}: {
  items: PlanItem[];
  start: number;
  end: number;
}) {
  let positive = BigInt(0),
    negative = BigInt(0),
    partial = false,
    outside = false,
    unfunded = false;
  for (const item of items.filter((p) => p.is_enabled)) {
    if (!item.estimate_status || item.estimate_status === "NOT_ESTIMATED")
      partial = true;
    if (item.unfunded) unfunded = true;
    for (const impact of item.impacts ?? []) {
      if (impact.year < start || impact.year > end) {
        outside = true;
        continue;
      }
      if (["NEW_REVENUE", "EXPENSE_REDUCTION"].includes(impact.impact_type))
        positive += cents(impact.amount);
      else negative += cents(impact.amount);
    }
  }
  const aggregate = fiscalAggregateState(items.filter((item) => item.is_enabled)
    .flatMap((item) => (item.impacts ?? []).filter((impact) => impact.year >= start && impact.year <= end)));
  const blocked = aggregate === "INCOMPLETE" || aggregate === "HETEROGENEOUS";
  return (
    <aside className="editor-sidebar">
      <p>
        Prévia do rascunho · {start}–{end}
      </p>
      <h2>As escolhas, juntas.</h2>
      {!blocked && <div className="balance-values">
        <p>
          Receitas + economias <strong>{money(decimal(positive))}</strong>
        </p>
        <p>
          Despesas + renúncias <strong>{money(decimal(negative))}</strong>
        </p>
      </div>}
      <div aria-live="polite" aria-atomic="true">
        {blocked ? <p className="notice">{aggregateMessages[aggregate]}</p> : <ImpactMeter
          positive={decimal(positive)}
          negative={decimal(negative)}
          partial={partial}
        />}
      </div>
      <p className="muted">
        {items.filter((p) => p.is_enabled).length} propostas no cálculo. Prévia
        local; use “Simular plano” para registrar uma execução verificável.
      </p>
      {unfunded && (
        <p className="notice">Há medidas sem financiamento definido.</p>
      )}
      {outside && (
        <p className="notice">
          Existem impactos fora dos anos do plano; ficaram fora desta prévia.
        </p>
      )}
      <a href="/metodologia">Confira o que o cálculo considera →</a>
    </aside>
  );
}
