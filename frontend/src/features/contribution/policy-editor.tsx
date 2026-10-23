"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/provider";
import { categories, impacts, fundings, decimalInput } from "@/lib/format";
import type {
  Policy,
  PolicyVersion,
  Source,
  Impact,
  Funding,
} from "@/lib/types";
import { ApiError } from "@/lib/api";
import { DraftBaselineControl } from "@/components/draft-baseline-control";
import { BaselinePanel } from "@/components/baseline-panel";
import { PageHero, Skeleton } from "@/components/page-kit";
import styles from "./editor.module.css";
import { ImpactMeter, cents, decimal } from "@/components/impact-meter";
import type { Indicator } from "@/lib/indicator-types";
import type { Baseline } from "@/lib/types";
import { SourceForm } from "./sources";
import {
  fiscalMetadataBody, fiscalAggregateState, aggregateMessages,
  fiscalScopes, accountingBases, priceBases, fiscalComponents, periodBases,
  unspecifiedFiscalMetadata,
} from "@/lib/fiscal-compatibility";

const empty: PolicyVersion = {
  id: "",
  version_number: 1,
  status: "DRAFT",
  title: "",
  summary: "",
  problem: "",
  proposal: "",
  category: "OTHER",
  implementation_start: null,
  implementation_end: null,
  financial_impact_status: "NOT_ESTIMATED",
  impact_justification: "",
  change_summary: "",
  impacts: [],
  fundings: [],
  sources: [],
};
function draftBody(v: PolicyVersion) {
  return {
    ...(v.proposal_details ? { proposal_details: v.proposal_details } : {}),
    title: v.title,
    summary: v.summary,
    problem: v.problem,
    proposal: v.proposal,
    category: v.category,
    implementation_start: v.implementation_start,
    implementation_end: v.implementation_end,
    financial_impact_status: v.financial_impact_status,
    impact_justification: v.impact_justification || null,
    change_summary: v.change_summary || null,
    impacts: v.impacts.map((r) => ({
      year: r.year,
      impact_type: r.impact_type,
      description: r.description,
      amount: decimalInput(r.amount),
      ...fiscalMetadataBody(r),
    })),
    fundings: v.fundings.map((r) => ({
      year: r.year,
      funding_type: r.funding_type,
      description: r.description,
      amount: r.amount ? decimalInput(r.amount) : null,
    })),
    sources: v.sources.map((r) => ({
      source_id: r.source.id,
      usage_description: r.usage_description,
    })),
  };
}
export function PolicyEditor({ id }: { id?: string }) {
  const { request } = useAuth();
  const router = useRouter();
  const [policyId, setPolicyId] = useState(id);
  const [step, setStep] = useState(0);
  const [autoStatus, setAutoStatus] = useState(
    "O rascunho é privado. Comece a escrever.",
  );
  const dirty = useRef(false),
    attempted = useRef(""),
    inFlight = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const [values, setValues] = useState(empty);
  const [sources, setSources] = useState<Source[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(Boolean(id));
  useEffect(() => {
    let active = true;
    if (id)
      request<Policy>(`policies/${id}/draft`)
        .catch((e) => {
          if (e instanceof ApiError && e.code === "DRAFT_NOT_FOUND")
            return request<Policy>(`policies/${id}/draft`, { method: "POST" });
          throw e;
        })
        .then((r) => {
          if (active) setValues(r.data.version);
        })
        .catch((e: Error) => {
          if (active) setError(e.message);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    return () => {
      active = false;
    };
  }, [id, request]);
  useEffect(() => {
    let active = true;
    const q = encodeURIComponent(search);
    Promise.all([
      request<Source[]>(`sources/mine?page_size=100&q=${q}`),
      request<Source[]>(`sources?page_size=100&q=${q}`),
    ])
      .then(([mine, published]) => {
        if (active)
          setSources([
            ...new Map(
              [...mine.data, ...published.data].map((s) => [s.id, s]),
            ).values(),
          ]);
      })
      .catch((e: Error) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [request, search]);
  function field<K extends keyof PolicyVersion>(
    key: K,
    value: PolicyVersion[K],
  ) {
    dirty.current = true;
    setValues((v) => ({ ...v, [key]: value }));
  }
  function detailField(key: "beneficiaries" | "adversely_affected" | "risks", value: string) {
    const details = values.proposal_details;
    if (!details || details.level !== "COMPLETE") return;
    field("proposal_details", { ...details, [key]: value });
  }
  function changeImpact(index: number, value: Partial<Impact>) {
    field(
      "impacts",
      values.impacts.map((row, i) =>
        i === index ? { ...row, ...value } : row,
      ),
    );
  }
  function changeFunding(index: number, value: Partial<Funding>) {
    field(
      "fundings",
      values.fundings.map((row, i) =>
        i === index ? { ...row, ...value } : row,
      ),
    );
  }
  useEffect(() => {
    if (loading || busy || !dirty.current || inFlight.current) return;
    let body: ReturnType<typeof draftBody>;
    try {
      body = draftBody(values);
    } catch {
      return;
    }
    const fingerprint = JSON.stringify(body);
    if (attempted.current === fingerprint) return;
    if (
      body.impacts.some(
        (r) => !r.description.trim() || !/^\d+(\.\d{1,2})?$/.test(r.amount) ||
          (r.price_basis === "CONSTANT" && !Number.isInteger(r.price_base_year)),
      ) ||
      body.fundings.some((r) => !r.description.trim()) ||
      body.sources.some((r) => !r.usage_description.trim())
    )
      return;
    const timer = setTimeout(async () => {
      if (inFlight.current) return;
      attempted.current = fingerprint;
      inFlight.current = true;
      setBusy(true);
      setAutoStatus("Salvando rascunho…");
      try {
        const result = await request<Policy>(
          policyId ? `policies/${policyId}` : "policies",
          { method: policyId ? "PATCH" : "POST", body: fingerprint },
        );
        if (mounted.current) {
          setPolicyId(result.data.id);
          setValues((current) => ({
            ...current,
            id: result.data.version.id,
            baseline_snapshot: result.data.version.baseline_snapshot,
            version_number: result.data.version.version_number,
          }));
          setAutoStatus(
            "Rascunho salvo automaticamente. Ele está no seu painel.",
          );
        }
      } catch (error) {
        if (mounted.current)
          setAutoStatus(
            error instanceof Error
              ? `Não salvo: ${error.message}`
              : "Não salvo. Use o botão de salvar para tentar novamente.",
          );
      } finally {
        inFlight.current = false;
        if (mounted.current) setBusy(false);
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [values, policyId, request, loading, busy]);
  useEffect(() => {
    if (id) return;
    let active = true;
    const code = new URLSearchParams(window.location.search).get("indicador");
    request<Baseline>("indicators/baseline/current")
      .then((r) => {
        if (active)
          setValues((v) => (v.id ? v : { ...v, baseline_snapshot: r.data }));
      })
      .catch(() => {});
    if (code)
      request<Indicator>(`indicators/${encodeURIComponent(code)}`)
        .then((r) => {
          if (active && r.data.latest) {
            const latest = r.data.latest;
            dirty.current = true;
            setValues((v) => ({
              ...v,
              sources: v.sources.some(
                (link) => link.source.id === latest.source.id,
              )
                ? v.sources
                : [
                    ...v.sources,
                    {
                      source: latest.source,
                      usage_description: `Contexto inicial: ${r.data.name}, ${latest.value} ${r.data.unit}, referência ${latest.reference_date}. A fonte contextual não estima sozinha os efeitos desta proposta.`,
                    },
                  ],
            }));
          }
        })
        .catch((e: Error) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [id, request]);
  async function save(publish: boolean) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const body = draftBody(values);
      const result = await request<Policy>(
        policyId ? `policies/${policyId}` : "policies",
        { method: policyId ? "PATCH" : "POST", body: JSON.stringify(body) },
      );
      setPolicyId(result.data.id);
      attempted.current = JSON.stringify(body);
      setValues(result.data.version);
      setAutoStatus("Rascunho salvo.");
      if (publish) {
        const published = await request<Policy>(
          `policies/${result.data.id}/publish`,
          { method: "POST" },
        );
        router.push(`/propostas/${published.data.slug}`);
      } else {
        setMessage("Rascunho salvo. Só você pode consultá-lo.");
        if (!policyId) router.replace(`/painel/propostas/${result.data.id}`);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  if (loading) return <Skeleton />;
  let previewIncomplete =
    values.financial_impact_status === "ESTIMATED" && !values.impacts.length;
  let positive = BigInt(0),
    negative = BigInt(0);
  for (const row of values.impacts) {
    try {
      const amount = decimalInput(row.amount);
      if (!/^\d+(\.\d{1,2})?$/.test(amount)) {
        previewIncomplete = true;
        continue;
      }
      if (["NEW_REVENUE", "EXPENSE_REDUCTION"].includes(row.impact_type))
        positive += cents(amount);
      else negative += cents(amount);
    } catch {
      previewIncomplete = true;
    }
  }
  const aggregate = fiscalAggregateState(values.impacts);
  const steps = ["Problema", "Solução", "Impacto", "Fontes", "Revisar"];
  return (
    <div className={styles.workspace}>
      <PageHero title={id ? "Editar proposta" : "Nova proposta"} tone="yellow"
        description="Problema, solução, custos e fontes: construa uma versão que outras pessoas possam conferir."
        action={<span className={styles.status}>Rascunho privado · versão {values.version_number}</span>} />
      <details className={styles.reference}>
        <summary>Brasil de referência e base deste rascunho</summary>
      {!policyId && (
        <p className="muted">
          A base de referência será capturada ao salvar o primeiro rascunho.
        </p>
      )}
      <BaselinePanel
        baseline={values.baseline_snapshot}
        preserved={Boolean(policyId)}
      />
      <DraftBaselineControl
        kind="policies"
        id={policyId}
        disabled={busy}
        onUpdated={(baseline) => {
          setValues((v) => ({ ...v, baseline_snapshot: baseline }));
        }}
      />
      </details>
      <nav className={`editor-stepper ${styles.steps}`} aria-label="Etapas da proposta">
        {steps.map((text, index) => (
          <button
            key={text}
            type="button"
            aria-current={step === index ? "step" : undefined}
            onClick={() => setStep(index)}
          >
            <span aria-hidden="true">{index + 1}</span> {text}
          </button>
        ))}
      </nav>
      <p className={styles.progressText}>Etapa {step + 1} de {steps.length} · {steps[step]}</p>
      <p className="autosave-status" role="status">
        {autoStatus}
      </p>
      <div className={`editor-layout ${styles.layout}`}>
        <form
          noValidate
          className={`editor ${styles.form}`}
          onSubmit={(e) => {
            e.preventDefault();
            void save(false);
          }}
        >
          <div className="editor-step" hidden={step !== 0}>
            <h2>Qual problema precisa mudar?</h2>
            <label>
              Título
              <input
                value={values.title}
                maxLength={200}
                onChange={(e) => field("title", e.target.value)}
              />
            </label>
            <label>
              Resumo
              <textarea
                value={values.summary}
                maxLength={5000}
                onChange={(e) => field("summary", e.target.value)}
              />
            </label>
            <label>
              Problema
              <textarea
                value={values.problem}
                maxLength={20000}
                onChange={(e) => field("problem", e.target.value)}
              />
            </label>
          </div>
          <div className="editor-step" hidden={step !== 1}>
            <h2>O que você faria diferente?</h2>
            {values.proposal_details?.level === "COMPLETE" && (
              <fieldset>
                <legend>Quem é afetado pela mudança?</legend>
                <p className="notice">Esta proposta começou no fluxo de ideias. Ao criar uma nova versão, preserve ou revise também quem ganha, quem pode perder e os riscos. A autoria e os rótulos de assistência por IA permanecem registrados.</p>
                {([
                  ["beneficiaries", "Quem ganha com essa mudança?"],
                  ["adversely_affected", "Quem poderia perder com isso?"],
                  ["risks", "O que poderia dar errado?"],
                ] as const).map(([key, label]) => (
                  <label key={key}>
                    {label}
                    {values.proposal_details?.assisted_fields.includes(key) && <small>Assistido por IA · texto confirmado pelo autor</small>}
                    <textarea value={values.proposal_details?.[key] ?? ""} maxLength={10000} onChange={(event) => detailField(key, event.target.value)} />
                  </label>
                ))}
              </fieldset>
            )}
            <label>
              Solução proposta
              <textarea
                value={values.proposal}
                maxLength={20000}
                onChange={(e) => field("proposal", e.target.value)}
              />
            </label>
            <div className="fields">
              <label>
                Categoria
                <select
                  value={values.category}
                  onChange={(e) => field("category", e.target.value)}
                >
                  {Object.entries(categories).map(([code, label]) => (
                    <option key={code} value={code}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Ano inicial
                <input
                  type="number"
                  min={1900}
                  max={2200}
                  value={values.implementation_start ?? ""}
                  onChange={(e) =>
                    field(
                      "implementation_start",
                      e.target.value ? Number(e.target.value) : null,
                    )
                  }
                />
              </label>
              <label>
                Ano final
                <input
                  type="number"
                  min={1900}
                  max={2200}
                  value={values.implementation_end ?? ""}
                  onChange={(e) =>
                    field(
                      "implementation_end",
                      e.target.value ? Number(e.target.value) : null,
                    )
                  }
                />
              </label>
            </div>
          </div>
          <div className="editor-step" hidden={step !== 2}>
            <h2>Quanto custa? Como pagar?</h2>
            <fieldset>
              <legend>Impacto fiscal</legend>
              <label>
                Estado da estimativa
                <select
                  value={values.financial_impact_status}
                  onChange={(e) =>
                    field("financial_impact_status", e.target.value)
                  }
                >
                  <option value="NOT_ESTIMATED">Ainda não estimado</option>
                  <option value="ESTIMATED">Estimado por ano</option>
                  <option value="NOT_APPLICABLE">
                    Não aplicável (justificar)
                  </option>
                </select>
              </label>
              <label>
                Premissas e justificativa
                <textarea
                  value={values.impact_justification ?? ""}
                  onChange={(e) =>
                    field("impact_justification", e.target.value)
                  }
                />
              </label>
              {values.impacts.map((row, index) => (
                <div className="row-editor" key={index}>
                  <div className="fields">
                    <label>
                      Ano
                      <input
                        type="number"
                        min={1900}
                        max={2200}
                        required
                        value={row.year}
                        onChange={(e) =>
                          changeImpact(index, { year: Number(e.target.value) })
                        }
                      />
                    </label>
                    <label>
                      Tipo
                      <select
                        value={row.impact_type}
                        onChange={(e) =>
                          changeImpact(index, { impact_type: e.target.value })
                        }
                      >
                        {Object.entries(impacts).map(([code, label]) => (
                          <option key={code} value={code}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Valor anual (R$)
                      <input
                        inputMode="decimal"
                        required
                        value={row.amount}
                        onChange={(e) =>
                          changeImpact(index, { amount: e.target.value })
                        }
                        placeholder="1000,00"
                      />
                    </label>
                  </div>
                  <fieldset>
                    <legend>O que este valor representa</legend>
                    <p className="muted">Informe o recorte da estimativa. Se não souber, mantenha “Não informado”; o site não completa isso por você.</p>
                    <div className="fields">
                      {([
                        ["fiscal_scope", "De qual governo?", fiscalScopes],
                        ["accounting_basis", "Quando o valor é contado?", accountingBases],
                        ["price_basis", "Preços usados", priceBases],
                        ["component", "Inclui juros?", fiscalComponents],
                        ["period_basis", "Período coberto", periodBases],
                      ] as const).map(([key, label, options]) => (
                        <label key={key}>
                          {label}
                          <select value={row[key] ?? "UNSPECIFIED"}
                            onChange={(e) => changeImpact(index, {
                              [key]: e.target.value,
                              ...(key === "price_basis" && e.target.value !== "CONSTANT" ? { price_base_year: null } : {}),
                            })}>
                            {Object.entries(options).map(([code, text]) => <option key={code} value={code}>{text}</option>)}
                          </select>
                        </label>
                      ))}
                      {row.price_basis === "CONSTANT" && (
                        <label>Ano-base dos preços
                          <input type="number" min={1900} max={2200} required
                            value={row.price_base_year ?? ""}
                            onChange={(e) => changeImpact(index, { price_base_year: e.target.value ? Number(e.target.value) : null })} />
                        </label>
                      )}
                    </div>
                    <p className="muted">Se for estado ou município, identifique qual nas premissas. Preços nominais são os do ano do impacto. A base observada é do Governo Central, em caixa e sem juros; anos futuros exigem um cenário com premissas próprias.</p>
                  </fieldset>
                  <label>
                    Como foi calculado
                    <textarea
                      required
                      value={row.description}
                      onChange={(e) =>
                        changeImpact(index, { description: e.target.value })
                      }
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      field(
                        "impacts",
                        values.impacts.filter((_, i) => i !== index),
                      )
                    }
                  >
                    Remover impacto {index + 1}
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() =>
                  field("impacts", [
                    ...values.impacts,
                    {
                      year:
                        values.implementation_start ?? new Date().getFullYear(),
                      impact_type: "NEW_EXPENSE",
                      amount: "",
                      description: "",
                      ...unspecifiedFiscalMetadata,
                    },
                  ])
                }
              >
                Adicionar impacto anual
              </button>
              <p className="muted">
                Informe cada ano separadamente. Valores declarados não são
                automaticamente corrigidos pela inflação.
              </p>
            </fieldset>
            <fieldset>
              <legend>Financiamento</legend>
              {values.fundings.map((row, index) => (
                <div className="row-editor" key={index}>
                  <div className="fields">
                    <label>
                      Tipo
                      <select
                        value={row.funding_type}
                        onChange={(e) =>
                          changeFunding(index, { funding_type: e.target.value })
                        }
                      >
                        {Object.entries(fundings).map(([code, label]) => (
                          <option key={code} value={code}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Ano (opcional)
                      <input
                        type="number"
                        min={1900}
                        max={2200}
                        value={row.year ?? ""}
                        onChange={(e) =>
                          changeFunding(index, {
                            year: e.target.value
                              ? Number(e.target.value)
                              : null,
                          })
                        }
                      />
                    </label>
                    <label>
                      Valor (opcional)
                      <input
                        inputMode="decimal"
                        value={row.amount ?? ""}
                        onChange={(e) =>
                          changeFunding(index, {
                            amount: e.target.value || null,
                          })
                        }
                      />
                    </label>
                  </div>
                  <label>
                    Origem ou pendência
                    <textarea
                      required
                      value={row.description}
                      onChange={(e) =>
                        changeFunding(index, { description: e.target.value })
                      }
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      field(
                        "fundings",
                        values.fundings.filter((_, i) => i !== index),
                      )
                    }
                  >
                    Remover financiamento {index + 1}
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() =>
                  field("fundings", [
                    ...values.fundings,
                    {
                      funding_type: "UNFUNDED",
                      year: null,
                      amount: null,
                      description: "",
                    },
                  ])
                }
              >
                Adicionar financiamento
              </button>
              <p className="muted">
                Novas despesas e renúncias exigem uma declaração, inclusive
                quando o financiamento ainda não foi definido.
              </p>
            </fieldset>
          </div>
          <div className="editor-step" hidden={step !== 3}>
            <h2>De onde vêm suas informações?</h2>
            <fieldset>
              <legend>Referências da proposta</legend>
              {values.sources.map((row, index) => (
                <div className="row-editor" key={row.source.id}>
                  <h3>{row.source.title}</h3>
                  <label>
                    Como esta fonte sustenta a proposta
                    <textarea
                      required
                      value={row.usage_description}
                      onChange={(e) =>
                        field(
                          "sources",
                          values.sources.map((s, i) =>
                            i === index
                              ? { ...s, usage_description: e.target.value }
                              : s,
                          ),
                        )
                      }
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      field(
                        "sources",
                        values.sources.filter((_, i) => i !== index),
                      )
                    }
                  >
                    Remover referência {index + 1}
                  </button>
                </div>
              ))}
              <label>
                Buscar fontes cadastradas
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </label>
              <label>
                Vincular fonte
                <select
                  value=""
                  onChange={(e) => {
                    const source = sources.find((s) => s.id === e.target.value);
                    if (source)
                      field("sources", [
                        ...values.sources,
                        { source, usage_description: "" },
                      ]);
                  }}
                >
                  <option value="">Escolha uma fonte</option>
                  {sources
                    .filter(
                      (s) => !values.sources.some((r) => r.source.id === s.id),
                    )
                    .map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.title} · {s.institution}
                      </option>
                    ))}
                </select>
              </label>
            </fieldset>
          </div>
          <div className="editor-step" hidden={step !== 4}>
            <h2>Revise antes de colocar a ideia na mesa.</h2>
            <p>
              {values.sources.length} fontes vinculadas ·{" "}
              {values.impacts.length} impactos anuais. Os dados da base
              contextual não validam automaticamente sua estimativa.
            </p>
            <label>
              O que mudou nesta versão (opcional)
              <textarea
                value={values.change_summary ?? ""}
                onChange={(e) => field("change_summary", e.target.value)}
              />
            </label>
          </div>
          <div className="actions">
            {step > 0 && (
              <button
                type="button"
                className="button secondary"
                onClick={() => setStep(step - 1)}
              >
                Voltar
              </button>
            )}
            {step < 4 && (
              <button
                type="button"
                className="button"
                onClick={() => setStep(step + 1)}
              >
                Continuar →
              </button>
            )}
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          {message && <p role="status">{message}</p>}
          <div className="actions">
            <button className="button secondary" disabled={busy}>
              Salvar rascunho
            </button>
            <button
              className="button"
              type="button"
              disabled={busy || step !== 4}
              onClick={() => void save(true)}
            >
              Publicar proposta
            </button>
          </div>
        </form>
        <aside className={`editor-sidebar ${styles.preview}`}>
          <p className={styles.status}>Prévia da proposta</p><h2>Veja como está ficando.</h2>
          <div className="editor-preview">
            <span className="category-tag" data-category={values.category}>
              {categories[values.category]}
            </span>
            <h3>{values.title || "O título aparece aqui"}</h3>
            <p>
              {values.summary ||
                "Escreva um resumo direto: o que muda e para quem?"}
            </p>
            <p>
              {values.implementation_start ?? "Ano inicial"}–
              {values.implementation_end ?? "Ano final"}
            </p>
            {aggregate === "INCOMPLETE" || aggregate === "HETEROGENEOUS" ? (
              <p className="notice" role="status">{aggregateMessages[aggregate]}</p>
            ) : (
              <ImpactMeter
                positive={decimal(positive)}
                negative={decimal(negative)}
                partial={previewIncomplete || values.financial_impact_status === "NOT_ESTIMATED"}
              />
            )}
          </div>
          <p className="muted">
            Prévia local. Campos de valores e referências incompletos precisam
            ser preenchidos para salvar.
          </p>
          {policyId && (
            <a href={`/painel/propostas/${policyId}`}>Abrir rascunho salvo →</a>
          )}
        </aside>
      </div>
      <details className="notice" hidden={step !== 3}>
        <summary>Cadastrar uma nova fonte por link</summary>
        <SourceForm
          onCreated={(source) => {
            setSources((s) => [source, ...s]);
            field("sources", [
              ...values.sources,
              { source, usage_description: "" },
            ]);
          }}
        />
      </details>
    </div>
  );
}
