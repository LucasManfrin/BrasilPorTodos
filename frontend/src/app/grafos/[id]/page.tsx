import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { GraphGuide } from "@/features/graphs/guide";
import { graphPath } from "@/features/graphs/helpers";
import type { GraphRecord } from "@/features/graphs/types";
import { GraphWorkspace } from "@/features/graphs/workspace";
import { serverApi } from "@/lib/server-api";
import styles from "../route.module.css";

export const metadata: Metadata = {
  title: "Rede de conexões — BrasilPorTodos",
  description: "Consulte uma rede publicada, suas relações e as evidências preservadas de cada versão.",
};

export default async function GraphPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!graphPath(id)) notFound();
  const initialRecord = await serverApi<GraphRecord>(`graphs/${id}`);
  return (
    <main id="conteudo" tabIndex={-1} className={styles.graphPage}>
      <GraphWorkspace initial={null} initialId={id} initialRecord={initialRecord?.data ?? null} />
      <GraphGuide />
    </main>
  );
}
