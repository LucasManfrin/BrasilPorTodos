import { serverApi } from "@/lib/server-api";
import type { Policy } from "@/lib/types";
import { categories } from "@/lib/format";
import { ContributionCard } from "@/components/contribution-card";
import {
  PageHero,
  FilterBar,
  EmptyState,
  Pagination,
} from "@/components/page-kit";
import { Button } from "@/components/ui";
export default async function Policies({
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
        ([k, v]) => ["q", "category", "author", "year"].includes(k) && v,
      ),
    ),
  } as Record<string, string>);
  const result = await serverApi<Policy[]>(`policies?${query}`);
  const items = result?.data.filter(
    (item) => process.env.NODE_ENV === "development" || !item.is_example,
  );
  const filtered =
    page > 1 ||
    [params.q, params.category, params.author, params.year].some(Boolean);
  return (
    <main id="conteudo" tabIndex={-1} className="internal-page">
      <PageHero
        title="Propostas completas. Escolhas às claras."
        description="Quem ganha? Quanto custa? De onde vem o dinheiro? Uma proposta precisa encarar essas perguntas."
        tone="yellow"
        breadcrumb="Propostas"
        action={<Button href="/painel/propostas/nova">Preparar proposta completa</Button>}
      />
      <div className="wide-container page-body">
        <FilterBar
          path="/propostas"
          query={params}
          categories={categories}
          advanced
        />
        <div className="feed-heading">
          <p>
            Propostas completas primeiro, por fontes e financiamento declarado.
            Esse critério documental não comprova os efeitos nem a qualidade da ideia.
          </p>
          <Button href="/ideias" variant="secondary">Ver ideias em construção</Button>
        </div>
        {!result ? (
          <EmptyState
            error
            title="Não deu para abrir o feed."
            description="Tente mais uma vez em instantes."
            href="/propostas"
            action="Tentar de novo"
          />
        ) : items?.length ? (
          <>
            <div className="data-grid contribution-grid">
              {items.map((item) => (
                <ContributionCard key={item.id} kind="policies" item={item} />
              ))}
            </div>
            <Pagination
              path="/propostas"
              query={query}
              page={page}
              total={result.pagination?.total ?? 0}
            />
          </>
        ) : (
          <EmptyState
            title={
              filtered
                ? "Nenhuma proposta com esses filtros."
                : "Ainda não tem proposta aqui."
            }
            description={
              filtered
                ? "Tente outra busca ou limpe os filtros para ver o catálogo."
                : "Já tem uma medida definida? Detalhe custos, financiamento e fontes para publicar uma proposta completa."
            }
            href={filtered ? "/propostas" : "/painel/propostas/nova"}
            action={filtered ? "Limpar filtros" : "Preparar proposta completa"}
          />
        )}
      </div>
    </main>
  );
}
