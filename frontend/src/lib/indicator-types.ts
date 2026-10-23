import type { Source } from "./types";
export type Observation = {
  id: string;
  reference_date: string;
  value: string;
  retrieved_at: string;
  revision: number;
  revision_reason: string;
  source: Source;
  provenance: {
    dataset_url?: string;
    license?: string;
    income_price_reference?: string;
    income_price_period?: string;
    source_release_date?: string;
    method?: string;
    institution?: string;
    definition?: { unit: string; methodology: string };
  };
};
export type Indicator = {
  id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  unit: string;
  frequency: string;
  scope: string;
  methodology: string;
  base_year: number | null;
  is_active: boolean;
  data_status: string;
  latest: Observation | null;
  history?: Observation[];
  series?: { reference_date: string; value: string; revision: number }[];
};
export function indicatorValue(value: string) {
  const negative = value.startsWith("-");
  const [whole, fraction] = value.replace(/^-/, " ").trim().split(".");
  return (
    (negative ? "− " : "") +
    new Intl.NumberFormat("pt-BR").format(BigInt(whole)) +
    (fraction ? "," + fraction.replace(/0+$/, "") : "").replace(/,$/, "")
  );
}
