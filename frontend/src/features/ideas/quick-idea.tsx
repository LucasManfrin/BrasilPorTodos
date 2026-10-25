"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Icon } from "@/components/ui";
import { PageHero, Skeleton } from "@/components/page-kit";
import { useAuth } from "@/features/auth/provider";
import { emptyIdea, ideaInput, normalizedIdea } from "./state";
import { ideaDevelopmentPath, updateQuickIdea } from "./navigation";
import type { Idea } from "./state";
import styles from "./quick-idea.module.css";

export function QuickIdea({ id }: { id?: string }) {
 const { request } = useAuth();
 const router = useRouter();
 const [record,setRecord] = useState<Idea | null>(null);
 const [title,setTitle] = useState("");
 const [summary,setSummary] = useState("");
 const [loading,setLoading] = useState(Boolean(id));
 const [saving,setSaving] = useState(false);
 const [error,setError] = useState("");
 const [message,setMessage] = useState("");
 const [retry,setRetry] = useState(0);
 const ready = Boolean(title.trim() && summary.trim());
 const dirty = record ? title !== record.title || summary !== record.summary : Boolean(title || summary);
 useEffect(() => {
   if (!id) return;
   let active = true;
   request<Idea>(`ideas/${encodeURIComponent(id)}`).then(response => {
     if (active) { setRecord(response.data); setTitle(response.data.title); setSummary(response.data.summary); setError(""); }
   }).catch((e: Error) => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); });
   return () => { active = false; };
 }, [id,request,retry]);
 useEffect(() => {
   function warn(event: BeforeUnloadEvent) { if (dirty) event.preventDefault(); }
   window.addEventListener("beforeunload",warn);
   return () => window.removeEventListener("beforeunload",warn);
 }, [dirty]);
 async function save(): Promise<Idea> {
   if (!ready) throw new Error("Para salvar, basta um título e uma frase.");
   if (record && !dirty) return record;
   const input = updateQuickIdea(record ? ideaInput(record) : emptyIdea(),title,summary);
   const result = await request<Idea>(record ? `ideas/${record.id}` : "ideas",{method:record ? "PATCH" : "POST",body:JSON.stringify(normalizedIdea(input))});
   setRecord(result.data);setTitle(result.data.title);setSummary(result.data.summary);
   return result.data;
 }
 async function action(kind: "save" | "develop" | "share" | "unshare") {
   if (saving) return;
   setSaving(true);setError("");setMessage("");
   try {
     if (kind === "unshare" && record) {
       const result=await request<Idea>(`ideas/${record.id}/unshare`,{method:"POST"});
       setRecord(result.data);setMessage("Ideia privada. A cópia pública foi retirada.");return;
     }
     const saved=await save();
     if (kind === "develop") { router.push(ideaDevelopmentPath(saved.id)); return; }
     if (kind === "share") {
       const result=await request<Idea>(`ideas/${saved.id}/share`,{method:"POST"});
       setRecord(result.data);setMessage("Ideia compartilhada. Você pode retirar a cópia pública quando quiser.");
     } else setMessage("Ideia salva. Você não precisa completar mais nada agora.");
     if (!id) router.replace(`/painel/ideias/${saved.id}`);
   } catch(e) { setError(e instanceof Error ? e.message : "Não foi possível salvar. Seu texto continua aqui."); }
   finally { setSaving(false); }
 }
 if (loading) return <Skeleton />;
 if (id && !record) return <section className={styles.form}><h1>Não conseguimos abrir esta ideia.</h1><p role="alert">{error}</p><Button onClick={()=>{setLoading(true);setRetry(value=>value+1);}}>Tentar novamente</Button><Link href="/painel/ideias">Voltar às minhas ideias</Link></section>;
 if (record?.status === "PROMOTED" || record?.status === "ARCHIVED") return <section className={styles.form}><h1>{record.title}</h1><p>{record.summary}</p><p>{record.status === "PROMOTED" ? "Esta ideia já virou uma proposta completa." : "Esta ideia foi arquivada."}</p>{record.promoted_policy_id && <Button href={`/painel/propostas/${record.promoted_policy_id}`}>Abrir proposta</Button>}<Link href="/painel/ideias">Minhas ideias</Link></section>;
 return <div className={styles.workspace}>
  <div className={styles.hero}><PageHero title={id ? "Sua ideia. Sem complicar." : "Guarde a ideia. O resto vem depois."} breadcrumb={id ? "Sua ideia" : "Criar ideia"} description="Um título e uma frase. Você não precisa chegar com custos, fontes ou todas as respostas." tone="green" /></div>
  <div className={styles.layout}>
   <form className={styles.form} onSubmit={e=>{e.preventDefault();void action("save");}} aria-busy={saving}>
    <span className={styles.label}><Icon name="edit"/> {record?.status === "SHARED" ? "Ideia compartilhada" : "Ideia privada"}</span>
    <h2>O que você quer mudar?</h2>
    <label htmlFor="idea-title">Um título<input id="idea-title" value={title} onChange={e=>{setTitle(e.target.value);setMessage("");}} maxLength={200} required disabled={saving} placeholder="Dê um nome simples à sua ideia" autoComplete="off" /></label>
    <label htmlFor="idea-summary">Sua ideia em uma frase<textarea id="idea-summary" value={summary} onChange={e=>{setSummary(e.target.value);setMessage("");}} maxLength={5000} required disabled={saving} placeholder="Escreva do seu jeito: o que você gostaria de mudar?" aria-describedby="idea-note" /></label>
    <p id="idea-note" className={styles.support}>{record?.status === "SHARED" ? "Salvar uma alteração retira a cópia pública. Você decide se quer compartilhar novamente." : "Salvar não publica. Você escolhe se quer compartilhar ou desenvolver depois."}</p>
    {error && <p role="alert" className={styles.error}>{error}</p>}
    {message && <p role="status" className={styles.message}>{message}</p>}
    <div className={styles.actions}><Button type="submit" disabled={saving||!ready}>{saving ? "Aguarde…" : record ? "Salvar alterações" : "Salvar ideia privada"}</Button>{record && <Button variant="secondary" type="button" disabled={saving||!ready||(record.status === "SHARED"&&!dirty)} onClick={()=>void action("share")}>{record.status === "SHARED" && !dirty ? "Já está compartilhada" : dirty && record.status === "SHARED" ? "Salvar e compartilhar novamente" : "Compartilhar ideia"}</Button>}</div>
    {record?.status === "SHARED" && <div className={styles.actions}><Link href={`/ideias/${record.id}`}>Ver cópia pública ↗</Link><Button variant="tertiary" type="button" disabled={saving} onClick={()=>void action("unshare")}>Tornar privada</Button></div>}
    <p className={styles.support}>Não entra em cálculos nem em planos. Não precisa de checklist para continuar sendo uma ideia.</p>
   </form>
   <aside className={styles.aside}><h2>Quer dar o próximo passo?</h2><p>Uma proposta explica como fazer a mudança acontecer: medida, pessoas afetadas, riscos, fontes e financiamento.</p><Button variant="secondary" type="button" disabled={saving||!ready} onClick={()=>void action("develop")}>Desenvolver em proposta <Icon name="arrow"/></Button><p className={styles.support}>Vamos salvar sua ideia antes. Depois você escolhe ajuda da IA ou preenchimento manual. Nada é publicado automaticamente.</p><Link href="/painel/ideias">Voltar às minhas ideias</Link></aside>
  </div>
 </div>;
}
