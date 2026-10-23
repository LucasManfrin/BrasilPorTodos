export type FiscalScenarioYear = {
  year: number;
  net_revenue: string | null;
  primary_expenditure: string | null;
  justification: string;
  source_urls: string[];
};
export type FiscalScenarioInput = {
  title: string;
  explanation: string;
  reference_baseline_id: string | null;
  years: FiscalScenarioYear[];
};
export type FiscalScenario = FiscalScenarioInput & {
  excludes_plan_impacts?: boolean;
  review_input_hash?: string;
  reviewed_input_hash?: string | null;
  reviewed_at?: string | null;
};
export type FiscalScenarioAmounts = {
  net_revenue: string | null;
  primary_expenditure: string | null;
  primary_balance: string | null;
};
export type ScenarioIssue = { code: string; message?: string; field?: string };
export type FiscalScenarioResultData = {
  scenario: FiscalScenarioInput & { start_year?: number; end_year?: number; excludes_plan_impacts?: boolean };
  historical_year: number | null;
  status: string;
  years: {
    year: number;
    declared: FiscalScenarioAmounts;
    incremental: {
      year: number;
      new_expenses: string;
      expense_reductions: string;
      new_revenues: string;
      revenue_reductions: string;
      net_impact: string;
    };
    combined: FiscalScenarioAmounts | null;
    issues?: ScenarioIssue[];
  }[];
  impacts?: { year: number; status: string; issues: ScenarioIssue[] }[];
  issues: ScenarioIssue[];
  warnings: ScenarioIssue[];
  cumulative_incremental: string;
  incremental_is_partial: boolean;
  aggregate_basis: string;
  price_basis: string;
  scenario_method_version: string;
  aggregation_engine_version: string;
  limitations: string[];
};
/** Reais remain decimal strings. Empty is missing; explicit zero remains zero. */
export function normalizeScenarioMoney(value: string | null | undefined): string | null {
  if (value === null || value === undefined || !value.trim()) return null;
  let cleaned = value.trim();
  if (cleaned.includes(",")) {
    if (!/^(?:\d+|\d{1,3}(?:\.\d{3})+),\d{1,2}$/.test(cleaned))
      throw new Error("Informe reais completos, como 1000,00, com até duas casas decimais.");
    cleaned = cleaned.replaceAll(".", "").replace(",", ".");
  }
  if (!/^\d+(?:\.\d{1,2})?$/.test(cleaned))
    throw new Error("Receita e despesa devem ser valores não negativos, com até duas casas decimais.");
  const [whole, fraction = ""] = cleaned.split(".");
  const canonical = BigInt(whole).toString();
  if (canonical.length > 16)
    throw new Error("O valor excede o limite de 16 dígitos antes dos centavos.");
  return canonical + "." + fraction.padEnd(2, "0");
}
/** Only author-editable fields cross create/PATCH or duplication. */
export function fiscalScenarioBody(scenario: FiscalScenario | null | undefined): FiscalScenarioInput | null {
  if (!scenario) return null;
  return {
    title: scenario.title,
    explanation: scenario.explanation,
    reference_baseline_id: scenario.reference_baseline_id ?? "",
    years: scenario.years.map((row) => ({
      year: row.year,
      net_revenue: normalizeScenarioMoney(row.net_revenue),
      primary_expenditure: normalizeScenarioMoney(row.primary_expenditure),
      justification: row.justification,
      source_urls: row.source_urls.map((url) => url.trim()).filter(Boolean),
    })),
  };
}
export function invalidateScenarioReview(scenario: FiscalScenario | null | undefined): FiscalScenario | null {
  if (!scenario) return null;
  return { ...scenario, excludes_plan_impacts: false, reviewed_input_hash: null, reviewed_at: null };
}
export function scenarioIsReviewed(scenario: FiscalScenario | null | undefined) {
  return Boolean(scenario?.excludes_plan_impacts && scenario.reviewed_at &&
    scenario.review_input_hash && scenario.reviewed_input_hash === scenario.review_input_hash);
}
export function scenarioHorizon(start: number, end: number): number[] {
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 1900 || end > 2200 || end < start || end - start + 1 > 30)
    throw new Error("O cenário aceita de 1 a 30 anos. Revise o início e o fim do plano.");
  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}
export function reconcileScenarioYears(scenario: FiscalScenario, start: number, end: number): FiscalScenario {
  const existing = new Map(scenario.years.map((row) => [row.year, row]));
  const years = scenarioHorizon(start, end).map((year) => existing.get(year) ?? {
    year, net_revenue: null, primary_expenditure: null, justification: "", source_urls: [],
  });
  return invalidateScenarioReview({ ...scenario, years })!;
}
export function createFiscalScenario(referenceId: string | null, start: number, end: number): FiscalScenario {
  return reconcileScenarioYears({ title: "", explanation: "", reference_baseline_id: referenceId, years: [] }, start, end);
}
export function scenarioYearsMatch(scenario: FiscalScenario, start: number, end: number) {
  try {
    const expected = scenarioHorizon(start, end);
    return scenario.years.length === expected.length &&
      new Set(scenario.years.map((row) => row.year)).size === expected.length &&
      expected.every((year) => scenario.years.some((row) => row.year === year));
  } catch { return false; }
}
export function scenarioAmountState(value: string | null | undefined) {
  return value === null || value === undefined ? { available: false, value: null } : { available: true, value };
}

export function planEditResetsScenarioReview(field: string) {
  return ["fiscal_scenario", "start_year", "end_year", "policies", "baseline_snapshot"].includes(field);
}
