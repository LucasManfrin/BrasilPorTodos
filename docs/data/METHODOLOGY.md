# Metodologia da V1

## O que a plataforma apresenta

**Dado observado:** valor publicado por uma fonte, com unidade, referência, recorte e data de coleta. **Estimativa:** cálculo com hipóteses explicitadas pelo autor. **Proposta:** escolha de política pública que pode usar dados e estimativas como justificativa.

Cadastrar uma fonte não comprova automaticamente uma afirmação. A descrição de uso deve explicar o que a referência sustenta. Tipo oficial ou científico não substitui avaliação de contexto e qualidade.

## Cálculo fiscal

Para cada ano do período do plano:

```text
líquido = reduções de despesa + novas receitas
        - novas despesas - reduções de receita
acumulado = soma dos líquidos anuais
```

Resultado positivo representa melhora incremental do saldo fiscal pelas medidas cadastradas; negativo representa piora. O cálculo não entrega o resultado primário total do país nem a trajetória da dívida.

Exemplo exclusivamente didático: economias de R$ 30 bilhões + receitas de R$ 20 bilhões − despesas de R$ 40 bilhões − redução de receitas de R$ 5 bilhões = R$ 5 bilhões no ano.

## Regras de entrada e interpretação

- Valores em reais na base de preços declarada por parcela, sem conversão/indexação automática. Preços constantes exigem ano-base. Metadados ausentes ou misturados impedem interpretar o somatório como conta homogênea; o legado conserva ausência explícita. [Contrato de compatibilidade](FISCAL_COMPATIBILITY.md).
- Valores usam Decimal com centavos, magnitudes finitas e não negativas. O tipo define o sinal. JSON deve transportar dinheiro como string decimal.
- Somente propostas habilitadas e impactos dentro do período entram no cálculo. Impactos fora dele geram aviso e são excluídos.
- `NOT_ESTIMATED` não equivale a zero. A soma dos valores conhecidos deve ser rotulada como parcial e identificar propostas não estimadas.
- `NOT_APPLICABLE` é uma declaração explícita que precisa de justificativa; não produzir linhas de impacto fictícias.
- Em proposta estimada, anos sem linhas significam nenhum efeito cadastrado naquele ano; não extrapolar ou repetir automaticamente um valor.
- Financiamento é explicação de como cobrir um impacto. Para afetar o resultado, uma economia ou receita deve existir como impacto anual explícito, contado uma única vez. Endividamento não melhora o saldo fiscal primário calculado.
- Repetir a mesma versão de proposta num plano é inválido. Sobreposições entre propostas distintas podem existir e precisam ser informadas; a V1 não detecta automaticamente todas elas.

## Reprodução

Execuções publicadas identificam versão do plano, versões de propostas, impactos habilitados, horizonte, versão do motor, premissas e momento da execução. Snapshots dos dados usados evitam alterações silenciosas por mudanças posteriores em cadastros.

A versão inicial do motor é `1.0.0`. Mudanças na aritmética exigem nova versão do motor e documentação. A avaliação adicional de recortes tem versão própria 1.0.0, preservada no snapshot/hash das novas execuções; não recalcula as antigas. A biblioteca valida entradas e emite avisos; execuções publicadas já preservam entrada e resultado para consulta. A base fiscal observada acrescentada depois continua separada do cálculo incremental do motor.

## Limitações

A V1 não modela crescimento do PIB, inflação futura, comportamento dos contribuintes, multiplicadores, transição demográfica, juros da dívida, efeitos distributivos, emprego ou viabilidade jurídica. Não oferece intervalos de confiança sem estimativas que os sustentem.

O Cenário Base organiza indicadores observados e medidas cadastradas. Indicadores contextualizam a análise; não entram automaticamente como previsão de receitas/despesas futuras. A soma é uma ferramenta para explicitar escolhas e hipóteses.

## Correções

Correções em propostas e planos geram novas versões. Correções de dados oficiais mantêm referência à divulgação original, motivo e data da revisão. Arquivamento sinaliza estado e preserva histórico, observadas futuras regras documentadas para retirada de conteúdo inadequado.

## Brasil de referência — 2026-10-07

Uma nova versão parte das últimas observações disponíveis. Cada número conserva sua própria referência e abrangência; "atual" significa último publicado/coletado, não valor de hoje para todos os indicadores. Snapshot e hash são preservados ao publicar e integram a entrada da simulação. Rascunhos podem adotar nova base por ação explícita. Versões legadas não recebem números posteriores como se fossem a base histórica.

Na entrega de 2026-10-07, a base era exclusivamente contextual. A entrega de 2026-10-09 acrescenta um objeto fiscal observado do Governo Central e PIB nacional para proporções, descritos abaixo; isso continua sem representar um orçamento nacional completo. Taxas (%), índices e estoques não podem ser somados a fluxos anuais em reais. O resultado do simulador permanece a variação incremental das medidas informadas, com avisos para bases distintas e dados ausentes.

As comparações não demonstram causalidade: desemprego exige avaliar participação, ocupação, renda e informalidade; janelas trimestrais móveis se sobrepõem. IBC-Br sem ajuste sazonal é comparado com o mesmo mês do ano anterior e não chamado de PIB. Separar observação, hipótese sobre motivo, evidência concorrente e consequência observada/projetada. Modelo para revisão humana em [RESEARCH_BRIEF](RESEARCH_BRIEF.md). Análise por IA permanece futura.

## Referência fiscal observada — 2026-10-09

A base fiscal usa o Resultado do Tesouro Nacional: receita primária líquida, despesa primária e resultado primário do Governo Central, em caixa/pagamento efetivo, acima da linha, reais nominais. Exige doze meses das três séries no mesmo ano fechado e conjunto compatível. Pode recuar para um ano completo anterior, mas identifica explicitamente o recuo; ano parcial não é anualizado.

```text
resultado primário calculado = receita primária líquida − despesa primária
```

O resultado publicado pela fonte permanece preservado, junto com a diferença entre o calculado e o publicado. A importação usa Decimal e conversão de R$ milhões para reais, com half-even nos centavos; reconciliação mensal aceita até R$ 0,03. O total anual soma os meses e pode acumular diferenças mensais de arredondamento. Não esconder a diferença nem alterar um dos agregados para forçar igualdade.

Na coleta real da entrega, o ano comum de 2025 apresentou receita de `2332555301431.48`, despesa de `2394249610412.52`, resultado publicado de `-61694308980.99` e resultado calculado de `-61694308981.04`, em reais. A diferença calculado menos publicado foi `-0.05`. Esses valores registram a evidência da entrega, não constantes imutáveis do país; revisões posteriores geram nova fotografia.

## PIB como denominador, não como orçamento

O PIB nominal nacional é a soma de quatro trimestres do mesmo ano da SIDRA 1846, variável 585, classificação 11255/categoria 90707. São valores a preços correntes e de mercado, em R$ milhões com duas casas decimais: precisão publicada de R$ 10.000. O total anual das CNT é revisável e não se apresenta como resultado anual definitivo do SCN.

```text
proporção fiscal = 100 × fluxo anual do Governo Central / PIB nacional do mesmo ano
```

As proporções são apresentadas com quatro casas decimais. O numerador continua sendo Governo Central e o denominador representa a economia nacional; a razão não torna o fluxo um gasto do Governo Geral nem indica recursos disponíveis. Sem quatro trimestres válidos do mesmo ano, não calcular proporção; a conta absoluta continua disponível.

Para a fotografia da entrega, o PIB anual de 2025 foi `12738565620000.00` reais. Receita, despesa e resultado publicado corresponderam a `18.3110%`, `18.7953%` e `-0.4843%` desse PIB, respectivamente. Não inferir precisão econômica de centavos pela representação monetária, nem interpretar o déficit primário isolado como resultado nominal ou cumprimento de meta fiscal.

## Preservação da referência e limites do cenário

Os conjuntos RTN e PIB são validados e gravados atomicamente, com fontes, unidades, critérios, períodos e impressão digital. Podem ser atualizados independentemente e manter o conjunto anterior quando a origem falhar. A montagem anual usa revisões atuais coerentes. O RTN identifica os três componentes de cada mês em conjunto; o PIB identifica os quatro trimestres do ano em conjunto. Mudar um componente pode gerar revisão dos demais valores inalterados daquele conjunto, sem fabricar uma mudança monetária.

Rascunhos e publicações preservam a fotografia que adotaram. Atualização diária não muda uma publicação existente; nova base exige ação explícita no rascunho. O objeto fiscal fica separado dos demais indicadores e da soma incremental de impactos.

DATA-06A acrescenta metadados por impacto e avaliação persistida de compatibilidade com a referência histórica. DATA-06B acrescenta um cenário futuro opcional, separado do observado, com receita/despesa anuais declaradas e revisão humana sobre exclusão das medidas. Repetir um ano histórico em todos os anos futuros não é previsão. Outros entes, juros, resultado nominal, efeitos comportamentais e relações causais exigem métodos próprios e não entram silenciosamente no cálculo.

Contratos, identificadores das fontes e seleção do período em [docs/data/FISCAL_BASELINE.md](FISCAL_BASELINE.md).

## Cenário anual declarado — 2026-10-10

DATA-06B1/06B2 implementam motor puro e integração opcional ao plano, com premissas, revisão e resultados preservados. Usa premissas explícitas de receita/despesa em cada ano futuro, sem repetir a referência histórica. Só combina parcelas compatíveis com esse cenário nominal primário do Governo Central; ausência/divergência/estimativa desconhecida/dupla contagem não revista/componentes negativos ou acima do limite bloqueiam todo o horizonte. Cenário declarado não é observado nem previsão oficial. [Contrato](FISCAL_SCENARIOS.md).

A confirmação de exclusão dos efeitos está vinculada ao hash do snapshot, período, premissas e composição. Mudanças fiscais exigem nova revisão; cópias/novos rascunhos não herdam confirmação. É uma declaração humana, não detector de dupla contagem nem validação causal. Configuração incompleta impede simular/publicar cenário ativo; incompatibilidade de parcelas mantém os valores separados e a combinação indisponível.

## Composição primária — DATA-07A

Detalhar receita total/transferências e quatro grupos diretos de despesa do mesmo RTN, ano e critérios. Soma assinada preserva incentivos negativos; pai e filhos não entram juntos. Três identidades mensais têm tolerância R$ 0,03 e diferença anual publicada, sem resíduo artificial. Essa classificação não é gasto por Saúde/Educação nem espaço automaticamente disponível para uma proposta. Composição separada não altera snapshots ou o motor. [Contrato e evidência oficial](FISCAL_COMPOSITION.md).

## Juros e resultado nominal — DATA-07B1

Leitura observada do Governo Central separada da conta primária acima da linha: primário abaixo da linha em caixa + juros assinados por competência = nominal em regime misto. Não subtrair duas vezes o juro negativo, tratar como amortização ou somar aos impactos das propostas. Doze meses do mesmo ano, fonte/coleta e residual explícitos; métodos e versões anteriores preservados. [Contrato e fontes](FISCAL_INTEREST.md).

## Gasto federal por função — DATA-07B2

Separar natureza Primária/Financeira/Extra-Siafi e pago no exercício/RAP/total. Rótulos do código 99 sem classificação não viram Reserva. Dinheiro Decimal normalizado por linha com half-even versionado; identidade e diferenças explicitadas, cobertura observada sem zeros imputados. Classificação funcional federal não equivale ao RTN nem prova qualidade/mínimos/margem para cortes. [Contrato](FISCAL_SPENDING.md).


## Outros governos e consolidação oficial

EFGG tem competência modificada, Governo Geral/estados/municípios e eliminação publicada de transações entre unidades. Não equivale ao RTN, NFSP ou funções OFSS. Cobertura/extrapolação e precisão explicitadas; valores assinados e resíduos preservados. Sem soma automática de medidas ou efeito causal inferido. [Contrato e correspondência](GENERAL_GOVERNMENT.md).


## Contextos e evidências — DATA-05A

Contrato isolado diferencia observação referenciada, hipóteses/alternativas, contrapartidas, evidências e consequências observadas/projetadas. Fonte oficial ou correlação não prova causa. Revisão correspondente é registro declarado vinculado ao conteúdo, não autenticação, autorização ou selo de verdade. Persistência, publicação e primeiros contextos humanos permanecem DATA-05B/C; não há contexto causal real publicado, grafo, IA ou efeito numérico novo. [Contrato](CONTEXT_EVIDENCE.md).


## Revisão/publicação de contexto — DATA-05B

API agora persiste contextos privados e exige revisão por administrador distinto antes da publicação pelo autor. Metadados oficiais e recortes vêm de referências reais; conteúdo publicado conserva a versão/registro humano/fontes. Checklist é conferência humana registrada, sem prova causal, coeficientes ou avaliação automática de ideia. Interface e primeiros contextos efetivamente pesquisados/revisados continuam DATA-05C. [Contrato](CONTEXT_EVIDENCE.md).


## Contextos na interface — DATA-05C

Dados, explicações possíveis e consequências ficam separados nas telas públicas. Publicação preserva a observação exata e revisão/fontes; indicador posterior não altera a análise. Editor manual salva privadamente e exige conferência por outro administrador; aceitação não certifica causalidade. Primeiro rascunho pesquisado está [preparado para revisão humana](FIRST_CONTEXT_RESEARCH.md), sem análise real publicada. Grafo, IA e coeficientes continuam futuros.


## Grafo qualitativo — GRAPH-01A

Uma aresta registra uma alegação documentada sobre aumentar/adotar a origem e a dimensão de destino, com premissas, contrapontos e limites. Tipos de efeito e consenso são rótulos declarados; revisão correspondente não autentica revisor, publica ou prova causa. Contrato puro diagnostica duplicatas/conflitos/ciclos e preserva versões/fontes; não calcula impactos em cadeia, magnitude ou efeito fiscal. [Contrato e sequência](GRAPH_CONTRACT.md).


## Criação guiada e sensibilidade declarada — 2026-10-19

O roteiro `1.0.0` é público e igual para todos os temas e posições. A fonte de verdade é `backend/app/modules/guidance/script.json`, servida em `GET /api/v1/guidance/script`; a página Metodologia apresenta as mesmas perguntas. Nenhum modelo escolhe a pergunta seguinte:

1. Que nome você daria à sua ideia?
2. Em uma frase, o que você quer mudar?
3. Qual problema você quer resolver e quem vive esse problema?
4. O que mudaria na prática com a sua proposta?
5. Quem poderia ganhar com isso?
6. Quem poderia perder com isso?
7. O que poderia dar errado?
8. De onde sairia o dinheiro e em quais informações você se baseia? Se não souber, pode dizer não sei.

Cada resposta exige confirmação humana antes de preencher. “Não sei” deixa o campo sem estimativa. O modo guiado funciona sem IA. Com o prompt 4.0.0, Gemini desenvolve a intenção informal em redação de proposta e pode sugerir possibilidades de implantação, contrapartidas e lacunas. Essas sugestões ficam separadas e desmarcadas; o autor escolhe e confirma, com rótulo de ponto a avaliar. Não são efeitos comprovados ou posições já assumidas. Não deve inventar números, fontes ou legislação. Original e proposta aparecem antes da confirmação. O servidor valida formato e tamanho, sem rejeitar sugestões por comparação semântica com o original. O prompt orienta a geração; o autor confere fatos, intenção e sugestões antes de aceitar. O sistema não comprova fidelidade nem veracidade da saída. Resultado gerado recebe “assistido por IA”; não é revisão de mérito nem cálculo. [Contrato, limites e privacidade](../product/PROPOSAL_CREATION.md).

`DECLARED_SENSITIVITY_1` calcula sensibilidade de uma **versão pública completa e estimada**, com o motor fiscal `1.0.0`, sem alterar a publicação ou o resultado dos planos. IDEIAs, legado sem o novo contrato, não estimado e não aplicável retornam indisponibilidade explícita. A conta exige parcelas no período e recortes homogêneos de ente, critério contábil, preços/ano-base, componente e cobertura anual. Ausência e mistura bloqueiam a faixa; não viram zero nem combinação implícita com a referência nacional.

O autor escolhe multiplicadores de custos (nova despesa/redução de receita) e ganhos (nova receita/redução de despesa). Mínimo entre 0 e 1; máximo entre 1 e 2; ambos contêm o valor declarado 1. A entrada aceita strings decimais com até quatro casas. Todos os quatro começam em 1; sem ajuste não existe faixa artificial.

| Resultado | Custos | Ganhos |
| --- | --- | --- |
| Saldo menor nas premissas escolhidas | Multiplicador máximo | Multiplicador mínimo |
| Valores declarados | 1 | 1 |
| Saldo maior nas premissas escolhidas | Multiplicador mínimo | Multiplicador máximo |

O backend usa Decimal (precisão intermediária 40), arredonda cada parcela ao centavo com `ROUND_HALF_UP` e chama o motor para resultados anuais/acumulados. Identifica versões do método/motor e premissas na resposta de `GET /api/v1/guidance/impact/{slug}?version=...`. O financiamento descritivo não é somado como receita; só parcelas explícitas entram uma vez. Limites monetários continuam válidos.

O rótulo é **estimativa declarada**: custos não foram verificados pelo cálculo. A faixa não contém probabilidades, confiança estatística, previsão causal ou efeito de grafo. Não calcula emprego, PIB, dívida ou sobreposição entre políticas. Selos causais “efeito direto”/“especulativo” não são inferidos deste exercício.

`DOC_COMPLETENESS1` ordena completas por documentação: uma fonte vinculada (1), financiamento definido diferente de `UNFUNDED` (1), revisão técnica (0, `NOT_ASSESSED`, ainda indisponível). Máximo contratual três; máximo disponível dois. Não é ranking de popularidade, qualidade política ou comprovação da fonte. Legado não recebe pontuação retroativa; IDEIAs ficam fora.
