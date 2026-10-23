import { date } from "@/lib/format";
import { indicatorValue } from "@/lib/indicator-types";

export type SeriesPoint = {
  reference_date: string;
  value: string;
  revision: number;
};
export function Sparkline({
  points,
  name,
  large = false,
}: {
  points: SeriesPoint[];
  name: string;
  large?: boolean;
}) {
  if (points.length < 2)
    return (
      <p className="chart-missing">Mais observações vão formar o histórico.</p>
    );
  const values = points.map((p) => Number(p.value));
  const min = Math.min(...values),
    max = Math.max(...values);
  const polyline = values
    .map(
      (v, i) =>
        `${8 + (i / (values.length - 1)) * 384},${max === min ? 55 : 102 - ((v - min) / (max - min)) * 94}`,
    )
    .join(" ");
  return (
    <figure className={`sparkline ${large ? "chart-large" : ""}`}>
      <svg
        viewBox="0 0 400 110"
        role="img"
        aria-label={`${name}: ${date(points[0].reference_date)} a ${date(points.at(-1)!.reference_date)}, mínimo ${indicatorValue(String(min))}, máximo ${indicatorValue(String(max))}. Escala ajustada ao período.`}
      >
        <path d="M8 104h384" stroke="currentColor" opacity=".2" />
        <polyline
          points={polyline}
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          vectorEffect="non-scaling-stroke"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <figcaption>
        <span>{date(points[0].reference_date)}</span>
        <span>{date(points.at(-1)!.reference_date)}</span>
      </figcaption>
    </figure>
  );
}
