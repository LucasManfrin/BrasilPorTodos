"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Card, Icon } from "@/components/ui";
import { compactParts, formatCompact, formatExact, getTrend, referenceLabel, selectCalendarPeriod } from "@/lib/data-format";
import type { Indicator } from "@/lib/indicator-types";
import { SeriesChart } from "./series-chart";
import styles from "./indicators.module.css";

const themes: Record<string, string> = { FISCAL: "Contas públicas", ECONOMY: "Economia", SOCIAL: "Trabalho e renda", PUBLIC_SPENDING: "Gastos públicos" };
const shortNames: Record<string, string> = { "renda-trabalho-real": "Renda real do trabalho", informalidade: "Informalidade", "participacao-forca-trabalho": "Participação no trabalho", desocupacao: "Desemprego", "ipca-mensal": "Inflação · IPCA", "ipca-12-meses": "Inflação em 12 meses", "selic-meta": "Juros · Selic", "divida-bruta-pib": "Dívida bruta / PIB", "divida-liquida-pib": "Dívida líquida / PIB", "rtn-resultado-primario": "Resultado primário", "rtn-receita-liquida": "Receita líquida", "rtn-despesa-primaria": "Despesa primária", "pib-nominal-trimestral": "PIB nominal", "atividade-ibc-br": "Atividade econômica" };
const chartThemes: Record<string, string> = { desocupacao: styles.chartBlue, "ipca-mensal": styles.chartBlue, "selic-meta": styles.chartNight, "divida-bruta-pib": styles.chartNight, "divida-liquida-pib": styles.chartNight, "rtn-receita-liquida": styles.chartBlue, "rtn-despesa-primaria": styles.chartBlue, "rtn-resultado-primario": styles.chartBlue, "atividade-ibc-br": styles.chartBlue, "pib-nominal-trimestral": styles.chartNight };

function AnimatedValue({ value, unit }: { value: string; unit: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [frame, setFrame] = useState<{ value: string; label: string; parts: ReturnType<typeof compactParts> } | null>(null);
  useEffect(() => {
    const node = ref.current;
    const target = Number(value);
    if (!node || !Number.isFinite(target) || !window.IntersectionObserver || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let request = 0;
    let disposed = false;
    const observer = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      observer.disconnect();
      const start = performance.now();
      function step(now: number) {
        if (disposed) return;
        const progress = Math.min(1, (now - start) / 540);
        // Animation alone uses Number; the completed value always comes from the original decimal string.
        const drawnValue = progress === 1 ? value : target * (1 - Math.pow(1 - progress, 3));
        setFrame({ value, label: formatCompact(drawnValue, unit), parts: compactParts(drawnValue, unit) });
        if (progress < 1) request = requestAnimationFrame(step);
      }
      request = requestAnimationFrame(step);
    }, { threshold: .25 });
    observer.observe(node);
    return () => { disposed = true; observer.disconnect(); cancelAnimationFrame(request); };
  }, [value, unit]);
  const parts = frame?.value === value ? frame.parts : compactParts(value, unit);
  const finalParts = compactParts(value, unit);
  return <span ref={ref} aria-hidden="true" data-value-label={frame?.value === value ? frame.label : formatCompact(value, unit)} className={styles.valueParts}><span className={styles.valueSizer}><span>{finalParts.number}</span>{finalParts.unit && <small className={styles.numberUnit}>{finalParts.unit}</small>}</span><span className={styles.valueAnimating}><span className={styles.numberDigits}>{parts.number}</span>{parts.unit && <small className={styles.numberUnit}>{parts.unit}</small>}</span></span>;
}

export function IndicatorTile({ item, onOpen, variant = "standard", featured = false, highlighted = false, horizontal = false, context }: {
  item: Indicator;
  onOpen: (item: Indicator) => void;
  variant?: "standard" | "blue" | "yellow" | "green" | "night";
  featured?: boolean;
  highlighted?: boolean;
  horizontal?: boolean;
  context?: string;
}) {
  const latest = item.latest;
  const trend = getTrend(item);
  const shortName = shortNames[item.code] ?? item.name;
  const exact = latest ? formatExact(latest.value, item.unit) : "Sem observações";
  const balanceLabel = latest && item.code === "rtn-resultado-primario" ? !/[1-9]/.test(latest.value) ? "Equilíbrio primário" : latest.value.startsWith("-") ? "Déficit primário" : "Superávit primário" : null;
  const debtProportion = latest && item.code === "divida-bruta-pib" && Number.isFinite(Number(latest.value)) ? Number(latest.value) : null;
  return (
    <Card className={`${styles.tile} ${styles[variant]} ${variant === "standard" ? chartThemes[item.code] ?? styles.chartBlue : ""} ${featured ? styles.featured : ""} ${highlighted ? styles.withHighlight : ""} ${horizontal ? styles.horizontal : ""}`} category={item.category}>
      <button type="button" className={`icon-button ${styles.openOverlay}`} onClick={() => onOpen(item)} aria-label={`Abrir detalhes de ${item.name}`} />
      <div className={styles.tileTop}><span className={styles.themeChip}>{themes[item.category] ?? item.category}</span>{highlighted && <span className={styles.highlightBadge}>Em destaque</span>}<button type="button" className={`icon-button ${styles.help}`} onClick={() => onOpen(item)} aria-label={`Entender ${item.name}`}>?</button></div>
      <div className={styles.tileMain}>
        <div className={styles.tileCopy}>
          <h2 className={styles.tileTitle} title={item.name}>{shortName}</h2>
          {latest ? <><p className={styles.value} title={exact}><span className="sr-only">{exact}</span><AnimatedValue value={latest.value} unit={item.unit} /></p>{(balanceLabel || item.unit === "R$") && <p className={styles.unit}>{balanceLabel ? `${balanceLabel} · ` : ""}{item.unit === "R$" ? (item.code === "renda-trabalho-real" ? "Renda corrigida pela inflação" : "Reais nominais") : ""}</p>}<p className={styles.trend}><span aria-hidden="true">{trend.symbol}</span> {trend.label}</p></> : <p className={styles.missing}>Sem observações disponíveis. Nenhum valor foi preenchido como zero.</p>}
          {latest && <p className={styles.reference}>Ref. {referenceLabel(latest.reference_date, item.frequency)}{["desocupacao", "renda-trabalho-real", "informalidade", "participacao-forca-trabalho"].includes(item.code) ? " · trimestre móvel" : ""}</p>}
        </div>
        <SeriesChart points={selectCalendarPeriod(item.series ?? [], "5y")} name={item.name} unit={item.unit} frequency={item.frequency} trend={trend} />
      </div>
      {featured && context && <p className={styles.tileContext}>{context}</p>}
      {debtProportion !== null && variant === "green" && <div className={styles.proportion} role="img" aria-label={`Dívida bruta: ${exact}. Barra visual de zero a 100% do PIB; a dívida pode ultrapassar 100%.`}><div className={styles.proportionTrack}><span className={styles.proportionFill} style={{ width: `${Math.max(0, Math.min(100, debtProportion))}%` }} /></div><span>Proporção do PIB · eixo visual até 100%</span></div>}
      <div className={styles.tileFooter}><button type="button" className={`icon-button ${styles.sourceAction}`} onClick={() => onOpen(item)}>{latest?.source.institution ?? "Fonte e método"}<Icon name="arrow" /></button><span className={styles.dataFlag}>{latest?.source.is_example ? "Exemplo fictício" : latest?.source.source_type === "OFFICIAL" ? "Dado oficial" : "Fonte informada"}</span></div>
      <div className={styles.tileActions}><button type="button" className={`icon-button ${styles.methodAction}`} onClick={() => onOpen(item)}>Fonte e método</button><Button href={`/painel/propostas/nova?indicador=${encodeURIComponent(item.code)}`} variant="secondary" className={styles.proposalAction}>Usar em proposta<Icon name="edit" /></Button></div>
    </Card>
  );
}
