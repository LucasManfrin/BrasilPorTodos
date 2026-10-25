"use client";
import Link from "next/link";
import { Button, Icon } from "@/components/ui";
import type { ReactNode } from "react";
import type { IdeaInput, Organized } from "./state";
import { reviewGuidance } from "./state";
import { GuidanceTrace } from "./guidance-trace";
import styles from "./ideas.module.css";

export function ModeChoiceCard({ guided, onChoose }: { guided?: boolean; onChoose: () => void }) {
  return <button className={`${styles.modeChoice} ${guided ? styles.guidedChoice : ""}`} onClick={onChoose}>
    <span className={styles.choiceIcon}><Icon name={guided ? "layers" : "edit"} /></span>
    <span className={styles.choiceTitle}>{guided ? "Me ajuda a montar" : "Eu preencho"}</span>
    {guided && <span className={styles.badge}>Assistido por IA</span>}
    <span>{guided ? "Conte do seu jeito. A IA ajuda a desenvolver e você confirma cada resposta." : "Organize problema, solução, impacto e fontes com campos por etapa."}</span>
    <span className={styles.choiceTime}>{guided ? "~5 min · uma pergunta por vez" : "~10 min · você escreve direto"}<small>Tempo aproximado; siga no seu ritmo.</small></span>
    <span className={styles.choiceCta}>{guided ? "Começar com ajuda" : "Abrir formulário"}<Icon name="arrow" /></span>
  </button>;
}
export function GuidedStepper({ current, total, version }: { current: number; total: number; version: string }) {
  return <div className={styles.guideProgress}><div><strong>Pergunta {current + 1} de {total}</strong><small>roteiro {version}</small></div><progress max={total} value={current + 1} aria-label={`Pergunta ${current + 1} de ${total}`} /></div>;
}
export function AiConsentCard({ days, onAccept, onWithout }: { days: number; onAccept: () => void; onWithout: () => void }) {
  return <section className={styles.consentCard} aria-labelledby="consent-title"><span className={styles.badge}>Antes de começar</span><h2 id="consent-title">Sua ideia. Sua escolha.</h2>
    <p>Suas respostas e trechos já confirmados serão enviados ao Gemini para ajudar a desenvolver a proposta.</p><p>O registro privado da chamada fica armazenado por até <strong>{days} dias</strong>. Evite dados pessoais sensíveis.</p>
    <div className={styles.actions}><Button onClick={onAccept}>Aceitar e começar com IA</Button><Button variant="secondary" onClick={onWithout}>Continuar sem IA</Button></div><small>Vale para esta criação enquanto você estiver nesta sessão. Você pode mudar a escolha no topo.</small></section>;
}
export function AiResponseCard({ pending, answer, selected, onSelect, onConfirm, onCorrect, onOriginal }: { pending: Organized; answer: string; selected: number[]; onSelect: (index: number, checked: boolean) => void; onConfirm: () => void; onCorrect: () => void; onOriginal: () => void }) {
  const review = reviewGuidance(pending, answer);
  return <section className={styles.confirmation} aria-label="Confira sua resposta"><header className={styles.responseHeading}><h3>Confira antes de preencher</h3>{pending.assisted_by_ai && <span className={styles.badge}>Assistido por IA</span>}</header>
    <div className={styles.original}><strong>O que você escreveu</strong><blockquote className={styles.text}>{review.original}</blockquote></div>
    {pending.unknown ? <p>“Não sei” é válido. Este campo ficará em aberto; uma resposta anterior confirmada será preservada.</p> : <details open className={styles.responseBlock}><summary>Como ficou organizado</summary><p className={styles.text}>{review.suggestion}</p>{review.kind === "unchanged" && <p className={styles.muted}>A redação principal foi mantida.</p>}</details>}
    {(pending.suggestions?.length ?? 0) > 0 && <details className={styles.responseBlock}><summary>Sugestões opcionais para desenvolver <span>{pending.suggestions!.length}</span></summary><p className={styles.muted}>São possibilidades da IA, não decisões já tomadas nem efeitos comprovados. Você pode ignorar todas. Só as sugestões marcadas entram no texto depois de você confirmar.</p><div className={styles.suggestionGrid}>{pending.suggestions!.map((suggestion, index) => <label className={styles.suggestion} data-selected={selected.includes(index)} key={index}><input type="checkbox" checked={selected.includes(index)} onChange={event => onSelect(index,event.target.checked)} /><span>{suggestion}</span><span className={styles.selectionMark} aria-hidden="true">{selected.includes(index) ? "✓ Vou incluir" : "+ Quero incluir"}</span></label>)}</div></details>}
    {(pending.open_questions?.length ?? 0) > 0 && <details className={styles.responseBlock}><summary>Perguntas para pensar depois <span>{pending.open_questions!.length}</span></summary><ul>{pending.open_questions!.map((item,index) => <li key={index}>{item}</li>)}</ul><p className={styles.muted}>Não precisa resolver agora. São dúvidas para desenvolver a proposta; não preenchem campos nem impedem salvar a ideia.</p></details>}
    {pending.call_id && <details className={styles.responseBlock}><summary>Detalhes técnicos</summary><GuidanceTrace key={pending.call_id} callId={pending.call_id} /></details>}
    {pending.assisted_by_ai && <p className={styles.muted}>Confira se o sentido continua o mesmo. Sugestões podem conter erros e precisam de revisão.</p>}
    <footer className={styles.confirmActions}><Button onClick={onConfirm}>{pending.unknown ? "Continuar sem preencher" : "Confirmo, pode preencher"}</Button><Button variant="secondary" onClick={onCorrect}>Quero corrigir</Button>{!pending.unknown && <Button variant="tertiary" onClick={onOriginal}>Manter meu texto original</Button>}</footer>
  </section>;
}
export function AiLoadingCard({ kind = "ai" }: { kind?: "ai" | "script" | "literal" }) { return <div className={styles.aiLoading} role="status" aria-live="polite"><strong>{kind === "script" ? "Abrindo roteiro…" : kind === "literal" ? "Conferindo sua resposta…" : "Desenvolvendo sua ideia…"}</strong><span className="skeleton" /><span className="skeleton" /><span className="skeleton" /><p>{kind === "script" ? "Carregando as perguntas. Nenhuma resposta é enviada nesta etapa." : kind === "literal" ? "Seu texto será apresentado para confirmação, sem chamada ao Gemini." : "O Gemini está preparando uma sugestão. Sua resposta continua preservada."}</p></div>; }
export function ProgressSidebar({ children, saving, status, complete, total, preview, previewCategory }: { children: ReactNode; saving: boolean; status: string; complete: number; total: number; preview: IdeaInput; previewCategory: string }) {
  return <aside className={styles.progressAside} aria-label="Progresso do rascunho"><details className={styles.progressSheet} open><summary><span>Seu rascunho</span><small>{saving ? "Aguarde…" : status}</small></summary><div className={styles.progressContent}>
    <p className={styles.support}>Sem pressão para saber tudo. Um título e uma frase bastam para salvar.</p>{total > 0 && <div className={styles.completion}><strong>{complete} de {total}</strong><span>requisitos no último salvamento</span><progress value={complete} max={total} aria-label={`${complete} de ${total} requisitos completos`} /></div>}
    {children}
    <details open className={styles.preview}><summary>Prévia do rascunho</summary><span className={styles.badge}>{previewCategory}</span><h3>{preview.title || "O título aparece aqui"}</h3><p>{preview.summary || "Sua ideia em uma frase, sem precisar chegar com tudo pronto."}</p><small>Ideia em construção · fora dos cálculos</small></details>
    <Link href="/metodologia#criar-proposta">O que muda ao publicar?</Link></div></details></aside>;
}
