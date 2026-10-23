# DATA-07B3 — SICONFI por ente: pesquisa verificada

Pesquisa somente leitura em 2026-10-11. Nenhuma integração, alteração de banco/runtime ou coleta em massa. Amostras: estado de São Paulo (IBGE 35) e município de São Paulo (3550308), exercício 2025. Não representam cobertura nacional.

## Recomendação

Para uma tela nacional, preferir o agregado oficial EFGG/GFSM, selecionado para integração no [contrato EFGG](GENERAL_GOVERNMENT.md). A DCA é alternativa útil para uma futura consulta por estado/município e sua composição funcional. Não produzir uma soma nacional própria de milhares de declarações nem misturar DCA com RTN. O recorte DCA implementável é anual por ente, receitas brutas/deduções observadas, despesa empenhada/liquidada/paga do exercício e RAP pago separado, com homologação, cobertura e revisão explícitas.

## Fontes primárias e termos

- [API/documentação oficial](https://apidatalake.tesouro.gov.br/docs/siconfi) e [Swagger YAML](https://apidatalake.tesouro.gov.br/docs/siconfi.yaml): JSON, sem chave, limite publicado de **uma requisição por segundo**; paginação padrão 5.000.
- [Apresentação da API](https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos): acesso automático público sem identificação/captcha. FINBRA é acesso/divulgação dos dados recebidos pelo SICONFI, não um critério fiscal novo.
- [Catálogo DCA](https://www.tesourotransparente.gov.br/ckan/dataset/api-dca-entes); package `26fab98f-8cd2-4d34-9176-eef0fb4a296e`; `license_id=odc-odbl`, ODbL confirmado na API CKAN. [Metadados DCA](https://www.tesourotransparente.gov.br/ckan/dataset/26fab98f-8cd2-4d34-9176-eef0fb4a296e/resource/1c5351ca-fcb4-4077-9bd9-95bdec8a204d/download/metadadosdca.pdf).
- [Catálogo RREO](https://www.tesourotransparente.gov.br/ckan/dataset/api-rreo-entes); package `b74a4483-54f5-4625-8d23-e65515b075ef`; ODbL também confirmado. [Metadados RREO](https://www.tesourotransparente.gov.br/ckan/dataset/b74a4483-54f5-4625-8d23-e65515b075ef/resource/a387c7ae-6993-4710-9054-9e9be549b66d/download/metadadosrreo.pdf).
- [Extrato de entregas](https://www.tesourotransparente.gov.br/ckan/dataset/api-extrato-entes): package `7c4dc876-2151-4d07-ac5f-9ee128637aca`, ODbL; [metadados](https://www.tesourotransparente.gov.br/ckan/dataset/7c4dc876-2151-4d07-ac5f-9ee128637aca/resource/171d3640-2357-4651-b91c-4eb059af78da/download/metadadosextratoentregas.pdf).
- [Regras da DCA 2025, atualizadas em 18/08/2026](https://siconfi.tesouro.gov.br/siconfi/pages/public/arquivo/conteudo/2026_Regras_Gerais_e_Instrucoes_de_preenchimento_DCA_2025_18_08_2026.pdf): unidade/abrangência pp.5–10, validações cruzadas I-D/I-E e I-F/I-G pp.27–30. [Tabela de fatos DCA 2025](https://siconfi.tesouro.gov.br/siconfi/pages/public/arquivo/conteudo/2026_Tabela_de_fatos_dca_2025_06022026.pdf): dimensões da receita p.70 e funções pp.130–147.
- [Tabela RREO Estados 2025](https://siconfi.tesouro.gov.br/siconfi/pages/public/arquivo/conteudo/2025_Tabela_de_Fatos_RREO_Estados_24092025.pdf), [Municípios 2025](https://siconfi.tesouro.gov.br/siconfi/pages/public/arquivo/conteudo/2025_Tabela_de_Fatos_RREO_Municipios_24092025.pdf).

Apache 2.0 no `info.license` do Swagger não substitui ODbL dos conjuntos de dados. Recursos CKAN apontam documentação HTTP; o cliente deve utilizar HTTPS verificado. Frequência dos valores DCA é anual, consulta atualizada diariamente; catálogo antigo não prova atraso das declarações atuais.

## Contrato HTTP real

Origem permitida `https://apidatalake.tesouro.gov.br`; prefixo `/ords/cdwhprd/siconfi/tt/`.

| Caminho | Parâmetros da amostra | Uso |
| --- | --- | --- |
| `entes` | nenhum | cadastro observado, não cobertura anual de entregas |
| `anexos-relatorios` | nenhum | nomes de anexos por esfera/demonstrativo |
| `extrato_entregas` | `id_ente=35&an_referencia=2025` | homologação/retificação/MSC por instituição |
| `dca` | `id_ente=35&an_exercicio=2025` | declaração anual completa |
| `dca` | mesmo + `no_anexo=DCA-Anexo%20I-C` | anexo revisado |
| `rreo` | `id_ente=35&an_exercicio=2025&nr_periodo=6&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo%2001` | execução acumulada no sexto bimestre |

Envelope real: `items`, `hasMore` boolean, `limit`, `offset`, `count`, `links`. Teste `limit=2&offset=2` devolveu dois registros, `hasMore=true`, próximo offset4. **Links contêm hostname interno `*.oraclevcn.com`**, não usar seus `href`: reconstruir apenas offset/limit no host/caminho oficiais. Página completa só quando `hasMore=false`, offsets/counts coerentes e não há repetição de identidade. Limites de bytes/páginas/tempo/linhas, nenhum redirect ou URL contribuída; cadência global ≤1req/s.

`valor` vem como JSON número decimal ou inteiro; usar `parse_float=Decimal`, não float. A saída das amostras tem até dois decimais em reais correntes; não escala de milhões. Preservar rawDecimal e precisão original, sem inventar centavos de medição. Nenhuma duplicata da chave completa nas duas amostras.

## Rubricas e dimensões que importam

| Anexo | Rubrica/coluna | Tratamento |
| --- | --- | --- |
| I-C | `ReceitasExcetoIntraOrcamentarias`, `ReceitasIntraOrcamentarias`, `TotalReceitas`; `Receitas Brutas Realizadas` | três raízes; total = exceto + intra; não somar pai/filho |
| I-C | `Deduções - Transferências Constitucionais`, `Deduções - FUNDEB`, `Outras Deduções da Receita` | deduções publicadas **positivas**; subtrair só na transformação definida, não trocar o sinal original |
| I-C | `RO1.7.0.0.00.0.0`, `RO2.4.0.0.00.0.0` | transferências correntes e de capital, já contidas na receita |
| I-C | `RO1.7.1.0.00.0.0`, `RO1.7.2.0.00.0.0`, `RO1.7.5.1.00.0.0` | União, estados/DF e FUNDEB; são filhos, não novas parcelas para somar ao total |
| I-D | `TotalDespesas`; `Despesas Empenhadas`, `Despesas Liquidadas`, `Despesas Pagas` | estágios alternativos do mesmo exercício, não parcelas aditivas |
| I-E | `TotalDespesas` **reutilizado em todas as linhas** | funções e subfunções estão na dimensão textual `conta`; não deduplicar pelo código |
| I-F/I-G | `Restos a Pagar Processados Pagos`, `Restos a Pagar Não Processados Pagos` | pagamento de compromissos anteriores; distinto do pago I-D/I-E |

Na função, raiz textual `Despesas Exceto Intraorçamentárias`, linhas `01 - Legislativa` etc., subfunções `01.031 - Ação Legislativa`, filhos `FU01 - Demais Subfunções` e raiz `Despesas Intraorçamentárias` compartilham código. Identidade mínima: `(exercicio, cod_ibge, instituicao, anexo, rotulo, coluna, cod_conta, conta)`; preservar nomes originais e validar contra taxonomia2025. Expor só pais funcionais de dois dígitos; não somar seus subfilhos. Intra tem total separado, sem detalhamento por função observável na amostra. Não distribuir proporcionalmente.

DCA anual é exercício inteiro, **não série de doze meses**. Pago do exercício + RAP processado pago + RAP não processado pago permite um agregado de desembolso orçamentário explicitamente derivado quando as três raízes existem; não primário RTN nem resultado GFSM. Empenhado, liquidado e inscrição de RAP não entram nessa soma.

RREO combina colunas `No Bimestre (b)` e `Até o Bimestre (c)`, além de estágios de despesa acumulados. Para anual usar apenas referência6/acumulado do ano e verificar demonstrativo/periodicidade. Nunca somar seis acumulados. Município simplificado precisa contrato próprio; não presumir equivalência dos anexos. Anexo03/RCL móvel de12meses não substitui receita orçamentária; anexo06 primário/nominal não é saldo receita bruta menos despesa.

## Prova Decimal de 2025

| Observação (R$) | Estado SP | Município SP |
| --- | ---: | ---: |
| Receita bruta total I-C | 413939458032.76 | 127308730789.66 |
| Bruta exceto intra | 400067309037.12 | 116192464926.51 |
| Bruta intra | 13872148995.64 | 11116265863.15 |
| Deduções FUNDEB total | 41120790900.41 | 3087353262.86 |
| Outras deduções total | ausente | 769578035.44 |
| Empenhado I-D | 385042592630.74 | 123571806691.25 |
| Liquidado I-D | 369170001590.10 | 117009214332.57 |
| Pago I-D | 348860917805.89 | 116798206872.08 |
| RAP processado pago I-F | 21649760401.40 | 257583808.54 |
| RAP não processado pago I-F | 8279736803.03 | 4805151784.37 |
| Soma derivada de pagamentos | 378790415010.32 | 121860942464.99 |

As duas receitas brutas conferiram exceto+intra=total, diferença0.00. Em todas as colunas observadas I-E/I-G, somar apenas funções disponíveis conferiu com a raiz exceto intra a centavos. Acrescentar a raiz intra quando presente conferiu com I-D/I-F. Onde intra não tem observação, a conferência cruzada fica **não verificável**, não zero. Vinte e quatro funções observadas nos três estágios principais em cada ente; conjuntos diferentes.

Estado: no RREO6, receita realizada total372818667132.35 e pago total348860917805.89; a receita coincide com bruta DCA menos FUNDEB observado; essa evidência não transforma outras deduções ausentes em zeros. Não publicar um líquido DCA universal sem política explícita e validada para campos omitidos. O RREO fornece seu próprio agregado realizado, separadamente rastreável.

SHA256 DCA estado `1c2f696e3b74558dd6abb6bee3aefb651aef114646f013bc6da0d0a45cfe1556`, 3.458 registros/1.111.009bytes. Município `2e4ca6d39e619d37ee94737208254790bd110fa79f482f3e727ac1a67969735c`, 3.197registros/1.063.733bytes. Ambos `hasMore=false`.

## Completude, revisões e correspondência futura

Extrato DCA usa `entregavel=Balanço Anual (DCA)`, `periodicidade=A`, `periodo=1`, status `HO` ou `RE`; `data_status` é homologação/retificação, não referência fiscal/coleta. DCA das amostras HO em30/04/2026; RREO6 de ambas RE (16/04/2026 estado,12/05/2026 município). Preservar timestamp/instituição/tipo/status original e versão interna append-only. A API não expôs identificador imutável da declaração: ler extrato antes/depois do lote, rejeitar mudança durante paginação, hash canônico de registros ordenados+proveniência e fontes congeladas. Homologação prova entrega, não certificação de exatidão ou auditoria independente.

Cadastro `entes` retornou5.598 registros: M5570, E26, D1, U1, todos `exercicio=2026`; o DF é `D` no cadastro, mas RREO usa esferaE. Não anunciar esses5570 como universo2025 já coberto. É necessário validar roster específico do exercício e divisões territoriais, separar solicitado/observado/entregue/ausente/falhou/inconsistente e cobertura institucional da DCA. Não consultei todas as declarações nem provei completude nacional. A API examinada não expõe o conjunto de órgãos/CNPJ da cobertura que a interface SICONFI permite consultar; a declaração consolidada recebida é a abrangência operacional, com limitação visível.

DCA inclui poderes e entidades dependentes do ente; suas transferências recebidas/realizadas já estão nos agregados. Tirar intraorçamentárias não elimina operações entre União/estados/municípios. A soma de entes duplica transferências intergovernamentais; a consolidação nacional requer eliminações recíprocas e metodologia própria. Mapeamento por natureza funcional DCA não converte regime orçamentário em regime GFSM/competência ou caixa RTN. Critério futuro: mesma identificação territorial/ano/estágio, declaração final estável, somas do próprio anexo e entre anexos, deduções/sinais preservados, nada adicionado à referência RTN/motor.

## Contrato curto recomendado (futuro)

`{status, year, entity:{ibge_code,name,uf,sphere}, scope:ENTITY_DECLARED_OFSS, currency:BRL, price_basis:CURRENT, periodicity:ANNUAL, report:DCA, accounting_basis:BUDGET_EXECUTION_STAGE_SPECIFIC, declaration:{institution,status,periodicity,period,data_status,type}, source, collected_at, parser_version,taxonomy_version,precision_version, fingerprint, row_count, coverage:{requested_entities,observed_entities,institutional_coverage_verified:false,missing_cells}, observations:[{annex,table,column,account_code,account_label,amount}], totals:{gross_revenue,paid_current_year,rap_processed_paid,rap_nonprocessed_paid}, functions:[{code,label,stage,amount}], intra:{stage,amount}, reconciliation, limitations}`.

Unavailable/null permanece separado de zero explícito. Status AVAILABLE significa recorte solicitado validado, não Brasil completo. Cada escolha de estágio/rubrica possui nome em linguagem clara. Nenhum snapshot já publicado muda.

## Reproduzir a evidência

Na pasta mirror: `python outputs/data07b3-research/sample.py` realiza sete consultas fixas, com pausa1.1s; `reconcile.py` gera `reconciliation.json` usando Decimal e somente pais funcionais; `probe.py pagination-sample.json` confirma paginação. `state-dca.json`, `city-dca.json`, seus extratos, cadastro/anexos, YAML e catálogos CKAN ficam apenas no mirror. Não incluir respostas completas no git; report/fixtures pequenos bastam após revisão. Nenhum resultado de pesquisa foi gravado em produção.
