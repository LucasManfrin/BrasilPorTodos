"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { usePanelData } from "./panel-data";
import styles from "./panel.module.css";
const links = [
  ["/painel", "Meu painel", ""], ["/painel/ideias", "Ideias", "ideas"],
  ["/painel/propostas", "Propostas", "policies"], ["/painel/planos", "Planos", "plans"],
  ["/painel/fontes", "Fontes", "sources"], ["/painel/contextos", "Contextos", "contexts"],
] as const;
export function PanelTabs() {
  const path = usePathname();
  const { summaries } = usePanelData();
  return <nav className={styles.tabs} aria-label="Painel"><div className={styles.tabsTrack}>{links.map(([href, title, kind]) => {
    const active = href === "/painel" ? path === href : path === href || path.startsWith(`${href}/`);
    const count = kind ? summaries[kind]?.total : null;
    return <Link key={href} href={href} aria-current={active ? "page" : undefined}>{title}{count != null && <span className={styles.count}>{count}</span>}</Link>;
  })}</div></nav>;
}
