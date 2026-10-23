"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/provider";
import type { Source } from "@/lib/types";
import { date } from "@/lib/format";
import { Button, Icon } from "@/components/ui";
import { EmptyState, Skeleton } from "@/components/page-kit";
import { usePanelData } from "@/features/panel/panel-data";
import { PanelHero, StatusChip } from "@/features/panel/kit";
import styles from "@/features/panel/panel.module.css";
export function SourceForm({
  onCreated,
}: {
  onCreated?: (source: Source) => void;
}) {
  const { request } = useAuth();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const result = await request<Source>("sources", {
        method: "POST",
        body: JSON.stringify({
          ...values,
          publication_date: values.publication_date || null,
        }),
      });
      onCreated?.(result.data);
      form.reset();
      setSuccess("Fonte cadastrada. Você pode vinculá-la a uma proposta.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="editor compact" onSubmit={submit}>
      <label>
        Título da fonte
        <input name="title" required maxLength={300} />
      </label>
      <label>
        Instituição
        <input name="institution" required maxLength={200} />
      </label>
      <label>
        Link da fonte
        <input name="url" type="url" required placeholder="https://…" />
      </label>
      <div className="fields">
        <label>
          Tipo
          <select name="source_type">
            <option value="OFFICIAL">Dados oficiais</option>
            <option value="SCIENTIFIC_STUDY">Estudo acadêmico</option>
            <option value="TECHNICAL_REPORT">Relatório técnico</option>
            <option value="INSTITUTIONAL_REPORT">
              Relatório institucional
            </option>
            <option value="JOURNALISM">Jornalismo</option>
            <option value="LEGISLATION">Legislação</option>
            <option value="OTHER">Outro</option>
          </select>
        </label>
        <label>
          Data de publicação (opcional)
          <input name="publication_date" type="date" />
        </label>
        <label>
          Data de acesso
          <input
            name="accessed_at"
            type="date"
            required
            defaultValue={new Date().toISOString().slice(0, 10)}
          />
        </label>
      </div>
      <label>
        Descrição
        <input name="description" maxLength={5000} />
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {success && <p role="status">{success}</p>}
      <button className="button" disabled={busy}>
        {busy ? "Cadastrando…" : "Cadastrar fonte"}
      </button>
      <p className="muted">
        Apenas links HTTP/HTTPS. A plataforma não recebe arquivos nem acessa
        automaticamente o conteúdo do link.
      </p>
    </form>
  );
}
export function SourcesPanel() {
  const { request } = useAuth();
  const { refresh } = usePanelData();
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [retry, setRetry] = useState(0);
  const [query, setQuery] = useState("");
  useEffect(() => {
    let active = true;
    request<Source[]>(`sources/mine?page=${page}&page_size=20`).then(r => {
      if (active) { setSources(r.data); setTotal(r.pagination?.total ?? 0); setError(""); }
    }).catch((e: Error) => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [page, request, retry]);
  const shown = sources.filter(source => `${source.title} ${source.institution}`.toLocaleLowerCase("pt-BR").includes(query.toLocaleLowerCase("pt-BR")));
  return <div className={styles.workspace}>
    <PanelHero title="Minhas fontes" description="Guarde os links que sustentam suas ideias. Uma fonte fica pública quando é usada em uma proposta publicada ou em um indicador." action={<Button href="#cadastrar-fonte">Cadastrar fonte <Icon name="edit" /></Button>} />
    <div className={styles.sourceLayout}><section className={styles.workspace} aria-labelledby="fontes-cadastradas"><div className={styles.filters}><label>Buscar nesta página<input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Título ou instituição" maxLength={120} /></label></div><div><h2 id="fontes-cadastradas" className={styles.sectionTitle}>Sua base de referências</h2><p className={styles.meta}>{loading ? "Consultando seus registros…" : `${shown.length} nesta página · ${total} no total`}</p></div>
      {loading ? <Skeleton /> : error ? <section className={styles.notice} role="alert"><h2>As fontes não carregaram.</h2><p>{error}</p><Button variant="secondary" onClick={() => { setLoading(true); setRetry(n => n + 1); }}>Tentar de novo</Button></section> : !sources.length ? <EmptyState title="Toda referência começa com um link." description="Cadastre dados, estudos ou legislação que ajudem outras pessoas a conferir sua ideia." href="#cadastrar-fonte" action="Cadastrar minha primeira fonte" /> : !shown.length ? <section className={styles.notice}><h2>Nenhuma fonte nesta busca.</h2><Button variant="secondary" onClick={() => setQuery("")}>Limpar busca</Button></section> : <div className={styles.sourceRows}>{shown.map(source => <article className={styles.sourceRow} key={source.id}><div><h3>{source.title}</h3><p>{source.institution}</p><p className={styles.meta}>Acesso em {date(source.accessed_at)}</p>{source.is_example && <StatusChip>Exemplo</StatusChip>}</div><a href={source.url} target="_blank" rel="noopener noreferrer">Abrir ↗<span className="sr-only"> {source.title}</span></a></article>)}</div>}
      {total > 20 && <nav className={styles.pagination} aria-label="Páginas de fontes"><Button variant="secondary" disabled={page === 1 || loading} onClick={() => { setLoading(true); setPage(n => n - 1); }}>Anterior</Button><span>Página {page}</span><Button variant="secondary" disabled={page * 20 >= total || loading} onClick={() => { setLoading(true); setPage(n => n + 1); }}>Próxima</Button></nav>}
    </section><section id="cadastrar-fonte" className={styles.sourceForm}><h2>Uma fonte para conferir.</h2><p>Informe o link e de onde ele vem. Sem upload de arquivos.</p><SourceForm onCreated={() => { setLoading(true); setPage(1); setRetry(n => n + 1); refresh(); }} /></section></div>
  </div>;
}
