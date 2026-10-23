import type { Baseline } from "@/lib/types";
import { date } from "@/lib/format";
import { indicatorValue } from "@/lib/indicator-types";
import { FiscalBaselinePanel } from "./fiscal-baseline-panel";
export function BaselinePanel({
  baseline,
  preserved = true,
  showFiscal = true,
}: {
  baseline?: Baseline | null;
  preserved?: boolean;
  showFiscal?: boolean;
}) {
  if (!baseline && !preserved) return null;
  if (!baseline)
    return (
      <p className="notice">
        Esta versão é anterior à base histórica. Nenhum dado atual foi atribuído
        retroativamente.
      </p>
    );
  return (
    <details className="baseline-panel">
      <summary>
        <span className="baseline-marker" aria-hidden="true" />
        Brasil de referência{" "}
        <span className="muted">
          · {date(baseline.captured_at)} ·{" "}
          {baseline.status === "EMPTY" ? "sem dados" : "base parcial"}
        </span>
      </summary>
      <p>
        {preserved
          ? "Estes dados ficam preservados nesta versão."
          : "Estes são os últimos dados salvos. A base será capturada ao criar o rascunho."}{" "}
        Cada série tem seu próprio período. A base dá contexto; o cálculo fiscal
        continua mostrando o efeito das medidas.
      </p>
      <div className="baseline-values">
        {baseline.observations.map((row) => (
          <div key={row.code}>
            <strong>{row.name}</strong>
            <span>
              {indicatorValue(row.observation.value)} {row.unit}
            </span>
            <small>
              Ref. {date(row.observation.reference_date)} ·{" "}
              {row.observation.source.institution}
            </small>
          </div>
        ))}
      </div>
      {showFiscal && baseline.fiscal && (
        <FiscalBaselinePanel fiscal={baseline.fiscal} preserved={preserved} />
      )}
      {baseline.missing.length > 0 && (
        <p className="muted">Ainda falta: {baseline.missing.join("; ")}.</p>
      )}
      <small>
        Identificador da base: <code>{baseline.id.slice(0, 12)}</code>
      </small>
    </details>
  );
}
