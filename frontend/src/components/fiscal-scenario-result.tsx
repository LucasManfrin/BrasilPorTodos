import type { FiscalScenarioResultData } from "@/lib/fiscal-scenario";
import { formatCompact, formatExact } from "@/lib/data-format";
import styles from "./fiscal-scenario.module.css";

function Amount({ value, unavailable = "Não informado" }: { value: string | null | undefined; unavailable?: string }) {
  if (value === null || value === undefined) return <span>{unavailable}</span>;
  return <span className={styles.amount} title={formatExact(value, "R$")}>{formatCompact(value, "R$")}</span>;
}
function IssueList({ issues }: { issues: FiscalScenarioResultData["issues"] }) {
  if (!issues?.length) return null;
  return <ul>{[...new Set(issues.map((issue) => issue.message ?? issue.code))].map((text) => <li key={text}>{text}</li>)}</ul>;
}
export function FiscalScenarioResult({ result }: { result?: FiscalScenarioResultData | null }) {
  if (!result) return null;
  const combinedCount = result.years.filter((row) => row.combined !== null).length;
  return (
    <section className={"fiscal " + styles.result}>
      <h2>Cenário futuro declarado</h2>
      <h3>{result.scenario.title}</h3>
      <p>Premissas do autor para o Governo Central, em caixa, reais nominais e anos inteiros, sem juros. São valores declarados; não são uma previsão oficial.</p>
      <p className="preserve">{result.scenario.explanation}</p>
      <p className="muted">Referência histórica
        {result.historical_year !== null ? " de " + result.historical_year : " indisponível"}: somente contexto, sem anualização nem crescimento automático.</p>
      <div className="notice">
        <p>{combinedCount === result.years.length && combinedCount > 0
          ? "Comparação calculada para os anos informados, conforme as premissas preservadas."
          : "Há anos sem comparação disponível. Não substituímos uma comparação bloqueada por zero."}</p>
        <p>Só exibimos “Com as propostas” quando a combinação com o cenário confirmado é permitida. Isso não demonstra que as estimativas ou os efeitos econômicos estejam corretos.</p>
        {(result.aggregate_basis !== "HOMOGENEOUS" || result.price_basis !== "NOMINAL") && <p>As medidas incrementais têm preços ou recortes diferentes do cenário, ou informações incompletas. A última coluna conserva os valores declarados e não os converte em reais nominais.</p>}
        {result.incremental_is_partial && <p>Há medidas sem estimativa. O impacto incremental é parcial.</p>}
        <IssueList issues={result.issues} />
        <IssueList issues={result.warnings} />
      </div>
      <div className="table-scroll">
        <table>
          <caption>Cenário e combinação em reais nominais; impactos conforme os preços e recortes declarados. Valores completos no título de cada número</caption>
          <thead>
            <tr><th scope="col">Ano</th><th scope="col">Conta</th><th scope="col">Cenário declarado</th><th scope="col">Com as propostas</th><th scope="col">Impacto incremental</th></tr>
          </thead>
          <tbody>
            {result.years.flatMap((row) => ([
              ["net_revenue", "Receita primária líquida"],
              ["primary_expenditure", "Despesa primária"],
              ["primary_balance", "Resultado primário"],
            ] as const).map(([account, label], index) => (
              <tr key={row.year + "-" + account}>
                {index === 0 && <th scope="rowgroup" rowSpan={3}>{row.year}</th>}
                <th scope="row">{label}</th>
                <td><Amount value={row.declared[account]} /></td>
                <td>{row.combined === null ? <span>Comparação indisponível</span> : <Amount value={row.combined[account]} />}</td>
                <td>{account === "primary_balance"
                  ? <Amount value={row.incremental.net_impact} />
                  : account === "net_revenue"
                    ? <><Amount value={row.incremental.new_revenues} /> em novas receitas<br /><Amount value={row.incremental.revenue_reductions} /> em receitas reduzidas</>
                    : <><Amount value={row.incremental.new_expenses} /> em novas despesas<br /><Amount value={row.incremental.expense_reductions} /> em economias</>}</td>
              </tr>
            )))}
          </tbody>
        </table>
      </div>
      <details className="notice">
        <summary>Conferir premissas, fontes e limites preservados</summary>
        <p>Referência da base: {result.scenario.reference_baseline_id || "Não informada"}.</p>
        <p>{result.scenario.excludes_plan_impacts
          ? "O autor confirmou que o cenário não inclui o efeito das propostas selecionadas. A revisão vale para a composição e as premissas preservadas nesta execução."
          : "O autor não confirmou a exclusão das propostas deste cenário. Não tratamos os valores declarados como uma conta sem essas medidas."}</p>
        {result.scenario.years.map((row) => (
          <div key={row.year}>
            <h3>{row.year}</h3>
            <p className="preserve">{row.justification || "Justificativa não informada."}</p>
            <p>Receita exata: {row.net_revenue === null ? "Não informada" : formatExact(row.net_revenue, "R$")} · Despesa exata: {row.primary_expenditure === null ? "Não informada" : formatExact(row.primary_expenditure, "R$")}</p>
            {row.source_urls.length > 0 ? <ul>{row.source_urls.map((url, index) => (
              <li key={index}><a href={url} target="_blank" rel="noopener noreferrer">{url} ↗</a></li>
            ))}</ul> : <p className="muted">Sem URLs declaradas para este ano.</p>}
          </div>
        ))}
        <IssueList issues={result.impacts?.flatMap((impact) => impact.issues) ?? []} />
        {result.limitations.length > 0 && <ul>{result.limitations.map((text) => <li key={text}>{text}</li>)}</ul>}
        <p className="muted">Método do cenário {result.scenario_method_version} · motor incremental {result.aggregation_engine_version}. Resultado preservado; a página não recalcula as parcelas.</p>
      </details>
    </section>
  );
}
