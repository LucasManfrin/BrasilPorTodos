import type { FiscalBaseline, FiscalComposition } from "./types";

/** Compare money without binary floats; missing/invalid input never means zero. */
export function compositionCents(value: unknown): bigint | null {
  if (typeof value !== "string" || value.length > 50) return null;
  const match = /^([+-]?)(\d+)(?:\.(\d{1,2}))?$/.exec(value);
  if (!match) return null;
  return (BigInt(match[2]) * BigInt(100) + BigInt((match[3] ?? "").padEnd(2, "0"))) * (match[1] === "-" ? BigInt(-1) : BigInt(1));
}

export function compositionState(fiscal: FiscalBaseline | null | undefined, composition: FiscalComposition | null | undefined): "READY" | "MISMATCH" | "UNAVAILABLE" {
  if (!composition || composition.status !== "AVAILABLE" || !composition.reference_amounts || !composition.totals || !composition.reconciliation || !fiscal || fiscal.status !== "AVAILABLE" || !fiscal.amounts) return "UNAVAILABLE";
  const keys = ["net_revenue", "primary_expenditure", "published_primary_balance"] as const;
  if (keys.some(key => compositionCents(composition.reference_amounts![key]) === null || compositionCents(fiscal.amounts![key]) === null)) return "UNAVAILABLE";
  if (Object.values(composition.totals).some(value => compositionCents(value) === null) || composition.revenue.length !== 4 || composition.expenditure.length !== 4 || [...composition.revenue, ...composition.expenditure].some(row => compositionCents(row.amount) === null)) return "UNAVAILABLE";
  if (composition.year !== fiscal.year || composition.period_start !== fiscal.period_start || composition.period_end !== fiscal.period_end || composition.scope !== fiscal.scope || composition.currency !== fiscal.currency || composition.accounting_basis !== fiscal.accounting_basis || composition.price_basis !== fiscal.price_basis || keys.some(key => compositionCents(composition.reference_amounts![key]) !== compositionCents(fiscal.amounts![key]))) return "MISMATCH";
  return "READY";
}

/** Exact displayed share. Number conversion is reserved for bounded SVG/CSS geometry. */
export function compositionShare(amount: string, total: string): { label: string; width: number } | null {
  const a = compositionCents(amount), t = compositionCents(total);
  if (a === null || t === null || t <= BigInt(0)) return null;
  const magnitude = a < BigInt(0) ? -a : a;
  const hundredths = (magnitude * BigInt(10000) + t / BigInt(2)) / t;
  const sign = a < BigInt(0) ? "−" : "";
  const label = magnitude > BigInt(0) && hundredths === BigInt(0) ? `${sign}menos de 0,01%` : `${sign}${hundredths / BigInt(100)},${(hundredths % BigInt(100)).toString().padStart(2, "0")}%`;
  const bounded = a <= BigInt(0) ? BigInt(0) : hundredths > BigInt(10000) ? BigInt(10000) : hundredths;
  return { label, width: Number(bounded) / 100 };
}
