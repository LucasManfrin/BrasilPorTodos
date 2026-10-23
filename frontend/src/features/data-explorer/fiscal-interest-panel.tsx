"use client";
import { useRouter } from "next/navigation";
import type { FiscalBaseline, FiscalInterest } from "@/lib/types";
import { dateLabel, formatCompact, formatExact } from "@/lib/data-format";
import { interestBalanceLabel, interestState } from "@/lib/fiscal-interest";
import styles from "./fiscal-interest.module.css";

export function FiscalInterestPanel({ fiscal, interest }: { fiscal?: FiscalBaseline | null; interest?: FiscalInterest | null }) {
  const router = useRouter();
  const state = interestState(fiscal, interest);
  if (state !== "READY" || !interest?.totals || !interest.reconciliation) return <details className={styles.panel}><summary>Quando os juros entram na conta</summary><p>{state === "MISMATCH" ? "Os juros e a conta primária foram consultados com referências diferentes. Recarregue para conferir o mesmo ano e recorte." : "Ainda faltam doze meses compatíveis de saldo primário, juros e saldo nominal abaixo da linha. Dado ausente não significa zero."}</p>{interest?.missing.length ? <ul>{interest.missing.map((text, index) => <li key={index}>{text}</li>)}</ul> : null}<button className="button secondary" onClick={() => router.refresh()}>Recarregar dados salvos</button></details>;
  const { totals, reconciliation } = interest;
  const values = [
    { name: "Saldo primário · abaixo da linha", value: totals.primary_balance, kind: "primary" as const, basis: "Caixa" },
    { name: "Juros líquidos · com sinal", value: totals.interest, kind: "interest" as const, basis: "Competência" },
    { name: "Saldo nominal", value: totals.nominal_balance, kind: "nominal" as const, basis: "Critério misto" },
  ];
  return <details className={styles.panel}><summary>Quando os juros entram na conta · {interest.year}</summary><p>Governo Central, abaixo da linha: os dados do Banco Central chegam aqui pelo Tesouro. É outra forma de apurar a conta; o saldo primário pode diferir do RTN mostrado acima.</p><dl className={styles.values}>{values.map(item => <div key={item.kind}><dt>{item.name}</dt><dd><strong title={formatExact(item.value, "R$")}>{formatCompact(item.value, "R$")}</strong><span>{interestBalanceLabel(item.value, item.kind)}</span><small>{item.basis}</small></dd></div>)}</dl><p className={styles.equation}>Saldo primário + juros com o sinal publicado = saldo nominal.</p><p>O primário é medido em caixa e os juros em competência: o saldo nominal combina esses critérios. Valores positivos e negativos são preservados. Esta conta observada não é somada às propostas nem projeta a dívida.</p><details className={styles.method}><summary>Fonte, valores exatos e método</summary><dl className={styles.exact}>{values.map(item => <div key={item.kind}><dt>{item.name}</dt><dd>{formatExact(item.value, "R$")}</dd></div>)}</dl><p>{interest.methodology}</p><p>Diferença anual de reconciliação: {formatExact(reconciliation.annual_difference, "R$")}. Cada mês aceita até {formatExact(reconciliation.monthly_tolerance, "R$")} de diferença por arredondamento; a soma anual conserva a diferença real, sem ajustar os números.</p><p>Referência: {dateLabel(interest.period_start)} a {dateLabel(interest.period_end)} · coletado em {dateLabel(interest.collected_at)} · método {interest.method_version}.</p>{interest.source && <p><a href={interest.source.url} target="_blank" rel="noopener noreferrer">{interest.source.title} ↗</a> · {interest.source.institution}. {interest.source.attribution} · <a href={interest.source.license_url} target="_blank" rel="noopener noreferrer">{interest.source.license}</a></p>}<ul>{interest.limitations.map((text, index) => <li key={index}>{text}</li>)}</ul></details></details>;
}
