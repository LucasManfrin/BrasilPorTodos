"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { FiscalBaseline, GeneralGovernment, GeneralGovernmentSectorCode } from "@/lib/types";
import { dateLabel, formatCompact, formatExact } from "@/lib/data-format";
import { generalGovernmentState, governmentFinancingLabel, governmentMetricLabels, governmentMetrics, governmentSectorLabels, governmentVisibleSectors } from "@/lib/general-government";
import styles from "./general-government.module.css";

export function GeneralGovernmentPanel({ fiscal, government }: { fiscal?: FiscalBaseline | null; government?: GeneralGovernment | null }) {
  const router = useRouter();
  const [sector, setSector] = useState<GeneralGovernmentSectorCode>("GENERAL");
  const state = generalGovernmentState(fiscal, government);
  if (state !== "READY" || !government?.payload) {
    return <details className={styles.panel}>
      <summary>União, estados e municípios</summary>
      <p>{state === "MISMATCH" ? "O Governo Geral e a referência RTN estão em anos diferentes. Recarregue para consultar o mesmo ano; os critérios de cada conta continuam separados." : "Ainda não temos um demonstrativo anual completo e verificado para este ano. Ausência de dado não significa receita ou gasto zero."}</p>
      {government?.missing?.length ? <ul>{government.missing.map((text, index) => <li key={index}>{text}</li>)}</ul> : null}
      <button className="button secondary" onClick={() => router.refresh()}>Recarregar dados salvos</button>
    </details>;
  }
  const p = government.payload;
  const chosen = p.sectors.find(row => row.sector === sector)!;
  const financingLabel = governmentFinancingLabel(chosen.amounts.net_lending);
  const titles = { revenue: "Receita", expense: "Despesa total", net_lending: financingLabel };
  return <details className={styles.panel}>
    <summary>União, estados e municípios · {government.year}</summary>
    <p>O Governo Geral reúne as três esferas, com operações internas eliminadas pela fonte. Esta conta segue o MEFP 2014, por competência modificada; o Banco Central fica fora do Governo Central deste demonstrativo.</p>
    <label className={styles.selector}>Qual recorte você quer ver?
      <select value={sector} onChange={event => setSector(event.target.value as GeneralGovernmentSectorCode)}>
        {governmentVisibleSectors.map(value => <option key={value} value={value}>{governmentSectorLabels[value]}</option>)}
      </select>
    </label>
    <p className={styles.coverage}>A fonte reúne {p.coverage.states_units} unidades estaduais e considera {p.coverage.municipal_units.toLocaleString("pt-BR")} municípios. A coleta municipal cobre aproximadamente {p.coverage.municipal_collection_approx_percent}% e é extrapolada: os valores municipais, e portanto o Governo Geral, incluem estimativas.</p>
    <dl className={styles.values} aria-live="polite">
      {(["revenue", "expense", "net_lending"] as const).map(metric => <div key={metric}>
        <dt>{titles[metric]}</dt>
        <dd><strong title={formatExact(chosen.amounts[metric], "R$")}>{formatCompact(chosen.amounts[metric], "R$")}</strong>
          <small>{metric === "revenue" ? "Receita no critério desta fonte" : metric === "expense" ? "Gasto + investimento líquido em ativos não financeiros" : "Receita − despesa total; sinal publicado preservado"}</small>
        </dd>
      </div>)}
    </dl>
    <p>{chosen.label} · reais correntes · ano completo. Capacidade de financiamento não é dinheiro livre no caixa. A necessidade inclui os juros no critério do demonstrativo e não é uma previsão.</p>
    <details className={styles.method}>
      <summary>Consolidação, valores exatos e fonte</summary>
      <p>Os oito grupos abaixo são as colunas da tabela 2.1. As colunas de consolidação mantêm os sinais oficiais: removem operações internas e não são um novo ente para somar.</p>
      <p>Central = orçamentário + extraorçamentário + consolidação central. Geral = Central + estados + municípios + consolidação do Governo Geral. O total consolidado já incorpora suas parcelas; somar total e filhos duplicaria valores.</p>
      <div className={styles.scroll} tabIndex={0} aria-label="Valores exatos e consolidação oficial do Governo Geral">
        <table>
          <caption>Tabela 2.1 · {government.year} · valores em reais, convertidos dos milhões publicados</caption>
          <thead><tr><th scope="col">Medida</th>{p.sectors.map(row => <th key={row.sector} scope="col">{governmentSectorLabels[row.sector]}</th>)}</tr></thead>
          <tbody>{governmentMetrics.map(metric => <tr key={metric}>
            <th scope="row">{governmentMetricLabels[metric]}</th>
            {p.sectors.map(row => <td key={row.sector} title={`Célula ${row.cells[metric]} · original: ${row.raw_millions[metric]} milhões`}>{formatExact(row.amounts[metric], "R$")}</td>)}
          </tr>)}</tbody>
        </table>
      </div>
      <p>“Gasto” e “despesa total” são medidas distintas: despesa total inclui investimento líquido em ativos não financeiros. O investimento líquido pode ser negativo. Juros na receita integram o resultado; juros no gasto seguem esta apuração, sem serem substituídos pela Selic ou pelo painel BCB.</p>
      <dl className={styles.exact}>
        {governmentMetrics.map(metric => <div key={metric}><dt>{governmentMetricLabels[metric]} · {governmentSectorLabels[sector]}</dt><dd>{formatExact(chosen.amounts[metric], "R$")}</dd></div>)}
      </dl>
      <details className={styles.audit}>
        <summary>Células originais e diferenças preservadas</summary>
        <div className={styles.scroll} tabIndex={0} aria-label="Células originais e precisão dos valores do recorte selecionado">
          <table className={styles.original}>
            <caption>{governmentSectorLabels[sector]} · valores originais em R$ milhões</caption>
            <thead><tr><th scope="col">Medida</th><th scope="col">Célula 2.1</th><th scope="col">Valor original em milhões</th></tr></thead>
            <tbody>{governmentMetrics.map(metric => <tr key={metric}><th scope="row">{governmentMetricLabels[metric]}</th><td>{chosen.cells[metric]}</td><td className={styles.raw}>{chosen.raw_millions[metric].replace(".", ",")}</td></tr>)}</tbody>
          </table>
        </div>
        <p>Receita − despesa total = capacidade (+)/necessidade (−). A medida primária MEFP = capacidade/necessidade + juros no gasto − juros na receita. Conferência por célula: tolerância {formatExact(p.reconciliation.tolerance, "R$")}; as identidades mostram publicado menos calculado, sem ajustar valores para forçar igualdade.</p>
        <dl className={styles.exact}>{p.reconciliation.identities.filter(row => row.sector === sector).flatMap(row => [["Despesa total − (gasto + investimento líquido)", row.expense_difference], ["Capacidade/necessidade − (receita − despesa total)", row.net_lending_difference], ["Medida primária publicada − medida calculada", row.primary_difference]]).map(([label, amount]) => <div key={label}><dt>{label}</dt><dd>{formatExact(amount, "R$")}</dd></div>)}</dl>
        <div className={styles.scroll} tabIndex={0} aria-label="Diferenças da consolidação e conferência do Governo Geral">
          <table>
            <caption>Consolidação e conferência com a tabela 3.1 do mesmo arquivo</caption>
            <thead><tr><th scope="col">Medida</th><th scope="col">Diferença Central</th><th scope="col">Diferença Geral</th><th scope="col">2.1 − 3.1</th><th scope="col">Célula 3.1</th></tr></thead>
            <tbody>{p.reconciliation.consolidation.map(row => {
              const reference = p.reconciliation.general_reference.find(value => value.metric === row.metric)!;
              return <tr key={row.metric}><th scope="row">{governmentMetricLabels[row.metric]}</th><td>{formatExact(row.central_difference, "R$")}</td><td>{formatExact(row.general_difference, "R$")}</td><td>{formatExact(reference.difference, "R$")}</td><td>{reference.cell}</td></tr>;
            })}</tbody>
          </table>
        </div>
        <p>A tabela 3.1 é uma conferência interna da mesma publicação, não uma segunda fonte independente. Milhões da planilha são convertidos para reais e normalizados a centavos pelo parser; isso não aumenta a precisão econômica dos dados estimados.</p>
      </details>
      <h3>Por que estas contas não são somadas às outras?</h3>
      <div className={styles.scroll} tabIndex={0} aria-label="Diferenças de critérios entre as camadas fiscais">
        <table className={styles.criteria}>
          <caption>Correspondência de critérios · nenhuma equivalência de valores é presumida</caption>
          <thead><tr><th scope="col">Camada</th><th scope="col">O que ela mede</th></tr></thead>
          <tbody>
            <tr><th scope="row">Governo Geral · MEFP 2014</th><td>Três esferas, consolidação oficial, competência modificada e extrapolação municipal. Central sem Banco Central.</td></tr>
            <tr><th scope="row">Conta primária RTN</th><td>Governo Central com Banco Central, acima da linha, caixa e sem juros. Seu primário não é a medida primária MEFP.</td></tr>
            <tr><th scope="row">Juros e nominal BCB/RTN</th><td>Abaixo da linha, primário de caixa e juros por competência. Não são as receitas ou os gastos deste demonstrativo.</td></tr>
            <tr><th scope="row">Gasto federal por função</th><td>Execução por ordem bancária/valor pago, RAP e ajustes Extra-Siafi. Não é classificação MEFP ou COFOG nem gasto de todos os entes.</td></tr>
          </tbody>
        </table>
      </div>
      <p>{government.methodology}</p>
      <p>Referência: {dateLabel(government.period_start)} a {dateLabel(government.period_end)} · coletado em {dateLabel(government.collected_at)} · revisão {government.revision}. Publicação: {dateLabel(p.resource.published_at)} · atualização na origem: {dateLabel(p.resource.updated_at)}. As datas da publicação não mudam o ano do dado.</p>
      <p>Parser {p.parser_version} · precisão {p.precision_version} · arquivo {(p.resource.size / 1000000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MB. SHA-256: <code className={styles.hash}>{p.resource.sha256}</code>. Identificador do conjunto: <code className={styles.hash}>{government.cohort_fingerprint}</code>.</p>
      <p><a href={government.source!.url} target="_blank" rel="noopener noreferrer">{government.source!.title} ↗</a> · {government.source!.institution} · <a href={government.source!.license_url} target="_blank" rel="noopener noreferrer">{government.source!.license}</a> · <a href={p.resource.publication_url} target="_blank" rel="noopener noreferrer">Página da publicação ↗</a> · <a href={p.resource.url} target="_blank" rel="noopener noreferrer">Planilha desta revisão ↗</a>.</p>
      <ul>{government.limitations.map((text, index) => <li key={index}>{text}</li>)}</ul>
    </details>
  </details>;
}
