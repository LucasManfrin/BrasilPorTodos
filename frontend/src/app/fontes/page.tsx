import { Suspense } from "react";
import { serverApi } from "@/lib/server-api";
import type { Source } from "@/lib/types";
import type { CollectionStatus } from "@/components/collection-status";
import { EmptyState, PageHero, Skeleton } from "@/components/page-kit";
import { SourcesDirectory } from "@/features/data-explorer/sources-directory";
import { loadDirectoryPages, type DirectoryIndicator } from "@/features/data-explorer/source-helpers";

// One request timestamp is reused by server rendering and client hydration.
async function requestClock() { return Date.now(); }

export default async function Sources() {
  const [sources, indicators, collection, now] = await Promise.all([
    loadDirectoryPages<Source>("sources", path => serverApi<Source[]>(path)),
    loadDirectoryPages<DirectoryIndicator & { id: string }>("indicators", path => serverApi<(DirectoryIndicator & { id: string })[]>(path)),
    serverApi<CollectionStatus>("indicators/collection/status"),
    requestClock(),
  ]);
  return (
    <main id="conteudo" tabIndex={-1} className="internal-page">
      <PageHero title="Dá para conferir." description="O caminho até cada número e argumento. Abra a referência e veja como ela foi usada." tone="night" breadcrumb="Fontes" />
      {sources === null || indicators === null ? <div className="wide-container page-body"><EmptyState error title="O diretório não carregou por completo." description="As referências salvas continuam preservadas. Tente novamente para consultar a lista e seus indicadores vinculados." href="/fontes" action="Tentar de novo" /></div>
        : <Suspense fallback={<div className="wide-container page-body"><Skeleton /></div>}><SourcesDirectory sources={sources} indicators={indicators} collection={collection?.data ?? null} development={process.env.NODE_ENV === "development"} now={now} /></Suspense>}
    </main>
  );
}
