# Escopo da V1

## Estado atual — 2026-10-23

O núcleo descrito abaixo foi implementado localmente; as extensões posteriores autorizadas estão nos registros datados e no [backlog](../project/BACKLOG.md). A entrega atual visa uso no próprio computador, com launchers Windows, banco existente e preservação do legado. Serviço público é um marco separado.

| Extensão autorizada | Disponível localmente | Limite |
| --- | --- | --- |
| Criação acessível UI-06 | IDEIA privada/compartilhada explicitamente, guiado/manual, confirmação e retomada, checklist/promoção para COMPLETA, cópias/sugestões e denúncia/moderação | Gemini opcional integrado; chamada real conferida localmente. Desativado por padrão nos exemplos; avaliação sistemática real pendente. Não abre automaticamente cadastro público. |
| Análise de completa | Sensibilidade fiscal declarada ajustável pelo motor, com método/recortes explícitos | Sem confiança estatística ou impacto causal. IDEIA e ausência de estimativa não entram na conta. |
| Completude documental | Ordenação por fontes/financiamento, revisão `NOT_ASSESSED`, legado sem nota retroativa | Sem avaliação técnica de propostas, reputação ou popularidade. |
| Contextos/grafos | Contrato, curadoria com revisão/publicação, explorador WebGL/lista e explicação | Pesquisa real precisa de pessoa revisora; grafo de demonstração fictício, sem magnitudes causais ou IA de curadoria. |
| Operação local | Start/stop/status nativos, Compose completo local, schema até 0017 e backup/restauração exercitados | Hospedagem, HTTPS e supervisão pública separados; coleta e IA opcionais. |

[Contrato da criação](PROPOSAL_CREATION.md) · [Método](../data/METHODOLOGY.md) · [Estado detalhado](../project/STATUS.md). “Fora da V1” abaixo registra o recorte original; não anula extensões explicitamente entregues e datadas. IA de análise de mérito, comentários/votos e modelos macroeconômicos continuam fora.

## Objetivo

Permitir compreender o Brasil Atual, criar propostas estruturadas e reunir versões específicas dessas propostas em Planos Brasil com simulação fiscal simples e fontes rastreáveis.

## Acesso

| Perfil | Permissões |
| --- | --- |
| Visitante | Ler indicadores, fontes públicas, versões publicadas de propostas e planos, histórico, simulações publicadas e metodologia |
| Autenticado | Cadastrar fontes por URL; criar, editar, simular e publicar suas propostas e planos |
| Administrador | Manter indicadores e usuários; tratar conteúdo inadequado e arquivar conteúdo com motivo registrado |

Rascunhos são privados ao autor e ao administrador. Login, cadastro e renovação de sessão têm fluxos próprios; autenticar não autoriza editar conteúdo de outra pessoa. Alterações em conteúdo publicado geram um novo rascunho.

## Entregas

### Brasil Atual e indicadores

Começar com cerca de 15 indicadores candidatos: PIB, PIB per capita, inflação, juros, desemprego, receita, despesa, resultado primário, dívida, dívida/PIB, população, pobreza e gastos em Previdência, Saúde e Educação. Seleção final depende de definições, cobertura e fontes verificadas.

Cada indicador apresenta descrição, unidade, referência temporal, abrangência, instituição, fonte por URL, data de coleta/atualização e histórico disponível. A ausência de um dado deve ser visível, sem valores inventados.

### Fontes

Referências externas com título, instituição, URL HTTP/HTTPS, tipo, publicação quando conhecida, data de acesso e descrição. Tipos: oficial, legislação, estudo científico, relatório técnico, relatório institucional, jornalismo e outro. Vincular uma fonte à versão de uma proposta com descrição de uso.

Não armazenar arquivos nem buscar automaticamente URLs arbitrárias pelo backend. Uma fonte só ligada a rascunho não deve expor o conteúdo privado no catálogo público.

### Propostas

Campos de publicação: título, resumo, problema, solução, categoria, período de implementação, estado da estimativa fiscal e fontes/justificativa rastreável. Categorias: Economia, Tributação, Educação, Saúde, Segurança, Previdência, Infraestrutura, Assistência Social, Administração Pública, Ciência e Tecnologia, Habitação, Energia, Meio Ambiente e Outros.

Impacto fiscal: `ESTIMATED`, `NOT_ESTIMATED` ou `NOT_APPLICABLE`. Quando estimado, informar ano, tipo, valor em reais e premissas. Cada parcela também declara ente, critério contábil, preços/ano-base, componente primário ou juros e cobertura anual; ausência permanece explícita. [Contrato](../data/FISCAL_COMPATIBILITY.md). Tipos: nova despesa, redução de despesa, nova receita e redução de receita.

Para nova despesa ou redução de receita, informar financiamento: corte de gasto, nova receita, aumento de tributo, dívida, substituição de programa, crescimento de arrecadação, não financiado ou outro. `UNFUNDED` é permitido e gera aviso; uma descrição de financiamento não entra automaticamente no cálculo como receita.

### Planos Brasil

Título, resumo, visão, período, autor e estado. Reunir propostas, ordenar e ativar/desativar itens no rascunho. Cada item aponta para uma **versão publicada específica** de proposta. Publicar congela essa composição e os parâmetros da execução fiscal.

Exibir resultado por ano, acumulado, premissas, versão do motor, propostas sem financiamento e impactos não estimados. Atualizar itens de um plano publicado exige nova versão do plano.

### Simulação

Um Cenário Base; soma anual de receitas adicionais e economias menos novas despesas e reduções de receita. O total é o efeito incremental das medidas estimadas, não uma previsão do orçamento ou da economia. Ver [docs/data/METHODOLOGY.md](../data/METHODOLOGY.md).

### Navegação e transparência

Busca e paginação de propostas, planos e fontes; filtros simples por categoria, autor e horizonte temporal conforme aplicável. Catálogos públicos exibem conteúdo publicado; arquivados permanecem acessíveis no histórico com sinalização.

Páginas públicas: `/`, `/brasil`, `/brasil/[indicador]`, `/propostas`, `/propostas/[slug]`, `/planos`, `/planos/[slug]`, `/fontes`, `/metodologia`, `/transparencia`.

Autenticação: `/entrar`, `/cadastro`. Área privada: `/painel`, `/painel/propostas`, `/painel/propostas/nova`, `/painel/propostas/[id]`, `/painel/planos`, `/painel/planos/novo`, `/painel/planos/[id]`, `/painel/fontes`.

## Fora do recorte original da V1

Upload de estudos/arquivos, comentários, votos, likes, seguidores, reputação, rankings, revisão por pares, grafo e sincronização de forks, Claims estruturados e sua contestação, colaboração simultânea, avaliação automática por IA, notificações, crowdfunding, aplicativo mobile, projeções de PIB/pobreza/emprego, impacto distributivo e cálculo previdenciário completo.

## Critério de conclusão

1. Visitante lê indicadores com referência e fonte, propostas e planos sem login.
2. Cria conta, cadastra uma fonte por URL, cria e publica proposta com impacto e financiamento explícitos.
3. Cria plano, inclui a proposta, verifica o cálculo anual e os avisos e publica.
4. Outro visitante consulta o plano, sua composição e resultado sem conta.
5. Uma nova versão da proposta não altera o plano anterior; o histórico continua acessível.
6. Rascunhos e dados de conta não vazam na API pública; escrita sem sessão e edição alheia são recusadas.
7. Testes de domínio, integração e fluxo completo passam; metodologia e limitações são acessíveis.

A fundação do repositório não representa a conclusão desses critérios.

## Histórico do escopo

Os registros datados abaixo preservam decisões anteriores. O quadro de estado atual acima prevalece sobre adiamentos e configurações antigos.

## Atualização de interface em 2026-10-06

O mantenedor solicitou uma home com sua motivação, identidade nas cores nacionais e mesma interface nas demais telas. A duplicação de propostas/planos foi incorporada como cópia autenticada para um rascunho privado, com atribuição ao original. Não publica automaticamente nem modifica a versão original; termos de conteúdo continuam pendentes. Apoios/comentários são sinalizados como futuros, sem ações ou contadores fictícios. Ver docs/design/DESIGN.md e ADR-020.

## Base atual e atualização implementadas — 2026-10-07

Sete séries oficiais automatizadas, histórico e comparação temporal, estado das fontes e atualização restrita a administrador. Novas versões de propostas/planos preservam uma base contextual parcial; atualizar rascunho exige ação explícita. Versões antigas sem base continuam identificadas assim. Saldo fiscal segue incremental: base fiscal nacional calculável depende de receitas/despesas compatíveis e PIB nominal. Ver [pesquisa necessária](../data/RESEARCH_BRIEF.md). IA, causas automáticas, apoios/comentários e Google login não estão implementados.

## Base fiscal observada implementada — 2026-10-09

Onze séries oficiais: as sete séries contextuais iniciais, três séries mensais RTN do Governo Central e PIB nominal trimestral IBGE. A base seleciona o último ano fechado com doze meses compatíveis, reconcilia os três agregados e, se houver quatro trimestres do mesmo ano, calcula suas proporções do PIB nacional. Falhas preservam os dados anteriores e lacunas não viram zero. Os snapshots de novas versões incluem a base fiscal e o denominador; publicações anteriores permanecem intactas.

O saldo das propostas continua incremental. Somá-lo a uma referência histórica ou projetar anos futuros depende de metadados de ente, critério e período dos impactos e de premissas explícitas (DATA-06). Esta entrega não representa orçamento consolidado do Brasil. Ver [contrato fiscal](../data/FISCAL_BASELINE.md).

## Emprego e renda ampliados — 2026-10-10

Catálogo atual com 14 séries oficiais: renda real habitual, informalidade e participação PNAD acrescentadas às onze anteriores. Histórico real, revisões, proveniência e atualização diária pelo coletor existente. Renda mantém preços coerentes em todo o histórico armazenado; não é receita fiscal. [Definições e fontes](../data/EMPLOYMENT_INDICATORS.md).

Brasil Atual mostra todos os indicadores por tema, mesmo quando destacados, e preenche as últimas linhas. Fontes conserva o visual aprovado com novos registros. Não foram implementados subutilização, endividamento, inadimplência, grafos, IA ou projeções causais nesta entrega.

## Compatibilidade histórica — 2026-10-10

Metadados fiscais preservados por parcela e avaliação versionada por execução, com motivos para ausência/divergência e tratamento do legado. Recortes declarados compatíveis não comprovam custos/causas. Base observada e impactos continuam separados. Um cenário futuro opcional permite comparar premissas anuais declaradas com parcelas compatíveis, com revisão humana e resultados preservados; não produz previsão oficial nem efeitos causais.

## Evolução do editor adiada — 2026-10-10

O épico UI-06 foi atualizado: **Criar proposta acessível**, com entrada simples e rigor na publicação completa. “Me ajuda a montar” (IA) e “Eu preencho” (manual por etapas) produzem o mesmo molde/análise, com alternância sem perda. IDEIA precisa só de título/uma frase e pode ser compartilhada explicitamente com selo “ideia em construção”; não entra no cálculo, planos ou ranking. COMPLETA exige problema, medida, financiamento, quem ganha/perde, riscos, fontes e campos fiscais, com checklist. Roteiro guiado fixo, igual para todos os temas/posições, confirmado pelo usuário, sem números inventados nem opinião da IA; análise calculada pelo motor. Limites/denúncia/ranking por solidez e testes registrados de imparcialidade são gates da abertura.

**Requisito futuro, ainda não implementado:** as regras atuais de rascunho privado, publicação, NOT_ESTIMATED/UNFUNDED e composição de planos permanecem no código até uma entrega específica do épico. Compartilhar IDEIA será exposição autorizada de um novo nível, não abertura automática dos rascunhos existentes. Rankings, denúncias, assistência e faixas/selos novos não passam a existir por esta atualização documental. [Requisito completo](PROPOSAL_CREATION.md).


## Cenário opcional nos planos — DATA-06B2

Modo incremental continua padrão. Cenário anual manual restrito ao Governo Central, caixa, preços nominais e componentes primários; ausência não vira zero. Até 30 anos posteriores à referência, uma premissa justificada por ano. Fontes por URL sem consulta automática. Confirmação autoral vinculada às entradas; edição/cópia exige revisão correspondente. Resultado conjunto condicionado aos recortes, separado do histórico e do efeito incremental. Criação guiada por IA segue adiada em UI-06.


## Criação acessível implementada localmente — 2026-10-19

Supera o adiamento de 2026-10-10 acima: UI-06A/B/E entregues e D concluído no recorte de sensibilidade declarada. IDEIA precisa de título/frase, começa privada, compartilhar exige ação explícita e editar retira a fotografia pública. Não entra em planos, cálculo ou ranking. Promoção exige checklist rigoroso no servidor, preservando regras fiscais e publicações imutáveis. Completa não se torna evidência de eficácia por cumprir campos.

Guiado/manual usam o mesmo contrato e confirmação. Roteiro fixo 1.0.0 público, “não sei” válido; Gemini apenas organiza palavras literais, sem decidir pergunta, mérito ou cálculo. Sem chave o guiado continua funcional sem IA. C/F e épico UI-06 ficam Preparados até avaliação real do modelo escolhido, ainda sem chave do mantenedor. Novas capacidades e limites detalhados em [PROPOSAL_CREATION](PROPOSAL_CREATION.md). Não reescrever versões legadas nem encerrar a revisão de conteúdo real por testes fictícios.
