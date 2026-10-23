import type { FiscalBaseline } from "@/lib/types";
import { date, money } from "@/lib/format";
import { indicatorValue } from "@/lib/indicator-types";

export function FiscalBaselinePanel({
  fiscal,
  preserved = false,
}: {
  fiscal?: FiscalBaseline | null;
  preserved?: boolean;
}) {
  const available = fiscal?.status === "AVAILABLE" && fiscal.amounts !== null;
  const amounts = available ? fiscal.amounts : null;
  const gdp = fiscal?.gdp;
  const gdpAvailable =
    available &&
    gdp?.status === "AVAILABLE" &&
    gdp.nominal_gdp !== null &&
    gdp.year === fiscal.year;
  const ratios = gdpAvailable ? fiscal?.ratios : null;
  return (
    <section className="baseline-panel" aria-label="Referência fiscal observada">
      <h2>A conta antes das propostas.</h2>
      <p>
        {preserved
          ? "Esta referência fica preservada nesta versão."
          : "Esta é a referência fiscal nos últimos dados salvos."}{" "}
        Governo Central, em reais nominais e pelo critério de caixa. Estados e
        municípios não estão incluídos.
      </p>
      {amounts && fiscal ? (
        <>
          <p>
            <strong>Ano fechado: {fiscal.year}.</strong>{" "}
            {fiscal.period_start && fiscal.period_end && (
              <span>
                {date(fiscal.period_start)} a {date(fiscal.period_end)}.
              </span>
            )}
          </p>
          <div className="baseline-values">
            <div>
              <strong>Receita líquida</strong>
              <span className="fiscal-value">{money(amounts.net_revenue)}</span>
              <small>Depois das transferências consideradas na fonte.</small>
              {ratios && (
                <small>{indicatorValue(ratios.net_revenue_pct_gdp)}% do PIB.</small>
              )}
            </div>
            <div>
              <strong>Despesa primária</strong>
              <span className="fiscal-value">{money(amounts.primary_expenditure)}</span>
              <small>Despesa pelo critério da fonte, sem juros.</small>
              {ratios && (
                <small>{indicatorValue(ratios.primary_expenditure_pct_gdp)}% do PIB.</small>
              )}
            </div>
            <div>
              <strong>Resultado primário publicado</strong>
              <span className="fiscal-value">{money(amounts.published_primary_balance)}</span>
              <small>Positivo: superávit. Negativo: déficit.</small>
              {ratios && (
                <small>{indicatorValue(ratios.primary_balance_pct_gdp)}% do PIB.</small>
              )}
            </div>
          </div>
          <details className="indicator-method">
            <summary>Confira como a conta foi feita</summary>
            <p className="formula">Receita líquida − despesa primária</p>
            <p>
              Calculado pelos componentes: {money(amounts.calculated_primary_balance)}.
              {" "}Diferença de reconciliação: {money(amounts.reconciliation_difference)}.
              O valor publicado é mostrado separadamente e não é substituído pelo
              cálculo dos componentes.
            </p>
            <p>{fiscal.methodology}</p>
            <p>
              A referência usa os 12 meses do mesmo ano. Revisões posteriores
              geram outra base; não alteram versões já publicadas.
            </p>
          </details>
          {gdpAvailable && gdp?.nominal_gdp ? (
            <>
              <div className="baseline-values">
                <div>
                  <strong>PIB nominal do Brasil em {gdp.year}</strong>
                  <span className="fiscal-value">{money(gdp.nominal_gdp)}</span>
                  <small>Soma dos quatro trimestres das Contas Nacionais Trimestrais.</small>
                </div>
              </div>
              <details className="indicator-method">
                <summary>Entenda o percentual do PIB</summary>
                <p>
                  Comparamos as contas do Governo Central com o PIB nacional do
                  mesmo ano. Usar esse denominador não inclui estados e
                  municípios nas contas apresentadas.
                </p>
                <p>
                  A soma dos quatro trimestres é sujeita a revisão e não é a
                  divulgação anual definitiva do Sistema de Contas Nacionais.
                  A precisão da fonte é de R$ 10 mil (0,01 milhão de reais);
                  converter para reais não aumenta essa precisão.
                </p>
                <p>
                  Fonte do PIB:{" "}
                  <a href={gdp.source.url} target="_blank" rel="noopener noreferrer">
                    {gdp.source.title} ↗
                  </a>{" "}
                  · {gdp.source.institution}.{" "}
                  <a href={gdp.source.license_url} target="_blank" rel="noopener noreferrer">
                    {gdp.source.license}
                  </a>
                </p>
                {gdp.limitations.length > 0 && (
                  <ul>
                    {gdp.limitations.map((limitation) => (
                      <li key={limitation}>{limitation}</li>
                    ))}
                  </ul>
                )}
              </details>
            </>
          ) : (
            <p className="notice">
              O PIB nominal compatível ainda não está disponível. Precisamos
              dos quatro trimestres do mesmo ano para mostrar os percentuais;
              ausência não significa zero.
              {gdp && gdp.missing.length > 0 && (
                <> Ainda falta: {gdp.missing.join("; ")}.</>
              )}
            </p>
          )}
          {gdpAvailable && !ratios && (
            <p className="notice">
              Os percentuais do PIB ainda não estão disponíveis nesta referência.
            </p>
          )}
        </>
      ) : (
        <div className="notice">
          <strong>
            {fiscal?.status === "INCOMPLETE"
              ? "Ainda falta fechar a referência fiscal."
              : "A referência fiscal ainda não está disponível."}
          </strong>
          <p>
            Precisamos de receitas, despesas e resultado primário compatíveis
            nos 12 meses de um ano fechado. Dados ausentes não significam zero.
          </p>
        </div>
      )}
      <p className="notice">
        Esta é uma conta observada, não uma previsão. O saldo das propostas
        continua mostrando apenas o efeito incremental das medidas e não é
        somado automaticamente a esta referência.
      </p>
      {fiscal?.source && (
        <p>
          Fonte:{" "}
          <a href={fiscal.source.url} target="_blank" rel="noopener noreferrer">
            {fiscal.source.title} ↗
          </a>{" "}
          · {fiscal.source.institution}.{" "}
          <a href={fiscal.source.license_url} target="_blank" rel="noopener noreferrer">
            {fiscal.source.license}
          </a>
        </p>
      )}
      {fiscal && fiscal.missing.length > 0 && (
        <p className="muted">Ainda falta: {fiscal.missing.join("; ")}.</p>
      )}
      {fiscal && fiscal.limitations.length > 0 && (
        <details className="indicator-method">
          <summary>Limites desta referência</summary>
          <ul>
            {fiscal.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
