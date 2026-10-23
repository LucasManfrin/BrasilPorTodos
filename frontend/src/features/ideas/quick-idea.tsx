"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Icon } from "@/components/ui";
import { PageHero } from "@/components/page-kit";
import { useAuth } from "@/features/auth/provider";
import { emptyIdea, normalizedIdea } from "./state";
import type { Idea } from "./state";
import styles from "./quick-idea.module.css";

export function QuickIdea() {
 const { request } = useAuth();
 const router = useRouter();
 const [title,setTitle] = useState("");
 const [summary,setSummary] = useState("");
 const [saving,setSaving] = useState(false);
 const [error,setError] = useState("");
 const ready = Boolean(title.trim() && summary.trim());
 async function save(guided=false) {
   if (!ready || saving) return;
   setSaving(true);setError("");
   try {
     const input = { ...emptyIdea(), title, summary };
     const result = await request<Idea>("ideas",{method:"POST",body:JSON.stringify(normalizedIdea(input))});
     router.push(guided ? `/painel/ideias/${result.data.id}?modo=guiado` : "/painel/ideias");
   } catch(e) { setError(e instanceof Error ? e.message : "Não foi possível salvar. Seu texto continua aqui."); }
   finally { setSaving(false); }
 }
 return <div className={styles.workspace}>
  <div className={styles.hero}><PageHero title="Guarde a ideia. O resto vem depois." breadcrumb="Criar ideia" description="Um título e uma frase. Você não precisa chegar com custos, fontes ou todas as respostas." tone="green" /></div>
  <div className={styles.layout}>
   <form className={styles.form} onSubmit={e=>{e.preventDefault();void save();}} aria-busy={saving}>
    <span className={styles.label}><Icon name="edit"/> Ideia em construção</span>
    <h2>O que você quer mudar?</h2>
    <label htmlFor="idea-title">Um título<input id="idea-title" value={title} onChange={e=>setTitle(e.target.value)} maxLength={200} required disabled={saving} placeholder="Dê um nome simples à sua ideia" autoComplete="off" /></label>
    <label htmlFor="idea-summary">Sua ideia em uma frase<textarea id="idea-summary" value={summary} onChange={e=>setSummary(e.target.value)} maxLength={5000} required disabled={saving} placeholder="Escreva do seu jeito: qual é o problema e o que você gostaria de mudar?" aria-describedby="idea-note" /></label>
    <p id="idea-note" className={styles.support}>O primeiro salvamento é privado. Depois você escolhe se quer compartilhar ou desenvolver.</p>
    {error && <p role="alert" className={styles.error}>{error}</p>}
    <div className={styles.actions}><Button type="submit" disabled={saving||!ready}>{saving ? "Salvando…" : "Salvar ideia privada"}</Button><Button variant="secondary" type="button" disabled={saving||!ready} onClick={()=>void save(true)}>Salvar e desenvolver com IA</Button></div>
    {saving && <p role="status">Salvando seu rascunho privado…</p>}
   </form>
   <aside className={styles.aside}><h2>Ideia ou proposta?</h2><div><strong>Ideia</strong><p>É o começo da conversa. Pode ter dúvidas, campos em aberto e nenhuma estimativa.</p><span>Fora dos cálculos e dos planos</span></div><div><strong>Proposta completa</strong><p>Explica a medida, quem é afetado, riscos, financiamento e fontes. Só entra em planos e cálculos depois de completa e publicada.</p><Link href="/painel/propostas/nova">Já tenho esses detalhes. Preparar proposta <Icon name="arrow"/></Link></div><Link href="/painel/ideias">Voltar às minhas ideias</Link></aside>
  </div>
 </div>;
}
