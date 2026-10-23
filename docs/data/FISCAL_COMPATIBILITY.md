# Compatibilidade dos impactos fiscais

Contrato DATA-06A, incorporado em 2026-10-10. [Metodologia](METHODOLOGY.md) · [Referência observada](FISCAL_BASELINE.md) · [Backlog](../project/BACKLOG.md).

## O que a avaliação responde

Uma parcela pode ser comparada com a referência histórica preservada na versão do plano? A avaliação compara declarações de recorte e período; não verifica a qualidade do custo estimado, a fonte causal ou a viabilidade da proposta. Não soma a referência aos impactos e não projeta anos futuros.

## Metadados por parcela

Além de ano, tipo, valor e descrição, cada impacto fiscal carrega:

| Campo | Valores aceitos | Regra |
| --- | --- | --- |
| fiscal_scope | CENTRAL_GOVERNMENT, GENERAL_GOVERNMENT, STATE, MUNICIPAL, OTHER, UNSPECIFIED | Governo Central não equivale a Governo Geral; estado/município específico ainda não é identificado |
| accounting_basis | CASH, ACCRUAL, UNSPECIFIED | Caixa: entrada/saída efetiva; competência: surgimento de direito/obrigação |
| price_basis | NOMINAL, CONSTANT, UNSPECIFIED | Nominal: preços do próprio ano; constante: preços do ano-base informado |
| price_base_year | Inteiro de 1900 a 2200 ou null | Obrigatório em CONSTANT; proibido nos demais |
| component | PRIMARY, INTEREST, UNSPECIFIED | Primário exclui juros |
| period_basis | FULL_YEAR, PARTIAL_YEAR, UNSPECIFIED | Ano inteiro ou parte do ano; não anualiza parcelas |

UNSPECIFIED é o padrão inclusive no legado: não inferir metadados por categoria, texto ou premissas antigas. API e banco validam os domínios e o ano-base. Rascunhos, autosave, novas versões e duplicações preservam os campos. Para mudar publicação, criar outra versão.

## Referência e estados

A avaliação usa exclusivamente baseline_snapshot.fiscal do plano, não o catálogo atual. A referência precisa ser AVAILABLE, em BRL nominal, Governo Central, caixa, primária, com ano fechado completo e reconciliação válida. O identificador contextual diferente entre plano/proposta continua produzindo seu aviso próprio; igualdade desse identificador não prova compatibilidade fiscal.

Para COMPATIBLE, todas as parcelas habilitadas dentro do horizonte devem declarar CENTRAL_GOVERNMENT, CASH, NOMINAL, PRIMARY e FULL_YEAR, no mesmo ano observado da referência. Uma base ausente/malformada não é aceita.

| Estado | Significado |
| --- | --- |
| COMPATIBLE | Recortes declarados coincidem com a referência histórica; não valida a estimativa |
| NOT_COMPARABLE | Pelo menos uma parcela diverge ou falta referência utilizável; motivos registrados |
| INCOMPLETE | Informação fiscal ausente ou medida ativa não estimada, sem outra incompatibilidade prevalente |
| NO_IMPACTS | Nenhuma parcela habilitada no horizonte e nenhuma estimativa ausente a considerar |

Um ano futuro recebe FUTURE_ASSUMPTIONS_REQUIRED. Não repetir o ano histórico, corrigir pela inflação, mudar abrangência, transformar competência em caixa ou excluir juros automaticamente. Parcela desativada ou fora do horizonte não entra na avaliação; o aviso de exclusão continua preservado.

## Somatório e interpretação

O motor aritmético permanece 1.0.0: soma receitas/economias e subtrai despesas/renúncias por ano, usando Decimal. Financiamento declarativo não vira receita; NOT_ESTIMATED não vira zero. is_partial mantém sua regra de estimativas ausentes, separada da cobertura de metadados.

A execução nova registra aggregate_basis como HOMOGENEOUS, MIXED ou UNSPECIFIED e price_basis como NOMINAL, CONSTANT, MIXED ou UNSPECIFIED. Preços constantes com anos-base distintos são mistura. Metadados ausentes/misturados geram avisos; interface deixa de apresentar o medidor como saldo comparável. O total aritmético permanece reproduzível, mas não deve ser interpretado como conta fiscal homogênea nessas condições. Mesmo homogêneo não significa compatível com a referência histórica.

## Reprodução e legado

Fiscal_compatibility tem versão própria 1.0.0, estado, baseline_year, baseline_combined=false, motivos gerais/por parcela e coverage (considered, compatible, not_comparable, incomplete). É gravado em input_snapshot e assumptions, junto com os metadados; participa do hash da nova execução. A versão do motor identifica a aritmética; a versão da avaliação identifica este contrato adicional.

A migration 0009 adiciona campos/constraints e defaults sem reescrever snapshots, resultados ou hashes antigos. Execuções antigas não recebem avaliação retroativa: a interface mostra ausência explícita. Nenhuma publicação passa a alegar que conhecia os novos metadados na data original.

## Cenário futuro separado

DATA-06B implementa premissas anuais manuais e combinação condicional em recorte restrito, separadas desta avaliação histórica. Conversões, juros, outros entes, efeitos comportamentais, grafos e IA não estão implementados por este contrato.

## Avanço de DATA-06B — 2026-10-10

Contrato e biblioteca de cenário anual declarado concluídos em DATA-06B1, separados desta avaliação histórica. Integração ao plano/API/publicação/interface concluída em DATA-06B2; revisão da exclusão das medidas vinculada às entradas preservadas. [Método e limites](FISCAL_SCENARIOS.md).
