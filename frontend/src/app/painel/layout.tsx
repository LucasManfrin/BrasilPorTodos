import { Suspense } from "react";
import { AuthGate } from "@/features/auth/gate";
import { GuidanceConsentProvider } from "@/features/ideas/consent";
import { PanelDataProvider } from "@/features/panel/panel-data";
import { PanelTabs } from "@/features/panel/tabs";
import styles from "@/features/panel/panel.module.css";
export default function PrivateLayout({ children }: { children: React.ReactNode }) {
  return <main id="conteudo" tabIndex={-1} className={`page ${styles.shell}`}><AuthGate><GuidanceConsentProvider><Suspense fallback={<p role="status">Abrindo seu painel…</p>}><PanelDataProvider><PanelTabs />{children}</PanelDataProvider></Suspense></GuidanceConsentProvider></AuthGate></main>;
}
