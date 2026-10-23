export function money(value: string) {
  const negative = value.startsWith("-");
  const [whole, fraction = "00"] = value.replace(/^-/, "").split(".");
  return `${negative ? "− " : ""}R$ ${new Intl.NumberFormat("pt-BR").format(BigInt(whole || "0"))},${fraction.padEnd(2, "0").slice(0, 2)}`;
}

export function decimalInput(value: string) {
  return value.includes(",")
    ? value.replaceAll(".", "").replace(",", ".")
    : value;
}

export function date(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(
    new Date(value.slice(0, 10) + "T12:00:00Z"),
  );
}

export const categories: Record<string, string> = {
  ECONOMY: "Economia",
  TAXATION: "Tributação",
  EDUCATION: "Educação",
  HEALTH: "Saúde",
  SECURITY: "Segurança",
  PENSION: "Previdência",
  INFRASTRUCTURE: "Infraestrutura",
  SOCIAL_ASSISTANCE: "Assistência Social",
  PUBLIC_ADMINISTRATION: "Administração Pública",
  SCIENCE_TECHNOLOGY: "Ciência e Tecnologia",
  HOUSING: "Habitação",
  ENERGY: "Energia",
  ENVIRONMENT: "Meio Ambiente",
  OTHER: "Outros",
};
export const impacts: Record<string, string> = {
  NEW_EXPENSE: "Nova despesa",
  EXPENSE_REDUCTION: "Redução de despesa",
  NEW_REVENUE: "Nova receita",
  REVENUE_REDUCTION: "Redução de receita",
};
export const fundings: Record<string, string> = {
  SPENDING_CUT: "Corte de gasto",
  NEW_REVENUE: "Nova receita",
  TAX_INCREASE: "Aumento de tributo",
  DEBT: "Endividamento",
  PROGRAM_REPLACEMENT: "Substituição de programa",
  REVENUE_GROWTH: "Crescimento de arrecadação",
  UNFUNDED: "Não financiado",
  OTHER: "Outro",
};
export const warnings: Record<string, string> = {
  FISCAL_METADATA_MISSING: "Algumas parcelas não informam abrangência, preços, período ou critério contábil. O total é aritmético e não foi validado como comparável.",
  FISCAL_AGGREGATE_HETEROGENEOUS: "O cálculo reúne recortes fiscais diferentes. Confira as parcelas; o somatório não representa um saldo fiscal único.",
  FISCAL_BASELINE_NOT_COMPARABLE: "Os impactos não são comparáveis à referência histórica preservada. Anos futuros dependem de um cenário e de premissas explícitas.",
  BASELINE_MISSING:
    "Esta versão não tem observações na base histórica. O saldo é apenas incremental.",
  BASELINE_DIFFERS:
    "Há propostas criadas com uma base de referência diferente. Revise a compatibilidade das premissas.",

  UNFUNDED: "Uma proposta declara financiamento ainda não definido.",
  NOT_ESTIMATED:
    "Uma proposta está sem estimativa fiscal. O total apresentado é parcial.",
  OUTSIDE_PERIOD:
    "Há impactos fora do período do plano; eles foram excluídos do cálculo.",
  INTERACTIONS_NOT_MODELED:
    "As medidas foram somadas sem modelar interações ou sobreposições. Revise suas premissas.",
};
