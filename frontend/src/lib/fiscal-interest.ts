import type { FiscalBaseline, FiscalInterest } from "./types";

export const fiscalInterestScope = "Governo Central: Tesouro Nacional, Previdência Social e Banco Central; exclui estados e municípios";

/** Integer cents keep signed observations and rounding checks exact. */
export function interestCents(value: unknown): bigint | null {
  if (typeof value !== "string" || value.length > 50) return null;
  const match = /^([+-]?)(\d+)(?:\.(\d{1,6}))?$/.exec(value);
  if (!match) return null;
  // PostgreSQL NUMERIC(20,6) serializes cent-exact observations with four trailing zeros.
  // Normalize those zeros; fractional cents remain invalid and are never rounded here.
  const fraction = match[3] ?? "";
  if (/[1-9]/.test(fraction.slice(2))) return null;
  return (BigInt(match[2]) * BigInt(100) + BigInt(fraction.slice(0, 2).padEnd(2, "0"))) * (match[1] === "-" ? BigInt(-1) : BigInt(1));
}

export function interestBalanceLabel(value: string, kind: "primary" | "interest" | "nominal"): string {
  const cents = interestCents(value);
  if (cents === null) return "Valor indisponível";
  if (kind === "interest") return cents < BigInt(0) ? "Juros líquidos · sinal negativo" : cents > BigInt(0) ? "Juros líquidos · sinal positivo" : "Juros líquidos nulos";
  const label = kind === "primary" ? "primário" : "nominal";
  return cents < BigInt(0) ? `Déficit ${label}` : cents > BigInt(0) ? `Superávit ${label}` : `Equilíbrio ${label}`;
}

export function interestState(fiscal: FiscalBaseline | null | undefined, interest: FiscalInterest | null | undefined): "READY" | "MISMATCH" | "UNAVAILABLE" {
  if (!interest || interest.status !== "AVAILABLE" || !interest.totals || !interest.reconciliation || !interest.source || !Array.isArray(interest.months) || interest.months.length !== 12 || !fiscal || fiscal.status !== "AVAILABLE") return "UNAVAILABLE";
  if (interest.year !== fiscal.year || interest.scope !== fiscal.scope) return "MISMATCH";
  if (!Number.isInteger(interest.year) || interest.scope !== fiscalInterestScope || interest.currency !== "BRL" || interest.price_basis !== "nominal" || interest.accounting_basis !== "mixed" || interest.methodology_basis !== "below_line" || interest.component_bases?.primary !== "cash" || interest.component_bases?.interest !== "accrual" || interest.period_start !== `${interest.year}-01-01` || interest.period_end !== `${interest.year}-12-31`) return "UNAVAILABLE";
  const keys = ["primary_balance", "interest", "nominal_balance"] as const;
  const annual = keys.map(key => interestCents(interest.totals![key]));
  const difference = interestCents(interest.reconciliation.annual_difference);
  if (annual.some(value => value === null) || difference === null || interestCents(interest.reconciliation.monthly_tolerance) !== BigInt(3)) return "UNAVAILABLE";
  const codes = ["rtn-primario-abaixo-linha", "rtn-juros-nominais", "rtn-resultado-nominal"];
  const sums = [BigInt(0), BigInt(0), BigInt(0)];
  const dates = new Set<string>();
  for (const month of interest.months) {
    if (!month || typeof month !== "object") return "UNAVAILABLE";
    const match = new RegExp(`^${interest.year}-(0[1-9]|1[0-2])-01$`).exec(month.reference_date);
    if (!match || dates.has(month.reference_date) || !Array.isArray(month.observations) || month.observations.length !== 3) return "UNAVAILABLE";
    dates.add(month.reference_date);
    const values = codes.map(code => {
      const rows = month.observations.filter(row => row && typeof row === "object" && row.code === code);
      return rows.length === 1 ? interestCents(rows[0].value) : null;
    });
    if (values.some(value => value === null)) return "UNAVAILABLE";
    const residual = values[0]! + values[1]! - values[2]!;
    if (residual < BigInt(-3) || residual > BigInt(3)) return "UNAVAILABLE";
    values.forEach((value, index) => sums[index] += value!);
  }
  if (sums.some((value, index) => value !== annual[index]) || annual[0]! + annual[1]! - annual[2]! !== difference || difference < BigInt(-36) || difference > BigInt(36)) return "UNAVAILABLE";
  return "READY";
}
