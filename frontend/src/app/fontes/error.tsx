"use client";
import styles from "@/features/data-explorer/dashboard.module.css";
export default function ErrorPage({reset}:{reset:()=>void}){return <main id="conteudo" tabIndex={-1}><div className={styles.error} role="alert"><h2>As referências deram uma pausa.</h2><p>Não conseguimos carregar esta tela. Os registros salvos continuam preservados.</p><button className="button" onClick={reset}>Tentar de novo</button></div></main>;}
