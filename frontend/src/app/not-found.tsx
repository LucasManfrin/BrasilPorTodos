import { Button } from "@/components/ui";
import styles from "@/components/public-reading.module.css";
export default function NotFound() {
  return <main id="conteudo" tabIndex={-1} className={styles.statusPage}><div className="wide-container"><div className={styles.statusBox}><div className={styles.statusArt} aria-hidden="true">404</div><div><h1>Essa página saiu do mapa.</h1><p>Confira o endereço ou encontre uma ideia para continuar explorando.</p><div className="actions"><Button href="/propostas">Explorar propostas</Button><Button href="/" variant="secondary">Voltar ao início</Button></div></div></div></div></main>;
}
