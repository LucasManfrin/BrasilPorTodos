# Pesquisa de gasto federal por função

Estado em 2026-10-11: **fonte verificada e contrato preparado, sem pipeline ou dados funcionais no produto**. DATA-07B2 permanece Preparado. Esta pesquisa orienta a próxima implementação; não é uma nova parcela já conciliada da referência fiscal.

## Fonte e unidade verificadas

[Despesas e Transferências Totais da União](https://www.tesourotransparente.gov.br/ckan/dataset/despesas-e-transferencias-totais), Secretaria do Tesouro Nacional, atualização mensal e licença declarada [ODbL](https://opendatacommons.org/licenses/odbl/1-0/). [Arquivo oficial 2025](https://www.tesourotransparente.gov.br/ckan/dataset/8675a0a4-31c5-4593-a24d-fb8e17376eca/resource/f40d5431-058d-48b8-9ab6-065fb0fce5b3/download/limite-gastos-lc200dez25.xlsx), recurso `f40d5431-058d-48b8-9ab6-065fb0fce5b3`, atualizado em 2026-02-25 segundo o catálogo consultado. Não confundir data de atualização, ano do dado e data da coleta.

Arquivo lido integralmente: 34.500.062 bytes; SHA-256 `886f4e3266e99907f976c4815dfe8da99ebcf9c670a6ce331925913e88e64b88`. Guia de dados: 155.738 linhas, ano 2025, movimentos dos doze meses. Valores em **reais correntes**; resumos podem ter unidade diferente, inclusive milhões. A presença de classificações RTN/LC 200 não torna o total funcional igual à despesa primária RTN.

[Metadados oficiais](https://www.tesourotransparente.gov.br/ckan/dataset/8675a0a4-31c5-4593-a24d-fb8e17376eca/resource/7f4f368c-646a-4155-856d-5e8b8c6ba42a/download/metadados-despesa-valor-pago---ec-95.pdf) identificam Governo Central/Orçamento Fiscal e da Seguridade Social, emissão de ordem bancária, RAP e ajustes Extra-Siafi. O documento antecede LC 200: não aplicar seus filtros antigos de EC 95 a 2025. Não representar saúde/educação de todos os entes, mínimos constitucionais ou qualidade dos serviços.

## Dimensões que precisam continuar separadas

Estágios iniciais: `DESPESAS_PAGAS` (pago no exercício), `RESTOS_A_PAGAR_PAGOS` (RAP pago) e `PAGAMENTOS_TOTAIS`. Identidade pago + RAP = pagamentos totais verificada em todas as linhas após normalização a centavos, diferença máxima zero. Empenhado/liquidado não substituem pagamentos.

Naturezas literais: **Primária**, **Despesa Financeira** e **Extra-Siafi**. Não descartar a terceira, converter ajustes negativos em despesas positivas ou assumir que operações financeiras não tenham tratamento específico na apuração primária. Somar valores da fonte mantém sinais e inclui transferências; isso não equivale à despesa RTN da referência atual.

São 29 funções orçamentárias observadas (01–28 e 99 Reserva de Contingência). Código **99** também aparece com os rótulos **N/A** e **OUTRAS**, em ajustes Extra-Siafi. Preservar natureza, código e rótulo; não fundir esses registros com Reserva. Zero explicitamente presente é diferente de grupo ausente.

| Exemplos anuais verificados, natureza Primária | Pago exercício | RAP pago | Total |
| --- | ---: | ---: | ---: |
| Saúde | R$ 214.921.315.805,14 | R$ 22.971.987.502,51 | R$ 237.893.303.307,65 |
| Educação | R$ 145.605.580.182,60 | R$ 23.448.725.698,83 | R$ 169.054.305.881,43 |

Estes exemplos são evidência revisável de pesquisa, não constantes de produção, limites para cortes ou consolidação de estados e municípios. Natureza Financeira e Extra-Siafi têm parcelas distintas para essas funções.

## Precisão e reconciliação

XML contém tanto ruído de representação binária quanto frações genuínas subcentavo em Extra-Siafi. Pesquisa conservou Decimal bruto e normalizou por linha a centavos com half-even. A implementação deve versionar e testar a política de precisão; não afirmar que todo dígito adicional é erro.

Resumo Pagamento Total da planilha cobre um subconjunto explícito de categorias RTN, incluindo operações financeiras selecionadas e Extra-Siafi. Reagregar exatamente esse subconjunto conciliou os doze meses com residual zero. Soma anual por linhas/meses a centavos: R$ 2.962.347.486.199,07; resumo anual arredondado uma vez: R$ 2.962.347.486.199,06, residual **+R$ 0,01**, preservado.

Essa conferência ajuda a verificar unidade/leitura, mas não é total externo independente para cada função/natureza/estágio. Comparar totais das mesmas linhas por caminhos diferentes não constitui reconciliação independente. Não inventar residual “outras” nem forçar equivalência com RTN.

## Aceite da próxima implementação

- Download automático de recurso deste catálogo oficial, HTTPS/host/caminho/ano validados, sem URLs contribuídas ou chave de API. Verificar também redirecionamentos, licença e revisão do recurso.
- Parser XLSX por streaming, limites de download/ZIP expandido/linhas/strings, CRC, índices, cabeçalhos e células; rejeitar arquivos truncados, ZIP bomb, paths anômalos, fórmulas ou definições desconhecidas. Não executar Excel, macros ou conexões externas. Parser de pesquisa não é o pipeline de produção.
- Conjunto indivisível por fonte/recurso/ano/hash/versão de parser e normalização; todas as naturezas e estágios da mesma revisão. Falha conserva o último lote bom, sem preencher ausência com zero.
- Dinheiro Decimal/NUMERIC; sinais e rótulos originais, frações Extra-Siafi e estágios preservados, cobertura dos doze meses explícita. Valores compactos/exatos e consulta por função/natureza/estágio.
- Fonte/licença/coleta/atualização/hash/método e diferenças acessíveis; agrupamentos sem classificação visíveis. Recurso bruto grande fora do git; fixture pequena com proveniência e agregados verificáveis.
- Catálogo auxiliar separado de baseline/current, snapshots e motor até existir ponte metodológica explícita. Não tratar orçamento funcional como parcela direta do resultado primário atual.

DATA-07B1 é a camada separada de [juros/nominal](FISCAL_INTEREST.md); DATA-07B3 mantém outras abrangências. Estados atuais e aceite no [backlog](../project/BACKLOG.md). Nenhuma fonte SIOP substitui este contrato automaticamente: licença, RAP e periodicidade exigem verificação própria.

## Continuação da pesquisa

A pesquisa original acima permanece como evidência. Contrato de integração, regras de revisão e consulta em [FISCAL_SPENDING](FISCAL_SPENDING.md); implementação/verificação em andamento, sem antecipar conclusão do DATA-07B2.


Integração DATA-07B2 concluída localmente em 2026-10-11, incluindo coleta real, migração, testes e painel. A pesquisa acima conserva sua evidência histórica; contrato e estado atual em [FISCAL_SPENDING](FISCAL_SPENDING.md).
