"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/provider";
import { date } from "@/lib/format";
import type { ContextRecord } from "./types";
import { statusLabel } from "./helpers";
import styles from "./editor.module.css";
import { EmptyState, PageHero, Skeleton } from "@/components/page-kit";
import { Button } from "@/components/ui";
export function ContextWorkspace({ reviewQueue = false }: {
    reviewQueue?: boolean;
}) {
    const { user, request } = useAuth();
    const [rows, setRows] = useState<ContextRecord[]>([]), [page, setPage] = useState(1), [total, setTotal] = useState(0), [loading, setLoading] = useState(true), [error, setError] = useState("");
    const load = useCallback(async () => {
        if (reviewQueue && user?.role !== "ADMIN") {
            setLoading(false);
            return;
        }
        setLoading(true);
        setError("");
        try {
            const r = await request<ContextRecord[]>(`contexts/${reviewQueue ? "review-queue" : "mine"}?page=${page}&page_size=20`);
            setRows(r.data);
            setTotal(r.pagination?.total ?? r.data.length);
        }
        catch (e) {
            setError((e as Error).message);
        }
        finally {
            setLoading(false);
        }
    }, [request, page, reviewQueue, user?.role]);
    useEffect(() => { if (reviewQueue && user?.role !== "ADMIN")
        return; let active = true; request<ContextRecord[]>(`contexts/${reviewQueue ? "review-queue" : "mine"}?page=${page}&page_size=20`).then(r => { if (active) {
        setRows(r.data);
        setTotal(r.pagination?.total ?? r.data.length);
    } }).catch(e => { if (active)
        setError((e as Error).message); }).finally(() => { if (active)
        setLoading(false); }); return () => { active = false; }; }, [request, page, reviewQueue, user?.role]);
    if (reviewQueue && user?.role !== "ADMIN")
        return <p>Esta fila é reservada aos administradores. Seus rascunhos estão em <Link href="/painel/contextos">Meus contextos</Link>.</p>;
    return <section className={styles.workspace}><PageHero title={reviewQueue ? "Revisar contextos" : "Meus contextos"} description={reviewQueue ? "Revise as fontes, os recortes e as explicações de outros autores antes da publicação." : "Vá além do número: reúna observações, fontes e explicações em um rascunho privado."} tone="blue" action={<Button href="/painel/contextos/novo">Criar contexto</Button>} />{user?.role === "ADMIN" && <div className={styles.actions}><Button variant="secondary" href={reviewQueue ? "/painel/contextos" : "/painel/contextos/revisao"}>{reviewQueue ? "Meus contextos" : "Fila de revisão"}</Button></div>}{loading ? <Skeleton /> : error ? <div className={styles.notice}><p role="alert">{error}</p><button onClick={() => void load()}>Tentar novamente</button></div> : <><p>{total} {total === 1 ? "contexto" : "contextos"} · Página {page}</p>{rows.length === 0 ? <EmptyState title={reviewQueue ? "Nenhum contexto para revisar" : "Seu primeiro contexto começa com um dado"} description={reviewQueue ? "A fila não inclui seus próprios textos nem versões já publicadas." : "Escolha uma observação, reúna evidências e registre explicações alternativas."} href={reviewQueue ? "/painel/contextos" : "/painel/contextos/novo"} action={reviewQueue ? "Meus contextos" : "Criar contexto"} /> : <div className={styles.list}>{rows.map(r => <article className={styles.entry} key={r.id}><p className={styles.badge}>{r.is_example ? "Exemplo · " : ""}{statusLabel(r.assessment.status)} · Revisão {r.revision}{r.published_at ? " · Publicada" : ""}</p><h2>{r.content.title || "Contexto sem título"}</h2><p>{r.content.observation_summary || "Resumo ainda em construção."}</p><p>Salvo em {date(r.content.updated_at)}</p><Link className="button secondary" href={`/painel/contextos/${r.id}`}>{reviewQueue ? "Abrir para revisar" : "Continuar edição"}</Link>{r.published_at && <p><Link href={`/contextos/${r.id}/versoes/${r.revision}`}>Ver publicação desta revisão</Link></p>}</article>)}</div>}<nav aria-label="Páginas de contextos" className={styles.actions}><button className="button secondary" disabled={page === 1} onClick={() => { setLoading(true); setError(""); setPage(p => p - 1); }}>Anterior</button><button className="button secondary" disabled={page * 20 >= total} onClick={() => { setLoading(true); setError(""); setPage(p => p + 1); }}>Próxima</button></nav></>}</section>;
}
