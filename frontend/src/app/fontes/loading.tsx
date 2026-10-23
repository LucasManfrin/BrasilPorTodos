import { PageHero } from "@/components/page-kit";
import styles from "@/features/data-explorer/sources.module.css";
export default function Loading() {
  return <main className="internal-page" id="conteudo" tabIndex={-1}><PageHero title="Dá para conferir." description="Carregando referências, instituições e estado das consultas." tone="night" breadcrumb="Fontes"/><div className="wide-container page-body" role="status" aria-label="Carregando fontes"><div className={styles.loadingRows}>{[0,1,2,3].map(index=><div key={index} aria-hidden="true"><span/><span/><span/></div>)}</div></div></main>;
}
