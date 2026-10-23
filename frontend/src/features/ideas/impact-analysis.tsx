"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { formatCompact } from "@/lib/data-format";
import { money } from "@/lib/format";
import { defaultPercentages, sensitivityAssumptions } from "./impact-state";
import type { SensitivityPercentages } from "./impact-state";
import styles from "./impact-analysis.module.css";

type Sensitivity = {
  available: boolean; reason?: string; method_version: string; engine_version?: string;
  classification?: string; unknowns?: string[]; assumptions?: SensitivityPercentages;
  scenarios?: { key: "lower" | "declared" | "upper"; label: string; cumulative_impact: string; years: { year: number; net_impact: string }[] }[];
};
const labels = { cost_low: "Mínimo (%)", cost_high: "Máximo (%)", gain_low: "Mínimo (%)", gain_high: "Máximo (%)" };

export function ImpactAnalysis({ slug, version }: { slug: string; version: number }) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<SensitivityPercentages>(defaultPercentages);
  const [response, setResponse] = useState<{ key: string; data: Sensitivity } | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const requestKey = JSON.stringify([slug, version, values]);
  let validation = "";
  try { sensitivityAssumptions(values); } catch (e) { validation = e instanceof Error ? e.message : "Confira os percentuais."; }
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      let assumptions: SensitivityPercentages;
      try { assumptions = sensitivityAssumptions(JSON.parse(requestKey)[2]); }
      catch { return; }
      setError("");
      const query = new URLSearchParams({ version: String(version), ...assumptions });
      fetchApi<Sensitivity>(`guidance/impact/${encodeURIComponent(slug)}?${query}`, { signal: controller.signal })
        .then((result) => { if (!controller.signal.aborted) setResponse({ key: requestKey, data: result.data }); })
        .catch((e: Error) => { if (!controller.signal.aborted) setError(e.message); });
    }, 300);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [slug, version, open, requestKey, retry]);
  const data = response?.key === requestKey ? response.data : null;
  const years = [...new Set(data?.scenarios?.flatMap((scenario) => scenario.years.map((item) => item.year)) ?? [])].sort((a, b) => a - b);
  return <details className={styles.analysis} onToggle={(event) => setOpen(event.currentTarget.open)}>
    <summary>Se as premissas mudarem, como a conta muda?</summary>
    <div className={styles.content}><span className={styles.badge}>Sensibilidade da estimativa declarada</span>
      <p>O motor recalcula os impactos informados pelo autor. Você escolhe como custos e ganhos variam; a IA não faz esta conta.</p>
      <p className={styles.notice}>Os limites começam em 100%: todos os resultados são iguais até você alterar uma premissa. A faixa é uma hipótese sua, sem probabilidade ou confiança estatística. Ela não prevê efeitos econômicos, comportamentos ou o saldo do país.</p>
      <div className={styles.inputs}>{([['Custos e receitas reduzidas', 'cost_low', 'cost_high'], ['Receitas e economias', 'gain_low', 'gain_high']] as const).map(([legend, low, high]) => <fieldset key={low}><legend>{legend}</legend><div className={styles.fields}>{([low, high] as const).map((key) => <label key={key}>{labels[key]}<input inputMode="decimal" value={values[key]} aria-invalid={Boolean(validation)} onChange={(event) => setValues((current) => ({ ...current, [key]: event.target.value }))} aria-describedby={`sensitivity-limits-${version}`} /></label>)}</div></fieldset>)}</div>
      <p id={`sensitivity-limits-${version}`} className={styles.muted}>100% mantém o valor declarado. Mínimos: de 0 a 100%. Máximos: de 100 a 200%. Até duas casas decimais.</p>
      <button onClick={() => setValues({ ...defaultPercentages })}>Restaurar premissas declaradas</button>
      {validation && <p role="alert">{validation}</p>}
      {error && <p className={styles.notice} role="alert">{error} <button onClick={() => setRetry((count) => count + 1)}>Tentar de novo</button></p>}
      {open && !validation && !error && !data && <p role="status">Recalculando no motor fiscal…</p>}
      {data && !validation && <div aria-live="polite">
        {!data.available ? <p className={styles.notice}>{data.reason || "Ainda não há dados comparáveis suficientes para esta análise. Nenhum valor ausente foi tratado como zero."}</p> : <>
          <div className={styles.scenarios}>{data.scenarios?.map((scenario) => <section className={styles.scenario} key={scenario.key}><h3>{scenario.label}</h3><strong className={styles.value} title={money(scenario.cumulative_impact)}>{formatCompact(scenario.cumulative_impact, "BRL")}</strong><p className={styles.muted}>Saldo incremental acumulado das medidas.</p></section>)}</div>
          <p>O limite inferior combina custos máximos com ganhos mínimos; o superior combina custos mínimos com ganhos máximos. Financiamento declarado não é contado novamente como receita.</p>
          <div className={styles.table}><table><caption>Resultado incremental por ano, em reais</caption><thead><tr><th scope="col">Ano</th>{data.scenarios?.map((scenario) => <th scope="col" key={scenario.key}>{scenario.label}</th>)}</tr></thead><tbody>{years.map((year) => <tr key={year}><th scope="row">{year}</th>{data.scenarios?.map((scenario) => { const item = scenario.years.find((entry) => entry.year === year); return <td key={scenario.key}>{item ? money(item.net_impact) : "Não informado"}</td>; })}</tr>)}</tbody></table></div>
        </>}
        {Boolean(data.unknowns?.length) && <section><h3>O que esta conta não sabe</h3><ul>{data.unknowns?.map((unknown, index) => <li key={index}>{unknown}</li>)}</ul></section>}
        <p className={styles.muted}>Método: {data.method_version}{data.engine_version ? ` · motor ${data.engine_version}` : ""} · versão {version} da proposta. <Link href="/metodologia">Conferir metodologia</Link></p>
      </div>}
    </div>
  </details>;
}
