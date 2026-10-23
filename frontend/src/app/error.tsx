"use client";
import { Button, Icon } from "@/components/ui";
import styles from "@/components/public-reading.module.css";
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main id="conteudo" tabIndex={-1} className={styles.statusPage}><div className="wide-container"><div className={styles.statusBox}><div className={styles.statusArt} aria-hidden="true"><Icon name="layers" /></div><div><h1>Uma pausa no caminho.</h1><p role="alert">Não conseguimos carregar esta página. Tente novamente. Se você estava escrevendo, as alterações ainda não salvas podem precisar ser retomadas.</p><div className="actions"><Button onClick={reset}>Tentar de novo</Button><Button variant="secondary" href="/">Voltar ao início</Button></div></div></div></div></main>;
}
