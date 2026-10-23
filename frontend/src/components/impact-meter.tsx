import { money } from "@/lib/format";

export function cents(value: string): bigint {
  const negative = value.startsWith("-");
  const [whole, fraction = ""] = value.replace(/^-/, "").split(".");
  const result =
    BigInt(whole || "0") * BigInt(100) +
    BigInt(fraction.padEnd(2, "0").slice(0, 2));
  return negative ? -result : result;
}
export function decimal(value: bigint): string {
  const abs = value < BigInt(0) ? -value : value;
  return `${value < BigInt(0) ? "-" : ""}${abs / BigInt(100)}.${String(abs % BigInt(100)).padStart(2, "0")}`;
}
export function ImpactMeter({
  positive = "0",
  negative = "0",
  partial = false,
  compact = false,
}: {
  positive?: string;
  negative?: string;
  partial?: boolean;
  compact?: boolean;
}) {
  const inflow = cents(positive);
  const outflow = cents(negative);
  const total = inflow + outflow;
  const width =
    total > BigInt(0) ? Number((inflow * BigInt(10000)) / total) / 100 : 50;
  const net = inflow - outflow;
  const label = partial
    ? "Estimativa parcial"
    : net < BigInt(0)
      ? "A compensar"
      : net > BigInt(0)
        ? "Saldo positivo"
        : "Saldo zero";
  if (partial && total === BigInt(0))
    return (
      <div className="impact-meter">
        <span className="impact-label attention">
          Sem estimativa disponível
        </span>
        <p className="muted">
          Não estimado não significa custo zero. Confira as premissas.
        </p>
      </div>
    );
  return (
    <div className={`impact-meter ${compact ? "compact" : ""}`}>
      <div className="impact-heading">
        <span
          className={`impact-label ${partial || net < BigInt(0) ? "attention" : ""}`}
        >
          {label}
        </span>
        <strong>{money(decimal(net))}</strong>
      </div>
      <div
        className="impact-track"
        role="img"
        aria-label={`Receitas e economias: ${money(positive)}. Despesas e receitas reduzidas: ${money(negative)}.`}
      >
        <span style={{ width: `${width}%` }} />
        <span style={{ width: `${100 - width}%` }} />
      </div>
      <p className="muted">
        Saldo incremental das medidas{" "}
        {partial ? "com valores informados" : "estimadas"}. Não é o saldo do
        país.
      </p>
    </div>
  );
}
