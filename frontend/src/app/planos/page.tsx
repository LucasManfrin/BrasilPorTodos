import reading from "@/components/public-reading.module.css";
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
        title="Junte ideias. Teste a conta."
        description="Um plano mostra as escolhas juntas: medidas, custos, economias e o que ainda falta resolver."
        tone="green"
        breadcrumb="Planos Brasil"
        action={<Button href="/painel/planos/novo">Criar plano</Button>}
      />
      <div className="wide-container page-body">
        <section className={reading.overview} aria-label="Como ler os planos"><div><h2>O conjunto importa.</h2><p>Uma medida sozinha conta uma parte da história. No plano, você vê quais propostas foram combinadas e o efeito fiscal declarado para cada ano.</p></div><ul><li>Versões específicas, preservadas na publicação.</li><li>Custos, receitas e lacunas à vista.</li><li>Simulação das medidas, sem prever o futuro do país.</li></ul></section>
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
