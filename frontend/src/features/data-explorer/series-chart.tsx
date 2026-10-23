"use client";

import { useId, useMemo, useState, type KeyboardEvent, type PointerEvent } from "react";
import { formatCompact, formatExact, referenceLabel, selectCalendarPeriod, type DataPoint, type Trend } from "@/lib/data-format";
import styles from "./indicators.module.css";

export function SeriesChart({ points, name, unit = "", frequency = "", trend, large = false }: {
  points: DataPoint[];
  name: string;
  unit?: string;
  frequency?: string;
  trend?: Trend;
  large?: boolean;
}) {
  const id = useId().replaceAll(":", "");
  const [active, setActive] = useState<number | null>(null);
  const chart = useMemo(() => {
    const valid = selectCalendarPeriod(points, "max").filter(point => Number.isFinite(Number(point.value)) && Number.isFinite(new Date(point.reference_date).getTime()));
    if (!valid.length) return null;
    // Number is used only to draw the series, never for fiscal arithmetic or changes.
    const values = valid.map(point => Number(point.value));
    const min = Math.min(...values), max = Math.max(...values);
    const firstTime = new Date(valid[0].reference_date).getTime(), lastTime = new Date(valid.at(-1)!.reference_date).getTime();
    const coordinates = valid.map((point, index) => ({ point, x: lastTime === firstTime ? 200 : 12 + (new Date(point.reference_date).getTime() - firstTime) / (lastTime - firstTime) * 376, y: max === min ? 65 : 116 - (values[index] - min) / (max - min) * 100 }));
    const line = coordinates.map(({ x, y }) => `${x},${y}`).join(" ");
    return { coordinates, line, area: `M${coordinates[0].x},124 L${line.replaceAll(" ", " L")} L${coordinates.at(-1)!.x},124 Z`, minPoint: valid[values.indexOf(min)], maxPoint: valid[values.indexOf(max)] };
  }, [points]);
  if (!chart) return <p className={styles.chartMissing}>Histórico ainda indisponível. Dados ausentes não são zero.</p>;
  const last = chart.coordinates.at(-1)!;
  const selected = active === null ? null : chart.coordinates[Math.min(active, chart.coordinates.length - 1)];
  function inspect(event: PointerEvent<SVGSVGElement>) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width * 400;
    let nearest = 0;
    chart!.coordinates.forEach((point, index) => { if (Math.abs(point.x - x) < Math.abs(chart!.coordinates[nearest].x - x)) nearest = index; });
    setActive(nearest);
  }
  function navigate(event: KeyboardEvent<SVGSVGElement>) {
    if (!["ArrowLeft", "ArrowRight", "Home", "End", "Escape"].includes(event.key)) return;
    event.preventDefault();
    if (event.key === "Escape") { setActive(null); return; }
    setActive(previous => event.key === "Home" ? 0 : event.key === "End" ? chart!.coordinates.length - 1 : Math.max(0, Math.min(chart!.coordinates.length - 1, (previous ?? chart!.coordinates.length - 1) + (event.key === "ArrowLeft" ? -1 : 1))));
  }
  return (
    <figure className={`${styles.chart} ${large ? styles.chartLarge : ""}`}>
      <span id={`${id}-hint`} className="sr-only">Passe o ponteiro ou toque para consultar. Use as setas do teclado para percorrer as observações.</span>
      <svg className={styles.chartSvg} viewBox="0 0 400 138" preserveAspectRatio="none" role="img" tabIndex={0}
        aria-label={`${name}. Último valor: ${formatExact(last.point.value, unit)}, ${referenceLabel(last.point.reference_date, frequency)}. ${trend?.label ?? ""} Escala ajustada ao período.`}
        aria-describedby={`${id}-hint${selected ? ` ${id}-tooltip` : ""}`}
        onPointerMove={inspect} onPointerDown={inspect} onPointerLeave={event => { if (event.pointerType !== "touch") setActive(null); }}
        onFocus={() => setActive(chart.coordinates.length - 1)} onBlur={() => setActive(null)} onKeyDown={navigate}>
        <defs><linearGradient id={`${id}-fill`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="currentColor" stopOpacity=".22" /><stop offset="100%" stopColor="currentColor" stopOpacity=".015" /></linearGradient></defs>
        <path d="M12 124h376" className={styles.chartBaseline} />
        <path d={chart.area} fill={`url(#${id}-fill)`} />
        <polyline points={chart.line} pathLength="1" className={styles.chartLine} />
        <circle cx={last.x} cy={last.y} r="4" fill="currentColor" />
        {selected && <><path d={`M${selected.x} 12v112`} className={styles.chartGuide} /><circle cx={selected.x} cy={selected.y} r="5" className={styles.chartPoint} /></>}
      </svg>
      {selected && <div id={`${id}-tooltip`} className={styles.chartTooltip} role="tooltip" style={{ left: `${Math.max(24, Math.min(76, selected.x / 4))}%` }}><strong>{formatExact(selected.point.value, unit)}</strong><span>{referenceLabel(selected.point.reference_date, frequency)}</span></div>}
      <figcaption className={styles.chartCaption}><span>{referenceLabel(chart.coordinates[0].point.reference_date, frequency)}</span><span>{referenceLabel(last.point.reference_date, frequency)}</span></figcaption>
      <div className={styles.chartRange}><span>Mín. {formatCompact(chart.minPoint.value, unit)}</span><span>Máx. {formatCompact(chart.maxPoint.value, unit)}</span></div>
    </figure>
  );
}
