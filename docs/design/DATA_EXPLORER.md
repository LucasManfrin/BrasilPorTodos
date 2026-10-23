# Brasil Atual e diretório de fontes

Redesign iniciado em 2026-10-09, concluído em 2026-10-10, restrito às rotas `/brasil` e `/fontes`. As páginas aprovadas, os tokens globais, os endpoints e os cálculos do backend são preservados. Os componentes novos ficam em `frontend/src/features/data-explorer/`; o helper decimal fica em `frontend/src/lib/data-format.ts`.

## Destaques fixos

Os destaques são configurados por código, sem classificação por melhora ou piora:

| Tema | Indicador | Papel |
| --- | --- | --- |
| Emprego | Desemprego | Acesso ao trabalho; precisa de renda, informalidade e participação como contexto |
| Preços | IPCA mensal | Mudança dos preços no mês; ler com IPCA acumulado e juros |
| Dívida | Dívida bruta / PIB | Estoque relativo à economia; ler com dívida líquida e definições de abrangência |
| Contas públicas | Resultado primário do Governo Central | Saldo sem juros; ler com receita, despesa, ente e período |

A regra também aparece em `/brasil`. A rota `/metodologia` não foi alterada porque o mantenedor restringiu o redesign às duas telas. Dados complementares ainda não verificados aparecem como “Em breve”, nunca como valores ilustrativos. Buscar ou selecionar um tema organiza todos os resultados por assunto.

## Números e comparações

- Valores monetários são compactados em mil, mi, bi e tri. Os valores completos, com centavos, ficam no tooltip e no detalhe. A formatação usa inteiros de precisão arbitrária sobre as strings decimais recebidas; não converte dinheiro em ponto flutuante.
- Taxas em percentuais usam diferença em pontos percentuais, inclusive quando a inflação mensal cruza zero. Uma mudança de −0,32% para 0,82% corresponde a +1,14 p.p.
- Reais e índices usam variação percentual somente com ambos os valores positivos e fora da faixa próxima de zero: pelo menos R$ 1 ou 0,01 unidade de índice. Essa faixa é uma proteção de apresentação, não uma hipótese econômica. Nos demais casos, mostram a diferença absoluta.
- Desemprego (trimestres móveis sobrepostos) e IBC-Br mantêm a comparação com a mesma referência do ano anterior. As demais séries usam a observação anterior, sem preencher meses ausentes. O mês comparado fica explícito.
- “Subiu”, “caiu” e as setas indicam direção. Cor não classifica a variação como boa ou ruim. “Déficit” e “superávit” descrevem o sinal do resultado primário.
- A linha do gráfico e a comparação visual de barras usam `Number` apenas para geometria. Os números finais e a aritmética de variação usam as strings decimais originais. Períodos de um/cinco anos usam meses de calendário, não quantidades de observações.
- A referência fiscal continua sendo a base anual observada, sem somar automaticamente efeitos incrementais de propostas. Resultado publicado, cálculo dos componentes e diferença de reconciliação permanecem separados.

## Fontes equivalentes e confiança

A deduplicação é somente de apresentação e limitada a identidades oficiais revisadas: instituição, dataset/série e variável. Todos os IDs históricos são preservados para publicações e revisões.

- As duplicatas de BCB SGS 432 (Selic) e SGS 13762 (DBGG) viram uma linha por série.
- Referências ao mesmo dataset Resultado do Tesouro Nacional viram uma linha com suas três medidas explicitadas.
- A tabela IBGE 1737 contém variáveis diferentes: IPCA mensal (63) e acumulado em 12 meses (2265). Essas fontes continuam distintas.
- URLs iguais sem identidade revisada não são deduplicadas. Contagens de publicações de registros equivalentes não são somadas, porque a API não entrega os IDs das publicações para eliminar interseções.
- Exemplos fictícios aparecem apenas em `NODE_ENV=development` e são excluídos dos demais ambientes antes de filtros, contadores e agrupamentos.
- Data de acesso, referência da observação e consulta automática são campos diferentes. O estado da consulta é associado aos códigos das séries efetivamente consultadas, e não presumido a partir de `accessed_at`.
- Referências sem coleta automática não recebem um selo de atualização inventado. Consultas indisponíveis ou antigas são explicitadas; o dado preservado não é descartado.

## Verificação

Testes puros de formatação, variação, recorte de calendário, identidade de fonte, filtragem e estado de consulta: `npm run test:data-explorer`. Verificações da interface incluem as larguras de 360, 768, 1280 e 1920 px, temas claro/escuro, ausência de overflow, navegação por teclado, Escape/restauração de foco do drawer e gráficos acessíveis. Respeitar `prefers-reduced-motion` em contagem, desenho e transições.


Resultado final em 2026-10-10: 44 testes passaram; lint, TypeScript e build passaram. Duas rotas, quatro larguras e dois temas, totalizando 16 combinações sem overflow ou falhas nos contrastes de texto medidos. Drawer, filtros, períodos, interação dos gráficos e memória fiscal conferidos. Evidências e limites da revisão em [docs/development/VERIFICATION.md](../development/VERIFICATION.md).

## Ajuste das seções de Brasil Atual — 2026-10-10

UX-03 restaura todos os indicadores por tema, incluindo os quatro destacados, com selo “Em destaque”. Anatomia aprovada do IndicatorTile mantida; adicionadas apenas a identificação e a variante horizontal para card que ocupa a linha inteira em largura suficiente.

Grade de 12 trilhas, capacidades 1/2/3/4 nas larguras 360/768/1280/1920. Totais distribuídos em linhas equilibradas: cinco itens na capacidade quatro formam 3+2; sete formam 4+3. Cards ocupam toda a largura, com altura igual na mesma linha. Sem textos substituindo destacados.

Busca com debounce reúne resultados em uma única grade; chips exibem os temas correspondentes. Faixa compacta mostra consulta e 12 fontes distintas, contando identidades oficiais, não séries; “Recarregar” lê nossa API/cache. Estado das fontes expande detalhes e explicita falhas com cache preservado. ResizeObserver mede as alturas para ajustar scroll-padding do documento e scroll-margin dos títulos/seções; o ajuste é restaurado ao sair da página.

Emprego reúne desemprego, renda real habitual, informalidade e participação. Comparação anual neutra nos quatro; renda com preços coerentes. Texto contextual do Destaque desemprego atualizado porque os dados existem; configuração, anatomia e visual dos Destaques preservados. [Contrato das novas séries](../data/EMPLOYMENT_INDICATORS.md).

Fontes conserva seu visual; recebeu somente identidades e registros pelo pipeline. Home, tokens, estilos globais e demais telas aprovadas preservados. 76 testes frontend e 56 combinações de grade/largura/tema passaram; [docs/development/VERIFICATION.md](../development/VERIFICATION.md).
