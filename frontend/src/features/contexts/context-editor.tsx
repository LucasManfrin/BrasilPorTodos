"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/provider";
import { ApiError } from "@/lib/api";
import type { Source } from "@/lib/types";
import type { Indicator } from "@/lib/indicator-types";
import { indicatorValue } from "@/lib/indicator-types";
import { date } from "@/lib/format";
import { blankContent, recordToContent, missingLabel, statusLabel } from "./helpers";
import type { ContextContentInput, ContextRecord, ContextObservation, ContextSource, ContextReviewInput, ContextEvidence, ContextHypothesis, ContextConsequence } from "./types";
import { ContextView } from "./context-view";
import { blankReview, internalDestination } from "./context-editor-state";
import styles from "./editor.module.css";
import { PageHero, Skeleton } from "@/components/page-kit";
import { Button } from "@/components/ui";
type Reference = {
    code: string;
    name: string;
    unit: string;
    scope: string;
    frequency: string;
    methodology: string;
    observations: (ContextObservation & {
        source: ContextSource;
    })[];
};
const toggle = (values: string[], value: string) => values.includes(value) ? values.filter(v => v !== value) : [...values, value];
const lines = (value: string) => value.split("\n");
const clearLines = (values: string[]) => values.map(v => v.trim()).filter(Boolean);
const observationLabel = (o: ContextObservation) => `${date(o.period_start)} a ${date(o.period_end)} · ${indicatorValue(o.value)} ${o.unit} · revisão ${o.revision}`;
const reviewChecks = [["references_checked", "Conferi as fontes e os trechos citados"], ["scopes_checked", "Conferi períodos, abrangências e métodos"], ["alternatives_checked", "Conferi as explicações alternativas e contrapartidas"], ["limitations_checked", "Conferi as limitações e o que ainda não se sabe"]] as const;
function TextField({ label, value, onChange, max = 2000, multiline = true }: {
    label: string;
    value: string;
    onChange: (value: string) => void;
    max?: number;
    multiline?: boolean;
}) {
    return <label>{label}{multiline ? <textarea value={value} maxLength={max} rows={3} onChange={e => onChange(e.target.value)}/> : <input value={value} maxLength={max} onChange={e => onChange(e.target.value)}/>}</label>;
}
function EvidenceChoices({ evidence, selected, onToggle }: {
    evidence: ContextEvidence[];
    selected: string[];
    onToggle: (id: string) => void;
}) {
    return <div className={styles.choices}>{evidence.length === 0 ? <p>Adicione uma evidência na etapa Fontes primeiro.</p> : evidence.map((e, i) => <label key={e.id}><input type="checkbox" checked={selected.includes(e.id)} onChange={() => onToggle(e.id)}/>{e.claim || `Evidência ${i + 1}`}</label>)}</div>;
}
export function ContextEditor({ id, initialIndicatorCode }: {
    id?: string;
    initialIndicatorCode?: string;
}) {
    const { user, request } = useAuth();
    const router = useRouter();
    const [record, setRecord] = useState<ContextRecord | null>(null);
    const [content, setContent] = useState<ContextContentInput>(blankContent);
    const [saved, setSaved] = useState(JSON.stringify(blankContent()));
    const [loading, setLoading] = useState(!!id);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [conflict, setConflict] = useState(false);
    const [discard, setDiscard] = useState(false);
    const [indicators, setIndicators] = useState<Indicator[]>([]);
    const [sources, setSources] = useState<Source[]>([]);
    const [sourcePage, setSourcePage] = useState(1);
    const [moreSources, setMoreSources] = useState(false);
    const [sourceBusy, setSourceBusy] = useState(true);
    const [sourceError, setSourceError] = useState("");
    const [catalogError, setCatalogError] = useState("");
    const [references, setReferences] = useState<Record<string, Reference>>({});
    const [refCode, setRefCode] = useState(initialIndicatorCode || "");
    const [refPage, setRefPage] = useState(1);
    const [refTotal, setRefTotal] = useState(0);
    const [refBusy, setRefBusy] = useState(false);
    const [refError, setRefError] = useState("");
    const [refRetry, setRefRetry] = useState(0);
    const [review, setReview] = useState(blankReview);
    const leaveDialog = useRef<HTMLDialogElement>(null);
    const leaveHref = useRef("");
    const leaveApproved = useRef(false);
    const dirty = JSON.stringify(content) !== saved;
    const own = !record || record.content.author_id === user?.id;
    const reviewer = !!record && !own && user?.role === "ADMIN";
    const anchors = useMemo(() => {
        const rows = new Map<string, ContextObservation>();
        record?.content.observations.forEach(o => rows.set(o.observation_id, o));
        Object.values(references).forEach(r => r.observations.forEach(o => rows.set(o.observation_id, o)));
        return rows;
    }, [record, references]);
    const sourceChoices = useMemo(() => {
        const rows = new Map<string, {
            id: string;
            title: string;
            institution: string;
        }>();
        record?.content.sources.forEach(s => rows.set(s.id, s));
        sources.forEach(s => rows.set(s.id, s));
        Object.values(references).forEach(r => r.observations.forEach(o => rows.set(o.source.id, o.source)));
        return [...rows.values()];
    }, [record, sources, references]);
    const apply = useCallback((r: ContextRecord) => {
        const next = recordToContent(r);
        setRecord(r);
        setContent(next);
        setSaved(JSON.stringify(next));
        setConflict(false);
        setDiscard(false);
        setReview(blankReview());
    }, []);
    const load = useCallback(async () => {
        const target = id ?? record?.id;
        if (!target)
            return;
        setLoading(true);
        setError("");
        try {
            apply((await request<ContextRecord>(`contexts/${target}/draft`)).data);
        }
        catch (e) {
            setError((e as Error).message);
        }
        finally {
            setLoading(false);
        }
    }, [id, record?.id, request, apply]);
    useEffect(() => {
        if (!id)
            return;
        let active = true;
        request<ContextRecord>(`contexts/${id}/draft`).then(r => { if (active)
            apply(r.data); }).catch(e => { if (active)
            setError((e as Error).message); }).finally(() => { if (active)
            setLoading(false); });
        return () => { active = false; };
    }, [id, request, apply]);
    const loadCatalog = useCallback(async () => {
        setCatalogError("");
        try {
            setIndicators((await request<Indicator[]>("indicators?page_size=100")).data);
        }
        catch (e) {
            setCatalogError((e as Error).message);
        }
    }, [request]);
    useEffect(() => { let active = true; request<Indicator[]>("indicators?page_size=100").then(r => { if (active)
        setIndicators(r.data); }).catch(e => { if (active)
        setCatalogError((e as Error).message); }); return () => { active = false; }; }, [request]);
    const loadSources = useCallback(async (page: number) => {
        setSourceBusy(true);
        setSourceError("");
        try {
            const results = await Promise.all([request<Source[]>(`sources?page=${page}&page_size=50`), request<Source[]>(`sources/mine?page=${page}&page_size=50`)]);
            setSources(prev => [...new Map([...prev, ...results.flatMap(r => r.data)].map(s => [s.id, s])).values()]);
            setSourcePage(page);
            setMoreSources(results.some(r => page * 50 < (r.pagination?.total ?? 0)));
        }
        catch (e) {
            setSourceError((e as Error).message);
        }
        finally {
            setSourceBusy(false);
        }
    }, [request]);
    useEffect(() => { let active = true; Promise.all([request<Source[]>("sources?page=1&page_size=50"), request<Source[]>("sources/mine?page=1&page_size=50")]).then(results => { if (active) {
        setSources([...new Map(results.flatMap(r => r.data).map(s => [s.id, s])).values()]);
        setMoreSources(results.some(r => 50 < (r.pagination?.total ?? 0)));
    } }).catch(e => { if (active)
        setSourceError((e as Error).message); }).finally(() => { if (active)
        setSourceBusy(false); }); return () => { active = false; }; }, [request]);
    useEffect(() => {
        if (!dirty)
            return;
        const warn = (e: BeforeUnloadEvent) => { if (!leaveApproved.current) e.preventDefault(); };
        window.addEventListener("beforeunload", warn);
        return () => window.removeEventListener("beforeunload", warn);
    }, [dirty]);
    useEffect(() => {
        if (!dirty) return;
        const intercept = (event: MouseEvent) => {
            if (leaveApproved.current || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            const element = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>("a[href]") : null;
            if (!element || element.hasAttribute("download")) return;
            const destination = internalDestination(element.href, window.location.href, element.target);
            if (!destination) return;
            event.preventDefault();
            event.stopPropagation();
            leaveHref.current = destination;
            if (!leaveDialog.current?.open) leaveDialog.current?.showModal();
        };
        document.addEventListener("click", intercept, true);
        return () => document.removeEventListener("click", intercept, true);
    }, [dirty]);
    useEffect(() => {
        if (!refCode)
            return;
        let active = true;
        request<Reference>(`contexts/references/${encodeURIComponent(refCode)}?page=${refPage}&page_size=50`).then(r => {
            if (!active)
                return;
            setReferences(prev => ({ ...prev, [refCode]: { ...r.data, observations: [...new Map([...(prev[refCode]?.observations ?? []), ...r.data.observations].map(o => [o.observation_id, o])).values()] } }));
            setRefTotal(r.pagination?.total ?? r.data.observations.length);
            setRefError("");
            setRefBusy(false);
        }).catch(e => { if (active) {
            setRefError((e as Error).message);
            setRefBusy(false);
        } });
        return () => { active = false; };
    }, [refCode, refPage, refRetry, request]);
    function patch(values: Partial<ContextContentInput>) { leaveApproved.current=false; setContent(prev => ({ ...prev, ...values })); setMessage(""); }
    function handleFailure(e: unknown) {
        setError((e as Error).message);
        if (e instanceof ApiError && e.status === 409)
            setConflict(true);
    }
    async function save(e: React.FormEvent) {
        e.preventDefault();
        setBusy(true);
        setError("");
        setMessage("");
        const observations = content.observation_ids.map(key => anchors.get(key)).filter((o): o is ContextObservation => !!o);
        const next = { ...content, limitations: clearLines(content.limitations), unknowns: clearLines(content.unknowns), consequences: content.consequences.map(c => ({ ...c, premises: clearLines(c.premises) })), source_ids: [...new Set([...observations.map(o => o.source_id), ...content.evidence.map(e => e.source_id).filter(Boolean)])] };
        try {
            const result = await request<ContextRecord>(record ? `contexts/${record.id}` : "contexts", { method: record ? "PATCH" : "POST", body: JSON.stringify(record ? { content: next, expected_revision: record.revision } : { content: next }) });
            apply(result.data);
            setMessage("Rascunho salvo. A avaliação abaixo usa esta revisão; nenhuma publicação foi feita.");
            if (!record) router.replace(`/painel/contextos/${result.data.id}`);
        }
        catch (e) {
            handleFailure(e);
        }
        finally {
            setBusy(false);
        }
    }
    async function submitReview(decision: ContextReviewInput["decision"]) {
        if (!record)
            return;
        setBusy(true);
        setError("");
        setMessage("");
        try {
            apply((await request<ContextRecord>(`contexts/${record.id}/review`, { method: "POST", body: JSON.stringify({ ...review, decision, expected_revision: record.revision }) })).data);
            setMessage("Revisão registrada. Aceitação é conferência do conteúdo, não prova de causalidade.");
        }
        catch (e) {
            handleFailure(e);
        }
        finally {
            setBusy(false);
        }
    }
    async function publish() {
        if (!record)
            return;
        setBusy(true);
        setError("");
        setMessage("");
        try {
            apply((await request<ContextRecord>(`contexts/${record.id}/publish`, { method: "POST", body: JSON.stringify({ expected_revision: record.revision }) })).data);
            setMessage("Esta revisão foi publicada. Seu conteúdo e revisão ficam preservados.");
        }
        catch (e) {
            handleFailure(e);
        }
        finally {
            setBusy(false);
        }
    }
    function updateEvidence(index: number, values: Partial<ContextEvidence>) { patch({ evidence: content.evidence.map((row, i) => i === index ? { ...row, ...values } : row) }); }
    function updateHypothesis(index: number, values: Partial<ContextHypothesis>) { patch({ hypotheses: content.hypotheses.map((row, i) => i === index ? { ...row, ...values } : row) }); }
    function updateConsequence(index: number, values: Partial<ContextConsequence>) { patch({ consequences: content.consequences.map((row, i) => i === index ? { ...row, ...values } : row) }); }
    function removeEvidence(key: string) {
        patch({ evidence: content.evidence.filter(e => e.id !== key), hypotheses: content.hypotheses.map(h => ({ ...h, evidence: h.evidence.filter(e => e.evidence_id !== key) })), consequences: content.consequences.map(c => ({ ...c, evidence_ids: c.evidence_ids.filter(id => id !== key) })) });
    }
    if (loading)
        return <Skeleton />;
    if (id && !record)
        return <div className={styles.notice}><p role="alert">{error || "Não foi possível abrir este contexto."}</p><button onClick={() => void load()}>Tentar de novo</button></div>;
    return <div className={styles.workspace}>
    <dialog ref={leaveDialog} className={styles.leaveDialog} aria-labelledby="leave-context-title">
      <h2 id="leave-context-title">Sair sem salvar?</h2><p>Suas alterações neste contexto serão perdidas. Fique no editor para salvar o rascunho primeiro.</p>
      <div className={styles.actions}><button type="button" className="button secondary" onClick={()=>leaveDialog.current?.close()}>Continuar editando</button><button type="button" className="button" onClick={()=>{leaveApproved.current=true;setContent(record?recordToContent(record):blankContent());leaveDialog.current?.close();router.push(leaveHref.current);}}>Descartar alterações e sair</button></div>
    </dialog>
    <PageHero title={reviewer ? "Revisar contexto" : record ? "Editar contexto" : "Novo contexto"} tone="blue"
      description="O dado é o começo. Reúna evidências, explicações possíveis e o que ainda falta saber."
      action={<Button href="/painel/contextos" variant="secondary">Meus contextos</Button>} />
    <div className={styles.editorMeta}><span className={styles.badge}>{record ? `Revisão ${record.revision} · ${statusLabel(record.assessment.status)}` : "Novo rascunho privado"}</span><span role="status">{dirty ? "Alterações ainda não salvas" : "Nenhuma alteração pendente"}</span>{record && <span>{record.published_at ? "Publicada" : "Privada"}</span>}</div>
    {record && !id && !dirty && <p><Link href={`/painel/contextos/${record.id}`}>Continuar neste rascunho salvo →</Link></p>}
    {error && <p className={styles.notice} role="alert">{error}</p>}
    {message && <p className={styles.notice} role="status">{message}</p>}
    {conflict && <div className={styles.notice} role="alert"><h2>O conteúdo mudou no servidor</h2><p>Seu texto continua aqui. Reabrir substitui os campos pela versão do servidor; copie o que quiser conservar antes.</p><label className={styles.check}><input type="checkbox" checked={discard} onChange={e => setDiscard(e.target.checked)}/>Entendi que minhas alterações não salvas serão descartadas</label><button type="button" disabled={!discard || busy} onClick={() => void load()}>Descartar alterações e reabrir</button></div>}
    {!own && record && <><h2>{record.content.title || "Contexto sem título"}</h2><ContextView record={record} showHistory={false}/></>}
    {own && <nav className={styles.stepNav} aria-label="Etapas do contexto">{["Dados", "Fontes", "Explicações", "Limites"].map((label, index) => <button key={label} type="button" onClick={() => { const section = document.getElementById(`context-step-${index}`) as HTMLDetailsElement | null; if (section) { section.open = true; section.scrollIntoView({ block: "start" }); section.querySelector("summary")?.focus(); } }}><span>{index + 1}</span>{label}</button>)}</nav>}
    {own && <form onSubmit={save} className={styles.form}>
      <fieldset disabled={busy} className={styles.body}><legend>Construir o contexto</legend>
      <TextField label="Título" value={content.title} max={180} multiline={false} onChange={title => patch({ title })}/>
      <TextField label="O que os dados mostram?" value={content.observation_summary} max={4000} onChange={observation_summary => patch({ observation_summary })}/>
      <p>Você pode salvar um rascunho sem completar tudo. Ao adicionar uma evidência, hipótese ou contrapartida, preencha seus campos ou remova esse bloco antes de salvar.</p>
      <details open id="context-step-0" className={styles.step}><summary>1. Dados e contrapartidas</summary><div className={styles.stack}>
        <p>Selecione observações já coletadas. Valores, revisões e períodos são fixados pelo servidor e não podem ser digitados aqui.</p>
        {catalogError && <p role="alert">{catalogError} <button type="button" onClick={() => void loadCatalog()}>Tentar catálogo novamente</button></p>}
        <label>Indicador<select value={refCode} onChange={e => { setRefCode(e.target.value); setRefPage(1); setRefBusy(Boolean(e.target.value)); setRefError(""); }}><option value="">Escolha um indicador</option>{indicators.map(i => <option key={i.code} value={i.code}>{i.name}</option>)}</select></label>
        {refBusy && <p role="status">Consultando períodos disponíveis…</p>}
        {refError && <p role="alert">{refError} <button type="button" onClick={() => { setRefRetry(p => p + 1); setRefBusy(true); }}>Tentar novamente</button></p>}
        {references[refCode] && <><p className={styles.meta}>{references[refCode].scope} · {references[refCode].frequency}</p><details><summary>Como esta série é medida</summary><p>{references[refCode].methodology}</p></details><div className={styles.observations}>{references[refCode].observations.length === 0 && <p>Nenhuma observação coletada para este indicador.</p>}{references[refCode].observations.map(o => <label key={o.observation_id}><input type="checkbox" checked={content.observation_ids.includes(o.observation_id)} onChange={() => { const selected = toggle(content.observation_ids, o.observation_id); patch({ observation_ids: selected, primary_observation_id: selected.includes(content.primary_observation_id ?? "") ? content.primary_observation_id : null, counterparts: content.counterparts.map(c => ({ ...c, observation_ids: c.observation_ids.filter(key => selected.includes(key)), availability: c.observation_ids.some(key => selected.includes(key)) ? "REFERENCED" : "NOT_COLLECTED" })), consequences: content.consequences.map(c => ({ ...c, observation_ids: c.observation_ids.filter(key => selected.includes(key)) })) }); }}/><span>{observationLabel(o)}<small>{o.source.title}</small></span></label>)}</div>{references[refCode].observations.length < refTotal && <button type="button" disabled={refBusy} onClick={() => { setRefPage(p => p + 1); setRefBusy(true); }}>Mais períodos</button>}</>}
        <label>Observação principal<select value={content.primary_observation_id ?? ""} onChange={e => patch({ primary_observation_id: e.target.value || null })}><option value="">Ainda não definida</option>{content.observation_ids.map(key => { const o = anchors.get(key); return o ? <option key={key} value={key}>{indicators.find(i => i.code === o.indicator_code)?.name ?? o.indicator_code} · {observationLabel(o)}</option> : null; })}</select></label>
        <details><summary>Observações selecionadas · {content.observation_ids.length}</summary><ul>{content.observation_ids.map(key => { const o = anchors.get(key); return o ? <li key={key}>{indicators.find(i => i.code === o.indicator_code)?.name ?? o.indicator_code} · {observationLabel(o)}</li> : null; })}</ul></details><h3>O que precisa ser lido junto?</h3><p>Uma contrapartida ajuda a evitar conclusões a partir de um número isolado.</p>
        {content.counterparts.map((c, index) => <fieldset key={c.indicator_code} className={styles.entry}><legend>Contrapartida {index + 1}</legend><p>{indicators.find(i => i.code === c.indicator_code)?.name ?? c.indicator_code}</p><TextField label="Por que ler esses dados juntos?" value={c.why_read_together} onChange={why_read_together => patch({ counterparts: content.counterparts.map((row, i) => i === index ? { ...row, why_read_together } : row) })}/><p>{c.availability === "NOT_COLLECTED" ? "Sem observação vinculada. Isso não significa zero." : "Observações vinculadas:"}</p><div className={styles.choices}>{content.observation_ids.map(key => anchors.get(key)).filter((o): o is ContextObservation => !!o && o.indicator_code === c.indicator_code).map(o => <label key={o.observation_id}><input type="checkbox" checked={c.observation_ids.includes(o.observation_id)} onChange={() => { const ids = toggle(c.observation_ids, o.observation_id); patch({ counterparts: content.counterparts.map((row, i) => i === index ? { ...row, observation_ids: ids, availability: ids.length ? "REFERENCED" : "NOT_COLLECTED" } : row) }); }}/>{observationLabel(o)}</label>)}</div><button type="button" onClick={() => patch({ counterparts: content.counterparts.filter((_, i) => i !== index) })}>Remover contrapartida {index + 1}</button></fieldset>)}
        <label>Adicionar contrapartida<select value="" onChange={e => { if (e.target.value)
            patch({ counterparts: [...content.counterparts, { indicator_code: e.target.value, why_read_together: "", availability: "NOT_COLLECTED", observation_ids: [] }] }); }}><option value="">Escolha outro indicador</option>{indicators.filter(i => !content.counterparts.some(c => c.indicator_code === i.code)).map(i => <option key={i.code} value={i.code}>{i.name}</option>)}</select></label>
      </div></details>
      <details id="context-step-1" className={styles.step}><summary>2. Fontes e evidências</summary><div className={styles.stack}><p>Uma fonte precisa apoiar uma afirmação específica, com localização do trecho e limites. São salvas as fontes das observações e das evidências selecionadas; removê-las não altera publicações anteriores.</p><p><Link href="/painel/fontes" target="_blank" rel="noopener">Cadastrar uma fonte em outra aba ↗</Link> · <button type="button" disabled={sourceBusy} onClick={() => void loadSources(1)}>Atualizar fontes</button></p>{sourceError && <p role="alert">{sourceError}</p>}{sourceBusy && <p role="status">Carregando fontes…</p>}{moreSources && <button type="button" disabled={sourceBusy} onClick={() => void loadSources(sourcePage + 1)}>Carregar mais fontes</button>}
      {content.evidence.map((e, index) => <fieldset className={styles.entry} key={e.id}><legend>Evidência {index + 1}</legend><label>Fonte<select value={e.source_id} onChange={event => updateEvidence(index, { source_id: event.target.value })}><option value="">Selecione uma fonte</option>{sourceChoices.map(s => <option key={s.id} value={s.id}>{s.institution} · {s.title}</option>)}</select></label><label>O que este trecho permite dizer?<select value={e.level} onChange={event => updateEvidence(index, { level: event.target.value as ContextEvidence["level"] })}><option value="DESCRIPTION">Descreve um dado</option><option value="ASSOCIATION">Mostra uma associação</option><option value="HYPOTHESIS_SUPPORT">Oferece suporte a uma hipótese</option></select></label>{([["claim", "Afirmação apoiada"], ["locator", "Página, tabela ou seção"], ["excerpt", "Trecho relevante"], ["scope", "Quem e onde o estudo cobre"], ["period", "Período estudado"], ["limitations", "Limites desta evidência"]] as const).map(([key, label]) => <TextField key={key} label={label} value={e[key]} max={key === "period" ? 200 : 2000} onChange={value => updateEvidence(index, { [key]: value })}/>)}<button type="button" onClick={() => removeEvidence(e.id)}>Remover evidência {index + 1} e seus vínculos</button></fieldset>)}<button type="button" disabled={content.evidence.length >= 64} onClick={() => patch({ evidence: [...content.evidence, { id: crypto.randomUUID(), source_id: "", level: "DESCRIPTION", claim: "", locator: "", excerpt: "", scope: "", period: "", limitations: "" }] })}>Adicionar evidência</button>
      </div></details>
      <details id="context-step-2" className={styles.step}><summary>3. Explicações possíveis</summary><div className={styles.stack}><p>Para ficar completo, o contexto precisa de pelo menos duas explicações diferentes. Uma hipótese não é uma causa comprovada.</p>
      {content.hypotheses.map((h, index) => <fieldset key={h.id} className={styles.entry}><legend>Hipótese {index + 1}</legend><TextField label="Qual é a explicação possível?" value={h.explanation} onChange={explanation => updateHypothesis(index, { explanation })}/><TextField label="O que deixa essa explicação incerta?" value={h.uncertainty} onChange={uncertainty => updateHypothesis(index, { uncertainty })}/><p>Quais evidências se relacionam com esta hipótese?</p><EvidenceChoices evidence={content.evidence} selected={h.evidence.map(e => e.evidence_id)} onToggle={key => updateHypothesis(index, { evidence: h.evidence.some(e => e.evidence_id === key) ? h.evidence.filter(e => e.evidence_id !== key) : [...h.evidence, { evidence_id: key, relation: "CONTEXT", justification: "" }] })}/>{h.evidence.map((link, li) => <div key={link.evidence_id} className={styles.entry}><p>{content.evidence.find(e => e.id === link.evidence_id)?.claim}</p><label>Relação<select value={link.relation} onChange={e => updateHypothesis(index, { evidence: h.evidence.map((row, i) => i === li ? { ...row, relation: e.target.value as typeof link.relation } : row) })}><option value="SUPPORTS">Apoia a hipótese</option><option value="CHALLENGES">Contesta a hipótese</option><option value="CONTEXT">Ajuda a contextualizar</option></select></label><TextField label="Por que este trecho tem essa relação?" value={link.justification} onChange={justification => updateHypothesis(index, { evidence: h.evidence.map((row, i) => i === li ? { ...row, justification } : row) })}/></div>)}<button type="button" onClick={() => patch({ hypotheses: content.hypotheses.filter((_, i) => i !== index) })}>Remover hipótese {index + 1}</button></fieldset>)}<button type="button" disabled={content.hypotheses.length >= 16} onClick={() => patch({ hypotheses: [...content.hypotheses, { id: `hipotese-${crypto.randomUUID().slice(0, 8)}`, explanation: "", evidence: [], uncertainty: "" }] })}>Adicionar hipótese</button>
      </div></details>
      <details id="context-step-3" className={styles.step}><summary>4. Consequências e lacunas</summary><div className={styles.stack}><p>Separe o que foi observado do que depende de premissas. Nenhum texto desta etapa alimenta o cálculo fiscal.</p>
      {content.consequences.map((c, index) => <fieldset key={c.id} className={styles.entry}><legend>Consequência {index + 1}</legend><label>Tipo<select value={c.kind} onChange={e => updateConsequence(index, { kind: e.target.value as ContextConsequence["kind"] })}><option value="OBSERVED">Observada, com referência</option><option value="PROJECTED">Projetada, depende de premissas</option></select></label><TextField label="Qual é a consequência?" value={c.description} onChange={description => updateConsequence(index, { description })}/><TextField label="Limites desta consequência" value={c.limitations} onChange={limitations => updateConsequence(index, { limitations })}/><TextField label="Premissas (uma por linha; só para projeções)" value={c.premises.join("\n")} onChange={value => updateConsequence(index, { premises: lines(value) })}/><p>Evidências relacionadas</p><EvidenceChoices evidence={content.evidence} selected={c.evidence_ids} onToggle={key => updateConsequence(index, { evidence_ids: toggle(c.evidence_ids, key) })}/><p>Observações relacionadas</p><div className={styles.choices}>{content.observation_ids.map(key => anchors.get(key)).filter((o): o is ContextObservation => !!o).map(o => <label key={o.observation_id}><input type="checkbox" checked={c.observation_ids.includes(o.observation_id)} onChange={() => updateConsequence(index, { observation_ids: toggle(c.observation_ids, o.observation_id) })}/>{indicators.find(i => i.code === o.indicator_code)?.name ?? o.indicator_code} · {observationLabel(o)}</label>)}</div><button type="button" onClick={() => patch({ consequences: content.consequences.filter((_, i) => i !== index) })}>Remover consequência {index + 1}</button></fieldset>)}<button type="button" disabled={content.consequences.length >= 32} onClick={() => patch({ consequences: [...content.consequences, { id: `consequencia-${crypto.randomUUID().slice(0, 8)}`, kind: "OBSERVED", description: "", evidence_ids: [], observation_ids: [], premises: [], limitations: "" }] })}>Adicionar consequência</button>
      <TextField label="Limitações do contexto (uma por linha)" value={content.limitations.join("\n")} onChange={value => patch({ limitations: lines(value) })}/><TextField label="O que ainda não se sabe? (um ponto por linha)" value={content.unknowns.join("\n")} onChange={value => patch({ unknowns: lines(value) })}/>
      </div></details>
      </fieldset><div className={styles.saveBar}><button className="button" disabled={busy || conflict || (!dirty && !!record)}>{busy ? "Salvando…" : "Salvar rascunho"}</button><span>{dirty ? "Alterações ainda não salvas" : "Nenhuma alteração pendente"}</span></div><p>Salvar uma alteração cria uma nova revisão e exige outra conferência antes de publicar. A versão já publicada permanece intacta.</p>
    </form>}
    {record && <section className={styles.notice} aria-label="Conferência da revisão salva"><h2>Conferir a revisão {record.revision}</h2>{dirty && <p>Você está editando. Este checklist descreve o conteúdo salvo, não as alterações acima.</p>}<p>{statusLabel(record.assessment.status)}</p>{record.assessment.missing.length > 0 ? <ul>{record.assessment.missing.map((code, i) => <li key={`${code}-${i}`}>{missingLabel(code)}</li>)}</ul> : <p>As exigências estruturais desta revisão foram conferidas. Isso não comprova causalidade.</p>}{record.review && <p>Última decisão: {record.review.decision === "ACCEPT" ? "aceitar revisão" : "solicitar ajustes"}. {record.review.rationale}</p>}
      {own && <><p>A publicação depende de aceitação por outro administrador ativo. O servidor reconfere os vínculos e permissões no momento de publicar.</p><button className="button" type="button" disabled={busy || dirty || conflict || !!record.published_at || record.assessment.status !== "REVIEW_MATCHES" || record.review?.decision !== "ACCEPT"} onClick={() => void publish()}>{record.published_at ? "Revisão já publicada" : "Publicar esta revisão"}</button>{record.published_at && <p><Link href={`/contextos/${record.id}/versoes/${record.revision}`}>Abrir esta publicação</Link></p>}<details><summary>Ver a revisão salva inteira</summary><ContextView record={record} showHistory={false}/></details></>}
      {reviewer && !record.published_at && <fieldset disabled={busy || conflict} className={styles.body}><legend>Revisão humana</legend><p>Confira as fontes e os recortes antes de registrar a decisão. Aceitar não publica o texto nem prova suas hipóteses.</p>{reviewChecks.map(([key, label]) => <label key={key} className={styles.check}><input type="checkbox" checked={review[key]} onChange={e => setReview(prev => ({ ...prev, [key]: e.target.checked }))}/>{label}</label>)}<TextField label="Explique sua decisão" value={review.rationale} onChange={rationale => setReview(prev => ({ ...prev, rationale }))}/><div className={styles.actions}><button type="button" className="button" disabled={!review.rationale.trim() || !reviewChecks.every(([key]) => review[key]) || record.assessment.status === "INCOMPLETE"} onClick={() => void submitReview("ACCEPT")}>Aceitar esta revisão</button><button type="button" className="button secondary" disabled={!review.rationale.trim()} onClick={() => void submitReview("REQUEST_CHANGES")}>Solicitar ajustes</button></div></fieldset>}
    </section>}
  </div>;
}
