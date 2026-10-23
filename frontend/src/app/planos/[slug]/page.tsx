import { ReadingLayout, PublicationMeta, BackToCatalog } from "@/components/public-reading";
import { EmptyState } from "@/components/page-kit";
import reading from "@/components/public-reading.module.css";
import Link from "next/link";
import { PageHero } from "@/components/page-kit";
import { CardActions } from "@/components/duplicate-button";
import { BaselinePanel } from "@/components/baseline-panel";
import { FiscalResult } from "@/components/fiscal";
import { serverApi } from "@/lib/server-api";
import type { HistoryItem, Plan } from "@/lib/types";

export default async function PlanPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ versao?: string }>;
}) {
  const { slug } = await params;
  const { versao } = await searchParams;
  const base = `plans/${encodeURIComponent(slug)}`;
  const [result, history] = await Promise.all([
    serverApi<Plan>(
      versao ? `${base}/versions/${encodeURIComponent(versao)}` : base,
    ),
    serverApi<HistoryItem[]>(`${base}/versions`),
  ]);
  if (!result) return <main id="conteudo" tabIndex={-1} className="internal-page"><div className="wide-container page-body"><EmptyState error title="Esta versão não está disponível." description="Ela pode não estar publicada ou o serviço está indisponível. Tente abrir o catálogo novamente." href="/planos" action="Voltar ao catálogo" /></div></main>;
  const plan=result.data;
  return (<main id="conteudo" tabIndex={-1} className={`internal-page ${reading.page}`}>
        <PageHero
          title={plan.version.title}
          description={plan.version.summary}
          tone="green"
          breadcrumb="Planos Brasil"
        />
        <div className="wide-container page-body">
          <BackToCatalog href="/planos">Todos os planos</BackToCatalog>
          <PublicationMeta author={plan.author.name} version={plan.version.version_number}><span>{plan.version.start_year}–{plan.version.end_year}</span></PublicationMeta>
          <ReadingLayout items={[{id:"visao",label:"Visão do plano"},{id:"composicao",label:"Medidas incluídas"},{id:"resultado",label:"Resultado fiscal"},{id:"historico",label:"Histórico"}]}>

          <BaselinePanel baseline={plan.version.baseline_snapshot} />
          {plan.status === "ARCHIVED" && (
            <p className="notice">Plano arquivado: {plan.archive_reason}</p>
          )}
          <section id="visao">
            <h2>Visão</h2>
            <p className="preserve">{plan.version.vision}</p>
          </section>
          <section id="composicao">
            <h2>Propostas deste plano</h2>
            <ol className={reading.composition}>
              {plan.version.policies.map((item) => (
                <li key={item.policy_version_id}>
                  <Link
                    href={`/propostas/${item.slug}?versao=${item.version_number}`}
                  >
                    {item.title} · v{item.version_number}
                  </Link>
                  {!item.is_enabled && (
                    <span className="muted"> · Desativada no cálculo</span>
                  )}
                </li>
              ))}
            </ol>
            <p className="muted">
              Cada item referencia a versão utilizada na publicação deste plano.
            </p>
          </section>
          <section id="resultado"><h2>A conta das medidas</h2>{plan.version.simulation ? <FiscalResult result={plan.version.simulation} /> : <p className="notice">Esta versão não tem uma simulação publicada. Ausência de estimativa não significa custo zero.</p>}</section>
          <section id="historico">
            <h2>Histórico público</h2>
            <nav aria-label="Versões deste plano">
              {history?.data.map((item) => (
                <Link
                  className="version-link"
                  key={item.id}
                  href={`/planos/${slug}?versao=${item.version_number}`}
                >
                  Versão {item.version_number}
                </Link>
              ))}
            </nav>
          </section>
          <Link href="/metodologia">
            Conheça a metodologia e suas limitações
          </Link>
          <CardActions
            kind="plans"
            slug={plan.slug}
            versionNumber={plan.version.version_number}
          />
          </ReadingLayout>
        </div>
      </main>
    );
}
