# União, estados, municípios e Governo Geral

DATA-07B3 integra a referência anual das Estatísticas Fiscais do Governo Geral (EFGG) da Secretaria do Tesouro Nacional. Entrega local concluída em 2026-10-12: coleta real, API/painel, revisões e preservação verificados; estado no [backlog](../project/BACKLOG.md) e [evidência](../development/VERIFICATION.md). Não amplia automaticamente o motor, os cenários declarados ou as bases congeladas dos planos.

## Fonte selecionada e abrangência

[Publicação e tabela oficial](https://www.tesourotransparente.gov.br/publicacoes/estatisticas-fiscais-do-governo-geral), metodologia [GFSM/MEFP 2014](https://www.gov.br/tesouronacional/pt-br/estatisticas-fiscais-e-planejamento/estatisticas-fiscais-do-governo-geral). O arquivo atual do segundo trimestre de 2026 contém a tabela 2.1 anual por esfera, incluindo 2025; a data da publicação não é o ano do dado. Não somar tabelas anuais, trimestrais e acumuladas como parcelas distintas.

Os oito grupos originais ficam separados: Governo Central Orçamentário; Extraorçamentário; consolidação interna do Central; Central consolidado; estaduais; municipais; consolidação entre esferas; Governo Geral consolidado. Os dois grupos de consolidação são ajustes, não novos governos. Zero só aparece quando a célula original o publica; vazio não vira zero.

Metadados do arquivo descrevem 26 estados e Distrito Federal, cobertura municipal aproximada de 90% e extrapolação da STN para o universo de 5.570 informado pela fonte. Não afirmar que todas as prefeituras foram observadas, que esse universo corresponde ao cadastro atual nem produzir nossa própria extrapolação. O Governo Central Orçamentário exclui o Banco Central. O setor público consolidado do BCB tem outro perímetro e não é sinônimo de Governo Geral.

## Conceitos e correspondência

| Conjunto | O que permite ler | O que não corresponde automaticamente |
| --- | --- | --- |
| RTN acima da linha | Governo Central, primário em caixa e pagamento efetivo | Receita/Despesa GFSM, todos os entes, juros ou gasto por função |
| B1 abaixo da linha | Primário e juros/nominal do Central, regime misto | Execução orçamentária paga ou despesa GFSM |
| B2 OFSS | Função federal, pago do exercício e RAP, naturezas e ajustes | COFOG, serviços de todos os entes ou soma nacional |
| EFGG | Receita, gasto, investimento líquido e capacidade/necessidade, competência modificada, consolidação oficial | Saldo primário RTN, orçamento de cada prefeitura ou corte fiscal disponível |
| DCA/SICONFI | Declarações anuais por ente e estágios da execução | Governo Geral consolidado; ausência de declaração não é zero |
| NFSP/SGS | Resultados abaixo da linha por governo, com precisão/sinal próprios | Receita/Despesa GFSM ou Governo Geral |

Despesa agregada EFGG inclui gasto mais investimento líquido em ativos não financeiros. Receita menos essa despesa corresponde à capacidade (+) ou necessidade (−) de financiamento da própria fonte. Juros recebidos e pagos ajudam a definir o resultado primário publicado no GFSM; nenhum primário RTN é substituído nessa conta. Investimento líquido pode conter valores assinados e não representa apenas novas obras.

Função orçamentária nacional e COFOG são classificações distintas. A publicação COFOG de Governo Geral verificada cobre 2024, enquanto a execução federal B2 cobre 2025. Não mapear códigos só pelo nome, comparar anos como se fossem iguais ou calcular transferência/custo causal a partir dessa correspondência. [COFOG oficial](https://www.tesourotransparente.gov.br/publicacoes/despesas-por-funcao-do-governo-geral).

## Consolidação e precisão

Usar a coluna de ajuste publicada pela STN. Para cada métrica, orçamentário + extraorçamentário + ajuste central = Central; Central + estaduais + municipais + ajuste entre esferas = Governo Geral. Preservar sinais. Transferências e juros entre unidades do mesmo setor são eliminados pela consolidação da fonte; não somar outra vez o total consolidado às parcelas ou às transferências do RTN.

Valores originais em milhões de reais correntes, lidos com Decimal e convertidos a BRL; centavos half-even por célula agregada, política versionada, valores brutos/células de origem preservados como proveniência. Centavos internos não são precisão econômica garantida. Conferir identidades, partições e referência da tabela 3.1 com tolerância de R$ 0,03; na revisão real de 2025 o maior resíduo absoluto foi R$ 0,01; mostrar o resíduo efetivo, sem corrigir valores para forçar igualdade. Tabela 3.1 do mesmo arquivo confere o agregado do Governo Geral; não é uma segunda fonte externa independente.

## Conjunto e consulta

Um recurso completo validado gera uma revisão anual imutável em `general_government_cohorts`, migration 0012. Conservar SHA-256, parser/precisão, fonte/termos congelados, coleta UTC e agregados string JSONB. O arquivo bruto permanece fora do Git. Mesma revisão semântica não duplica; nova semântica exige nova versão. Selecionar a revisão mais recente do ano antes de validar, sem voltar silenciosamente a uma anterior incompatível.

`GET /api/v1/indicators/government/general`: leitura pública salva, ano fechado da referência fiscal atual, estados EMPTY/INCOMPLETE/AVAILABLE, período, revisão, fingerprint, fonte/termos, cobertura, equações, diferenças e limitações. Não usar outro ano silenciosamente nem estender a abrangência da base RTN. Painel próprio em Brasil Atual; a leitura padrão é Governo Geral, com opções Central, estados e municípios, ajustes e valores exatos no método.

Grupo diário `general-government` usa o lock/cooldown do coletor. Download apenas dos endereços oficiais revisados, com limites HTTP/ZIP/XML, identidade e ano das tabelas. Nenhuma URL contribuída é consultada; visita/recarregamento não baixa arquivo. Falhas conservam os conjuntos anteriores e registram motivo público limitado. Fonte privada com URL igual não é promovida.

## Termos e alternativas verificadas

Este arquivo utiliza os [Termos de uso do Tesouro Transparente](https://www.tesourotransparente.gov.br/sobre/dados-abertos/termos-de-uso), com atribuição à Secretaria do Tesouro Nacional e URL. Não receberá ODbL por analogia a outro conjunto CKAN. A atribuição não significa aprovação da STN e não inclui sua logomarca. Os termos pedem comunicação à STN sobre produtos que usam os dados; registrar o contato no [roteiro de publicação](../governance/PUBLICATION.md), sem envio externo automático nesta tarefa.

[SICONFI por ente](SICONFI_RESEARCH.md) e [NFSP do BCB](PUBLIC_SECTOR_RESEARCH.md) conservam pesquisas e alternativas. Não foram habilitados novos coletores de milhares de declarações, rankings ou seletores por prefeitura. Futura granularidade deve ter contrato/cobertura/cadência próprios; não é requisito para fabricar uma soma nacional agora.
