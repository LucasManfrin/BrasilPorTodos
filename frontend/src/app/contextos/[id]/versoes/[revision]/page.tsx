import { EmptyState } from "@/components/page-kit";
import { BackToCatalog } from "@/components/public-reading";
import { PublicContextDetail } from "@/features/contexts/public-list";
export default async function Page({ params }: { params: Promise<{ id: string; revision: string }> }) {
  const { id, revision } = await params;
  const value = /^\d+$/.test(revision) ? Number(revision) : 0;
  return <main id="conteudo" tabIndex={-1} className="internal-page"><div className="wide-container page-body"><BackToCatalog href="/contextos">Contextos publicados</BackToCatalog>{Number.isInteger(value) && value >= 1 && value <= 2147483647 ? <PublicContextDetail id={id} revision={value} /> : <EmptyState title="Esta versão não existe." description="O número informado não é uma versão válida. Consulte os contextos publicados para continuar." href="/contextos" action="Ver contextos" />}</div></main>;
}
