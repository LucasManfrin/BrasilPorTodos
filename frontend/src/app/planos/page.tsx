import { serverApi } from "@/lib/server-api";
import type { Plan } from "@/lib/types";
import { ContributionCard } from "@/components/contribution-card";
import {
  PageHero,
  FilterBar,
  EmptyState,
  Pagination,
} from "@/components/page-kit";
import { Button } from "@/components/ui";
import { ContributionJourney } from "@/components/contribution-journey";
export default async function Plans({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams,
    page = Math.max(1, Number(params.page) || 1);
  const query = new URLSearchParams({
    page: String(page),
    page_size: "20",
    ...Object.fromEntries(
      Object.entries(params).filter(
        ([k, v]) => ["q", "author", "year"].includes(k) && v,
      ),
    ),
  } as Record<string, string>);
  const result = await serverApi<Plan[]>(`plans?${query}`),
    items = result?.data.filter(
      (item) => process.env.NODE_ENV === "development" || !item.is_example,
    );
  const filtered =
    page > 1 ||
    [params.q, params.category, params.author, params.year].some(Boolean);
  return (
    <main id="conteudo" tabIndex={-1} className="internal-page">
      <PageHero
        title="Combine propostas. Veja o conjunto."
        description="Reúna propostas completas já publicadas e confira juntas as medidas, os custos e o financiamento."
        tone="green"
        breadcrumb="Planos Brasil"
        action={<Button href="/painel/planos/novo">Criar plano</Button>}
      />
      <div className="wide-container page-body">
        <ContributionJourney current="plans" />
        <FilterBar path="/planos" query={params} advanced />
        {!result ? (
          <EmptyState
            error
            title="Os planos não carregaram."
            description="Tente novamente. As versões publicadas continuam preservadas."
            href="/planos"
            action="Tentar de novo"
          />
        ) : items?.length ? (
          <>
            <div className="data-grid contribution-grid">
              {items.map((item) => (
                <ContributionCard key={item.id} kind="plans" item={item} />
              ))}
            </div>
            <Pagination
              path="/planos"
              query={query}
              page={page}
              total={result.pagination?.total ?? 0}
            />
          </>
        ) : (
          <EmptyState
            title={
              filtered
                ? "Nenhum plano com esses filtros."
                : "O próximo plano pode ser seu."
            }
            description={
              filtered
                ? "Tente outra busca ou limpe os filtros para ver o catálogo."
                : "Combine propostas publicadas e veja o efeito fiscal das medidas, com suas limitações."
            }
            href={filtered ? "/planos" : "/painel/planos/novo"}
            action={filtered ? "Limpar filtros" : "Montar um plano"}
          />
        )}
      </div>
    </main>
  );
}
