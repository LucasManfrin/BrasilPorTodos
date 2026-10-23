"use client";
import { useState } from "react";
import { useAuth } from "@/features/auth/provider";
import styles from "./ideas.module.css";

/** Deliberate owner-only request; private prompts never go into browser storage or public logs. */
export function GuidanceTrace({ callId }: { callId: string }) {
  const { request } = useAuth();
  const [trace, setTrace] = useState<unknown>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function load() {
    if (open) { setOpen(false); return; }
    if (trace && callId !== "latest") { setOpen(true); return; }
    setBusy(true); setError("");
    try { setTrace((await request<unknown>(`guidance/calls/${callId}`)).data); setOpen(true); }
    catch (e) { setError(e instanceof Error ? e.message : "Não foi possível consultar o registro."); }
    finally { setBusy(false); }
  }
  return <section className={styles.trace} aria-label="Registro privado da chamada de IA">
    <button disabled={busy} aria-expanded={open} onClick={() => void load()}>{busy ? "Carregando registro…" : open ? "Ocultar chamada da IA" : callId === "latest" ? "Ver minha última chamada de IA" : "Ver chamada e retorno da IA"}</button>
    {error && <p role="alert">{error}</p>}
    {open && <><p>Registro privado desta chamada: modelo, instruções, conteúdo enviado e resposta recebida. A chave de API não faz parte deste registro. Sujeito ao prazo de retenção e ao apagamento.</p><pre tabIndex={0}>{JSON.stringify(trace,null,2)}</pre></>}
  </section>;
}
