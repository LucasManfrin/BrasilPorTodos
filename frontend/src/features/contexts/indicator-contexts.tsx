"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { dateLabel } from "@/lib/data-format";
import type { ContextRecord } from "./types";
import { anchorMismatch, contextPath } from "./helpers";
import styles from "./contexts.module.css";

export function IndicatorContexts(props: { indicatorCode: string; latestObservationId?: string | null }) {
  return <IndicatorContextResults key={props.indicatorCode} {...props} />;
}
function IndicatorContextResults({ indicatorCode, latestObservationId }: { indicatorCode: string; latestObservationId?: string | null }) {
  const [page, setPage] = useState(1);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<{ items: ContextRecord[] | null; total: number; error: boolean; loading: boolean }>({ items: null, total: 0, error: false, loading: true });
  useEffect(() => {
    const controller = new AbortController();
    void fetchApi<ContextRecord[]>(`contexts?${new URLSearchParams({ indicator_code: indicatorCode, page: String(page), page_size: "5" })}`, { signal: controller.signal }).then(r => { if (!controller.signal.aborted) setState({ items: r.data, total: r.pagination?.total ?? r.data.length, error: false, loading: false }); }).catch(() => { if (!controller.signal.aborted) setState({ items: null, total: 0, error: true, loading: false }); });
    return () => controller.abort();
  }, [indicatorCode, page, attempt]);
  return <section className={styles.indicator} aria-label="Contextos revisados"><h3>O número tem contexto?</h3><p>Explicações possíveis, contrapartidas e lacunas. Revisão não é prova de causa e efeito.</p>{state.loading ? <p role="status">Consultando análises publicadas…</p> : state.error ? <div role="status"><p>Não foi possível consultar as análises.</p><button type="button" className="button secondary" onClick={() => { setState(s => ({ ...s, loading: true })); setAttempt(n => n + 1); }}>Tentar de novo</button></div> : !state.items?.length ? <p className={styles.notice}>Ainda não há uma análise revisada para este indicador.</p> : <><div className={styles.stack}>{state.items.map(r => <div key={r.id} className={styles.reference}>{r.is_example && <span className={styles.example}>Exemplo fictício</span>}<h4><Link href={contextPath(r.id, r.revision)}>{r.content.title}</Link></h4><p>{r.content.observation_summary}</p><p className={styles.muted}>Versão {r.revision} · {dateLabel(r.published_at)}</p>{anchorMismatch(r, indicatorCode, latestObservationId) && <p className={styles.notice}>Esta análise usa outra observação, preservada na publicação. Ela não foi atualizada com o dado que você está vendo.</p>}<Link href={contextPath(r.id, r.revision)}>Ver hipóteses e evidências →</Link></div>)}</div><nav className={styles.pagination} aria-label="Páginas de análises do indicador"><button className="button secondary" disabled={page === 1} onClick={() => { setState(s => ({ ...s, loading: true })); setPage(n => n - 1); }}>Anterior</button><span>Página {page} · {state.total} análises</span><button className="button secondary" disabled={page * 5 >= state.total} onClick={() => { setState(s => ({ ...s, loading: true })); setPage(n => n + 1); }}>Próxima</button></nav></>}<p><Link href="/contextos">Todos os contextos</Link> · <Link href="/metodologia#contextos">Como essas análises funcionam</Link></p></section>;
}
