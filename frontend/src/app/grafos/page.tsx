import type { Metadata } from "next";
import { GraphGuide } from "@/features/graphs/guide";
import type { GraphSummary } from "@/features/graphs/types";
import { GraphWorkspace } from "@/features/graphs/workspace";
import { serverApi } from "@/lib/server-api";
import styles from "./route.module.css";

export const metadata: Metadata = {
  title: "Conexões — BrasilPorTodos",
  description: "Explore relações entre medidas, indicadores e pessoas. Abra fontes, condições, contrapontos e limites de cada conexão.",
};

export default async function GraphsPage() {
  const initial = await serverApi<GraphSummary[]>("graphs?page=1&page_size=20");
  return (
    <main id="conteudo" tabIndex={-1} className={styles.graphPage}>
      <GraphWorkspace initial={initial} />
      <GraphGuide />
    </main>
  );
}
