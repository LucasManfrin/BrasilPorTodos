"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { Envelope } from "@/lib/types";
import { DEMO_GRAPH } from "./demo";
import { initialGraphState } from "./state";
import { filterGraph, graphPath, graphWithinLimits, NODE_LABELS, DIRECTION_LABELS } from "./helpers";
import { GraphInspector } from "./inspector";
import { GraphScene } from "./scene";
import type { GraphRecord, GraphSummary, GraphVersion, NodeKind, Selection } from "./types";
import styles from "./workspace.module.css";

type Props = { initial: Envelope<GraphSummary[]> | null; initialRecord?: GraphRecord | null; initialId?: string; initialRevision?: number };
type SourceMode = "demo" | "published";
const kinds: ("ALL" | NodeKind)[] = ["ALL", "MEASURE", "INDICATOR", "MECHANISM", "AFFECTED_GROUP"];

export function GraphWorkspace({ initial, initialRecord, initialId, initialRevision }: Props) {
  const validInitial = initialRecord && graphWithinLimits(initialRecord) ? initialRecord : null;
  const boot = initialGraphState(initial, validInitial, initialId, initialRevision);
  const [mode, setMode] = useState<SourceMode>(boot.mode);
  const [record, setRecord] = useState<GraphRecord | null>(boot.record);
  const [catalog, setCatalog] = useState(initial);
  const [busy, setBusy] = useState(boot.busy);
  const [error, setError] = useState(boot.error);
  const [catalogBusy, setCatalogBusy] = useState(false);
  const [target, setTarget] = useState<{ id: string; revision?: number } | null>(boot.target);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [kind, setKind] = useState<"ALL" | NodeKind>("ALL");
  const [selection, setSelection] = useState<Selection>(null);
  const [view, setView] = useState<"network" | "list">("network");
  const [trail, setTrail] = useState<string[]>([]);
  const [reducedMotion, setReducedMotion] = useState(true);
  const [preferenceReady, setPreferenceReady] = useState(false);
  const [fallback, setFallback] = useState("");
  const [versions, setVersions] = useState<GraphVersion[] | null>(null);
  const [versionError, setVersionError] = useState("");
  const [versionBusy, setVersionBusy] = useState(false);
  const [showVersions, setShowVersions] = useState(false);
  const [listed, setListed] = useState(40);
  const container = useRef<HTMLDivElement>(null);
  const mapBody = useRef<HTMLDivElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const request = useRef<AbortController | null>(null);
  const versionRequest = useRef<AbortController | null>(null);
  const catalogRequest = useRef<AbortController | null>(null);
  const active = mode === "demo" ? DEMO_GRAPH : record;
  const source = active && graphWithinLimits(active) ? active : null;
  const filtered = useMemo(() => source ? filterGraph(source.content.nodes, source.content.edges, search, kind) : { nodes: [], edges: [] }, [source, search, kind]);
  const total = catalog?.pagination?.total ?? catalog?.data.length ?? 0;
  const page = catalog?.pagination?.page ?? 1;
  const pageSize = catalog?.pagination?.page_size ?? 20;
  useEffect(() => { const timer = setTimeout(() => setSearch(query), 180); return () => clearTimeout(timer); }, [query]);
  useEffect(() => { const media = matchMedia("(prefers-reduced-motion: reduce)"); const update = () => { setReducedMotion(media.matches); setPreferenceReady(true); }; update(); media.addEventListener("change", update); return () => media.removeEventListener("change", update); }, []);
  useEffect(() => {
    function escape(event: KeyboardEvent) {
      if (event.key !== "Escape" || event.defaultPrevented || !selection) return;
      closeSelection();
    }
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [selection]);
  useEffect(() => {
    if (validInitial || !initialId && !initial?.data.length) return;
    const controller = new AbortController();
    request.current = controller;
    const id = initialId ?? initial!.data[0].id;
    const revision = initialId ? initialRevision : initial!.data[0].revision;
    void fetchApi<GraphRecord>(`graphs/${id}${revision ? `/versions/${revision}` : ""}`, { signal: controller.signal }).then(response => {
      if (!graphWithinLimits(response.data)) throw new Error("Esta rede não está no formato esperado. Nenhuma relação foi cortada para exibi-la.");
      if (!controller.signal.aborted) { setRecord(response.data); setError(""); setBusy(false); }
    }).catch(() => { if (!controller.signal.aborted) { setBusy(false); setError("Não foi possível abrir esta versão. Tente novamente."); } });
    return () => controller.abort();
    // Only bootstraps the server-selected version. Explicit changes use load().
  }, [initialId, initialRevision, initial, validInitial]);
  useEffect(() => () => { request.current?.abort(); versionRequest.current?.abort(); catalogRequest.current?.abort(); }, []);
  useEffect(() => {
    const map = mapBody.current;
    if (!map || !selection) return;
    let frame = 0;
    const place = () => {
      frame = 0;
      if (document.fullscreenElement || map.dataset.immersive) {
        map.style.removeProperty("--graph-panel-top"); map.style.removeProperty("--graph-panel-height"); map.style.removeProperty("--graph-controls-bottom"); return;
      }
      const bounds = map.getBoundingClientRect();
      if (window.innerWidth < 1050) {
        const footer = map.querySelector<HTMLElement>("[data-graph-warning]")?.offsetHeight ?? 72;
        const bottom = Math.min(bounds.bottom - footer - 12, window.innerHeight - 16);
        const visibleTop = Math.max(90, bounds.top + 10);
        const height = Math.min(440, window.innerHeight * .43, Math.max(120, bottom - visibleTop));
        const top = Math.max(10, bottom - bounds.top - height);
        const stageHeight = map.querySelector<HTMLElement>("[data-graph-canvas-host]")?.offsetHeight ?? bounds.height - footer;
        map.style.setProperty("--graph-panel-top", `${top}px`);
        map.style.setProperty("--graph-panel-height", `${height}px`);
        map.style.setProperty("--graph-controls-bottom", `${Math.max(18, stageHeight - top + 12)}px`);
        return;
      }
      map.style.removeProperty("--graph-controls-bottom");
      const top = Math.min(Math.max(20, 96 - bounds.top), Math.max(20, bounds.height - 280));
      map.style.setProperty("--graph-panel-top", `${top}px`);
      map.style.setProperty("--graph-panel-height", `${Math.max(240, bounds.height - top - 92)}px`);
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(place); };
    place();
    window.addEventListener("scroll", schedule, { passive: true }); window.addEventListener("resize", schedule);
    document.addEventListener("fullscreenchange", schedule);
    return () => { cancelAnimationFrame(frame); window.removeEventListener("scroll", schedule); window.removeEventListener("resize", schedule); document.removeEventListener("fullscreenchange", schedule); };
  }, [selection, view]);

  function clearFilters() { setQuery(""); setSearch(""); setKind("ALL"); setListed(40); }
  function closeSelection() {
    setSelection(null);
    requestAnimationFrame(() => {
      const previous = returnFocus.current;
      if (previous?.isConnected && previous.tabIndex >= 0 && !previous.closest("[data-graph-overlay]")) previous.focus({ preventScroll: true });
      else container.current?.querySelector<HTMLElement>("[data-graph-focus-target], [data-graph-list]")?.focus({ preventScroll: true });
    });
  }
  function fallbackToList(reason: string) { setFallback(reason); setView("list"); }
  function select(value: Selection) {
    const focused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    if (value && !focused?.closest("[data-graph-overlay]")) returnFocus.current = focused;
    setSelection(value);
    if (value && view === "network" && window.innerWidth < 1050) {
      const bounds = mapBody.current?.getBoundingClientRect();
      if (bounds && (bounds.top < 70 || bounds.top > 120)) mapBody.current?.scrollIntoView({ behavior: reducedMotion || focused?.closest("[data-graph-keyboard]") ? "instant" : "smooth", block: "start" });
    }
    if (value?.kind === "node") setTrail(previous => [...previous.filter(id => id !== value.id), value.id].slice(-5));
    if (value && !focused?.closest("[data-graph-keyboard]")) requestAnimationFrame(() => {
      container.current?.querySelector<HTMLElement>("[data-graph-inspector-heading]")?.focus({ preventScroll: true });
    });
  }
  function changeMode(next: SourceMode) {
    request.current?.abort(); versionRequest.current?.abort(); catalogRequest.current?.abort(); setCatalogBusy(false); setMode(next); setSelection(null); setTrail([]); clearFilters();
    if (next === "demo") setBusy(false);
    else if (!record && catalog?.data.length) void load(catalog.data[0].id, catalog.data[0].revision);
  }
  async function load(id: string, revision?: number) {
    request.current?.abort(); versionRequest.current?.abort(); catalogRequest.current?.abort(); setCatalogBusy(false);
    const controller = new AbortController(); request.current = controller;
    setTarget({ id, revision });
    setMode("published"); setBusy(true); setError(""); setSelection(null); setRecord(null); setTrail([]); clearFilters(); setShowVersions(false); setVersions(null);
    try {
      const response = await fetchApi<GraphRecord>(`graphs/${encodeURIComponent(id)}${revision ? `/versions/${revision}` : ""}`, { signal: controller.signal });
      if (!graphWithinLimits(response.data)) throw new Error("Rede incompatível com os limites de exibição.");
      if (!controller.signal.aborted) setRecord(response.data);
    } catch { if (!controller.signal.aborted) setError("Não foi possível abrir esta versão pública. Nenhum rascunho é exibido aqui."); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  async function loadCatalog(nextPage = page) {
    catalogRequest.current?.abort();
    const controller = new AbortController(); catalogRequest.current = controller;
    setCatalogBusy(true); setError("");
    try {
      const response = await fetchApi<GraphSummary[]>(`graphs?page=${nextPage}&page_size=20`, { signal: controller.signal });
      if (controller.signal.aborted) return;
      setCatalog(response);
      if (response.data.length && mode === "published" && !record) void load(response.data[0].id, response.data[0].revision);
    } catch { if (!controller.signal.aborted) setError("Não foi possível consultar os mapas publicados. Tente novamente."); }
    finally { if (!controller.signal.aborted) setCatalogBusy(false); }
  }
  async function history() {
    setShowVersions(true);
    if (!record || versions) return;
    versionRequest.current?.abort();
    const controller = new AbortController(); versionRequest.current = controller;
    setVersionBusy(true); setVersionError("");
    try { const result = await fetchApi<GraphVersion[]>(`graphs/${record.id}/versions`, {signal: controller.signal}); if (!controller.signal.aborted) setVersions(result.data); }
    catch { if (!controller.signal.aborted) setVersionError("O histórico não carregou. A rede aberta continua disponível."); }
    finally { if (!controller.signal.aborted) setVersionBusy(false); }
  }
  return <div className={styles.workspace} ref={container}>
    <header className={styles.hero}><div><Link href="/brasil" className={styles.back}>← Brasil Atual</Link><h1>Uma ideia.<br /><span>Muitas conexões.</span></h1></div><div className={styles.heroAside}><span className={styles.heroSymbol} aria-hidden="true"><i /><i /><i /></span><p>Olhe para as ligações.<br />Confira o que sustenta cada uma.</p><a href="#como-funciona" className={styles.guideLink}>Primeira vez? Veja como ler o mapa <span aria-hidden="true">↘</span></a></div></header>
    <section className={styles.observatory} aria-label="Explorador de relações">
      <header className={styles.mapHeader}><div className={styles.mapHeading}><span className={styles.mapGlyph} aria-hidden="true"><i /><i /><i /></span><div><h2>Mapa de relações</h2><p>Explore. Questione. Abra as fontes.</p></div></div><div className={styles.sourceTabs} role="group" aria-label="Origem do mapa"><button type="button" aria-pressed={mode === "demo"} onClick={() => changeMode("demo")}>Exemplo didático</button><button type="button" aria-pressed={mode === "published"} onClick={() => changeMode("published")}>Publicados <span>{catalog ? total : "—"}</span></button></div></header>
      {mode === "demo" ? <div className={styles.demoNotice}><strong>Um cenário inventado para aprender.</strong><span>Não descreve o Brasil. Não tem evidência real nem revisão humana.</span><span className={styles.demoPill}>Demonstração</span></div> : <div className={styles.publicBar}><label>Mapa publicado<select value={record?.id ?? ""} onChange={event => void load(event.target.value, catalog?.data.find(item => item.id === event.target.value)?.revision)} disabled={catalogBusy || !catalog?.data.length}><option value="" disabled>Escolha um mapa</option>{record && !catalog?.data.some(item => item.id === record.id) && <option value={record.id}>{record.content.title} · v{record.revision}</option>}{catalog?.data.map(item => <option key={item.id} value={item.id}>{item.id === record?.id ? record.content.title : item.content.title} · v{item.id === record?.id ? record.revision : item.revision}{item.is_example ? " · Exemplo" : ""}</option>)}</select></label>{record && <button type="button" className={styles.textControl} onClick={() => void history()}>Versão {record.revision} · Ver histórico ↗</button>}<button type="button" className={styles.textControl} disabled={catalogBusy} onClick={() => void loadCatalog()}>{catalogBusy ? "Consultando…" : "Atualizar lista"}</button>{total > pageSize && <div className={styles.catalogPages}><button type="button" disabled={page === 1 || catalogBusy} onClick={() => void loadCatalog(page - 1)} aria-label="Página anterior de mapas">←</button><span>{page}</span><button type="button" disabled={page * pageSize >= total || catalogBusy} onClick={() => void loadCatalog(page + 1)} aria-label="Próxima página de mapas">→</button></div>}</div>}
      {mode === "published" && record?.is_example && <div className={styles.demoNotice}><strong>Publicação fictícia de demonstração.</strong><span>Não descreve relações reais do Brasil.</span></div>}
      {showVersions && mode === "published" && <div className={styles.history}><div><strong>Versões publicadas</strong><button type="button" className={styles.textControl} onClick={() => setShowVersions(false)}>Fechar</button></div>{versionBusy ? <p role="status">Carregando histórico…</p> : versionError ? <p role="alert">{versionError} <button type="button" onClick={() => void history()}>Tentar novamente</button></p> : <ul>{versions?.map(item => <li key={item.revision}><button type="button" onClick={() => void load(record!.id, item.revision)}>v{item.revision} · {item.title}</button><time>{new Date(item.published_at).toLocaleDateString("pt-BR")}</time></li>)}</ul>}</div>}
      <div className={styles.filterBar}><label className={styles.search}><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8" cy="8" r="5" /><path d="m12 12 5 5" /></svg><span className={styles.srOnly}>Buscar nós ou relações neste mapa</span><input type="search" value={query} maxLength={120} placeholder="Encontre uma conexão" onChange={event => { setQuery(event.target.value); setSelection(null); setListed(40); }} disabled={!source || busy} /></label><div className={styles.filterChips} role="group" aria-label="Tipo de nó">{kinds.map(value => <button type="button" key={value} aria-pressed={kind === value} disabled={!source || busy} onClick={() => { setKind(value); setSelection(null); setListed(40); }}><span className={styles.legendShape} data-kind={value} aria-hidden="true" />{value === "ALL" ? "Tudo" : NODE_LABELS[value]}</button>)}</div><div className={styles.viewSwitch} role="group" aria-label="Forma de explorar"><button type="button" aria-pressed={view === "network"} onClick={() => { setFallback(""); setView("network"); }}>Rede</button><button type="button" aria-pressed={view === "list"} onClick={() => setView("list")}>Lista</button></div></div>
      {query || kind !== "ALL" ? <div className={styles.filterSummary} role="status"><span>{filtered.nodes.length} nós · {filtered.edges.length} relações{kind !== "ALL" ? " · inclui pontas conectadas para manter o contexto" : ""}</span><button type="button" onClick={clearFilters}>Limpar filtros</button></div> : null}
      {fallback && <div className={styles.fallbackNotice} role="status"><span aria-hidden="true">≡</span><p>{fallback}</p><button type="button" onClick={() => setFallback("")} aria-label="Fechar aviso da lista">×</button></div>}
      <div className={styles.mapBody} data-graph-map ref={mapBody}>
        {source?.is_example && <div className={styles.immersiveExample}>Demonstração fictícia · sem evidência real</div>}
        <div className={styles.networkColumn}>
          {busy && mode === "published" ? <div className={styles.loading} role="status"><div className={styles.loadingOrbit} aria-hidden="true"><i /><i /><i /></div><h3>Conectando os pontos…</h3><p>Buscando a versão publicada e suas fontes.</p></div> : mode === "published" && error ? <div className={styles.empty} role="alert"><span className={styles.emptySymbol} aria-hidden="true">↗</span><h3>Esta conexão fez uma pausa.</h3><p>{error}</p><button type="button" onClick={() => target ? void load(target.id, target.revision) : void loadCatalog()} className="button">Tentar novamente</button><button type="button" onClick={() => changeMode("demo")} className={styles.emptyLink}>Enquanto isso, explorar o exemplo didático</button></div> : !source ? <div className={styles.empty}><span className={styles.emptySymbol} aria-hidden="true">↗</span><h3>As primeiras conexões<br />ainda estão em revisão.</h3><p>Uma relação só aparece depois de revisada e publicada. A ausência não significa que não existam conexões.</p><button type="button" onClick={() => changeMode("demo")} className="button">Conhecer o mapa com um exemplo →</button></div> : !filtered.nodes.length ? <div className={styles.empty}><span className={styles.emptySymbol} aria-hidden="true">⌕</span><h3>Nenhum ponto por aqui.</h3><p>Tente outro termo ou volte à rede inteira.</p><button type="button" onClick={clearFilters} className="button">Limpar filtros</button></div> : view === "network" ? preferenceReady ? <GraphScene key={source.version_id} nodes={filtered.nodes} edges={filtered.edges} selection={selection} onSelect={select} reducedMotion={reducedMotion} onFallback={fallbackToList} /> : <div className={styles.loading} role="status"><h3>Preparando o mapa…</h3><p>Ajustando a experiência às suas preferências.</p></div> : <div className={styles.listView} data-graph-list tabIndex={-1}><header><h3>As mesmas conexões.<br />Outro jeito de explorar.</h3><p>Origem → destino. Abra uma relação para ler suas condições e fontes.</p></header><ul className={styles.nodeList} aria-label="Nós do mapa">{filtered.nodes.map(node => <li key={node.id}><button type="button" aria-pressed={selection?.kind === "node" && selection.id === node.id} onClick={() => select({ kind: "node", id: node.id })}><span className={styles.legendShape} data-kind={node.kind} aria-hidden="true" />{node.label}<span>{NODE_LABELS[node.kind]} ↗</span></button></li>)}</ul><ol className={styles.relationList} aria-label="Relações do mapa">{filtered.edges.slice(0, listed).map((edge, index) => <li key={edge.id}><button type="button" onClick={() => select({ kind: "edge", id: edge.id })} aria-pressed={selection?.kind === "edge" && selection.id === edge.id}><span className={styles.relationIndex}>{String(index + 1).padStart(2, "0")}</span><span><strong>{edge.from_node.label} <span aria-hidden="true">→</span> {edge.to_node.label}</strong><small>{DIRECTION_LABELS[edge.direction]} · {source.is_example ? "Relação fictícia" : "Ver evidências e revisão"}</small></span><span aria-hidden="true">↗</span></button></li>)}</ol>{filtered.edges.length > listed && <button className="button secondary" type="button" onClick={() => setListed(current => current + 40)}>Mostrar mais {Math.min(40, filtered.edges.length - listed)} relações</button>}{!filtered.edges.length && <p>Sem ligações neste recorte. Nenhuma relação foi inferida.</p>}</div>}
          {source && !busy && <div className={styles.mapFoot} data-graph-warning><span>Posição, tamanho e distância são só visuais. <strong>Não medem força, importância ou certeza.</strong></span><span className={styles.neutralNote}><span aria-hidden="true">↗</span> Direção alegada.<br />Não é previsão.</span></div>}
        </div>
        {selection && source && !busy && !(mode === "published" && error) && <div className={styles.inspectorColumn} data-graph-overlay><GraphInspector record={source} selection={selection} onSelect={select} onClose={closeSelection} /></div>}
      </div>
      {source && <footer className={styles.explorationFooter}><div><span className={styles.explorationLabel}>Você explorou</span>{trail.length ? <nav aria-label="Últimos nós visitados">{trail.map(id => <button type="button" key={id} onClick={() => select({ kind: "node", id })}>{source.content.nodes.find(node => node.id === id)?.label}<span aria-hidden="true">↗</span></button>)}</nav> : <span>Seu percurso começa em qualquer ponto.</span>}</div>{mode === "published" && record && graphPath(record.id, record.revision) ? <Link href={graphPath(record.id, record.revision)!}>Abrir link desta versão ↗</Link> : <span>Aprender a navegar não é simular efeitos.</span>}</footer>}
    </section>
    <div className={styles.bottomNote}><p>Não existe linha mágica entre uma ideia e um resultado.<br /><strong>As condições e os limites fazem parte da história.</strong></p><Link href="/metodologia">Conheça o método <span aria-hidden="true">↗</span></Link></div>
  </div>;
}
