# Emprego e renda — fontes e coleta

Verificação oficial e integração em 2026-10-10. As três séries são da PNAD Contínua, Brasil (`N1[1]`), divulgadas mensalmente sobre **trimestres móveis**. A referência 202608 representa junho–agosto de 2026. Não é um trimestre fixo nem uma medição diária em 01/08.

| Código implementado | Tabela / variável SIDRA | Unidade | Definição |
| --- | --- | --- | --- |
| renda-trabalho-real | [6390 / 5933](https://sidra.ibge.gov.br/tabela/6390) | Reais na origem; R$ na API | Rendimento médio mensal real bruto habitualmente recebido em todos os trabalhos das pessoas ocupadas de 14 anos ou mais com rendimento do trabalho. Não é nominal, efetivo, domiciliar ou renda de toda a população. |
| informalidade | [8513 / 12466](https://sidra.ibge.gov.br/tabela/8513) | % | Ocupados informais / população ocupada de 14 anos ou mais. Inclui empregados privados e domésticos sem carteira, empregadores e trabalhadores por conta própria sem CNPJ e trabalhadores familiares auxiliares. |
| participacao-forca-trabalho | [5944 / 4096](https://sidra.ibge.gov.br/tabela/5944) | % | Força de trabalho (ocupados + desocupados) / população de 14 anos ou mais. Não confundir com nível de ocupação ou desemprego. |

Metadados: [6390](https://servicodados.ibge.gov.br/api/v3/agregados/6390/metadados), [8513](https://servicodados.ibge.gov.br/api/v3/agregados/8513/metadados), [5944](https://servicodados.ibge.gov.br/api/v3/agregados/5944/metadados). [Glossário IBGE](https://anuario.ibge.gov.br/2023/glossario-2023.html) e [definição das categorias informais](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/46676-pnad-continua-trimestral-desocupacao-sobe-em-15-das-27-ufs-no-1-trimestre-de-2026).

## Evidência da coleta

As três séries tiveram SUCCESS em 10/10/2026, com 35 observações cada, de out/2023 a ago/2026, usando a janela inicial de três anos do coletor existente. Últimos valores recebidos: renda R$ 3.777,00; informalidade 37,5%; participação 62,2%. São registros do banco, sujeitos a revisão; nenhum valor foi fixado no frontend.

A lista oficial de períodos da renda apontou agosto/2026 como última referência, com modificação em 29/09/2026. Data da divulgação/modificação, período observado e data da nossa consulta são distintos. [Períodos da renda](https://servicodados.ibge.gov.br/api/v3/agregados/6390/periodos). O catálogo atual contém 14 indicadores e 12 fontes oficiais distintas de três instituições. Fontes conserva seu visual e apresenta os novos registros pelo cadastro existente.

O parser valida identidade, unidade revisada, localidade nacional, ausência de classificações adicionais, períodos, números finitos e limites. Ausências não viram zero. Taxas entre 0 e 100; renda não negativa. Mantêm-se Decimal, URLs construídas por catálogo revisado, HTTP limitado, autorização, lock/cooldown e auditoria/revisões.

## Renda real e base de preços

A [nota técnica 02 do IBGE](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Mensal/Notas_tecnicas/nota_tecnica_02_pnadc_mensal.pdf) estabelece o deflacionamento pelo IPCA aos preços do trimestre móvel mais recente divulgado. A variável 5933 não entrega esse trimestre-base como campo explícito: a proveniência o identifica pela metodologia e pela última referência global da publicação, nunca pelo último mês solicitado numa janela histórica.

O coletor confere a referência global, seu valor, os períodos disponíveis e datas de modificação. Reconsulta a janela inicial e **todo o histórico já armazenado**, inclusive referências mais antigas que três anos. Valida todos os sublotes em memória e repete a conferência da âncora oficial; mudança durante a leitura ou ausência de mês já armazenado rejeita o lote. Grava tudo em uma transação, com referência/base de preços, unidade original Reais, URLs oficiais, hash do conjunto de períodos e motivo de revisão. Falha conserva o conjunto anterior.

A revisão reconhece mudança de base mesmo quando o valor arredondado permanece igual. “Máx.” significa histórico disponível no projeto (35 observações nesta inicialização), não toda a série desde 2012.

A API externa não oferece versão transacional imutável, e a data de modificação tem precisão de dia. A conferência antes/depois reduz inconsistências entre divulgações; não prova um snapshot externo. A transação local garante que o lote validado avance por inteiro. Renda real é contexto social: não se soma à base fiscal nominal nem vira receita automaticamente.

## Comparação e termos

Desemprego, renda real, informalidade e participação comparam o mesmo trimestre móvel do ano anterior; meses vizinhos compartilham dois meses. Taxas usam p.p.; renda usa variação percentual entre valores positivos na mesma base. Direção não representa julgamento de melhora/piora, significância amostral ou causa.

Preservados atribuição IBGE — PNAD Contínua, tabela/variável, referência, coleta e revisões. O cadastro existente usa “Termos do portal IBGE” e seu [link de política do portal](https://www.ibge.gov.br/acesso-informacao/acoes-e-programas/politica-de-privacidade.html). Os metadados não declaram licença SPDX/Creative Commons/ODbL; a consulta da página de política recebeu 403 nesta pesquisa. Portanto não se afirma uma licença específica de redistribuição, nem que política de privacidade seja licença de dados. MIT cobre código e documentação autoral, sem relicenciar dados oficiais.

## Sugestões, sem implementação nesta entrega

- Subutilização: [SIDRA 6441 / variável 4118](https://sidra.ibge.gov.br/tabela/6441), %, trimestre móvel; combina desocupação, insuficiência de horas e força potencial sobre a força ampliada. Fonte verificada; inclusão depende de decisão do mantenedor.
- Endividamento das famílias e inadimplência: candidatas para Dívida/Preços e juros; verificar séries, populações e definições antes de implementar.

Nenhum dos três novos indicadores ficou em preparação. PIB em volume continua em preparação, fora desta ampliação. Na execução real, IBC-Br e dívida líquida tiveram falha HTTP; dados anteriores preservados e status público explícito.
