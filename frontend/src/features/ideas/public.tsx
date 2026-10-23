"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/provider";
import { fetchApi } from "@/lib/api";
import type { Idea } from "./state";
import styles from "./public.module.css";
import { PageHero, EmptyState, Skeleton } from "@/components/page-kit";
import { Button } from "@/components/ui";
import { BackToCatalog } from "@/components/public-reading";

export function IdeaList({ mine = false }: { mine?: boolean }) {
  const { request } = useAuth();
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    const path = `${mine ? "ideas/mine" : "ideas"}?page=${page}&page_size=20`;
    (mine ? request<Idea[]>(path) : fetchApi<Idea[]>(path)).then((response) => {
      if (active) { setIdeas(response.data); setTotal(response.pagination?.total ?? response.data.length); setError(""); }
    }).catch((e: Error) => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [mine, request, page, retry]);
  return <div className={styles.public}>
    {mine ? <header className={styles.heading}><span className={styles.badge}>Ideias em construção</span><h1>Suas ideias têm lugar aqui.</h1><p>Rascunhos privados e cópias que você escolheu compartilhar. Retome de onde parou.</p></header> : <PageHero title="Uma ideia não precisa nascer pronta." breadcrumb="Ideias" description="Um título, uma frase e um espaço para construir junto. Aqui, as perguntas ainda estão abertas." tone="night" action={<Button href="/painel/ideias/nova">Começar uma ideia</Button>} />}
    <div className={mine ? undefined : "wide-container page-body"}>
      {!mine && <section className={styles.intro} aria-label="Sobre as ideias em construção"><div><h2>Tem uma inquietação?<br />Comece por ela.</h2><p>Leia o que outras pessoas querem mudar. Você pode desenvolver uma cópia ou sugerir uma fonte para ajudar o autor a ir além.</p></div><aside className={styles.introAside}><strong>Ainda é uma ideia.</strong><p>Não entra nos cálculos, nos planos ou no ranking de solidez. Antes disso, há perguntas para responder.</p></aside></section>}
      <div className={styles.toolbar}>{mine && <Button href="/painel/ideias/nova">Começar uma ideia</Button>}<Link href={mine ? "/ideias" : "/painel/ideias"}>{mine ? "Explorar ideias compartilhadas" : "Retomar minhas ideias →"}</Link>{!loading && !error && <span className={styles.muted}>{total} {total === 1 ? "ideia" : "ideias"}{mine ? " na sua conta" : " compartilhadas"}</span>}</div>
      {loading && <Skeleton />}
      {error && <section className={styles.panel} role="alert"><h2>Uma pausa na consulta.</h2><p>{error}</p><Button onClick={() => { setLoading(true); setRetry((n) => n + 1); }}>Tentar de novo</Button></section>}
      {!loading && !error && !ideas.length && <EmptyState title={mine ? "Ainda sem ideias salvas." : "Espaço aberto para a primeira ideia."} description="Basta um título e uma frase. O resto pode ser construído aos poucos." href="/painel/ideias/nova" action="Começar uma ideia" />}
      <div className={styles.cards}>{ideas.map((idea) => <article className={`${styles.panel} ${styles.ideaCard}`} key={idea.id}><span className={styles.badge}>{idea.status === "PROMOTED" ? "Virou proposta" : idea.status === "SHARED" ? "Ideia compartilhada" : "Privada"}</span><h2><Link href={mine ? `/painel/ideias/${idea.id}` : `/ideias/${idea.id}`}>{idea.title}</Link></h2><p className={styles.text}>{idea.summary}</p><div className={styles.author}><span className={styles.avatar} aria-hidden="true">{idea.author.name.slice(0, 1).toUpperCase()}</span><div>{idea.author.name}<small>@{idea.author.username}</small></div></div><div className={styles.cardFoot}>{idea.assisted_fields.length > 0 && <span>Assistido por IA</span>}<Link href={mine ? `/painel/ideias/${idea.id}` : `/ideias/${idea.id}`}>{mine ? "Retomar ideia →" : "Conhecer e ajudar →"}</Link></div></article>)}</div>
      {total > 20 && <nav className={styles.toolbar} aria-label="Paginação de ideias"><Button variant="secondary" disabled={page === 1 || loading} onClick={() => { setPage(page - 1); setLoading(true); }}>Anterior</Button><span>Página {page} · {total} ideias</span><Button variant="secondary" disabled={page * 20 >= total || loading} onClick={() => { setPage(page + 1); setLoading(true); }}>Próxima</Button></nav>}
    </div>
  </div>;
}

export function SharedIdea({ id }: { id: string }) {
  const { request, user } = useAuth();
  const router = useRouter();
  const [idea, setIdea] = useState<Idea | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    fetchApi<Idea>(`ideas/${encodeURIComponent(id)}/shared`).then((response) => { if (active) { setIdea(response.data); setError(""); } })
      .catch((e: Error) => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id, retry]);
  async function act(work: () => Promise<void>) { setBusy(true); setError(""); setMessage(""); try { await work(); } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível concluir."); } finally { setBusy(false); } }
  if (loading) return <div className="wide-container page-body"><Skeleton /></div>;
  if (!idea) return <div className="wide-container page-body"><EmptyState error title="Esta ideia não está disponível." description={error || "O autor pode ter retirado o compartilhamento."} href="/ideias" action="Explorar ideias" /><Button variant="secondary" onClick={() => { setLoading(true); setRetry((n) => n + 1); }}>Tentar novamente</Button></div>;
  const sections: [string, string][] = [["O problema", idea.content.problem], ["O que quer mudar", idea.content.proposal], ["Quem ganha", idea.beneficiaries], ["Quem poderia perder", idea.adversely_affected], ["O que poderia dar errado", idea.risks]];
  return <article className={styles.public}><PageHero title={idea.title} description={idea.summary} tone="yellow" breadcrumb="Ideia em construção" /><div className="wide-container page-body"><BackToCatalog href="/ideias">Ideias compartilhadas</BackToCatalog><div className={styles.author}><span className={styles.avatar} aria-hidden="true">{idea.author.name.slice(0, 1).toUpperCase()}</span><div>Por {idea.author.name} · @{idea.author.username}{idea.assisted_fields.length > 0 && <small>Assistido por IA · textos confirmados pelo autor.</small>}</div></div><p className={styles.notice}>Esta é uma cópia que o autor escolheu compartilhar. Ainda não é uma proposta completa: não entra no cálculo, em planos ou no ranking de solidez.</p><div className={styles.details}>{sections.map(([title, text]) => <section className={styles.panel} key={title}><h2>{title}</h2><p className={text ? styles.text : styles.unfilled}>{text || "Ainda em aberto. Este ponto precisa ser desenvolvido pelo autor."}</p></section>)}</div><section className={`${styles.panel} ${styles.references}`}><h2>Referências compartilhadas</h2>{idea.source_snapshots?.length ? idea.source_snapshots.map((source) => <div className={styles.row} key={source.id}><a href={/^https?:\/\//i.test(source.url) ? source.url : undefined} rel="noopener noreferrer" target="_blank">{source.title} ↗</a><p>{source.institution} · acesso em {source.accessed_at?.slice(0, 10)}</p></div>) : <p>O autor ainda não vinculou fontes.</p>}</section><section className={styles.help}><h2>Ajude a próxima versão a ir mais longe.</h2><p>Desenvolva uma cópia independente ou indique uma fonte. Só o autor decide o que entra nesta ideia.</p><div className={styles.actions}>{user ? <button className="button" disabled={busy} onClick={() => void act(async () => { const response = await request<Idea>(`ideas/${id}/duplicate`, { method: "POST" }); router.push(`/painel/ideias/${response.data.id}`); })}>Duplicar e desenvolver</button> : <Link className="button" href={`/entrar?next=${encodeURIComponent(`/ideias/${id}`)}`}>Entrar para ajudar ou duplicar</Link>}<Link href="/ideias">Outras ideias</Link></div></section>{user && <div className={styles.cards}><form className={`${styles.panel} ${styles.fields}`} onSubmit={(e) => { e.preventDefault(); const form = e.currentTarget; const values = Object.fromEntries(new FormData(form)); void act(async () => { await request(`ideas/${id}/suggestions`, { method: "POST", body: JSON.stringify(values) }); form.reset(); setMessage("Sugestão enviada ao autor. O conteúdo original não foi alterado."); }); }}><h2>Tem uma fonte para ajudar?</h2><label>Link da referência<input type="url" name="url" required maxLength={2000} placeholder="https://…" /></label><label>Como ela ajuda?<textarea name="note" required maxLength={2000} /></label><button disabled={busy}>Enviar sugestão</button><p className={styles.muted}>O link não é acessado automaticamente. Só o autor pode decidir incorporá-lo.</p></form><details className={styles.panel}><summary>Denunciar conteúdo</summary><form className={styles.fields} onSubmit={(e) => { e.preventDefault(); const form = e.currentTarget; const values = Object.fromEntries(new FormData(form)); void act(async () => { await request(`ideas/${id}/report`, { method: "POST", body: JSON.stringify(values) }); form.reset(); setMessage("Denúncia registrada para análise. Sua identidade não aparece na ideia."); }); }}><label>Descreva o motivo<textarea name="reason" required minLength={1} maxLength={2000} /></label><button disabled={busy}>Enviar denúncia</button></form></details></div>}{error && <p className={styles.notice} role="alert">{error}</p>}{message && <p className={styles.notice} role="status">{message}</p>}</div></article>;
}
