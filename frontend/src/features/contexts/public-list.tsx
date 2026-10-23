"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, fetchApi } from "@/lib/api";
import type { Envelope } from "@/lib/types";
import { dateLabel } from "@/lib/data-format";
import { Skeleton } from "@/components/page-kit";
import { contextPath } from "./helpers";
import { ContextView } from "./context-view";
import type { ContextRecord, ContextVersion } from "./types";
import styles from "./public.module.css";
import { ReadingLayout } from "@/components/public-reading";

export function ContextList({ initial }: { initial: Envelope<ContextRecord[]> | null }) {
  const [result, setResult] = useState(initial);
  const [q, setQ] = useState("");
  const [appliedQ, setAppliedQ] = useState("");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initial ? "" : "Não foi possível carregar os contextos.");
  async function load(nextPage: number, search: string) {
    setBusy(true); setError("");
    try { const data = await fetchApi<ContextRecord[]>(`contexts?${new URLSearchParams({ q: search.trim(), page: String(nextPage), page_size: "20" })}`); setResult(data); setPage(nextPage); setAppliedQ(search.trim()); } catch { setError("Não foi possível carregar os contextos. Tente novamente."); } finally { setBusy(false); }
  }
  return <div className={styles.stack}><section className={styles.intro} aria-label="Como ler um contexto"><div><h2>Um número mostra a mudança.<br />A explicação precisa de mais.</h2><p>Compare as hipóteses, abra as evidências e confira o que continua sem resposta. Revisão humana não é prova de causa e efeito.</p></div><ol><li><span>01</span> O dado observado</li><li><span>02</span> Explicações e contrapontos</li><li><span>03</span> Fontes, revisão e limites</li></ol></section><form className={styles.search} onSubmit={e => { e.preventDefault(); void load(1, q); }}><label>Pesquisar contextos<input type="search" value={q} maxLength={120} onChange={e => setQ(e.target.value)} placeholder="Título ou assunto" /></label><button type="submit" className="button" disabled={busy}>Buscar</button>{q && <button type="button" className="button secondary" disabled={busy} onClick={() => { setQ(""); void load(1, ""); }}>Limpar</button>}</form>{busy ? <Skeleton /> : error ? <div className={styles.empty} role="status"><h2>Uma pausa na consulta</h2><p>{error}</p><button type="button" className="button" onClick={() => void load(page, q)}>Tentar de novo</button></div> : !result?.data.length ? <div className={styles.empty}><h2>{appliedQ ? "Nenhum contexto encontrado" : "As análises estão sendo preparadas"}</h2><p>{appliedQ ? "Tente outro título ou limpe a busca." : "Ainda não há contextos publicados. Eles só aparecem aqui depois da revisão humana e da publicação."}</p><Link href="/brasil">Consultar os dados do Brasil Atual</Link></div> : <><p role="status">{result.pagination?.total ?? result.data.length} contextos publicados · página {page}</p><div className={styles.grid}>{result.data.map(record => <article key={record.id} className={styles.listCard}>{record.is_example && <span className={styles.example}>Exemplo fictício</span>}<span className={styles.muted}>Contexto publicado · versão {record.revision}</span><h2><Link href={contextPath(record.id)}>{record.content.title}</Link></h2><p>{record.content.observation_summary}</p><p className={styles.muted}>Versão {record.revision} · publicada em {dateLabel(record.published_at)}</p><Link href={contextPath(record.id, record.revision)}>Ler esta versão →</Link></article>)}</div><nav className={styles.pagination} aria-label="Páginas de contextos"><button className="button secondary" disabled={page === 1} onClick={() => void load(page - 1, appliedQ)}>Anterior</button><span>Página {page}</span><button className="button secondary" disabled={page * (result.pagination?.page_size ?? 20) >= (result.pagination?.total ?? result.data.length)} onClick={() => void load(page + 1, appliedQ)}>Próxima</button></nav></>}</div>;
}

export function PublicContextDetail(props: { id: string; revision?: number }) {
  return <PublicContextDetailContent key={`${props.id}:${props.revision ?? "latest"}`} {...props} />;
}
function PublicContextDetailContent({ id, revision }: { id: string; revision?: number }) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<{ loading: boolean; error: string; record: ContextRecord | null; versions: ContextVersion[] | null }>({ loading: true, error: "", record: null, versions: null });
  useEffect(() => {
    const controller = new AbortController();
    const path = `contexts/${encodeURIComponent(id)}`;
    void (async () => {
      try {
        const response = await fetchApi<ContextRecord>(revision ? `${path}/versions/${revision}` : path, { signal: controller.signal });
        let versions: ContextVersion[] | null = null;
        try { versions = (await fetchApi<ContextVersion[]>(`${path}/versions`, { signal: controller.signal })).data; } catch { /* Main record is independently available. */ }
        if (!controller.signal.aborted) setState({ loading: false, error: "", record: response.data, versions });
      } catch (error) { if (!controller.signal.aborted) setState({ loading: false, record: null, versions: null, error: error instanceof ApiError && error.status === 404 ? "Esta versão não está disponível para leitura pública." : "Não foi possível consultar o contexto. Tente novamente." }); }
    })();
    return () => controller.abort();
  }, [id, revision, attempt]);
  if (state.loading) return <Skeleton />;
  if (!state.record) return <section className={styles.empty} role="status"><h2>Contexto indisponível</h2><p>{state.error}</p><button className="button" type="button" onClick={() => { setState(s => ({ ...s, loading: true })); setAttempt(n => n + 1); }}>Tentar de novo</button><p><Link href="/contextos">Ver contextos publicados</Link></p></section>;
  return <><header className={styles.detailIntro}><h1 className={styles.title}>{state.record.content.title}</h1><p>Versão {state.record.revision} · publicada em {dateLabel(state.record.published_at)}. Leia a observação, as explicações e os limites juntos.</p></header><ReadingLayout items={[{id:"analise",label:"Análise e evidências"},{id:"versoes",label:"Versões publicadas"}]}><section id="analise" className={styles.contextBody}><ContextView record={state.record} /></section><section id="versoes"><h2>Versões publicadas</h2>{state.versions ? <ul className={styles.versions}>{state.versions.map(v => <li key={v.revision}><Link href={contextPath(id, v.revision)}>Versão {v.revision} · {v.title}</Link> · {dateLabel(v.published_at)}</li>)}</ul> : <p>O histórico não pôde ser consultado. A versão acima continua disponível.</p>}</section></ReadingLayout></>;
}
