import styles from "./route.module.css";

export default function Loading() {
  return (
    <main id="conteudo" tabIndex={-1} className={styles.graphPage}>
      <div className={styles.pending} role="status" aria-live="polite" aria-busy="true">
        <h1>Abrindo as conexões.</h1>
        <p>Buscando o conjunto publicado e suas versões preservadas.</p>
        <div className={styles.pendingNetwork} aria-hidden="true">
          <svg viewBox="0 0 900 440" focusable="false"><path d="M150 170 330 100 470 230 690 120M150 170 270 340 470 230 710 330 690 120M330 100 690 120" />{[[150,170],[330,100],[470,230],[690,120],[270,340],[710,330]].map(([cx,cy]) => <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="11" />)}</svg>
        </div>
      </div>
    </main>
  );
}
