import { serverApi } from "@/lib/server-api";
import type { Indicator } from "@/lib/indicator-types";
import type { Baseline, FiscalComposition, FiscalInterest, FunctionalSpending, GeneralGovernment } from "@/lib/types";
import { PageHero } from "@/components/page-kit";
import type { CollectionStatus } from "@/components/collection-status";
import { BrazilDashboard } from "@/features/data-explorer/brazil-dashboard";
async function allIndicators(): Promise<Indicator[] | null> {
    const items: Indicator[] = [];
    for (let page = 1;; page++) {
        const result = await serverApi<Indicator[]>(`indicators?page_size=100&page=${page}`);
        if (!result)
            return null;
        const known = new Set(items.map(item => item.id));
        const fresh = result.data.filter(item => !known.has(item.id));
        items.push(...fresh);
        const total = result.pagination?.total ?? items.length;
        if (items.length >= total)
            return items;
        if (!fresh.length)
            return null;
    }
}
export default async function Page() {
    const [items, status, baseline, composition, interest, spending, government] = await Promise.all([allIndicators(), serverApi<CollectionStatus>("indicators/collection/status"), serverApi<Baseline>("indicators/baseline/current"), serverApi<FiscalComposition>("indicators/baseline/composition"), serverApi<FiscalInterest>("indicators/baseline/interest"), serverApi<FunctionalSpending>("indicators/spending/functions"), serverApi<GeneralGovernment>("indicators/government/general")]);
    return <main id="conteudo" tabIndex={-1} className="internal-page"><PageHero title="O Brasil. Antes da ideia." description="Veja o ponto de partida. Entenda o número, a mudança e o que ele ainda não explica."/><div className="wide-container page-body"><BrazilDashboard items={items} status={status?.data ?? null} fiscal={baseline?.data.fiscal} composition={composition?.data ?? null} interest={interest?.data ?? null} spending={spending?.data ?? null} government={government?.data ?? null}/></div></main>;
}
