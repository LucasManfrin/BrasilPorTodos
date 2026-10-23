"use client";
import Link from "next/link";
import { useEffect, useRef, type MouseEvent, type ReactNode } from "react";
import { dateLabel, formatCompact, formatExact } from "@/lib/data-format";
import type { ContextRecord } from "./types";
import { contextPath, evidenceLevelLabel, relationLabel, safeReferenceUrl, statusLabel } from "./helpers";
import styles from "./contexts.module.css";

function ReferenceLink({ url, children }: { url: string; children: ReactNode }) {
  const safe = safeReferenceUrl(url);
  return safe ? <a href={safe} target="_blank" rel="noopener noreferrer">{children} ↗</a> : <span>{children} (link indisponível)</span>;
}
function TextList({ items, empty }: { items: string[]; empty: string }) {
  return items.length ? <ul>{items.map((text, i) => <li key={i}>{text}</li>)}</ul> : <p className={styles.muted}>{empty}</p>;
}
/** Reveal a cited passage before native fragment navigation and keyboard focus. */
function openContextReference(root: HTMLElement | null, hash: string) {
  if (!root || !/^#(?:observation|evidence|source)-[a-f0-9-]+$/i.test(hash)) return;
  const target = document.getElementById(hash.slice(1));
  if (!target || !root.contains(target)) return;
  let parent: HTMLElement | null = target;
  while (parent && parent !== root) {
    if (parent instanceof HTMLDetailsElement) parent.open = true;
    parent = parent.parentElement;
  }
  target.tabIndex = -1;
  target.focus({ preventScroll: true });
  target.scrollIntoView({ block: "start" });
}
export function ContextView({ record, showHistory = true }: { record: ContextRecord; showHistory?: boolean }) {
  const c = record.content;
  const rootRef = useRef<HTMLElement>(null);
  useEffect(() => {
    function openHash() { openContextReference(rootRef.current, window.location.hash); }
    openHash();
    window.addEventListener("hashchange", openHash);
    return () => window.removeEventListener("hashchange", openHash);
  }, [record.id, record.revision, record.content_hash]);
  function revealReference(event: MouseEvent<HTMLElement>) {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>("a[href^='#']") : null;
    if (link) openContextReference(rootRef.current, link.hash);
  }
  const primary = c.observations.find(o => o.observation_id === c.primary_observation_id);
  return <article ref={rootRef} onClick={revealReference} className={styles.contextView}>
    <div className={styles.meta}><span className={styles.badge}>{record.published_at ? "Contexto publicado" : "Prévia privada"}</span><span>Versão {record.revision}</span>{record.is_example && <strong className={styles.example}>Exemplo fictício</strong>}<span>{record.published_at ? `Publicado em ${dateLabel(record.published_at)}` : `Salvo em ${dateLabel(c.updated_at)}`}</span></div>
    <p className={styles.notice}>Um número mostra o que foi observado. As hipóteses tentam explicar por quê. Fontes e revisão humana, por si, não provam causa e efeito.</p>
    <section className={styles.section} aria-label="O dado observado"><h2>O que o dado mostra</h2><p className={styles.summary}>{c.observation_summary || "Resumo ainda não informado."}</p>{primary && <div className={styles.anchor}><Link href={`/brasil/${encodeURIComponent(primary.indicator_code)}`}>{primary.indicator_code}</Link><strong title={formatExact(primary.value, primary.unit)}>{formatCompact(primary.value, primary.unit)}</strong><span>Referência {dateLabel(primary.reference_date)} · revisão do dado {primary.revision}</span><span>{primary.scope}</span></div>}<details><summary>Observações usadas · {c.observations.length}</summary><div className={styles.stack}>{c.observations.map(o => <div key={o.observation_id} id={`observation-${o.observation_id}`} className={styles.reference}><h3><Link href={`/brasil/${encodeURIComponent(o.indicator_code)}`}>{o.indicator_code}</Link>{o.observation_id === c.primary_observation_id ? " · principal" : ""}</h3><p><strong>{formatExact(o.value, o.unit)}</strong> · ref. {dateLabel(o.reference_date)} · revisão {o.revision}</p><p>Valor original: <code>{o.value}</code> {o.unit}</p><p>Período: {dateLabel(o.period_start)} a {dateLabel(o.period_end)} · frequência: {o.frequency}</p><p>{o.scope}</p><p>Método: {o.methodology}</p><p>Coletado em {dateLabel(o.collected_at)} · <a href={`#source-${o.source_id}`}>Ver fonte</a></p></div>)}</div></details></section>
    <section className={styles.section}><h2>Explicações possíveis</h2><p>Leia as alternativas juntas. Apoio a uma hipótese não transforma associação em causalidade.</p><div className={styles.grid}>{c.hypotheses.map((h, i) => <div key={h.id} className={styles.hypothesis}><h3>Hipótese {i + 1}</h3><p>{h.explanation}</p><p><strong>Incerteza:</strong> {h.uncertainty}</p>{h.evidence.length ? <ul>{h.evidence.map(link => <li key={link.evidence_id}><a href={`#evidence-${link.evidence_id}`}>{relationLabel(link.relation)}</a><p>{link.justification}</p></li>)}</ul> : <p className={styles.muted}>Sem evidência vinculada. Continua uma hipótese.</p>}</div>)}</div>{!c.hypotheses.length && <p className={styles.muted}>Nenhuma hipótese registrada.</p>}</section>
    <section className={styles.section}><h2>Que outros números olhar junto?</h2><div className={styles.stack}>{c.counterparts.map(p => <div key={p.indicator_code} className={styles.reference}><h3>{p.indicator_code}</h3><p>{p.why_read_together}</p>{p.availability === "NOT_COLLECTED" ? <p className={styles.notice}>Não coletado neste contexto. Essa lacuna não significa zero.</p> : <><Link href={`/brasil/${encodeURIComponent(p.indicator_code)}`}>Ver indicador</Link><ul>{p.observation_ids.map(id => <li key={id}><a href={`#observation-${id}`}>Observação congelada · {dateLabel(c.observations.find(o => o.observation_id === id)?.reference_date)}</a></li>)}</ul></>}</div>)}</div>{!c.counterparts.length && <p className={styles.muted}>Contrapartidas ainda não registradas.</p>}</section>
    <section className={styles.section}><h2>Consequências: observado e projetado</h2><p>Uma projeção depende de premissas. Ela não é um efeito já medido nem entra no cálculo fiscal automaticamente.</p><div className={styles.grid}>{c.consequences.map(row => <div className={styles.reference} key={row.id}><span className={styles.badge}>{row.kind === "OBSERVED" ? "Observado" : "Projetado"}</span><p>{row.description}</p>{row.kind === "PROJECTED" && <><h3>Premissas</h3><TextList items={row.premises} empty="Premissas não informadas." /></>}<p><strong>Limites:</strong> {row.limitations || "Não informados."}</p>{row.evidence_ids.length > 0 && <ul>{row.evidence_ids.map(id => <li key={id}><a href={`#evidence-${id}`}>Evidência: {c.evidence.find(e => e.id === id)?.claim ?? "referência"}</a></li>)}</ul>}{row.observation_ids.length > 0 && <ul>{row.observation_ids.map(id => <li key={id}><a href={`#observation-${id}`}>Observação: {c.observations.find(o => o.observation_id === id)?.indicator_code ?? "referência"}</a></li>)}</ul>}</div>)}</div>{!c.consequences.length && <p className={styles.muted}>Nenhuma consequência registrada. Isso não significa ausência de efeitos.</p>}</section>
    <section className={styles.section}><h2>O que não sabemos</h2><TextList items={c.unknowns} empty="Lacunas ainda não registradas." /><h3>Limitações desta análise</h3><TextList items={c.limitations} empty="Limitações ainda não registradas." /></section>
    <section className={styles.section}><h2>Confira as evidências</h2><div className={styles.stack}>{c.evidence.map(e => <details key={e.id} id={`evidence-${e.id}`} className={styles.reference}><summary>{e.claim} · {evidenceLevelLabel(e.level)}</summary><p><strong>Trecho registrado:</strong> {e.excerpt}</p><p>Onde encontrar: {e.locator}</p><p>Recorte: {e.scope} · período: {e.period}</p><p>Limites: {e.limitations}</p><a href={`#source-${e.source_id}`}>Conferir a fonte</a></details>)}</div>{!c.evidence.length && <p className={styles.muted}>Nenhuma evidência registrada.</p>}</section>
    <section className={styles.section}><h2>Fontes e termos de uso</h2><div className={styles.stack}>{c.sources.map(s => <div key={s.id} id={`source-${s.id}`} className={styles.reference}><h3><ReferenceLink url={s.url}>{s.title}</ReferenceLink></h3><p>{s.institution} · publicação: {dateLabel(s.published_date)} · consulta: {dateLabel(s.consulted_at)}</p><p>{s.terms}</p><ReferenceLink url={s.terms_url}>Termos da fonte</ReferenceLink></div>)}</div>{!c.sources.length && <p className={styles.muted}>Nenhuma fonte registrada.</p>}</section>
    <section className={styles.section}><h2>Revisão e histórico</h2><p>{statusLabel(record.assessment.status)}. A revisão confere referências, recortes, alternativas e limitações; não certifica causalidade.</p>{record.review && <><p>Revisado em {dateLabel(record.review.reviewed_at)} · {record.review.decision === "ACCEPT" ? "Aceitação registrada" : "Ajustes solicitados"}</p><p>{record.review.rationale}</p><ul><li>Referências: {record.review.references_checked ? "conferidas" : "não conferidas"}</li><li>Recortes: {record.review.scopes_checked ? "conferidos" : "não conferidos"}</li><li>Alternativas: {record.review.alternatives_checked ? "conferidas" : "não conferidas"}</li><li>Limitações: {record.review.limitations_checked ? "conferidas" : "não conferidas"}</li></ul></>}{showHistory && record.published_at && <p><Link href={contextPath(record.id, record.revision)}>Link permanente desta versão</Link> · <Link href={contextPath(record.id)}>Ver publicação atual e histórico</Link></p>}<details><summary>Identificação desta versão</summary><p>Revisão {record.revision} · contrato {c.contract_version}</p><p className={styles.hash}>Hash do conteúdo: <code>{record.content_hash}</code></p></details></section>
  </article>;
}
