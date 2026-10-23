# Base fiscal observada do Governo Central

## O que esta base permite

A primeira base fiscal reúne receita primária líquida, despesa primária e resultado primário observado do Governo Central, em reais nominais, no mesmo ano fechado. Ela permite conferir a identidade receita líquida menos despesa primária igual a resultado primário e conhecer a escala monetária das contas que servem de referência.

Governo Central significa Tesouro Nacional, Previdência Social e Banco Central. Não equivale ao orçamento de todo o Brasil: estados, municípios e demais recortes do setor público não podem ser incorporados silenciosamente.

A tarefa DATA-04 reúne o núcleo fiscal observado e o PIB nominal nacional do mesmo ano, quando os quatro trimestres estão disponíveis, para mostrar proporções. A conta absoluta não depende do PIB. Identificar o ente, o critério contábil e o período dos impactos de cada proposta é uma etapa posterior, registrada em DATA-06. Ter esta referência não autoriza somar automaticamente o saldo incremental das propostas ao resultado fiscal observado, nem tratar essa soma como previsão.

## Fonte e contrato de coleta

Fonte: [Resultado do Tesouro Nacional — série histórica](https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional), Secretaria do Tesouro Nacional. O RTN apura o resultado primário acima da linha pelo regime de caixa e critério de pagamento efetivo, com os tratamentos metodológicos documentados, inclusive operações extra-SIAFI. Não é uma simples soma das despesas orçamentárias pagas. Juros, resultado nominal, resultado abaixo da linha e ajustes para acompanhamento de metas não pertencem à identidade deste núcleo.

Referência metodológica: [Manual do Boletim RTN](https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/28153_894487/Manual%20Externo%20RTN%20VF.pdf), especialmente seções 2.3 a 2.8 e seção 3.

API pública verificada:

```text
https://apiapex.tesouro.gov.br/aria/v1/series-temporais/custom/resultado-fiscal
```

Parâmetros obrigatórios do conector: `tema=10`, `codigo_da_serie` definido na tabela abaixo, `correcao_ipca=false`, início e fim em `MM/AAAA`. O filtro explícito evita misturar valores correntes com valores corrigidos pelo IPCA. O catálogo oficial dos códigos está em [API de séries disponíveis](https://apiapex.tesouro.gov.br/aria/v1/series-temporais/custom/series).

| Componente | Código da série | Tratamento |
| --- | --- | --- |
| Receita primária líquida | `10.01.2` | Núcleo; receita total menos transferências por repartição |
| Despesa primária total | `10.03.1` | Núcleo; despesa no critério RTN acima da linha |
| Resultado primário do Governo Central | `10.04.1` | Núcleo; positivo indica superávit, negativo indica déficit |
| Receita total | `10.01.1` | Referência para expansão e reconciliação da receita; não substitui a receita líquida |
| Transferências por repartição | `10.02.1` | Referência para expansão; não descontar novamente de uma receita já líquida |

Não substituir `10.04.1` por `10.07.1`: esta última é a série abaixo da linha, com critério diferente.

O envelope JSON real contém `status`, `page`, `pageSize`, `next` e `registros`. Os registros contêm `codigoTema`, `codigoSubtema`, `codigoSerie`, `nomeTema`, `nomeSubtema`, `nomeSerie`, `data` e `valor`. O parser confere a identidade da série, o tema mensal, o mês de referência e o valor finito; ausência, repetição ou mistura de séries não vira zero. O primeiro dia do mês é a convenção da referência, não a data de publicação. Datas como `2025-12-01T00:00:00.000Z` e `2026-08-01T00:00:00Z` são equivalentes nessa convenção.

A API pode fornecer `next` mesmo quando a página está vazia. A coleta tem limites de páginas, tamanho e tempo; não segue URLs arbitrárias de paginação e não depende de `next` ficar nulo. Requisições ficam restritas à origem e ao caminho oficiais permitidos, em HTTPS, sem aceitar redirecionamentos.

A [documentação pública da API](https://apiapex.tesouro.gov.br/aria/v1/series-temporais/docs) redirecionava para HTTP durante a pesquisa. A página equivalente foi consultada diretamente em [HTTPS no Tesouro](https://sisweb.tesouro.gov.br/apex/f?p=10250:29&id=1766). Esse comportamento não justifica permitir downgrade no conector de dados.

## Unidade confirmada e precisão

Os valores retornados pelo tema 10 estão em **R$ milhões correntes**. A descrição genérica do Swagger menciona R$, sem explicitar a escala. A escala foi confirmada por comparação com a planilha oficial da série histórica, aba `1.2`, célula `A3`: “R$ Milhões - Valores Correntes”. A linha 5 contém os meses; as linhas 62, 63 e 155 do arquivo inspecionado correspondem aos três agregados. Números de linha são evidência do arquivo consultado, não um contrato permanente para futuros arquivos.

Arquivo de referência: [série histórica até julho de 2026](https://www.tesourotransparente.gov.br/ckan/dataset/ab56485b-9c40-4efb-8563-9ce3e1973c4b/resource/527ccdb1-3059-42f3-bf23-b5e3ab4c6dc6/download/seriehistoricajul26.xlsx). Os recursos atuais podem ser descobertos na [API CKAN do conjunto](https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show?id=resultado-do-tesouro-nacional); não inferir o último período pelo nome do arquivo nem pela data do catálogo.

Comparação de janeiro de 2025, sem arredondar os valores publicados:

| Série | API e XLSX, em R$ milhões |
| --- | --- |
| Receita líquida | `258004.04353337252` |
| Despesa primária | `172940.00746023556` |
| Resultado primário | `85064.03607313696` |

São observações oficiais de referência para conferir o contrato, não valores fixos do produto. Os arquivos e as séries podem ser revisados.

O JSON é lido com `Decimal` antes de qualquer conversão para ponto flutuante. Cada observação é convertida de milhões para reais multiplicando por `1.000.000` e arredondada aos centavos de forma explícita. A referência original, a unidade de origem e a conversão permanecem rastreáveis. Os totais anuais somam os meses preservados; não acumulam valores já acumulados.

A reconciliação mensal admite diferença máxima de **R$ 0,03** após a conversão e arredondamento. Acima dessa tolerância a base não é apresentada como reconciliada. O total anual soma os meses arredondados e pode acumular pequenas diferenças mensais; a diferença anual é publicada separadamente, sem aplicar automaticamente a tolerância mensal de R$ 0,03 ao ano. Não ajustar receita, despesa ou resultado para forçar igualdade, nem esconder diferenças como “arredondamento” sem verificá-las. Na fotografia coletada da entrega, em 2025, receita `2332555301431.48` menos despesa `2394249610412.52` produziu resultado calculado `-61694308981.04`, contra publicado `-61694308980.99`, diferença de `-0.05` reais. Valores históricos da entrega são revisáveis, não constantes do produto.

## Escolha do período

A janela de coleta cobre os últimos cinco anos fechados e o ano em andamento. Para um total anual, selecionar o ano fechado mais recente que possua janeiro a dezembro nas três séries, com o mesmo critério, fonte e conjunto coerente de coleta. A coincidência de três últimas observações não substitui doze meses completos.

Se o ano fechado mais recente estiver incompleto, a seleção pode recuar para o ano completo anterior, mas informa o ano selecionado e o recuo. Meses ausentes, inconsistências e revisões não são preenchidos por estimativa. Se não existir um ano completo e reconciliado, a resposta explica a indisponibilidade.

O ano em andamento permanece mensal ou acumulado parcial identificado como tal; não multiplicar o acumulado por uma razão de meses para inventar resultado anual. A consulta durante a pesquisa confirmou oito meses de 2026 na API, enquanto a planilha vinculada no catálogo terminava em julho: período de referência e data de coleta são informações distintas.

## PIB nacional e proporção fiscal

O denominador usa o PIB a preços de mercado em valores correntes das Contas Nacionais Trimestrais (CNT), do IBGE: tabela SIDRA `1846`, variável `585`, classificação `11255`, categoria `90707`, Brasil `n1/1`. [Metadados oficiais](https://servicodados.ibge.gov.br/api/v3/agregados/1846/metadados) identificam a unidade como **Milhões de Reais**, código `1550`. Não usar índice de volume, taxa de crescimento, PIB per capita, componente setorial ou IBC-Br como substituto.

Consulta oficial para o ano de referência de 2025:

```text
https://apisidra.ibge.gov.br/values/t/1846/n1/1/v/585/p/202501,202502,202503,202504/c11255/90707/d/v585%202
```

O sufixo `/d/v585%202` solicita duas casas decimais em milhões. Sem esse parâmetro, o endpoint consultado retorna valores arredondados a milhões inteiros. A precisão publicada com duas casas em milhões equivale a **R$ 10.000**, não a centavos de medição do PIB. A representação monetária interna em centavos não aumenta a precisão da fonte.

A resposta SIDRA contém uma primeira linha de cabeçalhos seguida dos registros. O conector verifica `NC=1`, `NN=Brasil`, `MC=1550`, `MN=Milhões de Reais`, `D1C=1`, `D2C=585`, `D4C=90707`, período `D3C` e valor textual `V`. Os períodos `YYYY01` a `YYYY04` representam os quatro trimestres, não os primeiros quatro meses. Valores omitidos, inválidos ou não positivos não compõem um denominador utilizável.

Para o ano fiscal selecionado, somar exatamente quatro trimestres únicos do mesmo ano e conjunto de consulta, com `Decimal`, preservando cada observação e revisão. As proporções são `100 × fluxo anual do Governo Central / PIB nacional`, apresentadas com quatro casas decimais para receita líquida, despesa primária e resultado primário publicado. É uma proporção de fluxos federais em relação à economia nacional: não altera a abrangência do numerador para Governo Geral, nem transforma o PIB em receita disponível.

Os quatro valores publicados para 2025 na consulta de referência foram `3024722.91`, `3200345.02`, `3235707.54` e `3277790.15` milhões; somam `12738565.62` milhões. O [release oficial do IBGE](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/45968-pib-cresce-2-3-em-2025-e-fecha-o-ano-em-r-12-7-trilhoes) apresenta o total anual arredondado de R$ 12,7 trilhões. Os números são evidência da consulta, sujeitos a revisão; não são constantes do produto.

Esse total deve ser rotulado **PIB anual pela soma dos quatro trimestres das CNT**, e não resultado anual definitivo do Sistema de Contas Nacionais Anuais (SCN). Na pesquisa, a [tabela anual 6784](https://servicodados.ibge.gov.br/api/v3/agregados/6784/metadados), variável `9808`, terminava em 2023. Para esse ano, a soma trimestral `10943344.67` milhões corresponde ao total anual publicado de `10943345` milhões após arredondamento à precisão anual. A diferença entre precisões publicadas não deve ser “corrigida” alterando observações, nem submetida à tolerância de centavos usada na identidade fiscal do RTN.

A série nominal pode ser revisada; snapshots incluem os quatro trimestres, revisões, unidade e impressão digital do conjunto. A base fiscal absoluta continua disponível se o PIB falhar ou faltar. Nesse caso, o denominador e a proporção ficam ausentes, com motivo explícito: não usar outro ano, completar trimestre por estimativa nem calcular percentual com PIB parcial. A consulta de 2026 com os quatro períodos solicitados retornou somente os dois trimestres divulgados, em HTTP 200; isso não constitui um ano completo.

## Atualização, falhas e revisões

A coleta fiscal usa a rotina diária existente de indicadores. A leitura pública consulta o banco; abrir a página não dispara chamadas ao Tesouro. A operação manual administrativa segue as regras de autenticação, intervalo e exclusão mútua da coleta existente.

Buscar, interpretar e validar as três séries antes de escrever o conjunto fiscal, com uma única transação para suas observações e identificação do conjunto. O PIB é coletado e gravado em um conjunto próprio, também atômico: uma falha do IBGE não deve invalidar o núcleo fiscal do Tesouro, nem uma falha do Tesouro deve impedir a atualização independente do PIB. A compatibilidade anual é conferida na montagem da resposta.

Uma falha de rede, resposta inválida, série inesperada ou conjunto incompleto não deve substituir uma base utilizável por observações parciais daquela execução. Conservar o conjunto anterior e registrar a falha e sua data; a interface distingue a última coleta tentada da última atualização bem-sucedida. O coletor resolve colisões com fontes privadas que já tenham a mesma URL sem promover silenciosamente uma fonte privada nem expor conteúdo de rascunhos; a fonte oficial coletada é identificada pelo fluxo de importação.

Uma nova observação do mesmo mês com valor revisado gera uma revisão; a repetição do mesmo valor com a mesma fonte e proveniência semântica não gera artificialmente novo histórico. No RTN, a impressão digital reúne os três componentes de cada mês: uma mudança em um deles pode gerar revisão dos demais, mesmo com valores individuais iguais. No PIB, reúne os quatro trimestres do ano: mudar um trimestre pode gerar revisão dos outros. Isso preserva a coerência de cada conjunto. A montagem da base usa as revisões atuais pertencentes a um conjunto compatível. O identificador da base inclui a impressão digital desse conjunto, dos meses selecionados e das revisões usadas, além da versão do contrato. Não montar uma base misturando silenciosamente séries de execuções diferentes.

Rascunhos guardam uma fotografia da base. Atualizar os dados do país não modifica automaticamente uma proposta ou um plano existente. A atualização explícita da base de um rascunho cria uma nova referência; uma publicação continua presa à fotografia original, com identificador, período, fonte, valores e revisões preservados. Versões anteriores continuam interpretáveis pelo contrato que usaram.

## Consulta pública e relação com as simulações

O contrato de leitura pública oferece a base fiscal em `GET /api/v1/indicators/baseline/fiscal`. A base contextual em `GET /api/v1/indicators/baseline/current` incorpora o núcleo fiscal em um objeto separado, preservando a distinção entre indicadores de contexto e fluxos que compõem o resultado primário.

A resposta deve tornar verificáveis o ano selecionado, a abrangência, o critério, os três totais em reais, os doze meses e suas revisões, a reconciliação, a origem e as limitações. Quando disponível, o PIB mostra seus quatro trimestres, a origem nacional, a precisão e o percentual compatível. A data da consulta não é uma data inventada de publicação do dado.

O saldo das medidas do simulador continua **incremental**. A base observada é uma referência histórica. Para compor um cenário futuro será necessário identificar, em cada impacto, ente, critério contábil, período e compatibilidade com a base, além de explicitar as premissas de evolução das receitas e despesas. Repetir o ano histórico em anos futuros não é uma previsão validada.

## Licença e pendências

O catálogo oficial do RTN declara `license_id=odc-odbl`, licença [Open Database License — ODbL](https://opendatacommons.org/licenses/odbl/1-0/). Manter atribuição ao Tesouro e às séries originais. Para o PIB, manter atribuição ao IBGE/SIDRA e a referência aos [termos do portal IBGE](https://www.ibge.gov.br/acesso-informacao/acoes-e-programas/politica-de-privacidade.html) já usada no catálogo; não atribuir ODbL aos dados IBGE sem declaração correspondente. A licença MIT do código do BrasilPorTodos não substitui os termos dos dados utilizados.

Após a base observada com PIB, permanecem necessários:

- Tratamento de outros entes e abrangências; Governo Geral, setor público consolidado e Governo Central são recortes distintos.
- DATA-06: metadados de compatibilidade dos impactos antes de combinar medidas com a referência fiscal; cenários futuros precisam de ente, critério, período e premissas identificados.
- Juros, resultado nominal e composição do gasto com critérios próprios, sem dupla contagem.
- Evidências de causas e efeitos indiretos revisadas; a base fiscal não atribui causalidade nem prevê resultados sociais.

Este documento descreve o contrato e as referências verificadas. A execução dos testes e a validação da entrega ficam registradas separadamente em `docs/development/VERIFICATION.md`.

A composição primária adicional é separada desta referência: [FISCAL_COMPOSITION](FISCAL_COMPOSITION.md). Preserva o trio e seu método; não reescreve snapshots publicados.
