"use client";

import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type { Source } from "@/lib/types";
import type { CollectionStatus } from "@/components/collection-status";
import { dateLabel, referenceLabel } from "@/lib/data-format";
import { EmptyState } from "@/components/page-kit";
import {
  filterSources,
  groupSources,
  sourceCollectionState,
  sourceFacets,
  sourceKinds,
  type DirectoryIndicator,
  type DirectorySource,
  type SourceFilters,
} from "./source-helpers";
import styles from "./sources.module.css";

function externalLink(value: string | null | undefined) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? value : null;
  } catch { return null; }
}

function seriesLabel(row: DirectorySource) {
  if (row.identity.startsWith("bcb:")) return `SGS ${row.identity.split(":")[1]}`;
  if (row.identity.startsWith("ibge:")) {
    const [, table, variable] = row.identity.split(":");
    return `SIDRA ${table} · variável ${variable}`;
  }
  return row.identity === "tesouro:rtn" ? "RTN · Governo Central" : null;
}

/** Each source stays one semantic table row, including on narrow screens. */
export function SourceRow({ row, collection, now }: { row: DirectorySource; collection: CollectionStatus | null; now: number }) {
  const state = sourceCollectionState(row, collection, now);
  const references = [...new Set(row.metrics.flatMap(metric => metric.referenceDate
    ? [metric.frequency === "DAILY" ? dateLabel(metric.referenceDate) : referenceLabel(metric.referenceDate, metric.frequency)]
    : []))];
  const href = externalLink(row.source.url);
  const licenseHref = externalLink(row.source.license_url);
  const identifier = seriesLabel(row);
  return (
    <tr className={styles.sourceRow}>
      <th scope="row" className={styles.sourceCell}>
        <div className={styles.sourceTitle}>{row.source.title}</div>
        <div className={styles.sourceType}>
          <span>{sourceKinds[row.source.source_type] ?? "Referência"}</span>
          {identifier && <span>{identifier}</span>}
        </div>
        <div className={styles.visibleMetadata}>
          {row.source.license ? licenseHref
            ? <a className={styles.license} href={licenseHref} target="_blank" rel="noopener noreferrer">{row.source.license} ↗</a>
            : <span className={styles.license}>{row.source.license}</span>
            : <span className={styles.muted}>Termos não informados</span>}
          <span className={styles.muted}>Acesso cadastrado: {dateLabel(row.source.accessed_at)}</span>
        </div>
        <div className={styles.badges}>
          {row.source.is_example && <span className={styles.example}>Exemplo fictício</span>}
          {row.hasUsage && <span className={styles.usage}>{row.usageCount === null
            ? "Usada em publicações"
            : `${row.usageCount} ${row.usageCount === 1 ? "proposta publicada usa" : "propostas publicadas usam"} esta fonte`}</span>}
        </div>
        <details className={styles.metadata}>
          <summary>Ver metadados{row.records.length > 1 ? ` · ${row.records.length} registros preservados` : ""}</summary>
          <div className={styles.metadataBody}>
            <p><strong>Uso dos dados:</strong> {row.source.license
              ? licenseHref ? <a href={licenseHref} target="_blank" rel="noopener noreferrer">{row.source.license} ↗</a> : row.source.license
              : "Termos não informados pelo autor"}</p>
            <p><strong>Acesso informado no cadastro:</strong> {dateLabel(row.source.accessed_at)}. Essa data não é a última coleta.</p>
            {row.source.publication_date && <p><strong>Publicação informada:</strong> {dateLabel(row.source.publication_date)}</p>}
            {row.metrics.length > 0 && <>
              <strong>Indicadores vinculados</strong>
              <ul>{row.metrics.map(metric => <li key={metric.code}>{metric.name} <span className={styles.code}>({metric.code})</span></li>)}</ul>
            </>}
            <strong>{row.records.length > 1 ? "Registros históricos" : "Registro da fonte"}</strong>
            <ul>{row.records.map(record => <li key={record.id}>{record.title}<br /><span className={styles.code}>ID: {record.id}</span></li>)}</ul>
          </div>
        </details>
      </th>
      <td className={styles.referenceCell}>
        <span className={styles.mobileLabel}>Referência do dado</span>
        {references.length ? references.map(value => <strong key={value}>{value}</strong>) : <span className={styles.muted}>Não informada</span>}
        {row.metrics.length > 1 && <span className={styles.muted}>{row.metrics.length} indicadores</span>}
      </td>
      <td className={styles.collectionCell}>
        <span className={styles.mobileLabel}>Consulta automática</span>
        <span className={`${styles.collectionState} ${styles[state.tone]}`}><i aria-hidden="true" />{state.label}</span>
        {state.timestamp && <span className={styles.muted}>{dateLabel(state.timestamp)}</span>}
        {state.tone === "warning" && <span className={styles.saved}>Dados salvos preservados.</span>}
      </td>
      <td className={styles.actionCell}>
        {href ? <a className={styles.openSource} href={href} target="_blank" rel="noopener noreferrer" aria-label={`Abrir fonte: ${row.source.title}`}>Abrir fonte <span aria-hidden="true">↗</span></a>
          : <span className={styles.muted}>Link indisponível</span>}
      </td>
    </tr>
  );
}

export function SourcesDirectory({ sources, indicators, collection, development, now }: {
  sources: Source[];
  indicators: DirectoryIndicator[];
  collection: CollectionStatus | null;
  development: boolean;
  now: number;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const query = params.get("q") ?? "";
  const filters: SourceFilters = { q: query, institution: params.get("institution") ?? "", source_type: params.get("source_type") ?? "" };
  const [draft, setDraft] = useState(query);
  const [previousQuery, setPreviousQuery] = useState(query);
  const [pending, startTransition] = useTransition();
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Sync navigation/back changes while keeping typing independent of URL debounce.
  if (previousQuery !== query) {
    setPreviousQuery(query);
    setDraft(query);
  }
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  const rows = useMemo(() => groupSources(sources, indicators, development), [sources, indicators, development]);
  const visible = filterSources(rows, filters);
  const facets = sourceFacets(rows, filters);
  const institutions = [...new Set(rows.map(row => row.institution))].sort((a, b) => a.localeCompare(b, "pt-BR"));
  const kinds = [...new Set([...rows.map(row => row.source.source_type), ...(filters.source_type ? [filters.source_type] : [])])];
  const groups = new Map<string, DirectorySource[]>();
  for (const row of visible) groups.set(row.institution, [...(groups.get(row.institution) ?? []), row]);

  function updateFilters(change: SourceFilters, clear = false) {
    if (timer.current) { clearTimeout(timer.current); timer.current = null; }
    const next = new URLSearchParams(params.toString());
    const values = clear ? { q: "", institution: "", source_type: "" } : { q: draft.trim(), ...change };
    for (const [key, value] of Object.entries(values)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    next.delete("page");
    const url = next.size ? `/fontes?${next}` : "/fontes";
    startTransition(() => router.replace(url, { scroll: false }));
  }
  function search(value: string) {
    setDraft(value);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => updateFilters({ q: value.trim() }), 300);
  }
  const run = collection?.last_run;
  const finished = run?.finished_at && Date.parse(run.finished_at) <= now ? run.finished_at : null;
  const hasFilters = Boolean(query || filters.institution || filters.source_type);
  return (
    <section className={styles.directory} aria-label="Diretório de fontes">
      <div className={styles.filters}>
        <div className="wide-container">
          <form className={styles.filterForm} onSubmit={event => { event.preventDefault(); updateFilters({ q: draft.trim() }); }}>
            <label className={styles.search}>
              <span className="sr-only">Pesquisar fonte, instituição ou indicador</span>
              <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="10" cy="10" r="6" /><path d="m15 15 6 6" /></svg>
              <input type="search" name="q" value={draft} onChange={event => search(event.target.value)} placeholder="Fonte, instituição ou indicador" maxLength={120} autoComplete="off" />
            </label>
            <label className={styles.institutionFilter}>
              <span className="sr-only">Instituição</span>
              <select name="institution" value={filters.institution ?? ""} onChange={event => updateFilters({ institution: event.target.value })}>
                <option value="">Todas as instituições ({facets.institutions.reduce((sum, [, count]) => sum + count, 0)})</option>
                {institutions.map(institution => <option key={institution} value={institution}>{institution} ({facets.institutions.find(([name]) => name === institution)?.[1] ?? 0})</option>)}
                {filters.institution && !institutions.includes(filters.institution) && <option value={filters.institution}>{filters.institution} (0)</option>}
              </select>
            </label>
            <button type="submit" className={styles.searchButton}>Buscar</button>
          </form>
          <div className={styles.filterFooter}>
            <div className={styles.chips} aria-label="Tipo de fonte">
              <button type="button" aria-pressed={!filters.source_type} className={!filters.source_type ? styles.selected : undefined} onClick={() => updateFilters({ source_type: "" })}>Todos <span>{facets.totalKind}</span></button>
              {kinds.map(kind => <button type="button" key={kind} aria-pressed={filters.source_type === kind} className={filters.source_type === kind ? styles.selected : undefined} onClick={() => updateFilters({ source_type: kind })}>{sourceKinds[kind] ?? "Referências"} <span>{facets.kinds.get(kind) ?? 0}</span></button>)}
            </div>
            {hasFilters && <button className={styles.clear} type="button" onClick={() => { setDraft(""); updateFilters({}, true); }}>Limpar filtros</button>}
          </div>
        </div>
      </div>
      <div className={`wide-container ${styles.results}`} aria-busy={pending}>
        <div className={styles.resultSummary}>
          <p role="status" aria-live="polite"><strong>{visible.length} {visible.length === 1 ? "fonte" : "fontes"}</strong>{hasFilters ? ` de ${rows.length}` : ""} · {groups.size} {groups.size === 1 ? "instituição" : "instituições"}</p>
          <p className={styles.muted}>{finished ? run?.status === "SUCCESS" ? `Fontes automáticas consultadas em ${dateLabel(finished)}.` : `Última tentativa do coletor: ${dateLabel(finished)}.` : run?.status === "RUNNING" ? "Consulta automática em andamento." : "Última consulta automática não informada."}</p>
        </div>
        <p className={styles.guide}>Referência é o período do dado. Consulta é a conferência da fonte pelo coletor; um dado mensal não vira novo só porque foi consultado hoje.</p>
        {visible.length ? [...groups].map(([institution, group], index) => {
          const site = group.find(row => row.officialSite)?.officialSite;
          return <section className={styles.institutionGroup} key={institution} aria-labelledby={`source-institution-${index}`}>
            <header className={styles.groupHeader}>
              <div className={styles.groupTitle}><span className={styles.groupMark} aria-hidden="true">{institution === "Banco Central do Brasil" ? "BC" : institution === "IBGE" ? "IB" : institution === "Secretaria do Tesouro Nacional" ? "TN" : institution.slice(0, 2).toUpperCase()}</span><div><h2 id={`source-institution-${index}`}>{institution}</h2><p>{group.length} {group.length === 1 ? "fonte" : "fontes"}</p></div></div>
              {site && <a href={site} target="_blank" rel="noopener noreferrer">Site oficial <span aria-hidden="true">↗</span></a>}
            </header>
            <table className={styles.table}>
              <caption className="sr-only">Fontes de {institution}, referências e estado da consulta automática</caption>
              <colgroup><col className={styles.titleColumn} /><col className={styles.referenceColumn} /><col className={styles.collectionColumn} /><col className={styles.actionColumn} /></colgroup>
              <thead><tr><th scope="col">Fonte e série</th><th scope="col">Referência do dado</th><th scope="col">Consulta automática</th><th scope="col"><span className="sr-only">Link da fonte</span></th></tr></thead>
              <tbody>{group.map(row => <SourceRow key={row.identity} row={row} collection={collection} now={now} />)}</tbody>
            </table>
          </section>;
        }) : <EmptyState title="Sem fontes nesse recorte." description="Tente outro termo ou limpe os filtros para ver o diretório completo." href="/fontes" />}
        <p className={styles.footnote}>Cópias históricas da mesma série aparecem juntas; os registros originais continuam preservados. A consulta usa o intervalo do coletor mais 24 horas de tolerância. As datas são exibidas em UTC.</p>
      </div>
    </section>
  );
}
