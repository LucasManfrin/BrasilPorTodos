import type { FiscalBaseline, GeneralGovernment, GeneralGovernmentMetric, GeneralGovernmentSectorCode } from "./types";

export const governmentMetrics: GeneralGovernmentMetric[] = ["revenue", "interest_revenue", "expense", "spending", "interest_expense", "net_investment", "net_lending", "primary_net_lending"];
export const governmentSectors: GeneralGovernmentSectorCode[] = ["CENTRAL_BUDGETARY", "CENTRAL_EXTRA_BUDGETARY", "CENTRAL_CONSOLIDATION", "CENTRAL", "STATES", "MUNICIPALITIES", "GENERAL_CONSOLIDATION", "GENERAL"];
export const governmentVisibleSectors: GeneralGovernmentSectorCode[] = ["GENERAL", "CENTRAL", "STATES", "MUNICIPALITIES"];
export const governmentSectorLabels: Record<GeneralGovernmentSectorCode, string> = { CENTRAL_BUDGETARY: "Central orçamentário", CENTRAL_EXTRA_BUDGETARY: "Central extraorçamentário", CENTRAL_CONSOLIDATION: "Consolidação central", CENTRAL: "Governo Central", STATES: "Estados e DF", MUNICIPALITIES: "Municípios", GENERAL_CONSOLIDATION: "Consolidação do Governo Geral", GENERAL: "Governo Geral" };
export const governmentMetricLabels: Record<GeneralGovernmentMetric, string> = { revenue: "Receita", interest_revenue: "Juros · receita", expense: "Despesa total", spending: "Gasto", interest_expense: "Juros · gasto", net_investment: "Investimento líquido em ativos não financeiros", net_lending: "Capacidade (+) / necessidade (−) de financiamento", primary_net_lending: "Capacidade/necessidade primária · MEFP 2014" };

/** API cent strings can carry storage zeros. Never round a genuine fractional cent. */
export function governmentCents(value: unknown): bigint | null {
  if (typeof value !== "string" || value.length > 50) return null;
  const match = /^([+-]?)(\d+)(?:\.(\d{1,6}))?$/.exec(value);
  if (!match || /[1-9]/.test((match[3] ?? "").slice(2))) return null;
  const result = (BigInt(match[2]) * BigInt(100) + BigInt((match[3] ?? "").slice(0,2).padEnd(2,"0"))) * (match[1] === "-" ? BigInt(-1) : BigInt(1));
  return result <= -BigInt("10000000000000000") || result >= BigInt("10000000000000000") ? null : result;
}
export function governmentFinancingLabel(value: string): string {
  const cents = governmentCents(value);
  return cents === null ? "Financiamento não informado" : cents < BigInt(0) ? "Necessidade de financiamento (−)" : cents > BigInt(0) ? "Capacidade de financiamento (+)" : "Equilíbrio de financiamento";
}
const abs = (value: bigint) => value < BigInt(0) ? -value : value;
const keysMatch = (record: object, keys: string[]) => record && Object.keys(record).length === keys.length && keys.every(key => Object.hasOwn(record,key));
const sourceRows: Record<GeneralGovernmentMetric, number> = { revenue: 7, interest_revenue: 18, expense: 20, spending: 21, interest_expense: 25, net_investment: 30, net_lending: 35, primary_net_lending: 36 };
function sourceColumn(index: number): string {
  let result = "";
  while (index > 0) { index--; result = String.fromCharCode(65 + index % 26) + result; index = Math.floor(index / 26); }
  return result;
}
const rawDecimal = (value: unknown) => typeof value === "string" && value.length <= 60 && /^[+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d{1,2})?$/.test(value);

export function generalGovernmentState(fiscal: FiscalBaseline | null | undefined, cohort: GeneralGovernment | null | undefined): "READY" | "MISMATCH" | "UNAVAILABLE" {
  if (!cohort || cohort.status !== "AVAILABLE" || !cohort.payload || !cohort.source || !fiscal || fiscal.status !== "AVAILABLE") return "UNAVAILABLE";
  const p = cohort.payload;
  if (cohort.year !== fiscal.year || p.year !== cohort.year) return "MISMATCH";
  if (!Number.isInteger(p.year) || p.year < 2010 || p.year > 9999 || cohort.period_start !== `${p.year}-01-01` || cohort.period_end !== `${p.year}-12-31` || p.currency !== "BRL" || p.price_basis !== "CURRENT" || p.accounting_basis !== "MODIFIED_ACCRUAL" || p.methodology_basis !== "GFSM_2014" || p.period_basis !== "FULL_YEAR" || p.parser_version !== "1.0.0" || p.precision_version !== "million-cell-half-even-cent-v1" || !Number.isSafeInteger(cohort.revision) || cohort.revision! < 1 || !cohort.collected_at || !Number.isFinite(Date.parse(cohort.collected_at)) || !p.resource || !/^[a-f0-9]{64}$/.test(p.resource.sha256) || !/^[a-f0-9]{64}$/.test(p.fingerprint) || p.fingerprint !== cohort.cohort_fingerprint || !p.source || ["title", "institution", "url", "license", "license_url"].some(key => !p.source[key as keyof typeof p.source] || p.source[key as keyof typeof p.source] !== cohort.source?.[key as keyof typeof cohort.source])) return "UNAVAILABLE";
  if (!p.coverage || p.coverage.states_units !== 27 || p.coverage.municipal_units !== 5570 || p.coverage.municipal_collection_approx_percent !== "90" || p.coverage.municipal_extrapolated !== true || p.coverage.central_excludes_bcb !== true || !Array.isArray(p.sectors) || p.sectors.length !== 8 || !p.reconciliation || governmentCents(p.reconciliation.tolerance) !== BigInt(3)) return "UNAVAILABLE";
  const values = new Map<GeneralGovernmentSectorCode, Record<GeneralGovernmentMetric,bigint>>();
  for (let index=0;index<governmentSectors.length;index++) {
    const row = p.sectors[index];
    if (!row || row.sector !== governmentSectors[index] || typeof row.label !== "string" || !row.label.trim() || row.column !== sourceColumn(3 + 8 * (p.year - 2010) + index) || !row.amounts || !keysMatch(row.amounts,governmentMetrics) || !row.raw_millions || !keysMatch(row.raw_millions,governmentMetrics) || !row.cells || !keysMatch(row.cells,governmentMetrics)) return "UNAVAILABLE";
    const money = {} as Record<GeneralGovernmentMetric,bigint>;
    for (const metric of governmentMetrics) {
      const amount = governmentCents(row.amounts[metric]);
      if (amount === null || !rawDecimal(row.raw_millions[metric]) || row.cells[metric] !== `${row.column}${sourceRows[metric]}`) return "UNAVAILABLE";
      money[metric] = amount;
    }
    values.set(row.sector,money);
  }
  if (new Set(p.sectors.map(row=>row.column)).size !== 8) return "UNAVAILABLE";
  const recon=p.reconciliation;
  if (!Array.isArray(recon.identities) || recon.identities.length !== 8 || !Array.isArray(recon.consolidation) || recon.consolidation.length !== 8 || !Array.isArray(recon.general_reference) || recon.general_reference.length !== 8) return "UNAVAILABLE";
  for (let index=0;index<governmentSectors.length;index++) {
    const row=recon.identities[index], sector=governmentSectors[index], v=values.get(sector)!;
    if (!row || row.sector !== sector) return "UNAVAILABLE";
    const differences = [v.expense-v.spending-v.net_investment, v.net_lending-v.revenue+v.expense, v.primary_net_lending-v.net_lending-v.interest_expense+v.interest_revenue];
    if (differences.some((difference,index)=>abs(difference)>BigInt(3) || governmentCents([row.expense_difference,row.net_lending_difference,row.primary_difference][index]) !== difference)) return "UNAVAILABLE";
  }
  for (let index=0;index<governmentMetrics.length;index++) {
    const metric=governmentMetrics[index], row=recon.consolidation[index], reference=recon.general_reference[index];
    if (!row || row.metric !== metric || !reference || reference.metric !== metric || !rawDecimal(reference.raw_millions) || typeof reference.cell !== "string" || !reference.cell) return "UNAVAILABLE";
    const central=values.get("CENTRAL_BUDGETARY")![metric]+values.get("CENTRAL_EXTRA_BUDGETARY")![metric]+values.get("CENTRAL_CONSOLIDATION")![metric]-values.get("CENTRAL")![metric];
    const general=values.get("CENTRAL")![metric]+values.get("STATES")![metric]+values.get("MUNICIPALITIES")![metric]+values.get("GENERAL_CONSOLIDATION")![metric]-values.get("GENERAL")![metric];
    const referenceAmount=governmentCents(reference.amount);
    if (abs(central)>BigInt(3) || abs(general)>BigInt(3) || governmentCents(row.central_difference)!==central || governmentCents(row.general_difference)!==general || referenceAmount===null || abs(values.get("GENERAL")![metric]-referenceAmount)>BigInt(3) || governmentCents(reference.difference)!==values.get("GENERAL")![metric]-referenceAmount) return "UNAVAILABLE";
  }
  return "READY";
}
