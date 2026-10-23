import type { ReactNode } from "react";
import { PageHero } from "@/components/page-kit";
import styles from "./panel.module.css";
export function PanelHero({ title, description, tone = "blue", action }: { title: string; description: string; tone?: "blue" | "yellow" | "green" | "night"; action?: ReactNode }) {
  return <div className={styles.hero}><PageHero title={title} description={description} tone={tone} action={action} /></div>;
}
export function StatusChip({ children }: { children: ReactNode }) { return <span className={styles.status}><span aria-hidden="true">○</span>{children}</span>; }
