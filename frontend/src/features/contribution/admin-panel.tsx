"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/provider";
import type { Indicator } from "@/lib/indicator-types";
import type { Policy, Plan, Source } from "@/lib/types";
import { decimalInput } from "@/lib/format";
import { Skeleton } from "@/components/page-kit";
import { Button } from "@/components/ui";
import { PanelHero } from "@/features/panel/kit";
import styles from "@/features/panel/panel.module.css";
type Account = {
  id: string;
  username: string;
  name: string;
  role: string;
  is_active: boolean;
};
type Event = {
  id: string;
  actor_id: string;
  entity_kind: string;
  action: string;
  reason: string;
  created_at: string;
};
export function AdminPanel() {
  const { user, request } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [content, setContent] = useState<(Policy | Plan)[]>([]);
  const [kind, setKind] = useState("policies");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [selected, setSelected] = useState<Indicator | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  useEffect(() => {
    let active = true;
    if (user?.role === "ADMIN")
      Promise.all([
        request<Account[]>(
          `admin/users?page_size=20&page=${page}&q=${encodeURIComponent(search)}`,
        ),
        request<Indicator[]>("admin/indicators?page_size=100"),
        request<Event[]>("admin/audit?page_size=20"),
        request<Source[]>("sources/mine?page_size=100"),
        request<(Policy | Plan)[]>(
          `${kind}?page_size=20&q=${encodeURIComponent(search)}`,
        ),
      ])
        .then(([a, i, e, s, c]) => {
          if (active) {
            setAccounts(a.data);
            setTotal(a.pagination?.total ?? 0);
            setIndicators(i.data);
            setEvents(e.data);
            setSources(s.data);
            setContent(c.data);
            setLoaded(true);
            setError("");
          }
        })
        .catch((e: Error) => {
          if (active) { setError(e.message); setLoaded(true); }
        });
    return () => {
      active = false;
    };
  }, [user, request, revision, kind, search, page]);
  async function mutate(path: string, method: string, body: unknown) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await request(path, { method, body: JSON.stringify(body) });
      setMessage("Alteração registrada com autoria, data e motivo.");
      setRevision((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (user?.role !== "ADMIN")
    return (
      <div className={styles.workspace}><PanelHero title="Administração" description="Esta área exige uma conta administradora. As permissões também são conferidas pela API." /><Button href="/painel" variant="secondary">Voltar ao painel</Button></div>
    );
  return (
    <div className={styles.workspace}>
      <PanelHero title="Cuidar dos dados. Preservar a história." description="Cada alteração tem autoria e motivo. Correções criam revisões; arquivar retira do catálogo sem apagar as publicações." tone="night" action={<Button href="/painel/contextos/revisao" variant="secondary">Revisar contextos →</Button>} />
      <nav className={styles.adminNav} aria-label="Seções da administração"><a href="#usuarios">Contas</a><a href="#conteudo-publicado">Publicações</a><a href="#definicoes">Indicadores</a><a href="#observacoes">Observações</a><a href="#manutencao">Histórico</a></nav>
      {loaded ? null : <Skeleton />}
      {error && (
        <p role="alert" className="error">
          {error} <button type="button" className="button secondary" onClick={() => setRevision(n => n + 1)}>Tentar novamente</button>
        </p>
      )}
      {message && <p role="status">{message}</p>}
      <label className={styles.filters}>
        Buscar usuário ou título de conteúdo
        <input
          type="search"
          maxLength={120}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </label>
      <section id="usuarios" className={styles.adminSection}>
        <h2>Usuários</h2><p className={styles.meta}>{accounts.length} nesta página · {total} no total</p>
        <div className="catalog">
          {accounts.map((a) => (
            <article className="card" key={a.id}>
              <h3>
                {a.name} · @{a.username}
              </h3>
              <p>
                {a.role === "ADMIN"
                  ? "Administrador"
                  : a.is_active
                    ? "Conta ativa"
                    : "Conta desativada"}
              </p>
              {a.role !== "ADMIN" && (
                <form
                  className="editor"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const data = new FormData(e.currentTarget);
                    void mutate(`admin/users/${a.id}`, "PATCH", {
                      is_active: !a.is_active,
                      reason: data.get("reason"),
                    });
                  }}
                >
                  <label>
                    Motivo
                    <input name="reason" required maxLength={2000} />
                  </label>
                  <button disabled={busy}>
                    {a.is_active ? "Desativar conta" : "Reativar conta"}
                  </button>
                </form>
              )}
            </article>
          ))}
        </div>
        <div className="pagination">
          {page > 1 && (
            <button onClick={() => setPage(page - 1)}>Anterior</button>
          )}
          {page * 20 < total && (
            <button onClick={() => setPage(page + 1)}>Próxima</button>
          )}
        </div>
      </section>
      <section id="conteudo-publicado" className={styles.adminSection}>
        <h2>Conteúdo publicado</h2><p className={styles.meta}>Até 20 publicações por consulta. O arquivamento exige uma justificativa.</p>
        <label>
          Catálogo
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="policies">Propostas</option>
            <option value="plans">Planos</option>
          </select>
        </label>
        <div className="catalog">
          {content.map((c) => (
            <article className="card" key={c.id}>
              <h3>{c.version.title}</h3>
              <p>Por {c.author.name}</p>
              <form
                className="editor"
                onSubmit={(e) => {
                  e.preventDefault();
                  void mutate(`${kind}/${c.id}/archive`, "POST", {
                    reason: new FormData(e.currentTarget).get("reason"),
                  });
                }}
              >
                <label>
                  Motivo do arquivamento
                  <input name="reason" required maxLength={2000} />
                </label>
                <button disabled={busy}>Arquivar preservando histórico</button>
              </form>
            </article>
          ))}
        </div>
      </section>
      <section id="definicoes" className={styles.adminSection}>
        <h2>Definição de indicadores</h2>
        <label>
          Editar indicador
          <select
            value={selected?.id ?? ""}
            onChange={(e) =>
              setSelected(
                indicators.find((i) => i.id === e.target.value) ?? null,
              )
            }
          >
            <option value="">Novo indicador</option>
            {indicators.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name}
                {i.is_active ? "" : " (inativo)"}
              </option>
            ))}
          </select>
        </label>
        <form
          className="editor"
          key={selected?.id ?? "new"}
          onSubmit={(e) => {
            e.preventDefault();
            const values = Object.fromEntries(new FormData(e.currentTarget));
            const body = {
              ...values,
              base_year: values.base_year ? Number(values.base_year) : null,
              is_active: values.is_active === "on",
            };
            void mutate(
              selected ? `admin/indicators/${selected.id}` : "admin/indicators",
              selected ? "PUT" : "POST",
              body,
            );
          }}
        >
          {[
            ["code", "Código estável"],
            ["name", "Nome"],
            ["description", "Descrição"],
            ["unit", "Unidade"],
            ["scope", "Abrangência"],
            ["methodology", "Metodologia"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                name={key}
                required
                defaultValue={
                  selected ? String(selected[key as keyof Indicator] ?? "") : ""
                }
              />
            </label>
          ))}
          <div className="fields">
            <label>
              Categoria
              <select
                name="category"
                defaultValue={selected?.category ?? "ECONOMY"}
              >
                <option value="ECONOMY">Economia</option>
                <option value="FISCAL">Fiscal</option>
                <option value="SOCIAL">Social</option>
                <option value="PUBLIC_SPENDING">Gastos públicos</option>
              </select>
            </label>
            <label>
              Frequência
              <select
                name="frequency"
                defaultValue={selected?.frequency ?? "MONTHLY"}
              >
                <option value="DAILY">Diária</option>
                <option value="MONTHLY">Mensal</option>
                <option value="QUARTERLY">Trimestral</option>
                <option value="YEARLY">Anual</option>
                <option value="IRREGULAR">Irregular</option>
              </select>
            </label>
            <label>
              Ano-base (opcional)
              <input
                name="base_year"
                type="number"
                min={1900}
                max={2200}
                defaultValue={selected?.base_year ?? ""}
              />
            </label>
          </div>
          <label className="checkbox">
            <input
              type="checkbox"
              name="is_active"
              defaultChecked={selected?.is_active ?? true}
            />
            Exibir no catálogo público
          </label>
          <label>
            Motivo
            <input name="reason" required maxLength={2000} />
          </label>
          <button className="button" disabled={busy}>
            Salvar definição
          </button>
        </form>
      </section>
      <section id="observacoes" className={styles.adminSection}>
        <h2>Registrar observação ou revisão</h2>
        <p>
          Use uma fonte oficial cadastrada no painel. Referência e data de
          coleta devem corresponder ao dado consultado.
        </p>
        <form
          className="editor"
          onSubmit={(e) => {
            e.preventDefault();
            const values = Object.fromEntries(new FormData(e.currentTarget));
            const body = {
              reference_date: values.reference_date,
              value: decimalInput(String(values.value)),
              source_id: values.source_id,
              retrieved_at: new Date(String(values.retrieved_at)).toISOString(),
              revision_reason: values.revision_reason,
              provenance: {
                dataset_url: values.dataset_url,
                license: values.license,
                license_url: values.license_url,
                method: values.method,
                institution: values.institution,
              },
            };
            void mutate(
              `admin/indicators/${values.indicator_id}/values`,
              "POST",
              body,
            );
          }}
        >
          <label>
            Indicador
            <select name="indicator_id" required>
              <option value="">Escolha</option>
              {indicators.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Fonte cadastrada
            <select name="source_id" required>
              <option value="">Escolha</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </select>
          </label>
          <div className="fields">
            <label>
              Referência
              <input name="reference_date" type="date" required />
            </label>
            <label>
              Valor decimal
              <input name="value" inputMode="decimal" required />
            </label>
            <label>
              Data de coleta
              <input name="retrieved_at" type="datetime-local" required />
            </label>
          </div>
          {[
            ["dataset_url", "URL do conjunto"],
            ["license", "Licença dos dados"],
            ["license_url", "URL dos termos"],
            ["institution", "Instituição"],
            ["method", "Método / tabela / transformação"],
            ["revision_reason", "Motivo da importação ou revisão"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                name={key}
                type={key.endsWith("url") ? "url" : "text"}
                required
                maxLength={2000}
              />
            </label>
          ))}
          <button className="button" disabled={busy}>
            Registrar observação
          </button>
        </form>
      </section>
      <section id="manutencao" className={styles.adminSection}>
        <h2>Últimos registros de manutenção</h2>{loaded && !events.length && <p className={styles.meta}>Nenhum registro nesta consulta.</p>}
        <ul className={styles.auditList}>
          {events.map((event) => (
            <li key={event.id}>
              {new Date(event.created_at).toLocaleString("pt-BR")} ·{" "}
              {event.entity_kind} · {event.action} · {event.reason} ·
              responsável {event.actor_id}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
