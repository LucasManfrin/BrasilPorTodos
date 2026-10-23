import { ReadingLayout, BackToCatalog } from "@/components/public-reading";
import reading from "@/components/public-reading.module.css";
import { formatCompact, formatExact } from "@/lib/data-format";
import Link from "next/link";
import { IndicatorChart } from "@/components/indicator-chart";
import { IndicatorContexts } from "@/features/contexts/indicator-contexts";
import { PageHero, EmptyState } from "@/components/page-kit";
import { serverApi } from "@/lib/server-api";
import { date } from "@/lib/format";
import { indicatorValue, type Indicator } from "@/lib/indicator-types";
export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ code: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { code } = await params;
  const { page: rawPage } = await searchParams;
  const page = Math.max(1, Number(rawPage) || 1);
  const result = await serverApi<Indicator>(
    `indicators/${encodeURIComponent(code)}?page=${page}&page_size=20`,
  );
  if (!result) return <main id="conteudo" tabIndex={-1} className="internal-page"><div className="wide-container page-body"><EmptyState error title="Indicador indisponível" description="A série pode estar inativa ou o serviço indisponível. Volte ao catálogo e tente novamente." href="/brasil" action="Voltar ao Brasil Atual" /></div></main>;
  const item = result.data;
  return (
    <main id="conteudo" tabIndex={-1} className="internal-page">
      <PageHero
        title={item.name}
        description={item.description}
        breadcrumb="Brasil Atual"
      />
      <div className="wide-container page-body">
        <BackToCatalog href="/brasil">Brasil Atual</BackToCatalog>
        <ReadingLayout items={[{id:"serie",label:"Série histórica"},{id:"metodo",label:"Como interpretar"},{id:"observacao",label:"Último dado"},{id:"revisoes",label:"Histórico e revisões"}]}>
        <section id="serie"><h2>A série no tempo</h2><IndicatorChart name={item.name} points={item.series ?? []} />
        <dl className={reading.definition}>
          <div>
          <dt>Unidade</dt>
          <dd>{item.unit}</dd>
          </div><div><dt>Abrangência</dt>
          <dd>{item.scope}</dd>
          </div><div><dt>Periodicidade</dt>
          <dd>
            {item.code === "desocupacao"
              ? "Trimestre móvel, divulgado mensalmente"
              : ({
                  DAILY: "Diária",
                  MONTHLY: "Mensal",
                  QUARTERLY: "Trimestral",
                  YEARLY: "Anual",
                  IRREGULAR: "Irregular",
                }[item.frequency] ?? item.frequency)}
          </dd>
          </div></dl></section>
        <section id="metodo">
          <h2>Como interpretar</h2>
          <p>{item.methodology}</p>
          {item.base_year && <p>Ano-base: {item.base_year}</p>}
        </section>
        {item.latest ? (
          <section id="observacao">
            <h2>Última observação</h2>
            <p className={reading.value} title={formatExact(item.latest.value, item.unit)}>{formatCompact(item.latest.value, item.unit)}</p><p>Valor exato: {formatExact(item.latest.value, item.unit)}</p>
            <p>
              Referência: {date(item.latest.reference_date)}. Coleta:{" "}
              {date(item.latest.retrieved_at)}. Revisão {item.latest.revision}.
            </p>
            <p>
              Fonte:{" "}
              <a
                href={item.latest.source.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {item.latest.source.title} — {item.latest.source.institution} ↗
              </a>
            </p>
            <p className="muted">
              Termos registrados: {item.latest.provenance.license}. Dados
              oficiais conservam sua licença; a MIT do código não substitui
              esses termos.
            </p>
          </section>
        ) : (
          <p className="empty">
            Ainda não há observações importadas para esta série.
          </p>
        )}
        <IndicatorContexts indicatorCode={item.code} latestObservationId={item.latest?.id} />
        <section id="revisoes">
          <h2>Histórico e revisões</h2>
          <p>
            Correções acrescentam revisões. As observações anteriores continuam
            disponíveis.
          </p>
          <div className="table-scroll">
            <table>
              <caption>Observações com referência, coleta e fonte</caption>
              <thead>
                <tr>
                  <th scope="col">Referência</th>
                  <th scope="col">Valor ({item.unit})</th>
                  <th scope="col">Revisão</th>
                  <th scope="col">Coleta</th>
                  <th scope="col">Fonte / motivo</th>
                </tr>
              </thead>
              <tbody>
                {item.history?.map((row) => (
                  <tr key={row.id}>
                    <th scope="row">{date(row.reference_date)}</th>
                    <td>{indicatorValue(row.value)}</td>
                    <td>{row.revision}</td>
                    <td>{date(row.retrieved_at)}</td>
                    <td>
                      <a
                        href={row.source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {row.source.institution} ↗
                      </a>
                      <br />
                      {row.revision_reason.replace(
                        "API oficial SGS",
                        "API oficial",
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <nav className="pagination" aria-label="Histórico do indicador">
            {page > 1 && <Link href={`?page=${page - 1}`}>Anterior</Link>}
            <span>Página {page}</span>
            {page * 20 < (result.pagination?.total ?? 0) && (
              <Link href={`?page=${page + 1}`}>Próxima</Link>
            )}
          </nav>
        </section>
        </ReadingLayout>
      </div>
    </main>
  );
}
