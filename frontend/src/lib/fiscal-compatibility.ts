export type FiscalMetadata = {
  fiscal_scope?: string;
  accounting_basis?: string;
  price_basis?: string;
  price_base_year?: number | null;
  component?: string;
  period_basis?: string;
};
export const fiscalScopes: Record<string, string> = {
  UNSPECIFIED: "Não informado",
  CENTRAL_GOVERNMENT: "Governo Central (União, Banco Central e Previdência)",
  GENERAL_GOVERNMENT: "Governo Geral (União, estados e municípios)",
  STATE: "Governo estadual",
  MUNICIPAL: "Governo municipal",
  OTHER: "Outra abrangência",
};
export const accountingBases: Record<string, string> = {
  UNSPECIFIED: "Não informado",
  CASH: "Caixa: quando o dinheiro entra ou sai",
  ACCRUAL: "Competência: quando o direito ou obrigação surge",
};
export const priceBases: Record<string, string> = {
  UNSPECIFIED: "Não informado",
  NOMINAL: "Preços do próprio ano (nominais)",
  CONSTANT: "Preços de um ano-base (corrigidos pela inflação)",
};
export const fiscalComponents: Record<string, string> = {
  UNSPECIFIED: "Não informado",
  PRIMARY: "Receita ou despesa primária (sem juros)",
  INTEREST: "Juros",
};
export const periodBases: Record<string, string> = {
  UNSPECIFIED: "Não informado",
  FULL_YEAR: "Ano inteiro",
  PARTIAL_YEAR: "Parte do ano",
};
export const unspecifiedFiscalMetadata = {
  fiscal_scope: "UNSPECIFIED",
  accounting_basis: "UNSPECIFIED",
  price_basis: "UNSPECIFIED",
  price_base_year: null,
  component: "UNSPECIFIED",
  period_basis: "UNSPECIFIED",
};
export function fiscalMetadataBody(row: FiscalMetadata) {
  return {
    fiscal_scope: row.fiscal_scope ?? "UNSPECIFIED",
    accounting_basis: row.accounting_basis ?? "UNSPECIFIED",
    price_basis: row.price_basis ?? "UNSPECIFIED",
    price_base_year: row.price_basis === "CONSTANT" ? row.price_base_year ?? null : null,
    component: row.component ?? "UNSPECIFIED",
    period_basis: row.period_basis ?? "UNSPECIFIED",
  };
}
export function fiscalMetadataText(row: FiscalMetadata) {
  const data = fiscalMetadataBody(row);
  return [
    fiscalScopes[data.fiscal_scope] ?? "Não informado",
    accountingBases[data.accounting_basis] ?? "Não informado",
    (priceBases[data.price_basis] ?? "Não informado") +
      (data.price_basis === "CONSTANT" ? " · ano-base " + (data.price_base_year ?? "não informado") : ""),
    fiscalComponents[data.component] ?? "Não informado",
    periodBases[data.period_basis] ?? "Não informado",
  ];
}
const dimensions = {
  fiscal_scope: fiscalScopes,
  accounting_basis: accountingBases,
  price_basis: priceBases,
  component: fiscalComponents,
  period_basis: periodBases,
};
// A local preview checks only declared units. Matching units do not validate an estimate.
export function fiscalAggregateState(rows: FiscalMetadata[]): "EMPTY" | "HOMOGENEOUS" | "INCOMPLETE" | "HETEROGENEOUS" {
  if (!rows.length) return "EMPTY";
  let missing = false;
  for (const [field, options] of Object.entries(dimensions)) {
    const values = rows.map((row) => row[field as keyof FiscalMetadata]);
    const known = values.filter((value): value is string =>
      typeof value === "string" && value !== "UNSPECIFIED" && Object.hasOwn(options, value));
    if (new Set(known).size > 1) return "HETEROGENEOUS";
    if (known.length !== rows.length) missing = true;
  }
  const constant = rows.filter((row) => row.price_basis === "CONSTANT");
  const years = constant.map((row) => row.price_base_year);
  if (new Set(years.filter((year) => Number.isInteger(year))).size > 1) return "HETEROGENEOUS";
  if (years.some((year) => !Number.isInteger(year) || Number(year) < 1900 || Number(year) > 2200)) missing = true;
  return missing ? "INCOMPLETE" : "HOMOGENEOUS";
}
export const aggregateMessages = {
  INCOMPLETE: "Faltam informações sobre abrangência, preços, período ou critério do impacto. Confira as parcelas; ainda não há um total comparável.",
  HETEROGENEOUS: "As parcelas misturam abrangências, preços, períodos ou critérios diferentes. O total aritmético não representa um saldo fiscal comparável.",
};


/** Presentation adapts historical reasons without rewriting preserved simulation data. */
export function historicalFiscalIssueMessage(issue: { code: string; message: string }) {
  if (issue.code === "FUTURE_ASSUMPTIONS_REQUIRED")
    return "O ano da parcela é posterior à referência observada. Compare anos futuros no cenário declarado, separadamente.";
  if (issue.code === "YEAR_DIFFERS")
    return "O ano da parcela difere do ano observado. A referência histórica não foi ajustada para esse ano.";
  return issue.message;
}
