"use client";

import Link from "next/link";
import styles from "./route.module.css";

export default function GraphError({ retry, reset }: { error: Error & { digest?: string }; retry?: () => void; reset?: () => void }) {
  return (
    <main id="conteudo" tabIndex={-1} className={styles.graphPage}>
      <section className={styles.failure} role="alert" aria-labelledby="graph-error-title">
        <div className={styles.mark} aria-hidden="true">↗</div>
        <h1 id="graph-error-title">Essa conexão ficou pelo caminho.</h1>
        <p>Não conseguimos abrir a rede. Tente carregar novamente ou volte à lista de conjuntos publicados.</p>
        <div className={styles.actions}>
          <button type="button" className="button" onClick={() => (retry ?? reset ?? (() => window.location.reload()))()}>Tentar de novo</button>
          <Link className="button button-secondary" href="/grafos">Ver conjuntos</Link>
        </div>
      </section>
    </main>
  );
}
