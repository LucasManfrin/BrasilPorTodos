import { PageHero } from "@/components/page-kit";
import styles from "@/features/data-explorer/dashboard.module.css";
export default function Loading() { return <main className="internal-page" id="conteudo" tabIndex={-1}><PageHero title="O Brasil. Antes da ideia." description="Os dados estão chegando. Cada número vem com sua referência."/><div className="wide-container page-body" role="status" aria-label="Carregando indicadores"><div className={styles.skeleton}>{[0, 1, 2, 3].map(index => <div key={index} aria-hidden="true"><span /><span /><span /></div>)}</div></div></main>; }
