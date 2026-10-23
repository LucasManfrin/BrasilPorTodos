"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { CONSENSUS_LABELS, DIRECTION_LABELS, EFFECT_LABELS, HORIZON_LABELS, NODE_LABELS, safePublicPath, uuidFromSlug } from "./helpers";
import type { GraphEdge, GraphNode, GraphRecord, Selection } from "./types";
import styles from "./inspector.module.css";

type Props = { record: GraphRecord; selection: Selection; onSelect: (value: Selection) => void; onClose: () => void };
type Version = { revision: number; content_hash: string; published_at: string; statement: string };
type History = { key: string; loading: boolean; rows?: Version[]; error?: string };

const RELATION_LABELS = { SUPPORTS: "Sustenta a alegação", CHALLENGES: "Contesta a alegação", CONTEXT: "Ajuda a entender o contexto" };
const LEVEL_LABELS = { DESCRIPTION: "Descrição", ASSOCIATION: "Associação", HYPOTHESIS_SUPPORT: "Apoio à hipótese" };

function date(value: string | null | undefined) {
  if (!value) return "Não informada";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "Data indisponível" : new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeZone: "UTC" }).format(parsed);
}

function safeUrl(value: string) {
  if (/[\u0000-\u0020\u007f\\]/.test(value)) return null;
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) && url.hostname && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

function Glyph({ kind }: { kind: "network" | "node" | "edge" }) {
  return <svg viewBox="0 0 72 72" fill="none" aria-hidden="true" className={styles.glyph}>
    {kind === "network" ? <><path d="m14 43 22-26 22 26-22 13-22-13Zm22-26v39M14 43h44" stroke="currentColor" strokeWidth="1.5"/><circle cx="36" cy="17" r="6" fill="currentColor"/><circle cx="14" cy="43" r="5" fill="currentColor"/><circle cx="58" cy="43" r="5" fill="currentColor"/><circle cx="36" cy="56" r="4" fill="currentColor"/></> : kind === "node" ? <><path d="M36 7 65 36 36 65 7 36 36 7Z" stroke="currentColor" strokeWidth="1.5"/><circle cx="36" cy="36" r="15" fill="currentColor"/></> : <><circle cx="14" cy="36" r="7" fill="currentColor"/><circle cx="58" cy="36" r="7" stroke="currentColor" strokeWidth="2"/><path d="M23 36h24m-8-8 8 8-8 8" stroke="currentColor" strokeWidth="2"/></>}
  </svg>;
}

function Notes({ title, items }: { title: string; items: string[] }) {
  return <section className={styles.notes}><h4>{title}</h4>{items.length ? <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>Não informado. Isso é uma lacuna, não uma confirmação.</p>}</section>;
}

function NodeDetail({ node, record, onSelect }: { node: GraphNode; record: GraphRecord; onSelect: Props["onSelect"] }) {
  const incoming = record.content.edges.filter(edge => edge.to_node.id === node.id);
  const outgoing = record.content.edges.filter(edge => edge.from_node.id === node.id);
  return <>
    <div className={styles.nodeIdentity}><Glyph kind="node"/><span>{NODE_LABELS[node.kind]}</span><h3>{node.label}</h3><p>{node.definition}</p></div>
    <section className={styles.section}><h4>O que varia aqui</h4><p>{node.dimension}</p><dl className={styles.metadata}><div><dt>Unidade</dt><dd>{node.unit ?? "Não definida"}</dd></div><div><dt>Versão do nó</dt><dd>{node.revision}</dd></div></dl>{!record.is_example && node.indicator_code && <a className={styles.textLink} href={`/brasil/${encodeURIComponent(node.indicator_code)}`}>Ver o indicador no Brasil Atual ↗</a>}{node.policy_version_number && <p className={styles.muted}>Referência congelada à versão {node.policy_version_number} de uma proposta; não acompanha edições futuras.</p>}</section>
    {([{ title: "Ligações que chegam", edges: incoming, side: "from_node" }, { title: "Ligações que saem", edges: outgoing, side: "to_node" }] as const).map(group => <section key={group.title} className={styles.section}><div className={styles.sectionHeading}><h4>{group.title}</h4><span>{group.edges.length}</span></div>{group.edges.length ? <ul className={styles.connections}>{group.edges.map(edge => <li key={edge.id}><button type="button" onClick={() => onSelect({ kind: "edge", id: edge.id })}><span className={styles.connectionArrow} aria-hidden="true">{group.side === "from_node" ? "↙" : "↗"}</span><span><strong>{edge[group.side].label}</strong><small>{DIRECTION_LABELS[edge.direction]} · {HORIZON_LABELS[edge.horizon]}</small></span><span aria-hidden="true">→</span></button></li>)}</ul> : <p className={styles.muted}>Nenhuma nesta versão da rede. Isso não significa que não existam outras relações.</p>}</section>)}
    <div className={styles.caution}><strong>Um nó não é uma estatística atual.</strong><p>Ele descreve um conceito e sua dimensão. As ligações apresentam alegações com fontes, condições e limites.</p></div>
  </>;
}

function EdgeDetail({ edge, record, onSelect }: { edge: GraphEdge; record: GraphRecord; onSelect: Props["onSelect"] }) {
  const publication = record.publications.find(item => item.review.edge_id === edge.id && item.review.edge_revision === edge.revision);
  const realId = !record.is_example ? uuidFromSlug(edge.id, "edge") : null;
  const key = `${record.id}:${edge.id}:${edge.revision}`;
  const [history, setHistory] = useState<History | null>(null);
  const abort = useRef<AbortController | null>(null);
  useEffect(() => () => { abort.current?.abort(); }, [key]);
  const visibleHistory = history?.key === key ? history : null;
  async function loadHistory() {
    if (!realId) return;
    abort.current?.abort();
    const controller = new AbortController();
    abort.current = controller;
    setHistory({ key, loading: true });
    try {
      const response = await fetchApi<Version[]>(`graphs/edges/${realId}/versions`, { signal: controller.signal });
      if (!controller.signal.aborted) setHistory({ key, loading: false, rows: response.data });
    } catch {
      if (!controller.signal.aborted) setHistory({ key, loading: false, error: "Não foi possível consultar o histórico. A versão aberta continua disponível." });
    }
  }
  const disputed = publication?.publication_state === "DISPUTED";
  const exactPath = !record.is_example ? safePublicPath("edge", edge.id, edge.revision) : null;
  return <>
    <div className={styles.edgeIdentity}><span className={styles.objectType}>Ligação · versão {edge.revision}</span><div className={styles.endpoints}><button type="button" onClick={() => onSelect({ kind: "node", id: edge.from_node.id })}>{edge.from_node.label}</button><span aria-hidden="true">→</span><button type="button" onClick={() => onSelect({ kind: "node", id: edge.to_node.id })}>{edge.to_node.label}</button></div><h3>{edge.statement}</h3></div>
    <div className={`${styles.review} ${disputed ? styles.disputed : ""}`}><span aria-hidden="true">{record.is_example ? "◇" : disputed ? "!" : "✓"}</span><div><strong>{record.is_example ? "Demonstração fictícia" : disputed ? "Publicada em disputa" : publication ? "Publicada após conferência" : "Revisão não disponível"}</strong><p>{record.is_example ? "Sem revisão humana real. Fontes e relações servem só para aprender a usar a tela." : disputed ? "A revisão registrou uma divergência. Confira a justificativa e os limites." : "Conferência e publicação não demonstram causalidade nem garantem a alegação."}</p></div></div>
    <section className={styles.section}><h4>Como ler esta seta</h4><p>{edge.trigger === "ADOPTION" ? <>A alegação parte da <strong>adoção da medida de origem</strong>.</> : <>A alegação parte de <strong>aumentar a dimensão de origem</strong>: {edge.from_node.dimension}.</>} No destino, o sentido declarado é <strong>{DIRECTION_LABELS[edge.direction].toLocaleLowerCase("pt-BR")}</strong>, mantidas as premissas.</p><dl className={styles.labels}><div><dt>Prazo declarado</dt><dd>{HORIZON_LABELS[edge.horizon]}</dd></div><div><dt>Tipo de efeito</dt><dd>{EFFECT_LABELS[edge.effect]}</dd></div><div><dt>Consenso declarado pelo autor</dt><dd>{CONSENSUS_LABELS[edge.consensus]}</dd></div></dl><p className={styles.muted}>Essas classificações são declarações de quem escreveu. A direção não significa melhora ou piora.</p></section>
    <div className={styles.noEstimate}><Glyph kind="edge"/><div><strong>Sem estimativa numérica</strong><p>Esta seta não calcula dinheiro, probabilidades ou efeitos em cadeia.</p></div></div>
    <section className={styles.section}><h4>Onde e quando vale a alegação</h4><dl className={styles.metadata}><div><dt>Recorte</dt><dd>{edge.scope}</dd></div><div><dt>Período</dt><dd>{edge.period}</dd></div></dl></section>
    <section className={styles.section}><div className={styles.sectionHeading}><h4>Evidências para conferir</h4><span>{edge.evidence.length}</span></div><p className={styles.muted}>A ligação abaixo explica o uso de cada trecho. Uma fonte inteira não é um endosso.</p><div className={styles.evidenceList}>{edge.links.map(link => {
      const evidence = edge.evidence.find(item => item.id === link.evidence_id);
      if (!evidence) return null;
      const source = edge.sources.find(item => item.id === evidence.source_id);
      const url = source && !record.is_example ? safeUrl(source.url) : null;
      const termsUrl = source && !record.is_example ? safeUrl(source.terms_url) : null;
      return <details key={link.evidence_id} className={styles.evidence}><summary><span className={styles.relation} data-relation={link.relation}>{RELATION_LABELS[link.relation]}</span><strong>{evidence.claim}</strong><span className={styles.summarySource}>{source?.institution ?? "Fonte não disponível"}<span aria-hidden="true"> +</span></span></summary><div className={styles.evidenceBody}><h5>Por que este trecho foi usado</h5><p>{link.justification}</p><blockquote>{evidence.excerpt}</blockquote><dl className={styles.metadata}><div><dt>Localização</dt><dd>{evidence.locator}</dd></div><div><dt>Nível declarado</dt><dd>{LEVEL_LABELS[evidence.level]}</dd></div><div><dt>Recorte</dt><dd>{evidence.scope}</dd></div><div><dt>Período</dt><dd>{evidence.period}</dd></div><div><dt>Limites do trecho</dt><dd>{evidence.limitations}</dd></div></dl>{source && <div className={styles.source}><h5>{source.title}</h5><p>{source.institution}</p>{record.is_example ? <p className={styles.demoNote}>Material fictício, sem fonte real.</p> : url ? <a className={styles.textLink} href={url} target="_blank" rel="noopener noreferrer">Abrir fonte ↗</a> : <p>Link da fonte indisponível.</p>}<dl className={styles.metadata}><div><dt>Publicação da fonte</dt><dd>{date(source.published_date)}</dd></div><div><dt>Consulta em UTC</dt><dd>{date(source.consulted_at)}</dd></div><div><dt>Termos registrados</dt><dd>{source.terms}</dd></div></dl>{termsUrl && <a className={styles.textLink} href={termsUrl} target="_blank" rel="noopener noreferrer">Consultar termos ↗</a>}</div>}</div></details>;
    })}</div></section>
    <section className={styles.section}><h4>E o outro lado?</h4><div className={styles.counterpoint}><strong>{edge.counterpoint_status === "DOCUMENTED" ? "Contraponto documentado" : edge.counterpoint_status === "NOT_FOUND" ? "Busca declarada, sem contraponto encontrado" : "Contrapontos ainda não pesquisados"}</strong><p>{edge.counterargument_note || (edge.counterpoint_status === "NOT_RESEARCHED" ? "A ausência de pesquisa é uma lacuna. Não significa que não exista contestação." : "Confira as evidências de contestação acima.")}</p>{edge.counterpoint_status === "NOT_FOUND" && <p>Não encontrar não prova que uma contestação não existe.</p>}{edge.counterpoint_search_notes.length > 0 && <details><summary>Ver registro da busca</summary><ul>{edge.counterpoint_search_notes.map((note, index) => <li key={index}>{note}</li>)}</ul><p>Busca declarada em {date(edge.counterpoint_searched_at)} (UTC).</p></details>}</div></section>
    <Notes title="Depende destas premissas" items={edge.premises}/><Notes title="Limites da alegação" items={edge.limitations}/><Notes title="O que ainda não sabemos" items={edge.unknowns}/>
    <details className={styles.audit}><summary>Autoria, revisão e histórico</summary><div className={styles.auditBody}><p><strong>{edge.authorship === "AI_ASSISTED" ? "Assistido por IA" : "Autoria humana declarada"}</strong>. {record.is_example ? "Exemplo sem curadoria real." : "A versão aberta é a exata selecionada nesta rede."}</p><dl className={styles.metadata}><div><dt>Atualização em UTC</dt><dd>{date(edge.updated_at)}</dd></div><div><dt>Versão da ligação</dt><dd>{edge.revision}</dd></div>{!record.is_example && <div><dt>Identidade do autor</dt><dd className={styles.mono}>{edge.author_id}</dd></div>}{publication && !record.is_example && <><div><dt>Publicação em UTC</dt><dd>{date(publication.published_at)}</dd></div><div><dt>Revisão em UTC</dt><dd>{date(publication.review.reviewed_at)}</dd></div><div><dt>Identidade do revisor</dt><dd className={styles.mono}>{publication.review.reviewer_id}</dd></div><div><dt>SHA-256 da ligação</dt><dd className={styles.mono}>{publication.content_hash}</dd></div></>}</dl>{publication && !record.is_example && <><h4>Justificativa da revisão</h4><p>{publication.review.rationale}</p><p className={styles.muted}>O registro acompanha esta versão; uma edição posterior exige nova conferência.</p></>}{exactPath && <a className={styles.textLink} href={exactPath} target="_blank" rel="noopener noreferrer">Registro exato em JSON ↗</a>}{realId && <><button type="button" className={styles.historyButton} disabled={visibleHistory?.loading} onClick={loadHistory}>{visibleHistory?.loading ? "Consultando…" : visibleHistory?.rows ? "Atualizar histórico público" : "Consultar versões públicas"}</button>{visibleHistory?.loading && <p role="status">Buscando apenas publicações…</p>}{visibleHistory?.error && <p role="alert">{visibleHistory.error} Use o botão acima para tentar novamente.</p>}{visibleHistory?.rows && <ul className={styles.history}>{visibleHistory.rows.map(row => <li key={row.revision}><strong>Versão {row.revision}{row.revision === edge.revision ? " · aberta" : ""}</strong><span>{date(row.published_at)}</span><p>{row.statement}</p><a href={safePublicPath("edge", edge.id, row.revision) ?? undefined} target="_blank" rel="noopener noreferrer">Consultar JSON desta versão ↗</a></li>)}</ul>}</>}</div></details>
  </>;
}

export function GraphInspector({ record, selection, onSelect, onClose }: Props) {
  const body = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (body.current) body.current.scrollTop = 0;
  }, [selection?.kind, selection?.id]);
  const node = selection?.kind === "node" ? record.content.nodes.find(item => item.id === selection.id) : null;
  const edge = selection?.kind === "edge" ? record.content.edges.find(item => item.id === selection.id) : null;
  const selected = Boolean(node || edge);
  return <aside className={styles.panel} aria-label="Detalhes da rede">
    <header className={styles.header}><h2 tabIndex={-1} data-graph-inspector-heading>{selected ? "Olhe mais de perto" : "Siga uma conexão"}</h2>{selected && <button type="button" onClick={onClose} className={styles.close} aria-label="Fechar seleção e voltar à rede">×</button>}</header>
    <div ref={body} className={styles.body}>{node ? <NodeDetail node={node} record={record} onSelect={onSelect}/> : edge ? <EdgeDetail key={`${record.id}:${edge.id}:${edge.revision}`} edge={edge} record={record} onSelect={onSelect}/> : <div className={styles.empty}><div className={styles.emptyVisual}><Glyph kind="network"/><span>Uma ideia puxa outra.</span></div><h3>O caminho importa tanto quanto a ideia.</h3><p>Selecione um ponto para entender o que ele representa. Selecione uma linha para conferir a alegação, as fontes e o que falta saber.</p><ul className={styles.legend}><li><span className={styles.legendNode} aria-hidden="true"/><div><strong>Ponto = conceito</strong><span>Indicador, medida, mecanismo ou grupo afetado.</span></div></li><li><span className={styles.legendEdge} aria-hidden="true">→</span><div><strong>Linha = relação alegada</strong><span>Tem direção, condições, evidências e limites.</span></div></li></ul><div className={styles.caution}><strong>Uma conexão não é uma certeza.</strong><p>Esta rede ajuda a investigar relações. Não calcula o efeito de uma proposta no país.</p></div><Link className={styles.textLink} href="/grafos#como-funciona">Entenda como ler a rede ↗</Link></div>}</div>
  </aside>;
}
