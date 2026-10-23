"use client";
import { useEffect, useRef, useState } from "react";
import { Icon } from "./ui";

export function CountUp({
  value,
  suffix = "",
}: {
  value: number;
  suffix?: string;
}) {
  const element = useRef<HTMLSpanElement>(null);
  const [shown, setShown] = useState(value);
  useEffect(() => {
    if (
      !element.current ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    )
      return;
    let frame = 0;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        const update = (now: number) => {
          const progress = Math.min((now - start) / 850, 1);
          setShown(Math.round(value * (1 - (1 - progress) ** 3)));
          if (progress < 1) frame = requestAnimationFrame(update);
        };
        frame = requestAnimationFrame(update);
      },
      { threshold: 0.4 },
    );
    observer.observe(element.current);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value]);
  return (
    <span
      ref={element}
      aria-label={`${value}${suffix}`}
      style={{
        display: "inline-block",
        minWidth: `${String(value).length + suffix.length * 2}ch`,
      }}
    >
      <span aria-hidden="true">
        {shown}
        {suffix}
      </span>
    </span>
  );
}

export function HomePlayground() {
  const [spending, setSpending] = useState(60);
  const [revenue, setRevenue] = useState(30);
  const savings = 10;
  const net = revenue + savings - spending;
  const total = revenue + savings + spending;
  const width = ((revenue + savings) / total) * 100;
  return (
    <div className="playground-scene">
      <div className="shape-diamond" aria-hidden="true" />
      <div className="playground">
        <div className="playground-top">
          <span>
            <Icon name="chart" /> Seu plano, na conta
          </span>
          <span className="demo-tag">Exemplo interativo</span>
        </div>
        <div className="playground-title">
          <h2>
            Uma ideia muda
            <br />a conta inteira.
          </h2>
          <span className="year-tag">1 ano</span>
        </div>
        <p className="playground-hint">
          Arraste e veja o que precisa compensar.
        </p>
        <label className="slider-label" htmlFor="demo-spending">
          <span>
            Investir em serviços <strong>R$ {spending} bi</strong>
          </span>
          <input
            id="demo-spending"
            type="range"
            min="0"
            max="100"
            step="1"
            value={spending}
            aria-valuetext={`${spending} bilhões de reais de nova despesa`}
            onChange={(e) => setSpending(Number(e.target.value))}
          />
        </label>
        <label className="slider-label" htmlFor="demo-revenue">
          <span>
            Arrecadar mais <strong>R$ {revenue} bi</strong>
          </span>
          <input
            id="demo-revenue"
            type="range"
            min="0"
            max="100"
            step="1"
            value={revenue}
            aria-valuetext={`${revenue} bilhões de reais de nova receita`}
            onChange={(e) => setRevenue(Number(e.target.value))}
          />
        </label>
        <div className="saving-row">
          <span>Economizar em outros gastos</span>
          <strong>R$ {savings} bi</strong>
        </div>
        <div className="demo-balance" aria-live="polite" aria-atomic="true">
          <span>
            {net < 0
              ? "Ainda falta compensar"
              : net > 0
                ? "Saldo positivo dessas medidas"
                : "Essas medidas se equilibram"}
          </span>
          <strong>
            {net < 0 ? "−" : net > 0 ? "+" : ""} R$ {Math.abs(net)}{" "}
            <small>bi</small>
          </strong>
        </div>
        <div
          className="demo-track"
          role="img"
          aria-label={`Entradas: ${revenue + savings} bilhões. Saídas: ${spending} bilhões.`}
        >
          <span style={{ width: `${width}%` }} />
          <span style={{ width: `${100 - width}%` }} />
        </div>
        <div className="balance-legend">
          <span>Receitas + economias</span>
          <span>Novas despesas</span>
        </div>
        <p className="demo-disclaimer">
          Valores fictícios, só para experimentar. Isso soma escolhas; não prevê
          a economia nem representa o orçamento brasileiro.
        </p>
      </div>
      <span className="scene-caption" aria-hidden="true">
        Mais clareza. Menos chute.
      </span>
    </div>
  );
}
