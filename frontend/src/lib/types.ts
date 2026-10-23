import type { FiscalMetadata } from "./fiscal-compatibility";
import type { FiscalScenario, FiscalScenarioResultData } from "./fiscal-scenario";

export type User = {
  id: string;
  name: string;
  username: string;
  email: string;
  role: string;
};
export type Source = {
  is_example?: boolean;
  usage_count?: number;
  collection_code?: string | null;
  license?: string | null;
  license_url?: string | null;
  id: string;
  title: string;
  institution: string;
  url: string;
  source_type: string;
  publication_date: string | null;
  accessed_at: string;
  description: string | null;
};
export type Impact = FiscalMetadata & {
  year: number;
  impact_type: string;
  amount: string;
  description: string;
};
export type Funding = {
  funding_type: string;
  amount: string | null;
  year: number | null;
  description: string;
};
export type Evidence = { source: Source; usage_description: string };
export type ProposalDetails = {
  level?: "COMPLETE" | null; beneficiaries: string; adversely_affected: string; risks: string; assisted_fields: string[]; idea_id?: string | null; origin_attribution?: Record<string, unknown> | null;
};
export type PolicyVersion = {
  proposal_details?: ProposalDetails | null;
  baseline_snapshot?: Baseline | null;
  id: string;
  version_number: number;
  status: string;
  title: string;
  summary: string;
  problem: string;
  proposal: string;
  category: string;
  implementation_start: number | null;
  implementation_end: number | null;
  financial_impact_status: string;
  impact_justification: string | null;
  change_summary: string | null;
  impacts: Impact[];
  fundings: Funding[];
  sources: Evidence[];
};
export type Policy = {
  solidity?: { method: "DOC_COMPLETENESS1"; level: "COMPLETE" | "LEGACY"; score: number | null; max_score: number; has_sources: boolean; funding_defined: boolean; reviewed: boolean; review_status: "NOT_ASSESSED" } | null;
  is_example?: boolean;
  id: string;
  slug: string;
  status: string;
  archive_reason: string | null;
  author: { name: string; username: string };
  version: PolicyVersion;
};
export type PlanItem = {
  estimate_status?: string;
  impacts?: Impact[];
  unfunded?: boolean;
  baseline_id?: string | null;
  policy_version_id: string;
  policy_id: string;
  slug: string;
  version_number: number;
  title: string;
  position: number;
  is_enabled: boolean;
};
export type FiscalYear = {
  year: number;
  new_expenses: string;
  expense_reductions: string;
  new_revenues: string;
  revenue_reductions: string;
  net_impact: string;
};
export type FiscalCompatibility = {
  version: string;
  status: "COMPATIBLE" | "NOT_COMPARABLE" | "INCOMPLETE" | "NO_IMPACTS";
  baseline_year: number | null;
  baseline_combined: false;
  issues: { code: string; field: string; message: string }[];
  impacts: {
    impact_id: string;
    policy_version_id: string;
    year: number;
    status: "COMPATIBLE" | "NOT_COMPARABLE" | "INCOMPLETE";
    issues: { code: string; field: string; message: string }[];
  }[];
};
export type Simulation = {
  assumptions?: {
    price_basis?: "NOMINAL" | "CONSTANT" | "MIXED" | "UNSPECIFIED";
    price_base_year?: number | null;
    aggregate_basis?: "HOMOGENEOUS" | "MIXED" | "UNSPECIFIED";
    fiscal_compatibility?: FiscalCompatibility;
    fiscal_scenario?: FiscalScenarioResultData | null;
  };
  id: string;
  engine_version: string;
  input_hash: string;
  cumulative_impact: string;
  is_partial: boolean;
  warnings: { code: string; policy_version_id?: string }[];
  years: FiscalYear[];
};
export type Plan = {
  is_example?: boolean;
  id: string;
  slug: string;
  status: string;
  archive_reason: string | null;
  author: { name: string; username: string };
  version: {
    baseline_snapshot?: Baseline | null;
    fiscal_scenario?: FiscalScenario | null;
    id: string;
    version_number: number;
    status: string;
    title: string;
    summary: string;
    vision: string;
    start_year: number;
    end_year: number;
    change_summary: string | null;
    policies: PlanItem[];
    simulation: Simulation | null;
  };
};
export type Envelope<T> = {
  data: T;
  pagination?: { page: number; page_size: number; total: number };
};
export type HistoryItem = {
  id: string;
  version_number: number;
  title: string;
  published_at: string;
};

export type Baseline = {
  fiscal?: FiscalBaseline | null;
  id: string;
  captured_at: string;
  status: string;
  kind: string;
  missing: string[];
  limitations: string[];
  observations: {
    code: string;
    name: string;
    unit: string;
    scope: string;
    observation: { value: string; reference_date: string; source: Source };
  }[];
};

export type FiscalSource = {
  title: string;
  url: string;
  institution: string;
  license: string;
  license_url: string;
};

export type FiscalBaseline = {
  gdp?: {
    status: "AVAILABLE" | "INCOMPLETE" | "EMPTY";
    year: number;
    nominal_gdp: string | null;
    aggregation: "sum_four_quarters_cnt";
    source_precision: "0.01_million_brl";
    source: FiscalSource;
    quarters: {
      reference_date: string;
      observation: {
        id: string;
        revision: number;
        value: string;
        source: Source;
        provenance: Record<string, unknown>;
      };
    }[];
    limitations: string[];
    missing: string[];
  };
  ratios?: {
    net_revenue_pct_gdp: string;
    primary_expenditure_pct_gdp: string;
    primary_balance_pct_gdp: string;
  } | null;
  status: "AVAILABLE" | "INCOMPLETE" | "EMPTY";
  year: number | null;
  period_start: string | null;
  period_end: string | null;
  scope: string;
  accounting_basis: "cash";
  price_basis: "nominal";
  currency: "BRL";
  methodology: string;
  amounts: {
    net_revenue: string;
    primary_expenditure: string;
    published_primary_balance: string;
    calculated_primary_balance: string;
    reconciliation_difference: string;
  } | null;
  source: FiscalSource | null;
  missing: string[];
  limitations: string[];
  months: {
    reference_date: string;
    observations: {
      code: string;
      id: string;
      revision: number;
      value: string;
      source: Source;
      provenance: Record<string, unknown>;
    }[];
  }[];
};

export type FiscalCompositionItem = { code: string; series: string; label: string; amount: string };
export type FiscalComposition = {
  status: "AVAILABLE" | "INCOMPLETE" | "EMPTY";
  year: number | null;
  period_start: string | null;
  period_end: string | null;
  scope: string;
  currency: "BRL";
  accounting_basis: "cash";
  price_basis: "nominal";
  method_version: string;
  source: FiscalSource | null;
  collected_at: string | null;
  reference_amounts: { net_revenue: string; primary_expenditure: string; published_primary_balance: string } | null;
  totals: { gross_revenue: string; transfers: string; net_revenue: string; primary_expenditure: string } | null;
  revenue: FiscalCompositionItem[];
  expenditure: FiscalCompositionItem[];
  reconciliation: { revenue_components_difference: string; net_revenue_difference: string; expenditure_difference: string; monthly_tolerance: string } | null;
  months: { reference_date: string; period_fingerprint: string; observations: { code: string; id: string; revision: number; value: string; source: Source; provenance: Record<string, unknown> }[]; reference_observations: { code: string; id: string; revision: number; value: string; source: Source; provenance: Record<string, unknown> }[] }[];
  methodology: string;
  limitations: string[];
  missing: string[];
};

export type FiscalInterest = {
  status: "AVAILABLE" | "INCOMPLETE" | "EMPTY";
  year: number | null;
  period_start: string | null;
  period_end: string | null;
  scope: string;
  currency: "BRL";
  accounting_basis: "mixed";
  methodology_basis: "below_line";
  component_bases: { primary: "cash"; interest: "accrual" };
  price_basis: "nominal";
  method_version: string;
  source: (FiscalSource & { attribution: string }) | null;
  collected_at: string | null;
  totals: { primary_balance: string; interest: string; nominal_balance: string } | null;
  reconciliation: { monthly_tolerance: string; annual_difference: string } | null;
  months: { reference_date: string; period_fingerprint?: string; observations: { code: string; id: string; value: string; revision: number; source: Source; provenance: Record<string, unknown> }[] }[];
  methodology: string;
  limitations: string[];
  missing: string[];
};

export type SpendingStage = "PAID" | "RAP_PAID" | "TOTAL_PAID";
export type SpendingNature = "PRIMARY" | "FINANCIAL" | "EXTRA_SIAFI";
export type SpendingAmounts = Record<SpendingStage, string>;
export type SpendingFunction = {
  nature: SpendingNature;
  nature_label: string;
  function_key: string;
  function_code: string;
  source_function_code: string;
  function_label: string;
  classification: "BUDGET_FUNCTION" | "UNCLASSIFIED";
  row_count: number;
  amounts: SpendingAmounts;
};
export type SpendingNatureTotal = { nature: SpendingNature; nature_label: string; row_count: number; amounts: SpendingAmounts; observed_months: number[] };
export type SpendingPayload = {
  year: number;
  scope: "GOVERNMENT_CENTRAL_OFSS_SOURCE";
  currency: "BRL";
  price_basis: "CURRENT";
  accounting_basis: "OB_ISSUANCE_VALUE_PAID";
  periodicity: "MONTHLY_MOVEMENT";
  parser_version: string;
  precision_version: string;
  source: FiscalSource;
  resource: { id: string; url: string; last_modified: string; size: number; sha256: string };
  row_count: number;
  stages: SpendingStage[];
  months: { month: number; row_count: number; totals: SpendingAmounts; groups: SpendingFunction[] }[];
  totals: SpendingAmounts;
  natures: SpendingNatureTotal[];
  functions: (SpendingFunction & { observed_months: number[] })[];
  reconciliation: {
    row_payment_difference_max: string;
    group_total_differences: SpendingAmounts;
    raw_minus_rounded_totals: SpendingAmounts;
    published_subset: { labels: string[]; months: { month: number; published_total: string; calculated_total: string; difference: string }[]; annual_published_total: string; annual_calculated_total: string; annual_difference: string; scope: string };
  };
  absence_policy: string;
  fingerprint: string;
};
export type FunctionalSpending = {
  status: "AVAILABLE" | "INCOMPLETE" | "EMPTY";
  year: number | null;
  period_start: string | null;
  period_end: string | null;
  collected_at: string | null;
  revision: number | null;
  cohort_fingerprint: string | null;
  source: FiscalSource | null;
  payload: SpendingPayload | null;
  methodology: string;
  limitations: string[];
  missing: string[];
};


export type GeneralGovernmentMetric = "revenue" | "interest_revenue" | "expense" | "spending" | "interest_expense" | "net_investment" | "net_lending" | "primary_net_lending";
export type GeneralGovernmentSectorCode = "CENTRAL_BUDGETARY" | "CENTRAL_EXTRA_BUDGETARY" | "CENTRAL_CONSOLIDATION" | "CENTRAL" | "STATES" | "MUNICIPALITIES" | "GENERAL_CONSOLIDATION" | "GENERAL";
export type GeneralGovernmentAmounts = Record<GeneralGovernmentMetric, string>;
export type GeneralGovernmentSector = { sector: GeneralGovernmentSectorCode; label: string; column: string; amounts: GeneralGovernmentAmounts; raw_millions: GeneralGovernmentAmounts; cells: GeneralGovernmentAmounts };
export type GeneralGovernmentPayload = {
  year: number;
  currency: "BRL";
  price_basis: "CURRENT";
  accounting_basis: "MODIFIED_ACCRUAL";
  methodology_basis: "GFSM_2014";
  period_basis: "FULL_YEAR";
  parser_version: string;
  precision_version: string;
  source: FiscalSource;
  resource: { publication_url: string; publication_id: string; download_url: string; url: string; published_at: string; updated_at: string; size: number; sha256: string; etag: string | null; last_modified: string | null };
  coverage: { states_units: number; municipal_units: number; municipal_collection_approx_percent: string; municipal_extrapolated: boolean; central_excludes_bcb: boolean };
  sectors: GeneralGovernmentSector[];
  reconciliation: {
    tolerance: string;
    identities: { sector: GeneralGovernmentSectorCode; expense_difference: string; net_lending_difference: string; primary_difference: string }[];
    consolidation: { metric: GeneralGovernmentMetric; central_difference: string; general_difference: string }[];
    general_reference: { metric: GeneralGovernmentMetric; cell: string; raw_millions: string; amount: string; difference: string }[];
  };
  fingerprint: string;
};
export type GeneralGovernment = {
  status: "AVAILABLE" | "INCOMPLETE" | "EMPTY";
  year: number | null;
  period_start: string | null;
  period_end: string | null;
  collected_at: string | null;
  revision: number | null;
  cohort_fingerprint: string | null;
  source: FiscalSource | null;
  payload: GeneralGovernmentPayload | null;
  methodology: string;
  limitations: string[];
  missing: string[];
};
