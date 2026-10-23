"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui";
import { EmptyState, PageHero, Skeleton } from "@/components/page-kit";
import { useAuth } from "@/features/auth/provider";
import styles from "./moderation.module.css";

type Decision = "DISMISS" | "ARCHIVE";
type ReportSnapshot = {
  title?: string;
  summary?: string;
  beneficiaries?: string;
  adversely_affected?: string;
  risks?: string;
  assisted_fields?: string[];
  content?: { problem?: string; proposal?: string };
};
type Report = {
  id: string;
  idea_id: string;
  reason: string;
  created_at: string;
  status: string;
  idea_snapshot?: ReportSnapshot | null;
};

function reportDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Data não informada"
    : new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function ReportReview({ report, onResolve }: {
  report: Report;
  onResolve: (id: string, action: Decision, note: string) => Promise<void>;
}) {
  const formId = useId();
  const [action, setAction] = useState<Decision | "">("");
  const [note, setNote] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const errorRef = useRef<HTMLParagraphElement>(null);
  const snapshot = report.idea_snapshot;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !action || !note.trim() || (action === "ARCHIVE" && !confirmed)) return;
    setBusy(true);
    setError("");
    try { await onResolve(report.id, action, note.trim()); }
    catch (failure) {
      setError(failure instanceof Error ? failure.message : "Não foi possível registrar a decisão.");
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally { setBusy(false); }
  }
  return <article className={styles.report} aria-labelledby={`${formId}-title`}>
    <header className={styles.reportHeading}>
      <div><span className={styles.badge}>Denúncia pendente</span><h2 id={`${formId}-title`}>{snapshot?.title || "Ideia para conferir"}</h2><p className={styles.muted}>Recebida em <time dateTime={report.created_at}>{reportDate(report.created_at)}</time></p></div>
      <Link href={`/ideias/${report.idea_id}`}>Ver página atual da ideia →</Link>
    </header>
    <section aria-labelledby={`${formId}-reason`}><h3 id={`${formId}-reason`}>Motivo informado</h3><p className={styles.text}>{report.reason}</p></section>
    {snapshot ? <details className={styles.snapshot}><summary>Ler o conteúdo compartilhado no momento da denúncia</summary><p className={styles.muted}>Fotografia do conteúdo denunciado. Edições ou retirada posteriores não alteram este registro restrito.</p>{Boolean(snapshot.assisted_fields?.length) && <p>Conteúdo com trechos assistidos por IA.</p>}<dl>{[
      ["Ideia em uma frase", snapshot.summary], ["Problema", snapshot.content?.problem],
      ["Mudança proposta", snapshot.content?.proposal], ["Quem ganha", snapshot.beneficiaries],
      ["Quem pode perder", snapshot.adversely_affected], ["Riscos", snapshot.risks],
    ].filter(([, value]) => Boolean(value)).map(([label, value]) => <div key={label}><dt>{label}</dt><dd className={styles.text}>{value}</dd></div>)}</dl></details> : <p className={styles.muted}>Este registro não possui fotografia do conteúdo. A página atual pode estar indisponível se a ideia foi retirada ou virou proposta; não presuma o conteúdo anterior.</p>}
    <form onSubmit={submit} className={styles.form} aria-busy={busy}>
      <fieldset disabled={busy} className={styles.choices}><legend>O que fazer com esta denúncia?</legend>
        <label><input type="radio" name={`${formId}-action`} value="DISMISS" checked={action === "DISMISS"} onChange={() => { setAction("DISMISS"); setConfirmed(false); }} required />Encerrar denúncia sem arquivar a ideia</label>
        <label><input type="radio" name={`${formId}-action`} value="ARCHIVE" checked={action === "ARCHIVE"} onChange={() => { setAction("ARCHIVE"); setConfirmed(false); }} required />Arquivar a ideia em construção</label>
      </fieldset>
      <label htmlFor={`${formId}-note`}>Justificativa da decisão<textarea id={`${formId}-note`} value={note} onChange={(event) => setNote(event.target.value)} required minLength={1} maxLength={2000} disabled={busy} aria-describedby={`${formId}-privacy`} placeholder="Explique o que você conferiu e o motivo da decisão." /></label>
      <p id={`${formId}-privacy`} className={styles.muted}>A decisão e a justificativa ficam no registro administrativo. A identidade de quem denunciou não é exibida nesta fila nem na página pública.</p>
      {action === "ARCHIVE" && <div className={styles.confirmation}><p>O arquivamento retira a ideia em construção da área pública e impede novas edições. Versões de propostas já publicadas continuam preservadas.</p><label><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} required disabled={busy} />Conferi o conteúdo e confirmo o arquivamento desta ideia.</label></div>}
      {error && <p role="alert" tabIndex={-1} ref={errorRef} className={styles.notice}>{error}</p>}
      <Button type="submit" disabled={busy || !action || !note.trim() || (action === "ARCHIVE" && !confirmed)}>{busy ? "Registrando decisão…" : "Registrar decisão"}</Button>
    </form>
  </article>;
}

export function IdeaModeration() {
  const { user, loading: authLoading, request } = useAuth();
  const [result, setResult] = useState<{ owner: string; reports: Report[]; error: string } | null>(null);
  const [revision, setRevision] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState("");
  const headingRef = useRef<HTMLHeadingElement>(null);
  const owner = user?.id;
  const allowed = user?.role === "ADMIN";
  useEffect(() => {
    if (!allowed || !owner) return;
    let active = true;
    const controller = new AbortController();
    request<Report[]>("ideas/moderation", { signal: controller.signal }).then((response) => {
      if (active) setResult({ owner, reports: response.data, error: "" });
    }).catch((failure: unknown) => {
      if (active) setResult({ owner, reports: [], error: failure instanceof Error ? failure.message : "Não foi possível carregar a fila." });
    }).finally(() => { if (active) setRefreshing(false); });
    return () => { active = false; controller.abort(); };
  }, [allowed, owner, request, revision]);

  if (authLoading) return <Skeleton />;
  if (!allowed) return <section className={styles.shell}><h1>Moderação de ideias</h1><p>Esta área exige uma conta administradora. O acesso aos registros também é conferido pela API.</p><Link href="/painel">Voltar ao painel</Link></section>;
  const current = result?.owner === owner ? result : null;
  const loading = !current || refreshing;
  async function resolve(id: string, action: Decision, note: string) {
    await request(`ideas/moderation/${id}/resolve`, { method: "POST", body: JSON.stringify({ action, note }) });
    setResult((previous) => previous && previous.owner === owner ? { ...previous, reports: previous.reports.filter((report) => report.id !== id) } : previous);
    setMessage("Decisão registrada com autoria e justificativa. A denúncia saiu da fila de pendências.");
    requestAnimationFrame(() => headingRef.current?.focus());
  }
  return <div className={styles.shell}>
    <PageHero title="Conferir denúncias de ideias" tone="blue" description="Confira o conteúdo e registre uma decisão justificada. Discordância política, por si só, não é motivo para arquivar." action={<Button variant="secondary" href="/painel/admin">Administração</Button>} />
    <header className={styles.heading}><div><h2 ref={headingRef} tabIndex={-1}>Fila de denúncias</h2><p>Conteúdo restrito à equipe de moderação.</p></div><Button variant="secondary" disabled={loading} onClick={() => { setRefreshing(true); setMessage(""); setRevision((value) => value + 1); }}>Atualizar fila</Button></header>
    <p role="status" aria-live="polite">{message}</p>
    {loading ? <Skeleton /> : current?.error ? <section className={styles.notice} role="alert"><h2>A fila não carregou.</h2><p>{current.error}</p><Button variant="secondary" onClick={() => { setRefreshing(true); setRevision((value) => value + 1); }}>Tentar de novo</Button></section> : <>
      <p className={styles.muted}>{current?.reports.length ?? 0} denúncias pendentes nesta fila. A consulta mostra até 100 registros, do mais antigo ao mais recente.</p>
      {current?.reports.length ? <div className={styles.queue}>{current.reports.map((report) => <ReportReview key={report.id} report={report} onResolve={resolve} />)}</div> : <EmptyState title="Nenhuma denúncia pendente." description="Novos registros aparecerão aqui quando uma pessoa denunciar uma ideia compartilhada." href="/painel/admin" action="Voltar à administração" />}
    </>}
  </div>;
}
