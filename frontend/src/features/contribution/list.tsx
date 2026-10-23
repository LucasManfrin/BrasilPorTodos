"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/provider";
import { Button, Icon } from "@/components/ui";
import { EmptyState, Skeleton } from "@/components/page-kit";
import { PanelHero, StatusChip } from "@/features/panel/kit";
import type { Plan, Policy } from "@/lib/types";
import styles from "@/features/panel/panel.module.css";
export function OwnList({ kind }: { kind: "policies" | "plans" }) {
  const { request } = useAuth();
  const [rows, setRows] = useState<(Plan | Policy)[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [retry, setRetry] = useState(0);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [sort, setSort] = useState("default");
  const isPolicy = kind === "policies";
  const path = isPolicy ? "propostas" : "planos";
  const create = `/painel/${path}/${isPolicy ? "nova" : "novo"}`;
  useEffect(() => {
    let active = true;
    request<(Plan | Policy)[]>(`${kind}/mine?page=${page}&page_size=20`)
      .then(result => { if (active) { setRows(result.data); setTotal(result.pagination?.total ?? 0); setError(""); } })
      .catch((e: Error) => { if (active) setError(e.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [kind, page, request, retry]);
  const status = (row: Plan | Policy) => row.status === "ARCHIVED" ? "ARCHIVED" : row.version.status === "DRAFT" ? "DRAFT" : "PUBLISHED";
  const filtered = rows.filter(row => (filter === "ALL" || status(row) === filter) && `${row.version.title} ${row.version.summary}`.toLocaleLowerCase("pt-BR").includes(query.toLocaleLowerCase("pt-BR")));
  const shown = sort === "title" ? [...filtered].sort((a,b) => a.version.title.localeCompare(b.version.title,"pt-BR")) : filtered;
  function reload() { setLoading(true); setError(""); setRetry(n => n + 1); }
  return <div className={styles.workspace}>
    <PanelHero title={isPolicy ? "Minhas propostas" : "Meus planos"} description={isPolicy ? "Retome um rascunho ou acompanhe as versões que você publicou. Cada publicação conserva sua história." : "Reúna propostas publicadas, compare o conjunto e preserve as escolhas de cada versão."} tone={isPolicy ? "yellow" : "green"} action={<Button href={create}>Criar {isPolicy ? "proposta" : "plano"}<Icon name={isPolicy ? "edit" : "layers"} /></Button>} />
    <div className={styles.filters}><label>Buscar nesta página<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Título ou resumo" maxLength={120} /></label><label>Ordenar esta página<select value={sort} onChange={e => setSort(e.target.value)}><option value="default">Ordem do catálogo</option><option value="title">Título: A a Z</option></select></label><div className={styles.chips} role="group" aria-label="Filtrar por status">{[["ALL","Todos"],["DRAFT","Rascunhos"],["PUBLISHED","Publicados"],["ARCHIVED","Arquivados"]].map(([key,label]) => <button key={key} aria-pressed={filter === key} onClick={() => setFilter(key)}>{label}</button>)}</div></div>
    {loading ? <Skeleton /> : error ? <div className={styles.notice} role="alert"><h2>A lista não carregou.</h2><p>{error}</p><Button variant="secondary" onClick={reload}>Tentar novamente</Button></div> : <>
      <p className={styles.meta} role="status">{shown.length} nesta página · {total} no total</p>
      {!rows.length ? <EmptyState title={isPolicy ? "Toda proposta começa com uma ideia." : "Seu plano começa com uma escolha."} description={isPolicy ? "Detalhe medida, financiamento, riscos e fontes. Para guardar só uma frase, use Criar ideia no menu." : "Escolha propostas publicadas e veja o efeito fiscal incremental das medidas."} href={create} action={isPolicy ? "Preparar proposta completa" : "Montar meu primeiro plano"} /> : !shown.length ? <section className={styles.notice}><h2>Nenhum resultado nesta página.</h2><p>Tente outro termo ou consulte as demais páginas.</p><Button variant="secondary" onClick={() => { setQuery(""); setFilter("ALL"); }}>Limpar filtros</Button></section> : <div className={styles.list}>{shown.map(row => {
        const state = status(row);
        const policy = "impacts" in row.version ? row as Policy : null;
        const plan = "policies" in row.version ? row as Plan : null;
        return <article className={styles.draft} key={row.id}>
          <div className={styles.draftTop}><StatusChip>{state === "ARCHIVED" ? "Arquivado" : state === "DRAFT" ? "Rascunho privado" : isPolicy ? "Proposta publicada" : "Plano publicado"}</StatusChip><span className={styles.meta}>Versão {row.version.version_number}</span></div>
          <h2>{row.version.title || "Sem título"}</h2><p>{row.version.summary || "Resumo ainda em construção."}</p>
          {policy && <p className={styles.meta}>{policy.version.sources.length} fontes vinculadas · {policy.version.financial_impact_status === "ESTIMATED" ? "Com estimativa de impacto" : "Sem estimativa de impacto"}</p>}
          {policy?.solidity?.score != null && <div><label htmlFor={`complete-${row.id}`}>Completude documental: {policy.solidity.score} de {policy.solidity.max_score}</label><progress id={`complete-${row.id}`} max={policy.solidity.max_score} value={policy.solidity.score} /><p className={styles.meta}>Não é avaliação do mérito nem revisão técnica.</p></div>}
          {plan && <p className={styles.meta}>{plan.version.policies.length} propostas vinculadas · {plan.version.start_year}–{plan.version.end_year}</p>}
          <div className={styles.actions}>{row.status !== "ARCHIVED" && <Link className="button secondary" href={`/painel/${path}/${row.id}`}>{state === "DRAFT" ? "Continuar edição" : "Editar nova versão"}<Icon name="edit" /></Link>}{row.status !== "DRAFT" && <Link href={`/${path}/${row.slug}`}>Ver publicação →</Link>}</div>
        </article>;
      })}</div>}
      {total > 20 && <nav className={styles.pagination} aria-label={`Páginas de ${path}`}><Button variant="secondary" disabled={page === 1} onClick={() => { setLoading(true); setPage(n => n - 1); }}>Anterior</Button><span>Página {page} de {Math.ceil(total / 20)}</span><Button variant="secondary" disabled={page * 20 >= total} onClick={() => { setLoading(true); setPage(n => n + 1); }}>Próxima</Button></nav>}
    </>}
  </div>;
}
