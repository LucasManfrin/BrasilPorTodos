import Link from "next/link";
import { categories } from "@/lib/format";
import type { Plan, Policy } from "@/lib/types";
import { Card } from "./ui";
import { cents, decimal, ImpactMeter } from "./impact-meter";
import { CardActions } from "./duplicate-button";
import { fiscalAggregateState, aggregateMessages } from "@/lib/fiscal-compatibility";

export function ContributionCard({
  kind,
  item,
}: {
  kind: "policies" | "plans";
  item: Policy | Plan;
}) {
  const policy = kind === "policies" ? (item as Policy) : null;
  const plan = kind === "plans" ? (item as Plan) : null;
  let positive = BigInt(0);
  let negative = BigInt(0);
  if (policy)
    for (const impact of policy.version.impacts) {
      if (["NEW_REVENUE", "EXPENSE_REDUCTION"].includes(impact.impact_type))
        positive += cents(impact.amount);
      else negative += cents(impact.amount);
    }
  if (plan?.version.simulation)
    for (const year of plan.version.simulation.years) {
      positive += cents(year.new_revenues) + cents(year.expense_reductions);
      negative += cents(year.new_expenses) + cents(year.revenue_reductions);
    }
  const aggregate = policy ? fiscalAggregateState(policy.version.impacts) : null;
  const unsafe = aggregate === "INCOMPLETE" || aggregate === "HETEROGENEOUS"
    ? aggregateMessages[aggregate]
    : plan?.version.simulation?.warnings.some((warning) => warning.code === "FISCAL_AGGREGATE_HETEROGENEOUS" || warning.code === "FISCAL_METADATA_MISSING")
      ? "Parcelas com recortes diferentes ou não informados. Consulte a execução para conferir os limites do total aritmético."
      : null;
  const category = policy?.version.category ?? "PLAN";
  const partial = policy
    ? policy.version.financial_impact_status === "NOT_ESTIMATED"
    : !plan?.version.simulation || plan.version.simulation.is_partial;
  return (
    <Card className="contribution-card" category={category}>
      {item.is_example && <span className="example-tag">Exemplo fictício</span>}
      <span className="category-tag" data-category={category}>
        {policy ? categories[category] : "Plano Brasil"}
      </span>
      <h2>
        <Link href={`/${policy ? "propostas" : "planos"}/${item.slug}`}>
          {item.version.title}
        </Link>
      </h2>
      <p>{item.version.summary}</p>
      <p className="muted">
        {plan
          ? `${plan.version.start_year}–${plan.version.end_year}`
          : `${policy?.version.implementation_start ?? "Ano não informado"}–${policy?.version.implementation_end ?? ""}`}
      </p>
      <div className="card-meta">
        <span className="author-avatar" aria-hidden="true">
          {item.author.name.slice(0, 1).toUpperCase()}
        </span>
        <p>
          {item.author.name}
          <small>
            @{item.author.username} · Versão {item.version.version_number}
          </small>
        </p>
      </div>
      {policy?.version.financial_impact_status === "NOT_APPLICABLE" ? (
        <p className="notice">Sem impacto fiscal aplicável, segundo o autor.</p>
      ) : unsafe ? <p className="notice">{unsafe}</p> : (
        <ImpactMeter
          positive={decimal(positive)}
          negative={decimal(negative)}
          partial={Boolean(partial)}
          compact
        />
      )}
      {policy?.version.fundings.some((r) => r.funding_type === "UNFUNDED") && (
        <p className="muted">O autor ainda não definiu o financiamento.</p>
      )}
      {plan?.version.simulation?.warnings.some(
        (r) => r.code === "UNFUNDED",
      ) && (
        <p className="muted">
          Há financiamento ainda não definido. Confira os avisos do plano.
        </p>
      )}
      {policy && (
        <div className="evidence-summary">
          <span>
            {policy.version.sources.length}{" "}
            {policy.version.sources.length === 1
              ? "fonte citada"
              : "fontes citadas"}
          </span>
          <span>
            {policy.version.fundings.length &&
            !policy.version.fundings.some((f) => f.funding_type === "UNFUNDED")
              ? "Financiamento informado"
              : "Financiamento a conferir"}
          </span>
        </div>
      )}
      <CardActions
        kind={kind}
        slug={item.slug}
        versionNumber={item.version.version_number}
      />
    </Card>
  );
}
