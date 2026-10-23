import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { GraphGuide } from "@/features/graphs/guide";
import { graphPath } from "@/features/graphs/helpers";
import type { GraphRecord } from "@/features/graphs/types";
import { GraphWorkspace } from "@/features/graphs/workspace";
import { serverApi } from "@/lib/server-api";
import styles from "../../../route.module.css";

export const metadata: Metadata = {
  title: "Versão preservada da rede — BrasilPorTodos",
  description: "Uma fotografia publicada da rede, com as versões exatas de suas relações, fontes e revisões.",
};

export default async function GraphVersionPage({ params }: { params: Promise<{ id: string; revision: string }> }) {
  const { id, revision } = await params;
  const value = /^\d+$/.test(revision) ? Number(revision) : 0;
  if (!graphPath(id, value)) notFound();
  const initialRecord = await serverApi<GraphRecord>(`graphs/${id}/versions/${value}`);
  return (
    <main id="conteudo" tabIndex={-1} className={styles.graphPage}>
      <GraphWorkspace initial={null} initialId={id} initialRevision={value} initialRecord={initialRecord?.data ?? null} />
      <GraphGuide />
    </main>
  );
}
