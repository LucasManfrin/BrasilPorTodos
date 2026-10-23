# DATA-07B3 — revisão independente das séries BCB/NFSP

Pesquisa em 11/10/2026. Somente dados públicos oficiais e arquivos deste diretório; nenhuma alteração em produção, documentação do repositório, banco ou runtime.

## Recorte recomendado

Uma primeira camada mensal/ano fechado **abaixo da linha**, com seis recortes publicados e 18 séries: Governo Federal + Banco Central (ponte com B1), estados, municípios, regionais, empresas estatais e setor público consolidado. Cada recorte conserva seu trio primário/juros/nominal. Estados e municípios são agregados nacionais, não uma consulta a uma UF/prefeitura.

O total consolidado já existe na fonte e deve ser mostrado como observado; a soma dos componentes serve apenas à reconciliação. Não somar o consolidado aos filhos, regionais a estados+municípios, ou estatais novamente aos governos. Não incorporar ao motor incremental nem ao snapshot de referência atual.

**Governo Geral permanece uma pendência distinta.** A busca oficial `NFSP` encontrou 70 conjuntos, nenhum com título Governo Geral; a busca Governo Geral encontrou 36 conjuntos, principalmente estoques de dívida/crédito, nenhum trio mensal NFSP. Isso limita o resultado desta pesquisa, não prova inexistência de qualquer outro produto. Consolidado inclui BCB e estatais e não pode ser renomeado Governo Geral. Uma soma Federal sem BCB + estados + municípios seria um cálculo próprio, não a estatística oficial MEFP2014 do Tesouro.

## Catálogo verificado

Todos os códigos abaixo vieram da resposta CKAN oficial salva, não de memória. Cada série tem recursos JSON/CSV SGS, frequência mensal, unidade **milhões de reais**, início 01/12/2001 e licença `odc-odbl`. As 33 respostas consultadas contêm exatamente 12 referências de 01/01/2025 a 01/12/2025.

| Recorte oficial | Primário | Juros nominais | Nominal |
|---|---:|---:|---:|
| Governo Federal e Banco Central | 4639 | 4606 | 4573 |
| Governo Federal | 4640 | 4607 | 4574 |
| Banco Central | 4641 | 4608 | 4575 |
| Governos estaduais e municipais | 4642 | 4609 | 4576 |
| Governos estaduais | 4643 | 4610 | 4577 |
| Governos municipais | 4644 | 4611 | 4578 |
| Empresas estatais | 4645 | 4612 | 4579 |
| Empresas estatais federais | 4646 | 4613 | 4580 |
| Empresas estatais estaduais | 4647 | 4614 | 4581 |
| Empresas estatais municipais | 4648 | 4615 | 4582 |
| Setor público consolidado | 4649 | 4616 | 4583 |

URLs exatas por série, unidade/licença/frequência e hashes das respostas: `series-2025-verification.json` → metadata. Exemplos: [primário estados](https://dadosabertos.bcb.gov.br/dataset/4643-nfsp-sem-desvalorizacao-cambial---fluxo-mensal-corrente---resultado-primario---total---governo), [primário municípios](https://dadosabertos.bcb.gov.br/dataset/4644-nfsp-sem-desvalorizacao-cambial---fluxo-mensal-corrente---resultado-primario---total---governo), [nominal consolidado](https://dadosabertos.bcb.gov.br/dataset/4583-nfsp-sem-desvalorizacao-cambial---fluxo-mensal-corrente---resultado-nominal---total---setor-pu).

[Consulta JSON oficial de estados/primário em 2025](https://api.bcb.gov.br/dados/serie/bcdata.sgs.4643/dados?formato=json&dataInicial=01%2F01%2F2025&dataFinal=31%2F12%2F2025). Licença declarada: Open Data Commons ODbL; preservar atribuição BCB/Departamento Econômico e termos próprios, sem tratar como MIT.

## Critérios oficiais e limites

O [Manual BCB, maio/2019](https://www.bcb.gov.br/content/estatisticas/Documents/notas_metodologicas/estatisticas-fiscais/estatisticasfiscais.pdf), pp. 8–15 e 32–34, define abaixo da linha, primário por caixa, juros por competência, nominal misto e sinais: **positivo indica necessidade/déficit; negativo, superávit**. São valores correntes, sem deflacionamento; excluem o efeito cambial especificado nas NFSP. O consolidado inclui governos/Previdência, BCB e estatais não financeiras, excluindo Petrobras/Eletrobras; bancos públicos ficam fora. A consolidação elimina relações internas, evitando duplicidade. O agregado de dívida Governo Geral exclui BCB e estatais; não inferir correspondência automática entre estoque e fluxo. As estatísticas regionalizadas por UF/capital/amostra têm cobertura e periodicidade diferentes. Não substituí-las pelo agregado nacional. Transferências não geram automaticamente recursos novos no consolidado; não compensar novamente valores cuja fonte já consolidou.

Metadados próprios de cada série reiteram critério de caixa/competência e definição dos três resultados (`metadata-concept.txt` e catálogo bruto). Não são séries de receitas, despesas ou funções: elas não informam gasto em saúde/educação, orçamento disponível, qualidade de serviço, mínimo legal ou causalidade.

## Precisão e reconciliação observadas

Todas as respostas de 2025 têm duas casas em milhões: **quantum publicado de R$ 10.000**. Converter para BRL por Decimal × 1.000.000 não autoriza afirmar precisão de centavos. Mostrar valores exatos convertidos com nota de precisão; manter o valor original e transformação na proveniência.

A equação em sinal SGS é `primário + juros − nominal = residual`. Os onze trios tiveram residual mensal máximo absoluto **0,01 milhão = R$ 10.000**, devido à publicação arredondada. As partições Federal+BCB, estados+municípios, três estatais e consolidado também tiveram diferenças mensais máximas de R$ 10.000. Os resíduos anuais são a soma dos mensais, conservados no JSON; não substituir o nominal publicado por uma soma forçada.

Recomendação de contrato derivada do quantum: limite mensal de três parcelas arredondadas = `3 × 0,005 milhão = R$ 15.000`; partição com três filhos e pai = `4 × R$ 5.000 = R$ 20.000`. Identidades em centavos/arredondamento do B1 (R$ 0,03) não podem ser reutilizadas. Para o acumulado, validar cada mês e preservar o resíduo anual; teto conservador = soma dos tetos mensais, não um novo arredondamento anual. Esses limites são propostas de engenharia, não tolerâncias normativas publicadas pelo BCB. Investigar discrepâncias além deles; nunca ajustar automaticamente.

| Recorte | Primário SGS 2025 (R$ milhões) | Juros (R$ milhões) | Nominal (R$ milhões) |
|---|---:|---:|---:|
| Federal + BCB | 58.687,11 | 891.879,89 | 950.566,98 |
| Estados | −5.452,94 | 100.542,84 | 95.089,90 |
| Municípios | −4.083,99 | 10.221,15 | 6.137,18 |
| Regionais | −9.536,92 | 110.764,01 | 101.227,06 |
| Estatais | 5.871,23 | 4.909,19 | 10.780,44 |
| Consolidado | 55.021,37 | 1.007.553,12 | 1.062.574,47 |

A [nota oficial de 30/01/2026](https://www.bcb.gov.br/content/estatisticas/hist_estatisticasfiscais/202601_Texto_de_estatisticas_fiscais.pdf) confirma as ordens de grandeza: déficit primário consolidado R$55,0 bi, Governo Central R$58,7 bi, superávit regional R$9,5 bi; juros consolidados R$1.007,6 bi e déficit nominal R$1.062,6 bi. Os totais da tabela acima são **somas de observações mensais atuais do SGS**, não números anuais independentes de maior precisão.

## Correspondência com B1, A e B2

Comparação documental/numérica: Federal+BCB SGS 4639/4606/4573 corresponde ao recorte de 10.07.1/10.08.1/10.09.1 republicado STN, **com sinal inverso e menor precisão**. Nos 36 pares de 2025 já coletados na pesquisa B1, `STN + SGS × 1e6` teve máximos absolutos R$4.449,29, R$4.646,49 e R$4.643,68, respectivamente, dentro de meio quantum SGS (R$5.000). Comparação feita com evidência B1 salva anteriormente; não é releitura simultânea das duas autoridades, nem garantia contra revisão posterior.

Guardar SGS bruto publicado e indicar `sign_convention=positive_deficit`. Se a interface optar por mostrar resultado com superávit positivo, aplicar apenas apresentação `display=-raw`, explicitando a transformação para os três componentes. Não chamar juros de “pagos” nem esconder juros negativos: a série de estatais federais teve juros anuais SGS **−R$2,93257 bi**.

O primário acima da linha RTN (A/base atual) é outra apuração: não comparar com tolerância de mero arredondamento nem substituí-lo pelo SGS. A execução por função (B2) usa ordem bancária/valor pago e inclui transferências/Extra-Siafi; não há mapeamento numérico automático para NFSP. Publicar uma tabela de correspondência metodológica, não uma soma entre bases incompatíveis.

## Requisitos mínimos propostos para integração futura

- Coorte própria/auxiliar de ano fechado com IDs fixos, 12 meses para todos os seis recortes/18 séries, hashes, licença, data de coleta e contrato de precisão/sinal versionado. Nenhuma URL contribuída pode disparar coleta.
- Triplas e duas partições principais validadas mensalmente: estados+municípios→regionais; Federal+BCB+regionais+estatais→consolidado. Não contar pai+filhos na mesma soma. Preservar resultados publicados e resíduos.
- Coleta atômica; tentativa truncada não cria conjunto parcial. Nova revisão preserva a anterior; última revisão inválida não recorre silenciosamente à antiga. Referência atual escolhe só o ano; valores de A/B2 não ancoram esta identidade.
- Para detectar uma revisão oficial durante as 18 consultas, reconsultar/confirmar hashes dos recortes âncora antes de commit; uma reconciliação pode passar apesar de revisão pequena dentro da tolerância. Não declarar sincronismo de publicação apenas por terem sido baixadas no mesmo dia.
- Camada observada sem projeção, receitas/despesas inventadas ou incorporação ao motor. API/painel separado, origem/precisão/sinal visíveis, ausência e comparação incompatível explícitas.

## Evidência e limites de completude

`catalog-nfsp-monthly.json`: resposta oficial, 33 metadados completos. `catalog-nfsp-all.json`: 70 resultados NFSP. `catalog-general-all.json`: 36 resultados Governo Geral. `sgs-<id>-2025.json`: 33 respostas brutas. `series-2025-verification.json`: metadata/hash, somas, 11 identidades, quatro partições e 36 comparações B1. Scripts próprios reproduzem a verificação sem banco.

Pesquisa comprova cobertura **temporal e dimensional destes agregados SGS**. Não comprova declaração integral por todas as prefeituras/UF, conjunto completo de receitas/despesas/funções subnacionais, correspondência com MEFP2014, dados individualizados por município, nem comparabilidade internacional. Estes continuam recortes separados do B3.
