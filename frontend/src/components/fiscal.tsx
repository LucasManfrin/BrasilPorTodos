import { money, warnings } from "@/lib/format";
import { historicalFiscalIssueMessage } from "@/lib/fiscal-compatibility";
import type { FiscalCompatibility, Simulation } from "@/lib/types";
import { FiscalScenarioResult } from "./fiscal-scenario-result";
export function FiscalResult({ result }: { result: Simulation }) {
  const compatibility = result.assumptions?.fiscal_compatibility;
  const aggregateUncertain = result.warnings.some((warning) =>
    ["FISCAL_METADATA_MISSING", "FISCAL_AGGREGATE_HETEROGENEOUS"].includes(warning.code));
  const priceCaption = result.assumptions?.price_basis === "NOMINAL"
    ? "Impacto por ano, em reais nominais"
    : result.assumptions?.price_basis === "CONSTANT"
      ? "Impacto por ano, em reais a preços de " + (result.assumptions?.price_base_year ?? "ano-base não informado")
      : "Impacto por ano, em reais declarados; confira a base de preços das parcelas";
  return (
    <>
    <section className="fiscal" aria-labelledby={`calculo-${result.id}`}>
      <p className="eyebrow">Impacto fiscal incremental</p>
      <h2 id={`calculo-${result.id}`}>
        {aggregateUncertain
          ? "Somatório aritmético das parcelas"
          : result.is_partial
            ? "Total parcial das medidas estimadas"
            : "Total das medidas estimadas"}
      </h2>
      <p className="large-number">{money(result.cumulative_impact)}</p>
      <p>
        {aggregateUncertain
          ? "Somatório aritmético do período. As parcelas usam recortes diferentes ou não informados; o sinal não indica um saldo fiscal comparável."
          : "Somatório incremental do período, separado da referência histórica. Valores positivos aumentam o saldo pelas medidas declaradas; negativos o reduzem. Isso não valida as estimativas nem seus efeitos."}
      </p>
      <FiscalCompatibilityPanel assessment={compatibility} />
      {result.warnings.length > 0 && (
        <div className="notice">
          <h3>O que considerar</h3>
          <ul>
            {[...new Set(result.warnings.map((warning) => warning.code))].map(
              (code) => (
                <li key={code}>{warnings[code] ?? code}</li>
              ),
            )}
          </ul>
        </div>
      )}
      <div className="table-scroll">
        <table>
          <caption>{priceCaption}</caption>
          <thead>
            <tr>
              <th scope="col">Ano</th>
              <th scope="col">Novas receitas</th>
              <th scope="col">Economias</th>
              <th scope="col">Novas despesas</th>
              <th scope="col">Receitas reduzidas</th>
              <th scope="col">Líquido</th>
            </tr>
          </thead>
          <tbody>
            {result.years.map((year) => (
              <tr key={year.year}>
                <th scope="row">{year.year}</th>
                <td>{money(year.new_revenues)}</td>
                <td>{money(year.expense_reductions)}</td>
                <td>{money(year.new_expenses)}</td>
                <td>{money(year.revenue_reductions)}</td>
                <td>{money(year.net_impact)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted">
        Método {result.engine_version}. O resultado soma os impactos
        cadastrados; não prevê PIB, inflação ou dívida futura.
      </p>
    </section>
    <FiscalScenarioResult result={result.assumptions?.fiscal_scenario} />
    </>
  );
}
const compatibilityLabels = {
  COMPATIBLE: "Recortes declarados compatíveis",
  NOT_COMPARABLE: "Sem comparação com a referência",
  INCOMPLETE: "Informações fiscais incompletas",
  NO_IMPACTS: "Sem parcelas fiscais avaliáveis",
};
export function FiscalCompatibilityPanel({ assessment }: { assessment?: FiscalCompatibility }) {
  if (!assessment) return (
    <div className="notice">
      <h3>Compatibilidade não avaliada nesta execução</h3>
      <p>Esta execução foi preservada sem uma avaliação dos recortes fiscais. Nenhuma informação ausente foi completada depois da publicação.</p>
    </div>
  );
  const issues = [...new Set([
    ...assessment.issues.map(historicalFiscalIssueMessage),
    ...assessment.impacts.flatMap((impact) => impact.issues.map(historicalFiscalIssueMessage)),
  ])];
  return (
    <div className="notice">
      <h3>Comparação com a referência histórica</h3>
      <p><strong>{compatibilityLabels[assessment.status]}</strong>
        {assessment.baseline_year !== null ? " · referência de " + assessment.baseline_year : " · ano de referência indisponível"}</p>
      <p>Esta avaliação compara somente os recortes declarados: governo, ano, período, preços, contagem e juros. Não comprova os custos nem as relações de causa e efeito. A referência histórica não foi somada às medidas.</p>
      {issues.length > 0 && <ul>{issues.map((message) => <li key={message}>{message}</li>)}</ul>}
      {assessment.impacts.length > 0 && (
        <details>
          <summary>Conferir avaliação de cada parcela</summary>
          <ul>{assessment.impacts.map((impact, index) => (
            <li key={impact.impact_id}>
              Parcela {index + 1} · {impact.year}: {compatibilityLabels[impact.status]}
              {impact.issues.length > 0 && <ul>{impact.issues.map((issue, i) => <li key={i}>{historicalFiscalIssueMessage(issue)}</li>)}</ul>}
            </li>
          ))}</ul>
        </details>
      )}
      <p className="muted">Avaliação {assessment.version}, preservada com esta execução. Anos futuros só são comparados a um cenário declarado e confirmado pelo autor; a referência histórica não se transforma automaticamente em previsão.</p>
    </div>
  );
}
