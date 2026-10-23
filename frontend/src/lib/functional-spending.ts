import type { FiscalBaseline, FunctionalSpending, SpendingAmounts, SpendingFunction, SpendingNature, SpendingStage } from "./types";

export const spendingStages: SpendingStage[] = ["PAID", "RAP_PAID", "TOTAL_PAID"];
export const spendingNatures: SpendingNature[] = ["PRIMARY", "FINANCIAL", "EXTRA_SIAFI"];
export const spendingStageLabels: Record<SpendingStage, string> = { PAID: "Pago do exercício", RAP_PAID: "Restos a pagar pagos", TOTAL_PAID: "Pagamentos totais" };
export const spendingNatureLabels: Record<SpendingNature, string> = { PRIMARY: "Primária da fonte", FINANCIAL: "Financeira", EXTRA_SIAFI: "Extra-Siafi" };

/** Source precision is normalized by the provider; never round subcent values in the browser. */
export function spendingCents(value: unknown): bigint | null {
  if (typeof value !== "string" || value.length > 50) return null;
  const match = /^([+-]?)(\d+)(?:\.(\d{1,6}))?$/.exec(value);
  if (!match || /[1-9]/.test((match[3] ?? "").slice(2))) return null;
  return (BigInt(match[2]) * BigInt(100) + BigInt((match[3] ?? "").slice(0, 2).padEnd(2, "0"))) * (match[1] === "-" ? BigInt(-1) : BigInt(1));
}

function amounts(value: SpendingAmounts | null | undefined): bigint[] | null {
  if (!value || Object.keys(value).length !== 3) return null;
  const parsed = spendingStages.map(stage => spendingCents(value[stage]));
  if (parsed.some(value => value === null) || parsed[0]! + parsed[1]! !== parsed[2]) return null;
  return parsed as bigint[];
}
const clean = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
export function spendingFunctionIdentity(row: SpendingFunction): boolean {
  if (!row || !spendingNatures.includes(row.nature) || typeof row.function_code !== "string" || typeof row.function_label !== "string" || !row.function_label.trim()) return false;
  const code = row.function_code.padStart(2, "0");
  if (typeof row.source_function_code !== "string" || !/^\d{1,2}$/.test(row.source_function_code) || row.source_function_code.padStart(2, "0") !== code) return false;
  if (row.classification === "UNCLASSIFIED") return code === "99" && ((row.function_key === "UNCLASSIFIED_NA" && clean(row.function_label) === "N/A") || (row.function_key === "UNCLASSIFIED_OTHER" && clean(row.function_label) === "OUTRAS"));
  if (row.classification !== "BUDGET_FUNCTION" || row.function_key !== `FUNCTION_${code}`) return false;
  if (code === "99") return clean(row.function_label) === "RESERVA DE CONTINGENCIA";
  return /^(0[1-9]|1[0-9]|2[0-8])$/.test(code);
}

export function orderedSpendingFunctions(rows: SpendingFunction[]): SpendingFunction[] {
  return [...rows].sort((a, b) => Number(a.classification === "UNCLASSIFIED") - Number(b.classification === "UNCLASSIFIED") || a.function_code.padStart(2,"0").localeCompare(b.function_code.padStart(2,"0")) || a.function_key.localeCompare(b.function_key));
}

type Aggregate = { amount: bigint[]; rows: number; months: Set<number> };
const emptyAggregate = (): Aggregate => ({ amount: [BigInt(0), BigInt(0), BigInt(0)], rows: 0, months: new Set() });
const rowCount = (value: number) => Number.isSafeInteger(value) && value > 0 && value <= 200000;
function add(map: Map<string, Aggregate>, key: string, money: bigint[], rows: number, month: number) {
  const sum = map.get(key) ?? emptyAggregate();
  money.forEach((value, index) => sum.amount[index] += value);
  sum.rows += rows; sum.months.add(month); map.set(key, sum);
}
function matches(sum: Aggregate | undefined, value: SpendingAmounts, rows: number, observed: number[]) {
  const money = amounts(value);
  return Boolean(sum && money && money.every((value, index) => value === sum.amount[index]) && rows === sum.rows && Array.isArray(observed) && observed.length === sum.months.size && new Set(observed).size === observed.length && observed.every(month => sum.months.has(month)));
}

export function functionalSpendingState(fiscal: FiscalBaseline | null | undefined, cohort: FunctionalSpending | null | undefined): "READY" | "MISMATCH" | "UNAVAILABLE" {
  if (!cohort || cohort.status !== "AVAILABLE" || !cohort.payload || !cohort.source || !fiscal || fiscal.status !== "AVAILABLE") return "UNAVAILABLE";
  const p = cohort.payload;
  if (cohort.year !== fiscal.year || p.year !== cohort.year) return "MISMATCH";
  if (!Number.isInteger(p.year) || cohort.period_start !== `${p.year}-01-01` || cohort.period_end !== `${p.year}-12-31` || p.scope !== "GOVERNMENT_CENTRAL_OFSS_SOURCE" || p.currency !== "BRL" || p.price_basis !== "CURRENT" || p.accounting_basis !== "OB_ISSUANCE_VALUE_PAID" || p.periodicity !== "MONTHLY_MOVEMENT" || !rowCount(p.row_count) || p.stages?.join() !== spendingStages.join() || !Array.isArray(p.months) || p.months.length !== 12 || !Array.isArray(p.natures) || !Array.isArray(p.functions) || !p.reconciliation || p.fingerprint !== cohort.cohort_fingerprint || !/^[a-f0-9]{64}$/.test(p.fingerprint) || !p.resource || !/^[a-f0-9]{64}$/.test(p.resource.sha256)) return "UNAVAILABLE";
  if (p.parser_version !== "1.0.0" || p.precision_version !== "row-half-even-cent-v1" || !Number.isSafeInteger(cohort.revision) || cohort.revision! < 1 || !cohort.collected_at || !Number.isFinite(Date.parse(cohort.collected_at)) || !p.source || Object.values(p.source).some(value => typeof value !== "string" || !value.trim())) return "UNAVAILABLE";
  if (!p.reconciliation.group_total_differences || !p.reconciliation.raw_minus_rounded_totals || spendingStages.some(stage => typeof p.reconciliation.raw_minus_rounded_totals[stage] !== "string" || !/^[+-]?\d+(?:\.\d+)?$/.test(p.reconciliation.raw_minus_rounded_totals[stage]))) return "UNAVAILABLE";
  if (["title", "institution", "url", "license", "license_url"].some(key => p.source?.[key as keyof typeof p.source] !== cohort.source?.[key as keyof typeof cohort.source])) return "UNAVAILABLE";
  const total = amounts(p.totals);
  if (!total || spendingCents(p.reconciliation.row_payment_difference_max) !== BigInt(0) || spendingStages.some(stage => spendingCents(p.reconciliation.group_total_differences[stage]) !== BigInt(0))) return "UNAVAILABLE";
  const natures = new Map<string, Aggregate>(), functions = new Map<string, Aggregate>();
  const annual = emptyAggregate(), months = new Set<number>();
  for (const month of p.months) {
    if (!month || !Number.isInteger(month.month) || month.month < 1 || month.month > 12 || months.has(month.month) || !rowCount(month.row_count) || !Array.isArray(month.groups) || !month.groups.length) return "UNAVAILABLE";
    months.add(month.month);
    const monthly = emptyAggregate(), seen = new Set<string>();
    for (const group of month.groups) {
      const money = amounts(group?.amounts);
      if (!spendingFunctionIdentity(group) || !money || !rowCount(group.row_count)) return "UNAVAILABLE";
      const key = `${group.nature}:${group.function_key}`;
      if (seen.has(key)) return "UNAVAILABLE";
      seen.add(key); money.forEach((value,index) => monthly.amount[index] += value); monthly.rows += group.row_count;
      add(natures, group.nature, money, group.row_count, month.month);
      add(functions, key, money, group.row_count, month.month);
    }
    const reported = amounts(month.totals);
    if (!reported || monthly.rows !== month.row_count || reported.some((value,index) => value !== monthly.amount[index])) return "UNAVAILABLE";
    monthly.amount.forEach((value,index) => annual.amount[index] += value); annual.rows += monthly.rows;
  }
  if (annual.rows !== p.row_count || total.some((value,index) => value !== annual.amount[index]) || p.natures.length !== natures.size || p.functions.length !== functions.size) return "UNAVAILABLE";
  const seenNature = new Set<string>(), seenFunction = new Set<string>();
  for (const nature of p.natures) {
    if (!nature || !spendingNatures.includes(nature.nature) || seenNature.has(nature.nature) || !matches(natures.get(nature.nature),nature.amounts,nature.row_count,nature.observed_months)) return "UNAVAILABLE";
    seenNature.add(nature.nature);
  }
  for (const group of p.functions) {
    if (!group) return "UNAVAILABLE";
    const key = `${group.nature}:${group.function_key}`;
    if (!spendingFunctionIdentity(group) || seenFunction.has(key) || !matches(functions.get(key),group.amounts,group.row_count,group.observed_months)) return "UNAVAILABLE";
    seenFunction.add(key);
  }
  const subset = p.reconciliation.published_subset;
  if (!subset || !Array.isArray(subset.months) || subset.months.length !== 12) return "UNAVAILABLE";
  const subsetMonths = new Set<number>(); let calculated = BigInt(0);
  for (const month of subset.months) {
    if (!month) return "UNAVAILABLE";
    const published = spendingCents(month.published_total), value = spendingCents(month.calculated_total), difference = spendingCents(month.difference);
    if (!Number.isInteger(month.month) || !months.has(month.month) || subsetMonths.has(month.month) || published === null || value === null || difference === null || value - published !== difference || difference !== BigInt(0)) return "UNAVAILABLE";
    subsetMonths.add(month.month); calculated += value;
  }
  const published = spendingCents(subset.annual_published_total), annualCalculated = spendingCents(subset.annual_calculated_total), difference = spendingCents(subset.annual_difference);
  if (published === null || annualCalculated !== calculated || difference === null || calculated - published !== difference || difference < BigInt(-7) || difference > BigInt(7)) return "UNAVAILABLE";
  return "READY";
}
