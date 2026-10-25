"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/provider";
import { collectionTimestamp } from "@/lib/collection-time";
export type CollectionStatus = {
  interval_hours: number;
  schedule?: {
    enabled: boolean; daily_at: string; timezone: string;
    retry_minutes: number; next_attempt_at: string | null;
  };
  last_run: {
    status: string;
    started_at: string;
    finished_at: string | null;
    series: Record<string, { status: string }>;
  } | null;
  skipped?: boolean;
  accepted?: boolean;
};
export function CollectionStatusBar({
  initial,
  compact = false,
  sourceCount = 0,
  names = {},
}: {
  initial: CollectionStatus | null;
  compact?: boolean;
  sourceCount?: number;
  names?: Record<string, string>;
}) {
  const { user, request } = useAuth(),
    router = useRouter();
  const [status, setStatus] = useState(initial),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  async function refresh() {
    setBusy(true);
    setMessage("");
    try {
      const result = await request<CollectionStatus>(
        "admin/indicators/collect",
        { method: "POST" },
      );
      setStatus(result.data);
      if (result.data.skipped)
        setMessage(
          "Última tentativa recente. Uma nova consulta é liberada após uma hora.",
        );
      else if (result.data.accepted) {
        setMessage(
          "Consulta solicitada. A coleta ocorre em segundo plano; os dados salvos continuam disponíveis.",
        );
        const previous = result.data.last_run?.started_at;
        for (let attempt = 0; attempt < 12; attempt++) {
          await new Promise((resolve) => setTimeout(resolve, 5000));
          const progress = await request<CollectionStatus>(
            "indicators/collection/status",
          );
          setStatus(progress.data);
          if (
            progress.data.last_run?.started_at !== previous &&
            progress.data.last_run?.finished_at
          ) {
            setMessage(
              progress.data.last_run.status === "SUCCESS"
                ? "Fontes consultadas. Dados atualizados quando houve nova divulgação."
                : "Consulta concluída com algumas fontes indisponíveis. Dados anteriores preservados.",
            );
            break;
          }
          if (attempt === 11)
            setMessage(
              "A coleta segue em segundo plano. Recarregue a página para acompanhar o estado das fontes.",
            );
        }
      }
      router.refresh();
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Não deu para atualizar. Os dados salvos continuam disponíveis.",
      );
    } finally {
      setBusy(false);
    }
  }
  if (compact) return (
    <section className="collection-bar collection-compact" aria-label="Estado dos dados salvos">
      <p className="collection-line">
        <span aria-hidden="true">{status?.last_run?.status === "SUCCESS" ? "✓" : status?.last_run?.status === "RUNNING" ? "↻" : "!"}</span>
        <span>Dados salvos · {status?.last_run ? <>última tentativa {collectionTimestamp(status.last_run.finished_at ?? status.last_run.started_at, status.schedule?.timezone)}</> : "consulta ainda não informada"} · {sourceCount} {sourceCount === 1 ? "fonte" : "fontes"}</span>
      </p>
      <div className="collection-controls">
        <button className="button secondary" title="Recarrega os dados salvos; não inicia outra coleta." onClick={() => router.refresh()}>Recarregar</button>
        <details>
          <summary>Estado das fontes</summary>
          <div className="collection-outcomes">
            <p>A referência aparece em cada card. Consultar uma fonte não muda a data do dado.</p>
            {status?.schedule?.enabled && <p>Consulta diária programada às {status.schedule.daily_at}, no horário de {status.schedule.timezone === "America/Sao_Paulo" ? "São Paulo" : status.schedule.timezone}. O Docker precisa estar ativo. Se o computador estava desligado, a consulta pendente é retomada ao iniciar.</p>}
            {status?.last_run ? <ul>{Object.entries(status.last_run.series).map(([code, result]) => <li key={code}>
              {names[code] ?? (code === "rtn-composition" ? "Composição fiscal do Governo Central" : code)}: {result.status === "SUCCESS" ? "consultada" : result.status === "NO_DATA" ? "sem observações no período" : "indisponível; dados anteriores preservados"}
            </li>)}</ul> : <p>O coletor consulta as fontes uma vez ao dia quando está ativo.</p>}
            {user?.role === "ADMIN" && <button className="button secondary" disabled={busy} onClick={refresh}>{busy ? "Consultando fontes…" : "Consultar fontes agora"}</button>}
            {message && <p role="status">{message}</p>}
          </div>
        </details>
      </div>
    </section>
  );
  return (
    <section className="collection-bar">
      <div>
        <strong>Dados salvos, fontes conferíveis.</strong>
        <p>
          {status?.last_run ? (
            <>
              Última tentativa:{" "}
              {collectionTimestamp(status.last_run.finished_at ?? status.last_run.started_at, status.schedule?.timezone)}{" "}
              ·{" "}
              {status.last_run.status === "SUCCESS"
                ? "fontes disponíveis"
                : status.last_run.status === "RUNNING"
                  ? "coleta em andamento"
                  : "algumas fontes indisponíveis"}
              .
            </>
          ) : (
            "O coletor consulta as fontes uma vez ao dia quando está ativo."
          )}{" "}
          A data do dado aparece em cada card.
        </p>
        {status?.schedule?.enabled && <p>Consulta diária às {status.schedule.daily_at} ({status.schedule.timezone === "America/Sao_Paulo" ? "São Paulo" : status.schedule.timezone}), enquanto o Docker estiver ativo. Consultas perdidas são retomadas na inicialização.</p>}
      </div>
      <button
        className="button secondary"
        disabled={busy}
        onClick={user?.role === "ADMIN" ? refresh : () => router.refresh()}
      >
        {busy
          ? "Consultando fontes…"
          : user?.role === "ADMIN"
            ? "Consultar fontes agora"
            : "Recarregar dados salvos"}
      </button>
      {status?.last_run && (
        <details>
          <summary>Estado das fontes</summary>
          <ul>
            {Object.entries(status.last_run.series).map(([code, result]) => (
              <li key={code}>
                {code === "rtn-composition" ? "Composição fiscal do Governo Central" : code}:{" "}
                {result.status === "SUCCESS"
                  ? "consultada"
                  : result.status === "NO_DATA"
                    ? "sem observações no período"
                    : "indisponível; dados anteriores preservados"}
              </li>
            ))}
          </ul>
        </details>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
