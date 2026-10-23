# Fontes de dados

## Estado do catálogo

O catálogo automatizado tem 14 séries verificadas: quatro BCB, sete IBGE e três RTN/Tesouro. As três séries RTN formam o núcleo fiscal observado do Governo Central; o PIB nominal nacional de quatro trimestres permite proporções do mesmo ano. A tabela abaixo também inclui instituições e temas candidatos: sua presença não significa conector implementado. A cobertura ampliada planejada em F1-03 ainda exige seleção e validação. Ver [docs/data/INDICATORS.md](INDICATORS.md) e [docs/data/FISCAL_BASELINE.md](FISCAL_BASELINE.md) para contratos, termos, limites e operação.

| Instituição / portal | Uso candidato | Definições necessárias |
| --- | --- | --- |
| [IBGE](https://www.ibge.gov.br/) / [SIDRA](https://sidra.ibge.gov.br/) | PIB, PIB per capita, população, desemprego, inflação e pobreza | Pesquisa, território, período, unidade, deflator e definição de pobreza |
| [Banco Central](https://www.bcb.gov.br/) | Selic, dívida bruta e dívida/PIB | Taxa/meta, conceito da dívida, cobertura institucional e periodicidade |
| [Tesouro Nacional](https://www.tesourotransparente.gov.br/) | Receitas, despesas e resultado primário | Governo Central versus outros agregados, regime, consolidação e período |
| [SIOP](https://www.siop.planejamento.gov.br/) / [Orçamento Federal](https://www.gov.br/planejamento/pt-br/assuntos/orcamento) | Previdência, Saúde e Educação no orçamento federal | Função/programa, aprovado versus executado, empenhado/liquidado/pago |
| [Portal da Transparência](https://portaldatransparencia.gov.br/) | Consulta complementar de execução federal | Cobertura e correspondência com a série principal |
| [Planalto](https://www.planalto.gov.br/) | Referências legislativas | Texto, vigência, alterações e trecho utilizado |

## Registro mínimo

Fonte: título, instituição, URL HTTP/HTTPS, tipo, publicação quando conhecida, acesso e descrição. Indicador: código estável, conceito, abrangência territorial/institucional, frequência, unidade, método e eventual ano-base. Observação: valor decimal, referência temporal, fonte, data de coleta e revisão.

Uma proposta informa o uso de cada fonte. No momento da publicação, preservar os metadados citados para que uma edição posterior do catálogo não reescreva a justificativa histórica.

## Política de qualidade

Priorizar fontes primárias, registrar a tabela/série específica e verificar unidade, referência, cobertura e revisões antes de publicar. Não combinar gasto federal com gasto consolidado sem explicitar a diferença. Não somar séries que representem o mesmo fluxo.

Não substituir dado ausente por zero, interpolar silenciosamente nem apresentar demonstrações como números reais. Exibir atualização e ausência quando aplicável. Mudanças de definição interrompem comparabilidade e precisam de nota.

## Ingestão da V1

A fundação começou por seeds/scripts revisados ou manutenção administrativa; a operação atual usa coleta diária dos conectores verificados, mantendo esses caminhos administrativos. Clientes para IBGE, BCB, Tesouro e SIOP ficam isolados em `backend/app/integrations` quando implementados. Importações devem ser idempotentes, registrar proveniência e evitar sobrescrever revisões sem histórico.

URLs contribuídas são referências armazenadas, sem download de arquivos ou busca automática pelo backend. Código aberto não concede direitos sobre dados ou conteúdo de terceiros; registrar termos e atribuição de cada fonte na seleção da série.

## Primeiras séries selecionadas — 2026-10-06

SGS 432 e 13762 têm definição, unidade, periodicidade e licença ODbL registradas no catálogo revisado. O cliente BCB usa apenas URLs oficiais construídas com esses códigos. Dados são coletados em intervalo explícito, com limites e sem redirecionamentos; observações futuras ou fora do intervalo são recusadas. Importações repetidas preservam revisões; mudanças de valor/proveniência acrescentam revisão.

A seleção inicial não valida automaticamente PIB, emprego, pobreza, receitas ou gastos. F1-03 continua preparado até expandir e verificar o catálogo planejado. Nenhuma dessas séries pendentes recebe números demonstrativos.

## Expansão verificada — 2026-10-07

Além de SGS 432/13762, os conectores usam SGS 4513 (dívida líquida/PIB), SGS 24363 (IBC-Br sem ajuste sazonal), SIDRA 1737 variáveis 63/2265 (IPCA mensal/12 meses) e SIDRA 6381 variável 4099 (desocupação). Metadados oficiais, unidades e recortes foram conferidos; sete séries foram coletadas com sucesso. Política diária e termos em [docs/data/INDICATORS.md](INDICATORS.md).

O trecho acima sobre operação manual descreve a fundação inicial, superada pela coleta diária de ADR-021. O restante do catálogo candidato ainda exige validação. A lista priorizada para pesquisa manual está em [docs/data/RESEARCH_BRIEF.md](RESEARCH_BRIEF.md): primeiro fluxos fiscais compatíveis, depois contexto social e evidências causais. Registrar tabela/série, publicação, referência, unidade, cobertura e termos; não basta um link genérico.

## Base fiscal e PIB verificados — 2026-10-09

A expansão acrescenta RTN tema 10, séries `10.01.2` (receita líquida), `10.03.1` (despesa primária) e `10.04.1` (resultado primário acima da linha), com [API pública do Tesouro](https://apiapex.tesouro.gov.br/aria/v1/series-temporais/custom/resultado-fiscal) e [catálogo oficial](https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional). São valores nominais do Governo Central, em caixa/pagamento efetivo, convertidos de milhões para reais. Não representam Governo Geral, orçamento consolidado ou resultado nominal. O catálogo RTN declara ODbL; preservar fonte e atribuição.

O PIB vem da [SIDRA 1846](https://sidra.ibge.gov.br/tabela/1846), variável `585`, classificação `11255`, categoria `90707`, Brasil: valores correntes, PIB a preços de mercado. [Metadados oficiais](https://servicodados.ibge.gov.br/api/v3/agregados/1846/metadados) confirmam Milhões de Reais. A consulta pede duas casas decimais em milhões; a precisão da fonte é R$ 10.000, mesmo que dinheiro seja representado internamente com centavos. Usar os termos do portal IBGE, sem atribuir a licença ODbL do Tesouro a dados IBGE.

A coleta obtém cinco anos fechados e o ano corrente; valida os três fluxos antes de gravar o conjunto RTN em uma transação. O PIB é importado em conjunto próprio, independente. Mesmo valor e mesma proveniência semântica não duplicam observação; mudança na impressão digital de um conjunto pode criar revisões de valores individuais inalterados para manter consistência. Falhas conservam observações anteriores. Colisões com URLs de fontes privadas são resolvidas sem tornar rascunhos públicos.

A base escolhe o ano fechado completo mais recente, informa eventual recuo, mantém os doze meses e revisões e não substitui ausência por zero. O denominador anual de PIB exige os quatro trimestres do mesmo ano; é soma das CNT revisável, não uma divulgação anual definitiva do SCN. Os snapshots preservam as fontes, períodos, conjuntos e revisões usados nas publicações. Sem PIB compatível, não há percentual inventado.

O núcleo e as proporções não somam automaticamente impactos de propostas ao saldo observado. A tarefa DATA-06 ainda exige compatibilidade de ente, regime e período e premissas explícitas para cenários futuros. Composição do gasto, outros entes, juros e resultado nominal seguem pendentes de seleção específica; a coleta de onze séries não completa todo o catálogo candidato.

## Composição RTN verificada — 2026-10-10

Receita total/transferências, quatro filhos diretos da receita e quatro filhos da despesa usam o tema 10 do RTN, mesma fonte ODbL, Governo Central/caixa/nominal. Pesquisa API/XLSX de 2025 e limitações em [FISCAL_COMPOSITION](FISCAL_COMPOSITION.md). Incentivos fiscais dessa rubrica não são total de renúncias; programação financeira não é toda discricionária. A expansão é uma composição auxiliar, não dez indicadores novos de narrativa macroeconômica.

## Juros e nominal verificados — 2026-10-11

RTN tema 10: `10.07.1`, `10.08.1`, `10.09.1`, milhões correntes → BRL nominal; estatísticas BCB republicadas pela STN sob ODbL. Regime misto e primário abaixo da linha, separado do acima da linha. Conferidos 36 pares API/XLSX de 2025. [Método](FISCAL_INTEREST.md). Gasto por função usa outro conjunto oficial e ainda está em pesquisa/contrato, sem coleta no produto: [pesquisa](FEDERAL_SPENDING_RESEARCH.md).

## Integração funcional — DATA-07B2

Fonte oficial de despesas e transferências da União, ODbL, recurso do ano fechado da referência atual. Download controlado e parser de guia em reais correntes; mesma revisão reúne funções, naturezas e estágios. Consultas públicas leem agregados salvos, não fazem download por visita. [Contrato](FISCAL_SPENDING.md) e [pesquisa original](FEDERAL_SPENDING_RESEARCH.md); coleta real de 2025 e integração verificadas em 2026-10-11, com revisão 1, doze meses e histórico preservado.


## Governo Geral por esfera — DATA-07B3, 2026-10-12

EFGG anual, tabela 2.1 da publicação STN, mesma referência fechada do painel fiscal atual. Receita, despesa, gasto, investimento líquido, capacidade/necessidade, juros e primário GFSM: oito métricas e oito grupos, com ajustes oficiais e competência modificada. Municípios com cobertura aproximada de 90% e extrapolação informadas pela fonte; não afirmar cobertura observada universal. Termos do Tesouro Transparente com atribuição, não ODbL por analogia. Coleta real 2025, revisão íntegra/idempotente, API/painel e fontes verificados. [Contrato](GENERAL_GOVERNMENT.md).

São conjuntos próprios, além dos 14 indicadores principais e treze séries auxiliares RTN. SICONFI por ente e NFSP BCB foram pesquisados como alternativas, sem coletores habilitados. [SICONFI](SICONFI_RESEARCH.md) · [NFSP](PUBLIC_SECTOR_RESEARCH.md). Correspondência entre métodos é descritiva, sem conversão automática nem soma para simular orçamento nacional.
