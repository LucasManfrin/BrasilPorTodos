"use client";
import Link from "next/link";
import { Button, Icon } from "@/components/ui";
import { Skeleton, EmptyState } from "@/components/page-kit";
import { useAuth } from "@/features/auth/provider";
import { usePanelData } from "./panel-data";
import { PanelHero, StatusChip } from "./kit";
import styles from "./panel.module.css";
const metrics = [["ideas", "Ideias", "/painel/ideias"], ["policies", "Propostas", "/painel/propostas"], ["plans", "Planos", "/painel/planos"], ["sources", "Fontes", "/painel/fontes"]] as const;
export function PanelDashboard() {
  const { user } = useAuth();
  const { summaries, ideas, loading, refresh } = usePanelData();
  const draft = ideas.filter(idea => idea.status === "PRIVATE" || idea.status === "SHARED").sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
  const completed = draft?.checklist.filter(row => row.complete).length ?? 0;
  const required = draft?.checklist.length ?? 0;
  const percent = required ? Math.round(completed / required * 100) : null;
  const failed = Object.values(summaries).some(row => row?.error);
  return <div className={styles.workspace}>
    <PanelHero title={`Seu espaço, ${user?.name?.split(" ")[0] ?? "vamos começar"}.`} description="Comece uma ideia, reúna fontes e compare escolhas. Seus rascunhos continuam privados até você decidir compartilhar." action={<Button href="/painel/ideias/nova">Criar ideia <Icon name="edit" /></Button>} />
    {loading ? <Skeleton /> : <div className={styles.metrics}>{metrics.map(([kind, label, href]) => <Link key={kind} href={href} className={styles.metric}><span>{label}</span><strong>{summaries[kind]?.total ?? "—"}</strong><span>Ver meus registros <Icon name="arrow" /></span></Link>)}</div>}
    {failed && <div className={styles.notice} role="status"><p>Alguns totais não carregaram. Um traço significa indisponível, não zero.</p><Button variant="secondary" onClick={refresh}>Tentar novamente</Button></div>}
    <div className={styles.dashboardGrid}><section className={styles.resume}>
      <h2>Continue de onde parou.</h2>
      {loading ? <Skeleton /> : draft ? <><StatusChip>Ideia em construção</StatusChip><h3>{draft.title}</h3><p>{draft.summary}</p>{percent != null && <><label htmlFor="draft-progress">{completed} de {required} itens para virar completa · {percent}%</label><progress id="draft-progress" max={100} value={percent} /></>}<p className={styles.meta}>Ideia atualizada mais recentemente entre os {ideas.length} registros consultados.</p><Button href={`/painel/ideias/${draft.id}`}>Retomar ideia <Icon name="arrow" /></Button></> : summaries.ideas?.error ? <p>Não foi possível consultar suas ideias. Use a tentativa acima ou abra Minhas ideias.</p> : <EmptyState title="Sua primeira ideia começa com uma frase." description="Você não precisa chegar com todos os números. Escreva do seu jeito e complete aos poucos." href="/painel/ideias/nova" action="Começar uma ideia" />}
    </section><section className={styles.shortcuts}><h2>O próximo passo é seu.</h2><Link href="/painel/planos/novo"><Icon name="layers" /><div><h3>Monte um plano</h3><p>Combine versões publicadas e confira o impacto do conjunto.</p></div><Icon name="arrow" /></Link><Link href="/painel/fontes"><Icon name="chart" /><div><h3>Traga uma fonte</h3><p>Cadastre um link que ajude a conferir sua proposta.</p></div><Icon name="arrow" /></Link><Link href="/painel/contextos"><Icon name="edit" /><div><h3>Explique um dado</h3><p>Registre evidências, alternativas e o que ainda não se sabe.</p></div><Icon name="arrow" /></Link></section></div>
    {user?.role === "ADMIN" && <section className={styles.notice}><h2>Cuide do espaço.</h2><div className={styles.actions}><Button href="/painel/admin" variant="secondary">Administração</Button><Button href="/painel/ideias/moderacao" variant="secondary">Moderar ideias</Button><Button href="/painel/contextos/revisao" variant="secondary">Revisar contextos</Button></div></section>}
  </div>;
}
