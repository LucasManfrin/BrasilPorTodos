# O que pesquisar para formar a base do Brasil

Esta é a lista de trabalho do mantenedor. Não precisa pesquisar manualmente o que já tem um conector: primeiro escolha os recortes e acrescente contexto com referências. Valores ausentes continuam ausentes. Não há números inventados neste documento.

## Já coletados automaticamente

| Métrica | Fonte e identificador | O que guardar / cuidado |
| --- | --- | --- |
| Meta Selic | BCB, SGS 432 | % ao ano; diária; meta do Copom, não taxa efetiva nem rendimento |
| Dívida bruta / PIB | BCB, SGS 13762 | % do PIB; mensal; Governo Geral, não só União |
| Dívida líquida / PIB | BCB, SGS 4513 | % do PIB; mensal; setor público consolidado, abrangência diferente da dívida bruta |
| Atividade econômica | BCB, SGS 24363 | IBC-Br sem ajuste sazonal; índice, não PIB em reais |
| Inflação mensal | IBGE, SIDRA 1737, variável 63 | IPCA mensal em %; não somar percentuais para acumular inflação |
| Inflação em 12 meses | IBGE, SIDRA 1737, variável 2265 | Acumulado calculado pelo IBGE; janelas consecutivas se sobrepõem |
| Desemprego | IBGE, SIDRA 6381, variável 4099 | Pessoas de 14 anos ou mais; trimestre móvel encerrado no mês; guardar também comparação anual |
| Receita primária líquida | Tesouro RTN, tema 10, série 10.01.2 | Governo Central, caixa/pagamento efetivo, mês; convertido de R$ milhões para reais nominais |
| Despesa primária | Tesouro RTN, tema 10, série 10.03.1 | Mesmo recorte e critério da receita líquida; doze meses para a base anual |
| Resultado primário observado | Tesouro RTN, tema 10, série 10.04.1 | Acima da linha; conservar valor publicado e diferença de reconciliação; não misturar juros |
| PIB nominal trimestral | IBGE SIDRA 1846, variável 585, classificação 11255, categoria 90707 | PIB nacional a preços de mercado/correntes; quatro trimestres para proporções anuais; precisão R$ 10.000 |

Os conectores conservam unidade, período, fonte, termos e revisões. O catálogo pode mostrar a última observação divulgada meses antes da consulta. As referências oficiais e condições de coleta estão em [docs/data/INDICATORS.md](INDICATORS.md).

## Prioridade 1: ampliar a base fiscal e preparar cenários compatíveis

A base inicial do **Governo Central** já está implementada, em reais nominais e pelo critério acima da linha do RTN, com PIB nacional para proporções do mesmo ano. São onze séries automáticas ao todo. Não é uma equivalência ao orçamento de todo o Brasil: propostas municipais/estaduais precisarão de outra base fiscal. Não é necessário pesquisar à mão os três agregados RTN ou o PIB já conectados; concentre a pesquisa em composição, abrangência e premissas dos impactos. Ver [docs/data/FISCAL_BASELINE.md](FISCAL_BASELINE.md).

| Métrica / estado | Unidade e período solicitado | Fonte | Para que serve |
| --- | --- | --- | --- |
| Receita total e transferências por repartição | R$ milhões; mensal; últimos 5 anos | Tesouro, RTN | Explicar a passagem de receita bruta para líquida |
| Receita líquida — conectada | R$ nominais, mês, Governo Central; ano fechado | Tesouro, RTN 10.01.2 | Referência observada; compatibilidade dos impactos ainda precisa ser informada |
| Despesa primária total — conectada | Mesmo critério e período | Tesouro, RTN 10.03.1 | Base de despesa, sem misturar juros |
| Resultado primário — conectado | Mensal e ano fechado; positivo = superávit | Tesouro, RTN 10.04.1 | Conferir receita líquida menos despesa primária; conservar diferença explícita |
| Juros nominais e resultado nominal | R$ e % do PIB; recorte explicitamente compatível | BCB, estatísticas fiscais | Etapa posterior: distinguir primário de nominal; não misturar setor público consolidado com Governo Central |
| PIB nominal — conectado | R$ correntes; trimestre; soma dos quatro trimestres do ano | IBGE, SIDRA 1846/585/90707 | Proporções anuais; CNT revisável, não SCN anual definitivo nem orçamento disponível |
| Saúde, Educação, Previdência e assistência | Despesa paga; anual e mensal quando disponível | Tesouro, despesas da União; SIOP | Composição do gasto federal; separar RGPS/RPPS e pagamentos/restos a pagar |
| Investimento público | Despesa paga; anual | Tesouro | Distinguir investimento, custeio e despesas obrigatórias |
| Renúncias tributárias | R$; exercício; observado/estimado separado | Receita Federal, demonstrativo de gastos tributários | Mapear hipóteses de arrecadação; uma renúncia não é automaticamente recuperável |

Para cada nova série fiscal e impacto de proposta, confirmar: ente, cobertura, caixa/competência, nominal/real, moeda/escala, sinal de déficit/superávit, transferências e eventuais mudanças metodológicas. A base atual escolhe um ano fechado comum completo e preserva os meses e revisões. Uma eventual janela móvel de 12 meses exige a mesma janela nas séries e tratamento próprio do PIB; não reutilizar automaticamente um PIB de outro período. Não descontar novamente transferências de uma receita já líquida.

Fontes: [RTN e metodologia](https://www.gov.br/tesouronacional/pt-br/estatisticas-fiscais-e-planejamento/resultado-do-tesouro-nacional-rtn), [dados mensais RTN](https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional), [despesas mensais da União](https://www.tesourotransparente.gov.br/ckan/dataset/despesas-da-uniao-mensais-desde-2008), [Contas Nacionais IBGE](https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais.html), [Receita Federal: gastos tributários](https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/relatorios/renuncia/gastos-tributarios).

Receita líquida, despesa primária, resultado acima da linha e PIB nominal já têm conectores. As demais linhas são candidatas à expansão e não recebem valores inventados. A base fiscal observada fica separada da soma incremental do simulador. DATA-06 ainda exige ente, regime e período dos impactos e premissas explícitas antes de construir cenários que combinem propostas com a referência histórica.

## Prioridade 2: entender a vida das pessoas

| Métrica | Recorte que você precisa escolher | Fonte candidata / contexto |
| --- | --- | --- |
| Ocupação e população desocupada | Número de pessoas; Brasil, UF e faixa etária quando útil | IBGE PNAD Contínua; ajuda a interpretar o desemprego |
| Participação na força de trabalho | % da população em idade de trabalhar | IBGE PNAD; permite identificar saída/entrada na procura |
| Subutilização e desalento | Pessoas e taxas, conceitos separados | IBGE PNAD; queda do desemprego não resume todas as dificuldades |
| Informalidade | % e número de ocupados | IBGE PNAD; considerar qualidade/estabilidade do trabalho |
| Rendimento real e massa de rendimentos | Habitual/efetivo, deflator e período identificados | IBGE PNAD; comparar poder de compra, não só reais nominais |
| Emprego formal | Saldo de admissões/desligamentos e estoque separados | MTE Novo Caged; vínculos administrativos não são pessoas nem substituem a PNAD |
| População e estrutura etária | Pessoas; estimativa anual/censo separados | IBGE; demanda por serviços e denominadores por habitante |
| Pobreza e desigualdade | Linha de pobreza, renda, preços/PPC e ano explícitos | IBGE Síntese de Indicadores Sociais; não combinar linhas diferentes |
| Educação | Matrículas, abandono, aprendizagem/Ideb; rede e etapa | Inep; custos e resultados têm defasagens diferentes |
| Saúde | Cobertura, mortalidade, acesso e profissionais; população/território | Ministério da Saúde/DATASUS; qualidade e atraso de registros |
| Saneamento e habitação | Pessoas/domicílios atendidos, conceito de déficit | IBGE e SINISA; distinguir ausência de rede de ausência de serviço |

Para o desemprego, comece por **taxa + ocupação + participação + informalidade + rendimento real**. Compare o mesmo trimestre de cada ano e use os coeficientes/intervalos da pesquisa quando disponíveis. O conector inicial traz a taxa; as séries complementares ainda precisam ser selecionadas.

Fontes: [PNAD Contínua](https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html), [SIDRA 6381](https://sidra.ibge.gov.br/tabela/6381), [Novo Caged](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/novo-caged), [Indicadores educacionais Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais), [DATASUS](https://datasus.saude.gov.br/).

## Como entregar sua pesquisa

Use um bloco por métrica, com links; a V1 continua sem upload de estudos.

```text
Métrica e definição:
Instituição / URL da tabela ou documento:
Código da tabela / variável / filtros:
Valor e unidade:
Período de referência:
Data de divulgação e data da consulta:
Abrangência (Brasil / Governo Central / UF / município):
Histórico comparável (ideal: 5 anos; mudanças de método anotadas):
Nominal ou real / ano-base / escala:
Termos de uso / link:

O que aconteceu (descrição do dado):
Possível explicação (hipótese):
Evidência que sustenta essa hipótese / URL:
Outras explicações possíveis:
Consequências observadas e consequências esperadas (separadas):
Limitações / confiança / responsável pela revisão:
```

Exemplo de texto sem inventar valores: “A taxa caiu em relação ao mesmo trimestre do ano anterior. Para investigar o motivo, comparar ocupação, participação e renda; a taxa isolada não identifica a causa.”

Futuramente, a IA poderá organizar evidências e apontar hipóteses/contradições. Cada análise deverá registrar fontes, modelo, versão, data e revisão humana. Não há IA ou atribuição automática de causalidade nesta entrega.
