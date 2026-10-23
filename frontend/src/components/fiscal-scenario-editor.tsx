"use client";
import type { Baseline } from "@/lib/types";
import {
  createFiscalScenario, invalidateScenarioReview, scenarioIsReviewed,
  reconcileScenarioYears, scenarioYearsMatch,
  type FiscalScenario,
} from "@/lib/fiscal-scenario";
import { date } from "@/lib/format";
import styles from "./fiscal-scenario.module.css";

export function FiscalScenarioEditor({
  scenario, baseline, start, end, disabled, onChange, onConfirm, onError,
}: {
  scenario: FiscalScenario | null;
  baseline: Baseline | null;
  start: number;
  end: number;
  disabled: boolean;
  onChange: (value: FiscalScenario | null) => void;
  onConfirm: () => void;
  onError: (message: string) => void;
}) {
  const reviewed = scenarioIsReviewed(scenario);
  const baselineYear = baseline?.fiscal?.year ?? null;
  function change(value: Partial<FiscalScenario>) {
    if (scenario) onChange(invalidateScenarioReview({ ...scenario, ...value }));
  }
  function enable() {
    try { onChange(createFiscalScenario(baseline?.id ?? null, start, end)); }
    catch (error) { onError(error instanceof Error ? error.message : "Revise os anos do plano."); }
  }
  function adjustYears() {
    if (!scenario) return;
    try { onChange(reconcileScenarioYears(scenario, start, end)); }
    catch (error) { onError(error instanceof Error ? error.message : "Revise os anos do plano."); }
  }
  return (
    <fieldset className={styles.editor} disabled={disabled}>
      <legend>Como você quer ler a conta?</legend>
      <div className={styles.mode}>
        <label><input type="radio" name="fiscal-reading-mode" checked={!scenario}
          onChange={() => onChange(null)} />Somente impacto das propostas</label>
        <label><input type="radio" name="fiscal-reading-mode" checked={Boolean(scenario)}
          onChange={enable} />Comparar com cenário futuro</label>
      </div>
      {!scenario ? <p className="muted">O plano soma somente as medidas. Nenhuma receita ou despesa futura é presumida.</p> : (
        <>
          <p className="notice">Este é um cenário declarado por você, com suas premissas. Não é uma previsão oficial nem uma projeção automática do Brasil.</p>
          <p className="muted">Recorte fixo: Governo Central, caixa, preços nominais de cada ano, resultado primário sem juros e anos inteiros. A referência histórica
            {baselineYear !== null ? " de " + baselineYear : " sem ano disponível"} serve apenas de contexto.</p>
          <label>Título do cenário
            <input value={scenario.title} maxLength={200}
              onChange={(event) => change({ title: event.target.value })} />
          </label>
          <label>O que você está supondo para os próximos anos?
            <textarea value={scenario.explanation} maxLength={10000}
              onChange={(event) => change({ explanation: event.target.value })}
              placeholder="Explique as premissas de receita e despesa, sem incluir o efeito das propostas deste plano." />
          </label>
          {scenario.reference_baseline_id !== (baseline?.id ?? null) && (
            <div className="notice">
              <p>O cenário aponta para outra referência histórica. Seus valores anuais foram preservados. Adotar a base atual exige revisar e confirmar novamente.</p>
              <button type="button" className="button secondary" disabled={!baseline}
                onClick={() => change({ reference_baseline_id: baseline?.id ?? null })}>
                Adotar referência atual do rascunho
              </button>
            </div>
          )}
          {baselineYear === null && <p className="notice">Não há uma referência fiscal completa neste rascunho. Você pode salvar as premissas; a comparação depende de uma base disponível.</p>}
          {baselineYear !== null && start <= baselineYear && <p className="notice">Para o cenário futuro, todos os anos devem ser posteriores a {baselineYear}. Ajuste o período do plano.</p>}
          {!scenarioYearsMatch(scenario, start, end) && (
            <div className="notice">
              <p>Os anos do cenário diferem do período atual do plano. Nenhum valor foi alterado automaticamente. O ajuste conserva os anos mantidos, deixa novos anos sem valor e remove os que saíram do período.</p>
              <button type="button" className="button secondary" onClick={adjustYears}>Ajustar anos ao período do plano</button>
            </div>
          )}
          <p className="muted">Informe reais completos, como 1000,00, em até 30 anos. Campo vazio é ausência de estimativa; zero precisa ser informado. Não repetimos valores históricos nem aplicamos crescimento automático.</p>
          {scenario.years.map((row) => (
            <div className={styles.year} key={row.year}>
              <h3>Ano {row.year}</h3>
              <div className={styles.amounts}>
                <label>Receita primária líquida · {row.year} (R$)
                  <input inputMode="decimal" maxLength={24} value={row.net_revenue ?? ""}
                    placeholder="Valor declarado para este ano"
                    onChange={(event) => change({ years: scenario.years.map((item) => item.year === row.year ? { ...item, net_revenue: event.target.value || null } : item) })} />
                </label>
                <label>Despesa primária · {row.year} (R$)
                  <input inputMode="decimal" maxLength={24} value={row.primary_expenditure ?? ""}
                    placeholder="Valor declarado para este ano"
                    onChange={(event) => change({ years: scenario.years.map((item) => item.year === row.year ? { ...item, primary_expenditure: event.target.value || null } : item) })} />
                </label>
              </div>
              <label>Por que esses valores em {row.year}?
                <textarea value={row.justification} maxLength={5000}
                  onChange={(event) => change({ years: scenario.years.map((item) => item.year === row.year ? { ...item, justification: event.target.value } : item) })} />
              </label>
              <label>Fontes para {row.year} (opcional, uma URL por linha)
                <textarea value={row.source_urls.join("\n")} rows={2}
                  placeholder="https://..."
                  onChange={(event) => change({ years: scenario.years.map((item) => item.year === row.year ? { ...item, source_urls: event.target.value.split("\n") } : item) })} />
              </label>
            </div>
          ))}
          <div className={styles.review} role="status">
            {reviewed ? <p>Revisão confirmada em {date(scenario.reviewed_at!)}. O autor declarou que estas premissas não incluem o efeito das propostas selecionadas.</p>
              : <p>Revisão ainda não confirmada. Preencha as premissas e confira se as propostas selecionadas já estão embutidas nesses valores; contá-las de novo duplicaria o efeito.</p>}
            <p className="muted">A confirmação salva primeiro o rascunho atual. Alterar cenário, composição, período ou base exige nova revisão.</p>
          </div>
          <button type="button" className="button secondary" onClick={onConfirm}>
            Revisei: o cenário não inclui estas propostas
          </button>
        </>
      )}
    </fieldset>
  );
}
