import { PageHero } from "@/components/page-kit";
import { serverApi } from "@/lib/server-api";
import { ContextList } from "@/features/contexts/public-list";
import type { ContextRecord } from "@/features/contexts/types";
export default async function Page() {
  const initial = await serverApi<ContextRecord[]>("contexts?page=1&page_size=20");
  return <main id="conteudo" tabIndex={-1} className="internal-page"><PageHero title="O que pode explicar o número?" breadcrumb="Contextos" description="Leia o dado, as explicações possíveis e o que ainda falta saber. Toda análise publicada preserva suas fontes e a revisão humana." /><div className="wide-container page-body"><ContextList initial={initial} /></div></main>;
}
