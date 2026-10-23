import { ReadingLayout, PublicationMeta, BackToCatalog } from "@/components/public-reading";
import { EmptyState } from "@/components/page-kit";
import reading from "@/components/public-reading.module.css";
import Link from "next/link";
import { ImpactAnalysis } from "@/features/ideas/impact-analysis";
import detailStyles from "@/features/ideas/impact-analysis.module.css";
import { fiscalMetadataText } from "@/lib/fiscal-compatibility";
import { PageHero } from "@/components/page-kit";
import { CardActions } from "@/components/duplicate-button";
import { BaselinePanel } from "@/components/baseline-panel";
import { serverApi } from "@/lib/server-api";
import { fundings, impacts, money } from "@/lib/format";
import type { HistoryItem, Policy } from "@/lib/types";

export default async function PolicyPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ versao?: string }>;
}) {
  const { slug } = await params;
  const { versao } = await searchParams;
  const base = `policies/${encodeURIComponent(slug)}`;
  const [result, history] = await Promise.all([
    serverApi<Policy>(
      versao ? `${base}/versions/${encodeURIComponent(versao)}` : base,
    ),
    serverApi<HistoryItem[]>(`${base}/versions`),
  ]);
  if (!result) return <main id="conteudo" tabIndex={-1} className="internal-page"><div className="wide-container page-body"><EmptyState error title="Esta versão não está disponível." description="Ela pode não estar publicada ou o serviço está indisponível. Tente abrir o catálogo novamente." href="/propostas" action="Voltar ao catálogo" /></div></main>;
  const policy=result.data;
  const version=policy.version;
  return (<main id="conteudo" tabIndex={-1} className={`internal-page ${reading.page}`}>
        <PageHero
          title={version.title}
          description={version.summary}
          tone="yellow"
          breadcrumb="Propostas"
        />
        <div className="wide-container page-body">
          <BackToCatalog href="/propostas">Todas as propostas</BackToCatalog>
          <PublicationMeta author={policy.author.name} version={version.version_number}><span>Implementação {version.implementation_start}–{version.implementation_end}</span></PublicationMeta>
          <ReadingLayout items={[{id:"problema",label:"Problema"},{id:"medida",label:"Medida proposta"},{id:"impacto",label:"Impacto fiscal"},{id:"financiamento",label:"Financiamento"},{id:"fontes",label:"Fontes"},{id:"historico",label:"Histórico"}]}>

          <BaselinePanel baseline={version.baseline_snapshot} />
          {policy.solidity && <p className="notice">{policy.solidity.level === "LEGACY" ? "Publicação anterior ao fluxo de proposta completa; não foi reclassificada automaticamente." : `Documentação: ${policy.solidity.score ?? 0} de ${policy.solidity.max_score} critérios — fontes ${policy.solidity.has_sources ? "vinculadas" : "ausentes"}, financiamento ${policy.solidity.funding_defined ? "declarado" : "pendente"}, revisão técnica não realizada.`} A presença desses itens não comprova as estimativas nem avalia a posição política.</p>}
          {version.proposal_details && <>
            {version.proposal_details.assisted_fields.length > 0 && <p className="notice">Assistido por IA · os textos foram confirmados pelo autor. A IA não calcula o impacto nem publica a proposta.</p>}
            <div className={detailStyles.details}>
              <section><h2>Quem ganha</h2><p>{version.proposal_details.beneficiaries || "Ainda não informado."}</p></section>
              <section><h2>Quem poderia perder</h2><p>{version.proposal_details.adversely_affected || "Ainda não informado."}</p></section>
              <section><h2>O que poderia dar errado</h2><p>{version.proposal_details.risks || "Riscos ainda não descritos."}</p></section>
            </div>
          </>}
          {version.proposal_details?.level === "COMPLETE" && <ImpactAnalysis slug={policy.slug} version={version.version_number} />}
          {policy.status === "ARCHIVED" && (
            <p className="notice">
              Proposta arquivada: {policy.archive_reason}
            </p>
          )}
          <section id="problema">
            <h2>Problema</h2>
            <p className="preserve">{version.problem}</p>
          </section>
          <section id="medida">
            <h2>Solução proposta</h2>
            <p className="preserve">{version.proposal}</p>
          </section>
          <section id="impacto">
            <h2>Impacto fiscal</h2>
            {version.financial_impact_status === "NOT_ESTIMATED" ? (
              <p className="notice">
                Impacto ainda não estimado. Isso não significa custo zero.
              </p>
            ) : version.financial_impact_status === "NOT_APPLICABLE" ? (
              <p>
                O autor declara que o impacto não se aplica:{" "}
                {version.impact_justification}
              </p>
            ) : (
              <div className="table-scroll">
                <table>
                  <caption>Estimativas declaradas pelo autor</caption>
                  <thead>
                    <tr>
                      <th>Ano</th>
                      <th>Tipo</th>
                      <th>Valor</th>
                      <th>Premissa</th>
                      <th>Recorte fiscal declarado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {version.impacts.map((impact, index) => (
                      <tr key={index}>
                        <th scope="row">{impact.year}</th>
                        <td>{impacts[impact.impact_type]}</td>
                        <td>{money(impact.amount)}</td>
                        <td>{impact.description}</td>
                        <td><ul>{fiscalMetadataText(impact).map((text, i) => <li key={i}>{["Governo", "Contagem", "Preços", "Componente", "Período"][i]}: {text}</li>)}</ul></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          <section id="financiamento">
            <h2>Financiamento</h2>
            {version.fundings.length ? (
              <ul>
                {version.fundings.map((funding, index) => (
                  <li key={index}>
                    <strong>{fundings[funding.funding_type]}</strong>
                    {funding.amount ? ` · ${money(funding.amount)}` : ""}
                    {funding.year ? ` · ${funding.year}` : ""}
                    <p>{funding.description}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Nenhuma declaração de financiamento cadastrada.</p>
            )}
          </section>
          <section id="fontes">
            <h2>Fontes e uso</h2>
            {!version.sources.length && <p className="notice">Esta versão não tem fontes vinculadas. A ausência fica visível para você conferir os limites da proposta.</p>}
            {version.sources.map((evidence) => (
              <article className="citation" key={evidence.source.id}>
                <h3>
                  <a
                    href={evidence.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {evidence.source.title} ↗
                  </a>
                </h3>
                <p>
                  {evidence.source.institution} · {evidence.usage_description}
                </p>
                <small>Referência preservada na publicação desta versão.</small>
              </article>
            ))}
          </section>
          <section id="historico">
            <h2>Histórico público</h2>
            <nav aria-label="Versões desta proposta">
              {history?.data.map((item) => (
                <Link
                  className="version-link"
                  key={item.id}
                  href={`/propostas/${slug}?versao=${item.version_number}`}
                >
                  Versão {item.version_number}
                </Link>
              ))}
            </nav>
          </section>
          <CardActions
            kind="policies"
            slug={policy.slug}
            versionNumber={version.version_number}
          />
          </ReadingLayout>
        </div>
      </main>
    );
}
