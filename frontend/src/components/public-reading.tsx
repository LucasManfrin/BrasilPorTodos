import type { ReactNode } from "react";
import Link from "next/link";
import styles from "./public-reading.module.css";

export type ReadingItem = { id: string; label: string };
export function ReadingLayout({ items, children, label = "Nesta página" }: { items: ReadingItem[]; children: ReactNode; label?: string }) {
  return <div className={styles.layout}><aside className={styles.aside}><details open className={styles.index}><summary>{label}</summary><nav aria-label={label}>{items.map((item, i) => <a key={item.id} href={`#${item.id}`}><span aria-hidden="true">{String(i + 1).padStart(2, "0")}</span>{item.label}</a>)}</nav></details><p className={styles.asideNote}>Confira as fontes.<br />Conheça os limites.<br />Tire suas conclusões.</p></aside><div className={styles.document}>{children}</div></div>;
}
export function PublicationMeta({ author, version, children }: { author: string; version: number; children?: ReactNode }) {
  return <div className={styles.meta}><span className={styles.avatar} aria-hidden="true">{author.slice(0, 1).toUpperCase()}</span><div><strong>{author}</strong><span>Versão {version} · publicação preservada</span></div>{children}</div>;
}
export function BackToCatalog({ href, children }: { href: string; children: ReactNode }) { return <Link className={styles.back} href={href}>← {children}</Link>; }
export function ReadingSkeleton() { return <div className={styles.skeleton} role="status" aria-label="Carregando conteúdo"><span /><div><span /><span /><span /></div></div>; }
