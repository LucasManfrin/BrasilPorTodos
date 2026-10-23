"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/provider";
import { fetchApi } from "@/lib/api";
import { categories, impacts, fundings } from "@/lib/format";
import type { Source, Policy, Impact } from "@/lib/types";
import { fiscalScopes, accountingBases, priceBases, fiscalComponents, periodBases, unspecifiedFiscalMetadata } from "@/lib/fiscal-compatibility";
import { SourceForm } from "@/features/contribution/sources";
import { emptyIdea, confirmAnswer, readAnswer, normalizedIdea, ideaInput, canSave, guidanceContext, confirmedGuidanceText } from "./state";
import type { IdeaInput, Idea, Guidance, Organized } from "./state";
import { GuidanceTrace } from "./guidance-trace";
import { Button } from "@/components/ui";
import { PageHero, Skeleton } from "@/components/page-kit";
import { useCreationConsent } from "./consent";
import { ModeChoiceCard, GuidedStepper, AiConsentCard, AiResponseCard, AiLoadingCard, ProgressSidebar } from "./editor-kit";
import styles from "./ideas.module.css";

const stages = ["Problema", "Solução", "Impacto", "Fontes", "Revisar"];
const textFields = { title: "Dê um título à sua ideia", summary: "Conte sua ideia em uma frase", problem: "Qual problema você quer resolver?", proposal: "O que você quer mudar?", beneficiaries: "Quem ganha com essa mudança?", adversely_affected: "Quem poderia perder com isso?", risks: "O que poderia dar errado?" };
type Suggestion = { id: string; url: string; note: string; status: string };

export function IdeaEditor({ id, initialMode }: { id?: string; initialMode?: "manual" | "guided" }) {
  const { request } = useAuth();
  const router = useRouter();
  const [record, setRecord] = useState<Idea | null>(null);
  const [input, setInput] = useState<IdeaInput>(emptyIdea);
  const [mode, setMode] = useState<"choice" | "manual" | "guided">(initialMode ?? (id ? "manual" : "choice"));
  const [stage, setStage] = useState(0);
  const [loading, setLoading] = useState(Boolean(id));
  const [busy, setBusy] = useState(false);
  const [organizing, setOrganizing] = useState<"ai" | "literal" | null>(null);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [script, setScript] = useState<Guidance | null>(null);
  const [scriptError, setScriptError] = useState("");
  const [scriptRetry, setScriptRetry] = useState(0);
  // The quick entry already saved title and summary as the author wrote them.
  const [question, setQuestion] = useState(initialMode === "guided" && id ? 2 : 0);
  const [answer, setAnswer] = useState("");
  const [pending, setPending] = useState<Organized | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<number[]>([]);
  const [creationKey] = useState(() => `creation-${crypto.randomUUID()}`);
  const consentScope = useCreationConsent(id ?? creationKey);
  const consent = consentScope.consent;
  const [withoutAi, setWithoutAi] = useState(false);
  const [editingConsent, setEditingConsent] = useState(false);
  const answerRef = useRef<HTMLTextAreaElement>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceError, setSourceError] = useState("");
  const [sourceRetry, setSourceRetry] = useState(0);
  const [sourceSearch, setSourceSearch] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const revision = useRef(0);
  useEffect(() => {
    if (!id) return;
    let active = true;
    request<Idea>(`ideas/${id}`).then((response) => {
      if (active) { setRecord(response.data); setInput(ideaInput(response.data)); }
    }).catch((e: Error) => { if (active) setError(e.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id, request]);
  useEffect(() => {
    let active = true;
    fetchApi<Guidance>("guidance/script").then((response) => { if (active) { setScript(response.data); setScriptError(""); } })
      .catch((e: Error) => { if (active) setScriptError(e.message); });
    return () => { active = false; };
  }, [scriptRetry]);
  useEffect(() => {
    let active = true;
    Promise.all([request<Source[]>("sources?page_size=100"), request<Source[]>("sources/mine?page_size=100")])
      .then(([publicSources, mine]) => { if (active) { setSources([...new Map([...publicSources.data, ...mine.data].map((source) => [source.id, source])).values()]); setSourceError(""); } })
      .catch((e: Error) => { if (active) setSourceError(e.message); });
    return () => { active = false; };
  }, [request, sourceRetry]);
  useEffect(() => {
    if (!record?.id) return;
    let active = true;
    request<Suggestion[]>(`ideas/${record.id}/suggestions`).then((response) => { if (active) setSuggestions(response.data); }).catch(() => {});
    return () => { active = false; };
  }, [record?.id, request]);
  useEffect(() => {
    function warn(event: BeforeUnloadEvent) { if (dirty) event.preventDefault(); }
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  useEffect(() => {
    if (mode === "guided" && !editingConsent && (!script?.ai_available || consent || withoutAi)) {
      answerRef.current?.focus({ preventScroll: true });
      answerRef.current?.closest("[data-question]")?.scrollIntoView({ block: "start", behavior: "instant" });
    }
  }, [mode, question, consent, withoutAi, editingConsent, script?.ai_available]);
  function update(next: IdeaInput) { revision.current++; setInput(next); setDirty(true); setMessage(""); }
  function field(key: string, value: string) { update(confirmAnswer(input, key, value, false)); }
  function content(values: Partial<IdeaInput["content"]>) { update({ ...input, content: { ...input.content, ...values } }); }
  async function save(): Promise<Idea> {
    if (!canSave(input)) throw new Error("Para salvar, basta preencher o título e uma frase sobre a ideia.");
    const currentRevision = revision.current;
    const response = await request<Idea>(record ? `ideas/${record.id}` : "ideas", { method: record ? "PATCH" : "POST", body: JSON.stringify(normalizedIdea(input)) });
    setRecord(response.data);
    if (revision.current === currentRevision) setDirty(false);
    setMessage("Ideia salva no seu painel. Compartilhar é uma ação separada.");
    if (!id && revision.current === currentRevision) { consentScope.handoff(response.data.id); router.replace(`/painel/ideias/${response.data.id}`); }
    return response.data;
  }
  async function action(task: () => Promise<void>) {
    setBusy(true); setError(""); setMessage("");
    try { await task(); } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível concluir. Tente novamente."); }
    finally { setBusy(false); }
  }
  async function share() {
    const saved = dirty || !record ? await save() : record;
    const response = await request<Idea>(`ideas/${saved.id}/share`, { method: "POST" });
    setRecord(response.data); setMessage("Uma cópia desta ideia está compartilhada. Editar o rascunho torna a ideia privada até você compartilhar de novo.");
  }
  async function organize(useAi = true) {
    const step = script?.steps[question];
    if (!step) return;
    const enabled = useAi && consent && !withoutAi;
    setOrganizing(enabled ? "ai" : "literal");
    try {
      const response = await request<Organized>("guidance/organize", { method: "POST", body: JSON.stringify({ step_id: step.id, answer, consent: enabled, use_ai: enabled, context: enabled ? guidanceContext(input) : {} }) });
      setSelectedSuggestions([]); setPending(response.data);
    } finally { setOrganizing(null); }
  }
  function confirm() {
    const step = script?.steps[question];
    if (!pending || !step) return;
    let confirmed: string;
    try { confirmed = pending.unknown ? "" : confirmedGuidanceText(pending, selectedSuggestions, step.field); }
    catch (e) { setError(e instanceof Error ? e.message : "Confira o tamanho do texto."); return; }
    update(confirmAnswer(input, step.field, confirmed, pending.assisted_by_ai, pending.unknown));
    setPending(null); setAnswer("");
    if (question + 1 < (script?.steps.length ?? 0)) setQuestion(question + 1);
    else { setMode("manual"); setStage(2); setMessage("Respostas confirmadas. Agora você pode conferir prazos, valores e fontes. O que não souber pode ficar em aberto."); }
  }
  function textField(key: keyof typeof textFields) {
    const value = readAnswer(input, key);
    return <label key={key}>{textFields[key]}<small>{key === "title" || key === "summary" ? "Necessário para salvar a ideia" : "Opcional na ideia · necessário para proposta completa"}</small> {input.assisted_fields.includes(key) && <small>Assistido por IA</small>}
      {key === "title" ? <input value={value} maxLength={200} onChange={(e) => field(key, e.target.value)} /> : <textarea value={value} maxLength={key === "summary" ? 5000 : ["beneficiaries", "adversely_affected", "risks"].includes(key) ? 10000 : 20000} onChange={(e) => field(key, e.target.value)} />}
    </label>;
  }
  function changeImpact(index: number, values: Partial<Impact>) { content({ impacts: input.content.impacts.map((item, i) => i === index ? { ...item, ...values } : item) }); }
  const usingAi = Boolean(script?.ai_available && consent && !withoutAi);
  const needsConsent = Boolean(script?.ai_available && ((!consent && !withoutAi) || editingConsent));
  const complete = record?.checklist.filter((item) => item.complete).length ?? 0;
  const locked = record?.status === "PROMOTED" || record?.status === "ARCHIVED";
  if (loading) return <Skeleton />;
  if (id && !record) return <section className={styles.panel}><h1>Não conseguimos abrir esta ideia.</h1><p role="alert">{error}</p><button onClick={() => window.location.reload()}>Tentar de novo</button><Link href="/painel/ideias">Voltar às minhas ideias</Link></section>;
  if (locked) return <section className={styles.panel}><h1>{record.title}</h1><p>Esta ideia foi {record.status === "PROMOTED" ? "transformada em proposta completa" : "arquivada"}.</p>{record.promoted_policy_id && <Link className="button" href={`/painel/propostas/${record.promoted_policy_id}`}>Abrir proposta</Link>}<Link href="/painel/ideias">Minhas ideias</Link></section>;
  return <div className={styles.editor}><fieldset className={styles.editable} disabled={busy} aria-busy={busy} aria-label="Editor da ideia">
    <div className={styles.editorHero}><PageHero tone="yellow" breadcrumb={id ? "Desenvolver ideia" : "Preparar proposta completa"} title={mode === "choice" ? "Prepare uma proposta completa." : mode === "guided" ? "Conte do seu jeito." : id ? "Desenvolva sua ideia." : "Detalhe sua proposta."} description="Detalhe o problema, a solução, o financiamento, os riscos e as fontes. Só uma proposta completa e publicada entra nos planos e cálculos." /></div>
    <div className={styles.toolbar}>{!id && <Link href="/painel/ideias/nova">Só quero guardar uma ideia por enquanto →</Link>}<Link href="/painel/ideias">Já tenho uma ideia salva</Link>{mode !== "choice" && <Button variant="tertiary" onClick={() => setMode("choice")}>Trocar caminho</Button>}{record?.status === "SHARED" && <Link href={`/ideias/${record.id}`}>Ver cópia compartilhada ↗</Link>}</div>
    {record?.origin_attribution && <section className={styles.notice}><strong>Uma cópia com autoria preservada</strong><p>Você começou a partir de “{record.origin_attribution.title}”, de {record.origin_attribution.author.name} (@{record.origin_attribution.author.username}). A cópia é independente.</p>{record.origin_attribution.source_snapshots?.length > 0 && <details><summary>Referências da ideia original</summary><p>Estas referências preservam a atribuição. Para usá-las na sua proposta, cadastre e vincule o link na etapa Fontes, explicando o uso.</p><ul>{record.origin_attribution.source_snapshots.map((source) => <li key={source.id}>{source.title} · {source.institution}<p className={styles.text}>{source.url}</p></li>)}</ul></details>}</section>}
    {mode === "choice" ? <><section className={styles.modes} aria-label="Como você quer montar sua proposta?"><ModeChoiceCard guided onChoose={() => { setMode("guided"); setAnswer(current => current || readAnswer(input,script?.steps[question]?.field ?? "title")); }} /><ModeChoiceCard onChoose={() => setMode("manual")} /></section><div className={styles.levels}><div><strong>Ideia</strong><span>Título + uma frase. Salve e escolha se quer compartilhar.</span></div><span aria-hidden="true">→</span><div><strong>Proposta completa</strong><span>Premissas, fontes e impactos definidos para publicar e compor planos.</span></div></div><p className={styles.support}>Sem pressão para saber tudo. Complete no seu ritmo.</p></> : <div className={styles.modeSwitch} aria-label="Trocar modo sem perder respostas"><Button variant="tertiary" onClick={() => { setMode("guided"); setAnswer(current => current || readAnswer(input,script?.steps[question]?.field ?? "title")); }}>Me ajuda a montar</Button><Button variant="tertiary" onClick={() => setMode("manual")}>Eu preencho</Button></div>}
    {error && mode !== "guided" && <div className={styles.notice} role="alert">{error}</div>}{message && <p className={styles.notice} role="status">{message}</p>}
    {mode !== "choice" && <div className={`${styles.layout} ${mode === "guided" ? styles.guidedLayout : ""}`}><div className={styles.panel}>
      {mode === "guided" ? <div className={styles.fields}>
        {scriptError && <div className={styles.notice} role="alert"><p>{scriptError}</p><Button variant="secondary" onClick={() => setScriptRetry(n => n + 1)}>Tentar carregar roteiro</Button><Button variant="tertiary" onClick={() => setMode("manual")}>Continuar manualmente</Button></div>}
        {!script && !scriptError && <AiLoadingCard kind="script" />}
        {script && script.steps[question] && <>
          {needsConsent ? <AiConsentCard days={script.privacy.log_retention_days} onAccept={() => { consentScope.accept(); setWithoutAi(false); setEditingConsent(false); }} onWithout={() => { consentScope.revoke(); setWithoutAi(true); setEditingConsent(false); }} /> : <>
            <div className={styles.guideTop}><span className={styles.aiIndicator}>{usingAi ? "IA ativa ✓" : "Guiado sem IA"}</span>{script.ai_available && <Button variant="tertiary" onClick={() => setEditingConsent(true)}>mudar</Button>}</div>
            <GuidedStepper current={question} total={script.steps.length} version={script.version} />
            <div data-question className={styles.questionFrame} key={script.steps[question].id}><h2 className={styles.guideQuestion}>{script.steps[question].question}</h2><p className={styles.support}>Uma resposta de cada vez. “Não sei” também vale.</p>
            <label className={styles.answerLabel}>Sua resposta<textarea ref={answerRef} value={answer} maxLength={4000} placeholder={question === 0 ? "Um nome simples para a mudança que você quer ver." : "Pode escrever como você fala. Conte o que pensa e o que ainda não sabe."} aria-describedby="answer-count" onChange={e => { setAnswer(e.target.value); setPending(null); }} disabled={busy} /></label><small id="answer-count" className={styles.counter}>{answer.length.toLocaleString("pt-BR")} / 4.000 caracteres</small></div>
            {organizing && <AiLoadingCard kind={organizing} />}
            {!pending && !busy && <div className={styles.guideActions}><Button disabled={!answer.trim()} onClick={() => void action(() => organize())}>{usingAi ? "Desenvolver com IA" : "Conferir resposta"}</Button><Button variant="secondary" onClick={() => { setAnswer("Não sei"); setPending({ step_id: script.steps[question].id, question: script.steps[question].question, original_text: "Não sei", organized_text: "", unknown: true, assisted_by_ai: false, script_version: script.version }); }}>Não sei</Button>{usingAi && <Button variant="tertiary" disabled={!answer.trim()} onClick={() => void action(() => organize(false))}>Usar minhas palavras, sem IA</Button>}</div>}
            {pending && <AiResponseCard pending={pending} answer={answer} selected={selectedSuggestions} onSelect={(index, checked) => setSelectedSuggestions(items => checked ? [...items,index] : items.filter(item => item !== index))} onConfirm={confirm} onCorrect={() => { setPending(null); answerRef.current?.focus(); }} onOriginal={() => { setSelectedSuggestions([]); setPending({ ...pending, organized_text: pending.original_text ?? answer, rewritten: false, assisted_by_ai: false, suggestions: [], open_questions: [] }); }} />}
            {error && <div className={styles.notice} role="alert"><p>{error}</p><Button variant="secondary" onClick={() => void action(() => organize())}>Tentar de novo</Button><Button variant="tertiary" onClick={() => void action(() => organize(false))}>Seguir com minhas palavras</Button></div>}
            {script.ai_available && !pending && <details className={styles.technical}><summary>Detalhes técnicos</summary><GuidanceTrace callId="latest" /></details>}
            {question > 0 && <Button variant="tertiary" onClick={() => { setQuestion(question - 1); setAnswer(readAnswer(input,script.steps[question - 1].field)); setPending(null); }}>← Pergunta anterior</Button>}
          </>}
        </>}
      </div> : <>
        <div className={styles.manualProgress}><strong>Etapa {stage + 1} de {stages.length}</strong><progress max={stages.length} value={stage + 1} aria-label={`Etapa ${stage + 1} de ${stages.length}`} /></div><nav className={styles.steps} aria-label="Etapas da ideia">{stages.map((label, index) => <button key={label} aria-current={stage === index ? "step" : undefined} onClick={() => setStage(index)}>{index + 1}. {label}</button>)}</nav>
        <div className={styles.fields}>
          {stage === 0 && <><h2>Qual problema você quer resolver?</h2><p className={styles.support}>Título e uma frase bastam para salvar. Detalhes podem vir depois.</p>{textField("title")}{textField("summary")}{textField("problem")}<label>Área<select value={input.content.category} onChange={(e) => content({ category: e.target.value })}>{Object.entries(categories).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label></>}
          {stage === 1 && <><h2>O que muda na prática?</h2>{textField("proposal")}{textField("beneficiaries")}{textField("adversely_affected")}{textField("risks")}</>}
          {stage === 2 && <>
            <h2>O que dá para estimar?</h2><p>Não sabe os valores? Deixe sem estimativa e salve como ideia. Ninguém precisa inventar uma conta para participar.</p>
            <div className={styles.columns}>{(["implementation_start", "implementation_end"] as const).map((key) => <label key={key}>{key === "implementation_start" ? "Ano de início" : "Ano final"}<input type="number" min={1900} max={2200} value={input.content[key] ?? ""} onChange={(e) => content({ [key]: e.target.value ? Number(e.target.value) : null })} /></label>)}</div>
            <label>Estimativa fiscal<select value={input.content.financial_impact_status} onChange={(e) => content({ financial_impact_status: e.target.value })}><option value="NOT_ESTIMATED">Ainda não sei estimar</option><option value="ESTIMATED">Tenho uma estimativa</option><option value="NOT_APPLICABLE">Não se aplica (vou justificar)</option></select></label>
            <label>Premissas e justificativa {input.assisted_fields.includes("impact_justification") && <small>Assistido por IA</small>}<textarea value={input.content.impact_justification ?? ""} onChange={(e) => content({ impact_justification: e.target.value })} /></label>
            {input.content.financial_impact_status === "ESTIMATED" && <>
              {input.content.impacts.map((row, index) => <div className={styles.row} key={index}><h3>Impacto anual {index + 1}</h3><div className={styles.columns}><label>Ano<input type="number" min={1900} max={2200} value={row.year} onChange={(e) => changeImpact(index, { year: Number(e.target.value) })} /></label><label>Valor anual em R$<input inputMode="decimal" value={row.amount} placeholder="1000,00" onChange={(e) => changeImpact(index, { amount: e.target.value })} /></label></div><label>Tipo<select value={row.impact_type} onChange={(e) => changeImpact(index, { impact_type: e.target.value })}>{Object.entries(impacts).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><label>Como foi calculado<textarea value={row.description} onChange={(e) => changeImpact(index, { description: e.target.value })} /></label><details><summary>Recorte da estimativa (governo, preços e período)</summary><div className={styles.fields}>{([
                ["fiscal_scope", "De qual governo?", fiscalScopes], ["accounting_basis", "Critério contábil", accountingBases], ["price_basis", "Preços usados", priceBases], ["component", "Componente", fiscalComponents], ["period_basis", "Período coberto", periodBases],
              ] as const).map(([key, label, options]) => <label key={key}>{label}<select value={row[key] ?? "UNSPECIFIED"} onChange={(e) => changeImpact(index, { [key]: e.target.value, ...(key === "price_basis" && e.target.value !== "CONSTANT" ? { price_base_year: null } : {}) })}>{Object.entries(options).map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>)}{row.price_basis === "CONSTANT" && <label>Ano-base dos preços<input type="number" min={1900} max={2200} value={row.price_base_year ?? ""} onChange={(e) => changeImpact(index, { price_base_year: e.target.value ? Number(e.target.value) : null })} /></label>}</div></details><button onClick={() => content({ impacts: input.content.impacts.filter((_, i) => i !== index) })}>Remover impacto {index + 1}</button></div>)}
              <button onClick={() => content({ impacts: [...input.content.impacts, { year: input.content.implementation_start ?? new Date().getFullYear(), amount: "", description: "", impact_type: "NEW_EXPENSE", ...unspecifiedFiscalMetadata }] })}>Adicionar impacto anual</button>
            </>}
            <h3>De onde sai o dinheiro?</h3>{input.content.fundings.map((row, index) => <div className={styles.row} key={index}><label>Origem<select value={row.funding_type} onChange={(e) => content({ fundings: input.content.fundings.map((item, i) => i === index ? { ...item, funding_type: e.target.value } : item) })}>{Object.entries(fundings).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><label>Explique a fonte de financiamento<textarea value={row.description} onChange={(e) => content({ fundings: input.content.fundings.map((item, i) => i === index ? { ...item, description: e.target.value } : item) })} /></label><div className={styles.columns}><label>Valor (opcional)<input inputMode="decimal" value={row.amount ?? ""} onChange={(e) => content({ fundings: input.content.fundings.map((item, i) => i === index ? { ...item, amount: e.target.value || null } : item) })} /></label><label>Ano (opcional)<input type="number" min={1900} max={2200} value={row.year ?? ""} onChange={(e) => content({ fundings: input.content.fundings.map((item, i) => i === index ? { ...item, year: e.target.value ? Number(e.target.value) : null } : item) })} /></label></div><button onClick={() => content({ fundings: input.content.fundings.filter((_, i) => i !== index) })}>Remover financiamento {index + 1}</button></div>)}<button onClick={() => content({ fundings: [...input.content.fundings, { funding_type: "UNFUNDED", description: "", amount: null, year: null }] })}>Adicionar origem ou pendência</button>
          </>}
          {stage === 3 && <><h2>Deixe um caminho para conferir.</h2><p>Você escolhe as referências. Uma fonte não prova automaticamente uma afirmação.</p><label>Buscar no catálogo<input value={sourceSearch} onChange={(e) => setSourceSearch(e.target.value)} /></label>{sourceError && <p role="alert">{sourceError} <button onClick={() => setSourceRetry((n) => n + 1)}>Tentar carregar fontes</button></p>}
            {sources.filter((source) => `${source.title} ${source.institution}`.toLowerCase().includes(sourceSearch.toLowerCase())).map((source) => { const evidence = input.content.sources.find((item) => item.source_id === source.id); return <div className={styles.row} key={source.id}><strong>{source.title}</strong><p>{source.institution} · acesso em {source.accessed_at.slice(0, 10)}</p>{evidence ? <><label>Como esta fonte sustenta sua proposta?<textarea value={evidence.usage_description} onChange={(e) => content({ sources: input.content.sources.map((item) => item.source_id === source.id ? { ...item, usage_description: e.target.value } : item) })} /></label><button onClick={() => content({ sources: input.content.sources.filter((item) => item.source_id !== source.id) })}>Desvincular fonte</button></> : <button onClick={() => content({ sources: [...input.content.sources, { source_id: source.id, usage_description: "" }] })}>Usar esta fonte</button>}</div>; })}
            <details><summary>Cadastrar outra referência por link</summary><SourceForm onCreated={(source) => { setSources((items) => [source, ...items]); content({ sources: [...input.content.sources, { source_id: source.id, usage_description: "" }] }); }} /></details>
            {suggestions.filter((item) => item.status === "PENDING").length > 0 && <section><h3>Fontes sugeridas por outras pessoas</h3>{suggestions.filter((item) => item.status === "PENDING").map((item) => <div className={styles.row} key={item.id}><p className={styles.text}>{item.url}</p><p>{item.note}</p><p className={styles.muted}>Aceitar registra sua decisão. Cadastre e vincule a fonte acima para incluí-la na proposta.</p><div className={styles.actions}>{(["ACCEPT", "DISMISS"] as const).map((decision) => <button key={decision} disabled={busy} onClick={() => void action(async () => { await request(`ideas/${record!.id}/suggestions/${item.id}/resolve`, { method: "POST", body: JSON.stringify({ action: decision }) }); setSuggestions((rows) => rows.filter((row) => row.id !== item.id)); setMessage(decision === "ACCEPT" ? "Sugestão aceita. Cadastre e vincule a referência para incluí-la na proposta." : "Sugestão dispensada."); })}>{decision === "ACCEPT" ? "Aceitar sugestão" : "Dispensar"}</button>)}</div></div>)}</section>}
          </>}
          {stage === 4 && <IdeaAnalysis input={input} record={record} dirty={dirty} busy={busy} onSave={() => action(async () => { await save(); })} onPromote={() => action(async () => { const saved = dirty || !record ? await save() : record; const response = await request<Policy>(`ideas/${saved.id}/promote`, { method: "POST" }); setDirty(false); router.push(`/propostas/${response.data.slug}`); })} />}
        </div>
        <div className={styles.actions}>{stage > 0 && <button onClick={() => setStage(stage - 1)}>Etapa anterior</button>}{stage < 4 && <button className="button" onClick={() => setStage(stage + 1)}>Próxima etapa</button>}</div>
      </>}
    </div><ProgressSidebar saving={busy} status={dirty ? "Alterações não salvas" : record ? "Salvo no servidor" : "Ainda não foi salvo"} complete={complete} total={record?.checklist.length ?? 0} preview={input} previewCategory={categories[input.content.category] ?? "Outros"}>
      <div className={styles.sidebarActions}><Button disabled={busy || !canSave(input)} onClick={() => void action(async () => { await save(); })}>{busy ? "Aguarde…" : "Salvar ideia privada"}</Button><Button variant="secondary" disabled={busy || !canSave(input)} onClick={() => void action(share)}>Compartilhar como ideia</Button></div>
      <details className={styles.checklistDetails}><summary>Para virar completa</summary>{record ? <ul className={styles.checklist}>{record.checklist.map(item => <li key={item.key}><span aria-hidden="true">{item.complete ? "✓" : "○"}</span><span>{item.label}<small className="sr-only">{item.complete ? "Concluído" : "Pendente"}</small></span></li>)}</ul> : <p>Salve para consultar o checklist. Dados ausentes continuam em aberto.</p>}{dirty && <small>Salve para atualizar o checklist.</small>}</details>
      <div className={styles.actions}>{record?.status === "SHARED" && <Button variant="tertiary" disabled={busy} onClick={() => void action(async () => { const response = await request<Idea>(`ideas/${record.id}/unshare`, { method: "POST" }); setRecord(response.data); setMessage("Ideia retirada do compartilhamento."); })}>Tornar privada</Button>}<Button variant="tertiary" onClick={() => { setMode("manual"); setStage(4); }}>Ver análise e lacunas</Button></div><small className={styles.support}>Compartilhar torna uma cópia pública. Ideias continuam fora dos planos, cálculos e ranking.</small>
    </ProgressSidebar></div>}

  </fieldset></div>;
}

function IdeaAnalysis({ input, record, dirty, busy, onSave, onPromote }: { input: IdeaInput; record: Idea | null; dirty: boolean; busy: boolean; onSave: () => Promise<void>; onPromote: () => Promise<void> }) {
  const missing = record?.checklist.filter((item) => !item.complete) ?? [];
  return <section className={styles.analysis}><h2>O que sabemos. E o que falta.</h2><span className={styles.badge}>Ideia em construção · fora do cálculo</span><h3>{input.title || "Sua ideia"}</h3><p className={styles.text}>{input.summary || "Conte sua ideia em uma frase para começar."}</p><p>Sem cálculos inventados pela IA: esta análise mostra o que você declarou. Para entrar no motor fiscal e em planos, a proposta precisa estar completa e ser publicada por você.</p>{input.assisted_fields.length > 0 && <p className={styles.notice}>Conteúdo assistido por IA: {input.assisted_fields.join(", ")}. Você confirmou esses textos.</p>}<div className={styles.columns}><div className={styles.row}><h3>Quem ganha</h3><p className={styles.text}>{input.beneficiaries || "Ainda não informado."}</p></div><div className={styles.row}><h3>Quem pode perder</h3><p className={styles.text}>{input.adversely_affected || "Ainda não informado."}</p></div></div><div><h3>O que pode dar errado</h3><p className={styles.text}>{input.risks || "Riscos ainda não descritos."}</p></div><div className={styles.notice}><strong>Faixa de impacto e confiança</strong><p>{input.content.financial_impact_status === "NOT_ESTIMATED" ? "Sem estimativa. Isso não significa custo zero." : "Você informou uma estimativa ou justificativa. Ela ainda precisa passar pela validação do motor; presença de números não determina confiança."} Não há faixa nem grau de certeza atribuído automaticamente.</p></div><h3>O que falta para publicar como completa</h3>{!record || dirty ? <><p>Salve para validar o checklist atual no servidor.</p><button disabled={busy || !canSave(input)} onClick={() => void onSave()}>Salvar e conferir</button></> : missing.length ? <ul>{missing.map((item) => <li key={item.key}>{item.label}</li>)}</ul> : <p>Checklist preenchido. Confira todas as premissas e fontes antes de publicar.</p>}<button className="button" disabled={busy || dirty || !record || missing.length > 0} onClick={() => void onPromote()}>Publicar como proposta completa</button><p className={styles.muted}>Essa ação publica uma versão preservada. O cálculo continua incremental, depende das premissas e não é uma previsão do país.</p></section>;
}
