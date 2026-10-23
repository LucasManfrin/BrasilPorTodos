# Composição primária do Governo Central

## O que esta primeira camada responde

DATA-07A detalha a conta observada: de onde vem a receita total, o desconto das transferências por repartição até a receita líquida e quatro grupos de despesa primária. Usa o mesmo ano fechado da [base fiscal](FISCAL_BASELINE.md), Governo Central (Tesouro, Previdência e Banco Central), caixa/pagamento efetivo com tratamentos do RTN, reais nominais e fluxos primários sem juros.

Não é o orçamento de todo o Brasil, uma classificação por Saúde/Educação, a lei orçamentária aprovada ou uma estimativa de recursos que podem ser cortados. Dados observados não justificam medidas nem produzem efeitos causais automaticamente. Juros, resultado nominal, estados/municípios e gasto por função continuam em DATA-07B.

## Fonte, hierarquia e sinais

[Resultado do Tesouro Nacional](https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional), Secretaria do Tesouro Nacional, licença [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Método no [Manual do RTN](https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/28153_894487/Manual%20Externo%20RTN%20VF.pdf), seções 2/3. Catálogo em [séries oficiais](https://apiapex.tesouro.gov.br/aria/v1/series-temporais/custom/series); consulta no endpoint de [resultado fiscal](https://apiapex.tesouro.gov.br/aria/v1/series-temporais/custom/resultado-fiscal), tema 10, `correcao_ipca=false` e intervalo mensal explícito.

| Grupo | Série | Papel |
| --- | --- | --- |
| Receita total | `10.01.1` | Agregado bruto |
| Receita administrada pela RFB | `10.01.1.1` | Parcela da receita total |
| Incentivos fiscais | `10.01.1.2` | Parcela assinada; devoluções específicas FINOR/FINAM/FUNRES, não total de renúncias tributárias |
| Arrecadação líquida para o RGPS | `10.01.1.3` | Parcela da receita total |
| Receitas não administradas pela RFB | `10.01.1.4` | Parcela da receita total |
| Transferências por repartição | `10.02.1` | Dedução da receita total, uma única vez |
| Receita líquida | `10.01.2` | Receita total menos transferências; âncora já existente |
| Despesa primária total | `10.03.1` | Agregado já existente |
| Benefícios previdenciários | `10.03.1.1` | Parcela da despesa |
| Pessoal e encargos | `10.03.1.2` | Parcela da despesa |
| Outras despesas obrigatórias | `10.03.1.3` | Rubrica publicada; não resíduo inventado |
| Executivo sujeito à programação financeira | `10.03.1.4` | Inclui obrigatórias com controle de fluxo e discricionárias; não chamar todo o grupo de discricionário |
| Resultado primário acima da linha | `10.04.1` | Âncora já existente |

Receita e despesa somam apenas os quatro filhos diretos. Não somar o pai `.4` aos seus filhos `.4.1/.4.2`; esses subtotais não são parcelas extras nesta camada. Incentivos negativos entram com o sinal publicado, sem nova subtração. Transferências não são acrescentadas novamente à despesa.

## Unidade, precisão e reconciliação

Tema 10 retorna R$ milhões correntes. Ler JSON com Decimal, multiplicar por 1.000.000 e arredondar cada mês aos centavos com half-even. Limite de observação compatível com NUMERIC(20,6), valor absoluto menor que 10¹⁴ reais; nenhum float no cálculo. Somar os doze meses convertidos. Centavos da representação não aumentam a precisão econômica da fonte.

Conferir por mês: soma dos filhos menos receita total; receita total menos transferências menos receita líquida; soma dos filhos menos despesa total. Tolerância explícita de R$ 0,03 por identidade/mês contempla arredondamento independente das parcelas; a diferença efetiva fica visível. Anual depende de todos os meses aprovados e publica a soma das diferenças mensais, sem aplicar silenciosamente a tolerância mensal ao ano. Não ajustar dados nem criar uma categoria residual para forçar igualdade.

Pesquisa de 2026-10-10 comparou 180 pares (15 séries × 12 meses de 2025, incluindo subtotais consultados mas não somados nesta camada) da API com a planilha oficial, aba `1.2`, unidade em `A3`: [arquivo consultado](https://www.tesourotransparente.gov.br/ckan/dataset/ab56485b-9c40-4efb-8563-9ce3e1973c4b/resource/527ccdb1-3059-42f3-bf23-b5e3ab4c6dc6/download/seriehistoricajul26.xlsx). Todos coincidiram após conversão. Receita total: R$ 2.902.274.564.064,60; transferências: R$ 569.719.262.633,12; receita líquida: R$ 2.332.555.301.431,48. Despesa: R$ 2.394.249.610.412,52; diferença dos filhos: R$ 0,01 em abril e no anual. Incentivos: −R$ 1.431.077,65. São evidências revisáveis, não constantes do produto.

## Coleta, revisão e separação da referência

Composição tem catálogo e impressão digital próprios, separados do trio RTN v1. Consulta e gravação atômicas do conjunto; fonte/definição/proveniência, revisões mais recentes e doze meses completos são requisitos. Falha ou resposta truncada conserva o lote anterior, com motivo explícito. Revisão parcial ou diferença com o trio corrente impede apresentar os detalhes como compatíveis; ausência nunca vira zero.

Endpoint público: `GET /api/v1/indicators/baseline/composition`. Seleciona o ano da base fiscal atual, sem escolher outro ano silenciosamente. A resposta identifica a referência usada e cada observação/revisão/coleta. A página confere ano e três totais de referência antes de juntar respostas, evitando misturar uma atualização que ocorra entre consultas.

Dez séries auxiliares usam a infraestrutura de observações existente, mas ficam fora do catálogo de indicadores principais e de `baseline/current`. Assim, acrescentar composição não troca o contexto nem a referência de propostas/planos; snapshots, hashes, motor e resultados publicados anteriores permanecem intactos. Não é necessária migration nesta fatia.

A coleta participa da rotina diária controlada e da ação administrativa existente. Leitura pública usa dados salvos; visitas não disparam consulta ao Tesouro. Operação persistente supervisionada continua pendente antes de lançamento público. Repositório MIT não relicencia dados ODbL.

## Entrega local verificada — 2026-10-11

DATA-07A concluído: 120 observações reais de 2025, revisão máxima 1 após repetição, composição disponível e reconciliada; publicação/simulação/contexto anterior preservados. 457 testes backend/134 frontend e checks/build passaram; oito combinações de largura/tema verificadas. [Evidência](../development/VERIFICATION.md). DATA-07 segue Preparado, com DATA-07B A fazer.
