"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/features/auth/provider";
import { ApiError } from "@/lib/api";
import type { Plan, PlanItem, Policy, Simulation } from "@/lib/types";
import { DraftBalance } from "@/components/draft-balance";
import { DraftBaselineControl } from "@/components/draft-baseline-control";
import { BaselinePanel } from "@/components/baseline-panel";
import { PageHero, Skeleton } from "@/components/page-kit";
import styles from "./editor.module.css";
import type { Baseline } from "@/lib/types";
import { FiscalResult } from "@/components/fiscal";
import { FiscalScenarioEditor } from "@/components/fiscal-scenario-editor";
import { fiscalScenarioBody, invalidateScenarioReview, planEditResetsScenarioReview, type FiscalScenario } from "@/lib/fiscal-scenario";
type Draft = {
  title: string;
  summary: string;
  vision: string;
  start_year: number;
  end_year: number;
  change_summary: string;
  policies: PlanItem[];
  fiscal_scenario: FiscalScenario | null;
};
const year = new Date().getFullYear();
export function PlanEditor({ id }: { id?: string }) {
  const { request } = useAuth();
  const router = useRouter();
  const [planId, setPlanId] = useState(id);
  const [values, setValues] = useState<Draft>({
    title: "",
    summary: "",
    vision: "",
    start_year: year,
    end_year: year + 3,
    change_summary: "",
    policies: [],
    fiscal_scenario: null,
  });
  const [baseline, setBaseline] = useState<Baseline | null>(null);
  const [number, setNumber] = useState(1);
  const [available, setAvailable] = useState<Policy[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<Simulation | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(Boolean(id));
  useEffect(() => {
    let active = true;
    if (id)
      request<Plan>(`plans/${id}/draft`)
        .catch((e) => {
          if (e instanceof ApiError && e.code === "DRAFT_NOT_FOUND")
            return request<Plan>(`plans/${id}/draft`, { method: "POST" });
          throw e;
        })
        .then((r) => {
          if (active) {
            setValues({
              ...r.data.version,
              fiscal_scenario: r.data.version.fiscal_scenario ?? null,
              change_summary: r.data.version.change_summary ?? "",
            });
            setNumber(r.data.version.version_number);
            setBaseline(r.data.version.baseline_snapshot ?? null);
            setResult(r.data.version.simulation);
          }
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
    request<Policy[]>(`policies?page_size=100&q=${encodeURIComponent(search)}`)
      .then((r) => {
        if (active) setAvailable(r.data);
      })
      .catch((e: Error) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [search, request]);
  useEffect(() => {
    if (id) return;
    let active = true;
    request<Baseline>("indicators/baseline/current")
      .then((r) => {
        if (active) setBaseline(r.data);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [id, request]);
  function field<K extends keyof Draft>(key: K, value: Draft[K]) {
    setValues((v) => ({
      ...v,
      [key]: value,
      fiscal_scenario: key === "fiscal_scenario"
        ? invalidateScenarioReview(value as FiscalScenario | null)
        : planEditResetsScenarioReview(key)
          ? invalidateScenarioReview(v.fiscal_scenario)
          : v.fiscal_scenario,
    }));
    setResult(null);
  }
  function move(index: number, delta: number) {
    const rows = [...values.policies];
    [rows[index], rows[index + delta]] = [rows[index + delta], rows[index]];
    field("policies", rows);
  }
  function applySavedPlan(plan: Plan) {
    setPlanId(plan.id);
    setValues({
      ...plan.version,
      change_summary: plan.version.change_summary ?? "",
      fiscal_scenario: plan.version.fiscal_scenario ?? null,
    });
    setNumber(plan.version.version_number);
    setBaseline(plan.version.baseline_snapshot ?? null);
    setResult(plan.version.simulation);
  }
  async function save(action: "save" | "simulate" | "publish" | "confirm") {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const body = {
        title: values.title,
        summary: values.summary,
        vision: values.vision,
        start_year: values.start_year,
        end_year: values.end_year,
        change_summary: values.change_summary || null,
        fiscal_scenario: fiscalScenarioBody(values.fiscal_scenario),
        policies: values.policies.map((p) => ({
          policy_version_id: p.policy_version_id,
          is_enabled: p.is_enabled,
        })),
      };
      const r = await request<Plan>(planId ? `plans/${planId}` : "plans", {
        method: planId ? "PATCH" : "POST",
        body: JSON.stringify(body),
      });
      applySavedPlan(r.data);
      setResult(null);
      if (action === "confirm") {
        const hash = r.data.version.fiscal_scenario?.review_input_hash;
        if (!hash) throw new Error("O rascunho foi salvo, mas o cenário não está pronto para revisão. Confira as premissas e a referência.");
        const confirmed = await request<Plan>("plans/" + r.data.id + "/fiscal-scenario/confirm", {
          method: "POST",
          body: JSON.stringify({ expected_input_hash: hash }),
        });
        applySavedPlan(confirmed.data);
        setResult(null);
        setMessage("Cenário salvo e revisão confirmada para estas propostas. Agora você pode simular.");
      } else if (action === "publish") {
        const published = await request<Plan>(`plans/${r.data.id}/publish`, {
          method: "POST",
        });
        router.push(`/planos/${published.data.slug}`);
      } else if (action === "simulate") {
        const simulation = await request<Simulation>(
          `plans/${r.data.id}/simulate`,
          { method: "POST" },
        );
        setResult(simulation.data);
        setMessage("Rascunho salvo e simulação registrada.");
      } else setMessage("Rascunho salvo.");
      // The draft endpoint restores the saved simulation after navigation.
      if (!planId && action !== "publish")
        router.replace(`/painel/planos/${r.data.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (loading) return <Skeleton />;
  return (
    <div className={styles.workspace}>
      <PageHero title={id ? "Editar plano" : "Novo Plano Brasil"} tone="green"
        description="Junte propostas publicadas, confira as escolhas e veja o efeito fiscal delas em conjunto."
        action={<span className={styles.status}>Rascunho privado · versão {number}</span>} />
      <details className={styles.reference}>
        <summary>Brasil de referência e base deste rascunho</summary>
      {!planId && (
        <p className="muted">
          A base de referência será capturada ao salvar o primeiro rascunho.
        </p>
      )}
      <BaselinePanel baseline={baseline} preserved={Boolean(planId)} />
      <DraftBaselineControl
        kind="plans"
        id={planId}
        disabled={busy}
        onUpdated={(baseline) => {
          setBaseline(baseline);
          setValues((v) => ({ ...v, fiscal_scenario: invalidateScenarioReview(v.fiscal_scenario) }));
          setResult(null);
        }}
      />
      </details>
      <nav className={styles.sectionNav} aria-label="Seções do plano">
        <a href="#plan-description">1. Sua visão</a><a href="#plan-policies">2. Propostas</a><a href="#plan-scenario">3. Cenário</a><a href="#plan-review">4. Revisar</a>
      </nav>
      <div className={`editor-layout ${styles.layout}`}>
        <form
          className={`editor ${styles.form}`}
          onSubmit={(e) => {
            e.preventDefault();
            void save("save");
          }}
        >
          <section id="plan-description" className={styles.formSection}><h2>Qual Brasil você quer construir?</h2>
          <label>
            Título
            <input
                disabled={busy}
              value={values.title}
              maxLength={200}
              onChange={(e) => field("title", e.target.value)}
            />
          </label>
          <label>
            Resumo
            <textarea
              disabled={busy}
              value={values.summary}
              maxLength={5000}
              onChange={(e) => field("summary", e.target.value)}
            />
          </label>
          <label>
            Visão do plano
            <textarea
              disabled={busy}
              value={values.vision}
              maxLength={20000}
              onChange={(e) => field("vision", e.target.value)}
            />
          </label>
          <div className="fields">
            <label>
              Ano inicial
              <input
                disabled={busy}
                type="number"
                required
                min={1900}
                max={2200}
                value={values.start_year}
                onChange={(e) => field("start_year", Number(e.target.value))}
              />
            </label>
            <label>
              Ano final
              <input
                disabled={busy}
                type="number"
                required
                min={1900}
                max={2200}
                value={values.end_year}
                onChange={(e) => field("end_year", Number(e.target.value))}
              />
            </label>
          </div>
          </section>
          <fieldset id="plan-policies" className={styles.formSection}>
            <legend>Propostas do plano</legend>
            {values.policies.length === 0 && <div className={styles.empty}><h3>Seu plano começa com uma proposta.</h3><p>Busque uma publicação abaixo e escolha a versão que quer combinar.</p></div>}
            <ol className="plan-items">
              {values.policies.map((p, index) => (
                <li className="row-editor" key={p.policy_id}>
                  <h3>{p.title}</h3>
                  <p>
                    <Link
                      href={`/propostas/${p.slug}?versao=${p.version_number}`}
                      target="_blank"
                    >
                      Consultar versão {p.version_number} ↗
                    </Link>
                  </p>
                  <label className="checkbox">
                    <input
                disabled={busy}
                      type="checkbox"
                      checked={p.is_enabled}
                      onChange={(e) =>
                        field(
                          "policies",
                          values.policies.map((item, i) =>
                            i === index
                              ? { ...item, is_enabled: e.target.checked }
                              : item,
                          ),
                        )
                      }
                    />
                    Incluir no cálculo
                  </label>
                  <div className="actions">
                    <button
                      type="button"
                      disabled={busy || index === 0}
                      aria-label={`Subir ${p.title}`}
                      onClick={() => move(index, -1)}
                    >
                      Subir
                    </button>
                    <button
                      type="button"
                      disabled={busy || index === values.policies.length - 1}
                      aria-label={`Descer ${p.title}`}
                      onClick={() => move(index, 1)}
                    >
                      Descer
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        field(
                          "policies",
                          values.policies.filter((_, i) => i !== index),
                        )
                      }
                    >
                      Remover
                    </button>
                  </div>
                </li>
              ))}
            </ol>
            <label>
              Buscar propostas publicadas
              <input
                disabled={busy}
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
            <label>
              Adicionar versão ao plano
              <select
                disabled={busy}
                value=""
                onChange={(e) => {
                  const p = available.find((row) => row.id === e.target.value);
                  if (p)
                    field("policies", [
                      ...values.policies,
                      {
                        estimate_status: p.version.financial_impact_status,
                        impacts: p.version.impacts,
                        unfunded: p.version.fundings.some(
                          (f) => f.funding_type === "UNFUNDED",
                        ),
                        baseline_id: p.version.baseline_snapshot?.id,
                        policy_id: p.id,
                        policy_version_id: p.version.id,
                        slug: p.slug,
                        title: p.version.title,
                        version_number: p.version.version_number,
                        is_enabled: true,
                        position: values.policies.length,
                      },
                    ]);
                }}
              >
                <option value="">Escolha uma proposta</option>
                {available
                  .filter(
                    (p) =>
                      !values.policies.some((item) => item.policy_id === p.id),
                  )
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.version.title} · versão {p.version.version_number}
                    </option>
                  ))}
              </select>
            </label>
            <p className="muted">
              As versões já incluídas permanecem fixadas. Para trocar de versão,
              remova a proposta e selecione a publicação atual.
            </p>
          </fieldset>
          <section id="plan-scenario" className={styles.formSection}><h2>O cenário por trás da conta</h2>
          <FiscalScenarioEditor
            scenario={values.fiscal_scenario}
            baseline={baseline}
            start={values.start_year}
            end={values.end_year}
            disabled={busy}
            onChange={(scenario) => field("fiscal_scenario", scenario)}
            onConfirm={() => void save("confirm")}
            onError={(message) => setError(message)}
          />
          </section>
          <section id="plan-review" className={styles.formSection}><h2>Confira antes de publicar.</h2><p>Salvar mantém o plano privado. Simular registra o cálculo; publicar preserva esta versão e suas escolhas.</p>
          <label>
            O que mudou nesta versão (opcional)
            <textarea
              disabled={busy}
              value={values.change_summary}
              onChange={(e) => field("change_summary", e.target.value)}
            />
          </label>
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
              className="button secondary"
              type="button"
              disabled={busy}
              onClick={(e) => {
                if (e.currentTarget.form?.reportValidity())
                  void save("simulate");
              }}
            >
              Simular plano
            </button>
            <button
              className="button"
              type="button"
              disabled={busy}
              onClick={(e) => {
                if (e.currentTarget.form?.reportValidity())
                  void save("publish");
              }}
            >
              Publicar plano
            </button>
          </div>
          </section>
        </form>
        <DraftBalance
          items={values.policies}
          start={values.start_year}
          end={values.end_year}
        />
      </div>
      {result && <FiscalResult result={result} />}
    </div>
  );
}
