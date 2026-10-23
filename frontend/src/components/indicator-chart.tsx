"use client";
import { useState } from "react";
import { Sparkline, type SeriesPoint } from "./sparkline";
export function IndicatorChart({
  points,
  name,
}: {
  points: SeriesPoint[];
  name: string;
}) {
  const [period, setPeriod] = useState(12);
  const uniqueMonths = points.filter(
    (p, i) =>
      p.reference_date.slice(0, 7) !==
      points[i + 1]?.reference_date.slice(0, 7),
  );
  const monthIndex = (reference: string) =>
    Number(reference.slice(0, 4)) * 12 + Number(reference.slice(5, 7)) - 1;
  const latestReference = uniqueMonths.at(-1)?.reference_date;
  const cutoff = latestReference ? monthIndex(latestReference) - period + 1 : null;
  const displayedPoints =
    period && cutoff !== null
      ? uniqueMonths.filter((point) => monthIndex(point.reference_date) >= cutoff)
      : points;
  return (
    <section className="card history-chart">
      <div className="chart-heading">
        <h2>O número no tempo</h2>
        <div
          className="chart-period"
          role="group"
          aria-label="Período do gráfico"
        >
          {[6, 12, 24, 0].map((n) => (
            <button
              key={n}
              onClick={() => setPeriod(n)}
              aria-pressed={period === n}
            >
              {n ? `${n} meses` : "Disponível"}
            </button>
          ))}
        </div>
      </div>
      <Sparkline
        name={name}
        points={displayedPoints}
        large
      />
      <p className="muted">
        Última revisão de cada referência. Escala ajustada; períodos sem dado
        ficam ausentes. A tabela abaixo guarda também as revisões anteriores.
      </p>
    </section>
  );
}
