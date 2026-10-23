import { BackToCatalog } from "@/components/public-reading";
import { PublicContextDetail } from "@/features/contexts/public-list";
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <main id="conteudo" tabIndex={-1} className="internal-page"><div className="wide-container page-body"><BackToCatalog href="/contextos">Contextos publicados</BackToCatalog><PublicContextDetail id={id} /></div></main>;
}
