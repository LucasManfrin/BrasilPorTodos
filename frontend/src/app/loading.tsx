import { ReadingSkeleton } from "@/components/public-reading";
export default function Loading() {
  return <main id="conteudo" tabIndex={-1} className="internal-page" aria-busy="true"><div className="wide-container page-body"><p role="status">Um instante. Estamos juntando os dados.</p><ReadingSkeleton /></div></main>;
}
