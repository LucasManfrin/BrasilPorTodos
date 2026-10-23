# Gasto federal por função

DATA-07B2: integração da [pesquisa verificada](FEDERAL_SPENDING_RESEARCH.md) em coleta, revisão e leitura pública. Entrega local verificada em 2026-10-11; estado e evidência no [backlog](../project/BACKLOG.md).

## O que os valores representam

Fonte: [Despesas e Transferências Totais da União](https://www.tesourotransparente.gov.br/ckan/dataset/despesas-e-transferencias-totais), Secretaria do Tesouro Nacional, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Recorte federal descrito nos metadados do Orçamento Fiscal e da Seguridade Social, ordens bancárias e ajustes Extra-Siafi. Reais correntes, movimentos mensais do ano fechado correspondente à referência atual. Não é gasto consolidado de todos os governos nem classificação de resultados de uma política.

| Dimensão | Opções | Regra |
| --- | --- | --- |
| Natureza | Primária, Financeira, Extra-Siafi | Categorias literais da fonte; ajustes não são convertidos em despesa positiva |
| Estágio | Pago no exercício, RAP pago, pagamentos totais | Pago + RAP = total; o total não é uma terceira parcela para somar |
| Área | Função orçamentária federal | Código e rótulo originais preservados, sem atribuir grupos ausentes |

O padrão de leitura é Primária e pagamentos totais; todas as opções ficam acessíveis. São 29 funções observadas em 2025, códigos 01–28 e 99 Reserva de Contingência. Código 99 com rótulos N/A e OUTRAS fica separado como sem classificação, jamais renomeado para Reserva. Valores negativos e zeros explicitamente publicados são conservados.

Gastos desta base incluem transferências e operações com tratamentos próprios. Não comparar seu total diretamente com a despesa primária RTN ou somá-lo ao resultado nominal. Função Saúde/Educação não prova cobertura, qualidade, mínimo constitucional ou margem para corte. Outras abrangências permanecem DATA-07B3.

## Precisão, cobertura e conferência

A guia de dados é em reais; não aplicar a escala em milhões dos resumos a todo o arquivo. Normalização versionada: Decimal por linha, centavos half-even, sinais preservados; somar os registros normalizados. Conservar evidência de diferenças para a soma Decimal bruta: existem tanto ruído de representação quanto frações genuínas subcentavo nos ajustes.

Doze meses do arquivo completo são obrigatórios. Um grupo sem registros em determinado mês não recebe zero inventado. Somar os registros existentes no ano e informar os meses observados e contagem de linhas para cada natureza/função. Cobertura do arquivo não implica que cada combinação tenha doze observações explicitamente presentes.

A identidade pago + RAP = total é conferida por linha e nos agregados. Totais por natureza e função usam os mesmos registros: essa soma interna não é chamada de reconciliação externa independente. O resumo publicado da própria planilha cobre um subconjunto de categorias RTN; conferir exatamente esse subconjunto, sem somar pais e filhos. A pesquisa de 2025 conciliou os doze meses a centavos e encontrou +R$ 0,01 no anual, preservado e explicado pela normalização/soma. Nenhum resíduo artificial ou ajuste para forçar igualdade.

## Arquivo, revisão e banco

Uma coleta inteira forma um conjunto indivisível por fonte/recurso, ano, SHA-256, versões de parser e precisão. Somente agregados/proveniência são persistidos; o arquivo bruto de dezenas de megabytes e as linhas originais não são adicionados ao git. Selecionar a última revisão antes de validar; corrupção ou mudança incompatível na última revisão torna o estado incompleto, sem voltar silenciosamente a números antigos.

Migration 0011 cria `fiscal_spending_cohorts`, append-only, com revisão anual, fonte/autor/coleta, hash, versões, snapshot de fonte e payload JSONB com dinheiro em strings. Trigger impede UPDATE/DELETE; unicidade identifica a mesma revisão de arquivo/método. Correção exige nova revisão, nunca reescrita do conjunto anterior. Metadados e payload são validados antes de uma gravação atômica. Publicações e simulações existentes não recebem esses dados automaticamente.

Fonte oficial é criada/identificada pelo coletor, sem promover uma referência privada que coincida na URL. Visibilidade pública decorre do vínculo real com a coleta; os termos e o grupo de coleta são apresentados sem revelar autor privado ou credenciais.

## Consulta e operação

`GET /api/v1/indicators/spending/functions` lê o conjunto salvo do ano fechado da referência fiscal atual. Estados EMPTY, INCOMPLETE e AVAILABLE, períodos, revisão/hash, fonte/licença, data de coleta, atualização do recurso, versões e limitações explícitos. Não escolher outro ano silenciosamente nem substituir ausência por zero.

Brasil Atual tem painel expansível com natureza/estágio, três totais, funções e grupos sem classificação, valores compactos/exatos, cobertura e método. A interface confere o ano e as identidades em centavos inteiros; escopo funcional continua diferente do RTN.

Grupo `federal-spending` participa da coleta diária existente, com lock/cooldown. Leitura pública e recarregamento usam dados salvos; não baixar a planilha por visita. Pipeline aceita somente recurso deste catálogo oficial, com limites HTTP/ZIP/XML, cabeçalhos revisados, ano/meses/células e fórmulas validados; não executa Excel/macros/conexões externas nem URLs contribuídas. Falha conserva o último conjunto salvo e registra motivo público sem payload interno. Operação supervisionada de produção ainda pendente.


## Entrega verificada — 2026-10-11

609 testes backend passaram com PostgreSQL de integração, incluindo rollback da primeira coleta, revisões, imutabilidade por SQL e privacidade. 177 testes frontend, ESLint, TypeScript e build passaram. Ruff e formatação de 131 arquivos passaram; migration 0011 revertida/reaplicada somente em integração, Alembic sem drift. Demo recebeu apenas upgrade após backup.

Coleta oficial registrada terminou SUCCESS e importou uma revisão íntegra de 2025: 155.738 registros, 37 colunas, doze meses, 753 grupos mensais e 64 combinações anuais de natureza/função; 29 funções e dois rótulos sem classificação distintos. Os 2.259 valores mensais conferiram com a agregação independente da pesquisa. Pago + RAP = total em centavos; resumo publicado do subconjunto conciliou os doze meses e preservou diferença anual +R$ 0,01. Nova gravação do mesmo payload preservou ID, revisão 1 e referência corrente; nenhuma observação artificial foi adicionada ao catálogo.

Oito combinações de 360/768/1280/1920 nos temas claro/escuro com painel e método abertos passaram sem overflow da página. Tabela exata tem rolagem interna no celular; nove combinações de natureza/estágio em 360 px, sinais, grupos 99, teclado/foco de 3px e console sem erros/avisos conferidos. 46 pares visíveis de contraste passaram (23 por tema, mínimo 8,83:1); cabeçalho de 1×1 px recortado visualmente e mantido para leitores de tela excluído da medição visual. Fonte oficial mostrou licença ODbL e consulta atualizada, sem criar indicadores fictícios. Auditoria aprofundada permanece F2-01.

Checkpoint preservou quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados. API/site/worker diário local retomados. Não há atualização por visita, integração ao motor ou implantação pública; DATA-07B3 e operação supervisionada continuam pendentes.

Na verificação real, o primeiro processamento foi recusado pelo scanner de um metadado ignorado UTF-16 da própria planilha; suporte estrito de varredura UTF-16 foi acrescentado somente aos XML ignorados, sem execução, mantendo bloqueio de DTD/entidades e planilhas ativas UTF-8. Testes de regressão e arquivo completo passaram após o reparo. Última coleta registrada verificada conforme evidência desta entrega; sem alteração nos snapshots anteriores.
