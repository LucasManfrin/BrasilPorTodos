"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Button, Icon } from "@/components/ui";
import { fetchApi } from "@/lib/api";
import { dateLabel, formatExact, getTrend, referenceLabel, selectCalendarPeriod } from "@/lib/data-format";
import type { Indicator } from "@/lib/indicator-types";
import { IndicatorContexts } from "@/features/contexts/indicator-contexts";
import { SeriesChart } from "./series-chart";
import styles from "./indicators.module.css";

type LoadResult = { code: string; attempt: number; data?: Indicator; error?: string };

export function IndicatorDrawer({ item, onClose }: { item: Indicator | null; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const [result, setResult] = useState<LoadResult | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [period, setPeriod] = useState<"1y" | "5y" | "max">("5y");
  const code = item?.code;
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!code || !dialog) return;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    const previousPadding = document.body.style.paddingRight;
    const gap = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = "hidden";
    if (gap > 0) document.body.style.paddingRight = `${parseFloat(getComputedStyle(document.body).paddingRight) + gap}px`;
    if (!dialog.open) dialog.showModal();
    closeRef.current?.focus();
    return () => {
      if (dialog.open) dialog.close();
      document.body.style.overflow = previousOverflow;
      document.body.style.paddingRight = previousPadding;
      if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true });
    };
  }, [code]);
  useEffect(() => {
    if (!code) return;
    const controller = new AbortController();
    fetchApi<Indicator>(`indicators/${encodeURIComponent(code)}`, { signal: controller.signal }).then(response => {
      if (!controller.signal.aborted) setResult({ code, attempt, data: response.data });
    }).catch(error => {
      if (!controller.signal.aborted) setResult({ code, attempt, error: error instanceof Error ? error.message : "Não foi possível carregar o histórico." });
    });
    return () => controller.abort();
  }, [code, attempt]);
  const currentResult = result && result.code === code && result.attempt === attempt ? result : null;
  const detail = currentResult?.data ?? item;
  const latest = detail?.latest;
  const series = detail?.series?.length ? detail.series : detail?.history?.length ? detail.history : item?.series ?? [];
  const trend = detail ? getTrend({ ...detail, series: selectCalendarPeriod(series, "max") }) : undefined;
  const balanceLabel = latest && detail?.code === "rtn-resultado-primario" ? !/[1-9]/.test(latest.value) ? "Equilíbrio primário" : latest.value.startsWith("-") ? "Déficit primário" : "Superávit primário" : null;
  return (
    <dialog ref={dialogRef} className={styles.drawer} aria-labelledby={titleId} onCancel={event => { event.preventDefault(); onClose(); }} onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
      {detail && <div className={styles.drawerPanel}>
        <header className={styles.drawerHeader}><div><span className={styles.drawerEyebrow}>O número em contexto</span><h2 id={titleId}>{detail.name}</h2></div><button ref={closeRef} type="button" className={`icon-button ${styles.close}`} onClick={onClose} aria-label="Fechar detalhes">×</button></header>
        {!currentResult && <p className={styles.loadStatus} role="status">Carregando histórico e fontes…</p>}
        {currentResult?.error && <div className={styles.loadError} role="alert"><p>{currentResult.error}</p><Button variant="secondary" onClick={() => setAttempt(value => value + 1)}>Tentar novamente</Button></div>}
        <section className={styles.drawerValue}>{latest ? <><p className={styles.exactValue}>{formatExact(latest.value, detail.unit)}</p>{balanceLabel && <p className={styles.drawerReference}>{balanceLabel}</p>}<p className={styles.drawerReference}>Referência: {referenceLabel(latest.reference_date, detail.frequency)}{["desocupacao", "renda-trabalho-real", "informalidade", "participacao-forca-trabalho"].includes(detail.code) ? " · trimestre móvel encerrado no mês" : ""}</p><p className={styles.drawerTrend}><span aria-hidden="true">{trend?.symbol}</span> {trend?.label}</p></> : <p>Sem observações disponíveis. Ausência de dado não representa zero.</p>}</section>
        <section className={styles.drawerSection} aria-labelledby={`${titleId}-history`}><div className={styles.historyHeading}><h3 id={`${titleId}-history`}>O número no tempo</h3><div className={styles.periodControls} role="group" aria-label="Período do histórico">{(["1y", "5y", "max"] as const).map(value => <button key={value} type="button" className={`icon-button ${styles.periodButton}`} aria-pressed={period === value} onClick={() => setPeriod(value)}>{value === "1y" ? "1 ano" : value === "5y" ? "5 anos" : "Máx."}</button>)}</div></div><SeriesChart points={selectCalendarPeriod(series, period)} name={detail.name} unit={detail.unit} frequency={detail.frequency} trend={trend} large /><p className={styles.chartNote}>Escala ajustada ao período. Última revisão de cada referência; meses sem dado permanecem ausentes.</p></section>
        <section className={styles.drawerSection}><h3>O que este indicador mostra</h3><p>{detail.description}</p><p className={styles.contextNote}>Uma mudança neste número, sozinha, não explica suas causas nem avalia a qualidade de uma política.</p></section>
        <section className={styles.drawerSection}><h3>Fonte e método</h3>{detail.code === "renda-trabalho-real" && <p>Rendimento real habitual em todos os trabalhos, por pessoa ocupada. Preços do trimestre móvel encerrado em {latest?.provenance.income_price_reference ? referenceLabel(latest.provenance.income_price_reference) : "referência ainda não informada"}. O histórico foi consultado na mesma base de preços; esta renda não é receita fiscal.</p>}<dl className={styles.metadata}><div><dt>Abrangência</dt><dd>{detail.scope}</dd></div><div><dt>Unidade</dt><dd>{detail.unit}</dd></div><div><dt>Frequência</dt><dd>{{ DAILY: "Diária", MONTHLY: "Mensal", QUARTERLY: "Trimestral", ANNUAL: "Anual", YEARLY: "Anual" }[detail.frequency] ?? detail.frequency}</dd></div>{detail.base_year && <div><dt>Ano-base</dt><dd>{detail.base_year}</dd></div>}</dl><p>{detail.methodology}</p>{latest && <><dl className={styles.metadata}><div><dt>Instituição</dt><dd>{latest.source.institution}</dd></div><div><dt>Referência</dt><dd>{dateLabel(latest.reference_date)}</dd></div><div><dt>Coleta</dt><dd>{dateLabel(latest.retrieved_at)}</dd></div><div><dt>Revisão</dt><dd>{latest.revision}</dd></div><div><dt>Licença / termos</dt><dd>{latest.provenance.license ?? latest.source.license ?? "Não informados"}{latest.source.license_url && <> · <a href={latest.source.license_url} target="_blank" rel="noopener noreferrer">Consultar termos ↗</a></>}</dd></div></dl><a className={styles.externalSource} href={latest.source.url} target="_blank" rel="noopener noreferrer">{latest.source.title}<Icon name="arrow" /></a>{latest.provenance.method && <p className={styles.chartNote}>{latest.provenance.method}</p>}{latest.source.is_example && <p className={styles.contextNote}>Exemplo fictício para demonstração; não representa uma estatística do país.</p>}</>}</section>
        <IndicatorContexts indicatorCode={detail.code} latestObservationId={latest?.id} />
        <footer className={styles.drawerFooter}><Button href={`/painel/propostas/nova?indicador=${encodeURIComponent(detail.code)}`} variant="secondary">Usar em proposta<Icon name="edit" /></Button><a href={`/brasil/${encodeURIComponent(detail.code)}`}>Abrir página completa ↗</a></footer>
      </div>}
    </dialog>
  );
}
