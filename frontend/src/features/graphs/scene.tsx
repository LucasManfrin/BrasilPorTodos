"use client";

import dynamic from "next/dynamic";
import { Component, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import type { GraphNode, GraphEdge, Selection } from "./types";
import { fallbackReason } from "./spatial";
import styles from "./scene-shell.module.css";

const Canvas3D = dynamic(() => import("./graph-canvas-3d"), {
  ssr: false,
  loading: () => <SceneLoading />,
});
const INTRO_KEY = "bpt-graph-intro-dismissed-v1";
const LOAD_FAILURE = "O mapa 3D não carregou. As mesmas conexões continuam disponíveis na lista.";

type SceneProps = {
  nodes: GraphNode[]; edges: GraphEdge[]; selection: Selection;
  onSelect: (selection: Selection) => void; reducedMotion: boolean;
  onFallback: (reason: string) => void;
};

class SceneBoundary extends Component<{ children: ReactNode; onFailure: (reason: string) => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onFailure(LOAD_FAILURE); }
  render() { return this.state.failed ? <p className={styles.failure} role="status">{LOAD_FAILURE}</p> : this.props.children; }
}

function SceneLoading() {
  return <div className={styles.loading} role="status"><span className={styles.orbit} aria-hidden="true"><i /><i /><i /></span><strong>Preparando outra perspectiva.</strong><span>O mapa 3D só carrega quando você chega aqui.</span></div>;
}

function fallbackForDevice(reducedMotion: boolean): string | null {
  const device = navigator as Navigator & { deviceMemory?: number; connection?: { saveData?: boolean } };
  const hints = { reducedMotion, deviceMemory: device.deviceMemory, hardwareConcurrency: device.hardwareConcurrency, saveData: device.connection?.saveData };
  const early = fallbackReason({ ...hints, webgl: true });
  if (early) return early;
  const canvas = document.createElement("canvas");
  try {
    const context = canvas.getContext("webgl2", { failIfMajorPerformanceCaveat: true });
    if (!context) return fallbackReason({ ...hints, webgl: false });
    context.getExtension("WEBGL_lose_context")?.loseContext();
  } catch { return fallbackReason({ ...hints, webgl: false }); }
  return null;
}

function Onboarding() {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    let dismissed = false;
    try { dismissed = localStorage.getItem(INTRO_KEY) === "yes"; } catch { /* A preference is optional; access never depends on storage. */ }
    const frame = requestAnimationFrame(() => setVisible(!dismissed));
    return () => cancelAnimationFrame(frame);
  }, []);
  function dismiss() {
    setVisible(false);
    try { localStorage.setItem(INTRO_KEY, "yes"); } catch { /* Keep this visit usable even if storage is unavailable. */ }
  }
  if (!visible) return null;
  return <aside className={styles.intro} aria-label="Como explorar o mapa 3D"><div className={styles.introHeading}><strong>Entre nas conexões.</strong><button type="button" onClick={dismiss} aria-label="Fechar dicas do mapa">×</button></div><ol><li><span aria-hidden="true">↔</span><span><strong>Arraste para girar.</strong> Veja a rede de outros ângulos.</span></li><li><span aria-hidden="true">◎</span><span><strong>Toque num ponto.</strong> A câmera aproxima suas conexões.</span></li><li><span aria-hidden="true">↗</span><span><strong>Toque numa linha.</strong> Confira fontes e limites.</span></li></ol><button type="button" className={styles.begin} onClick={dismiss}>Entendi. Vamos explorar →</button></aside>;
}

export function GraphScene({ nodes, edges, selection, onSelect, reducedMotion, onFallback }: SceneProps) {
  const host = useRef<HTMLDivElement>(null);
  const [near, setNear] = useState(false);
  const [eligible, setEligible] = useState(false);
  const fallbackRef = useRef(onFallback);
  useEffect(() => { fallbackRef.current = onFallback; }, [onFallback]);
  useEffect(() => {
    const element = host.current;
    if (!element) return;
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) { setNear(true); observer.disconnect(); }
    }, { rootMargin: "160px" });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!near) return;
    const reason = fallbackForDevice(reducedMotion);
    if (reason) fallbackRef.current(reason);
    else { const frame = requestAnimationFrame(() => setEligible(true)); return () => cancelAnimationFrame(frame); }
  }, [near, reducedMotion]);
  // The renderer performs its own context creation and reports failures, too.
  // A reduced-motion or conservative device fallback never downloads Three.js.
  return <div className={styles.shell} ref={host} data-graph-focus-target tabIndex={-1} aria-label="Mapa de relações em três dimensões">
    {eligible && !reducedMotion ? <SceneBoundary onFailure={onFallback}><Canvas3D nodes={nodes} edges={edges} selection={selection} onSelect={onSelect} reducedMotion={reducedMotion} onFailure={onFallback} /><Onboarding /></SceneBoundary> : <SceneLoading />}
  </div>;
}
