# Histórico do estado do projeto

Arquivo preservado em 2026-10-23. Configurações, números de testes e pendências abaixo correspondem às respectivas datas, não ao estado atual. Consulte [STATUS](STATUS.md).

# Estado do BrasilPorTodos

Atualizado em 2026-10-22. Este documento é a visão atual; evidências anteriores permanecem no [histórico de verificação](../development/VERIFICATION.md) e no [backlog](BACKLOG.md).

## Onde estamos

**V1 funcional localmente, preparada para organizar contribuições.** Código público e serviço público são marcos separados. A arquitetura e o núcleo estão alinhados à visão: entender o país, propor medidas com custos/fontes e combinar planos comparáveis, com histórico preservado.

| Área | Implementado | Limite ou próximo trabalho |
| --- | --- | --- |
| Produto e interface | Home, Brasil Atual, Fontes, propostas, planos, cadastro; painel/editor/detalhes públicos consolidados em UI-07; consentimento único por criação/sessão e navbar agrupada; celular e dois temas | Auditoria completa de acessibilidade e regressão automatizada do navegador |
| Contas e publicação | Autenticação, autorização/autoria, rascunhos privados, versões imutáveis, cópias com atribuição | Termos/privacidade vigentes e operação pública |
| Dados oficiais | 14 indicadores BCB/IBGE/Tesouro e treze séries fiscais auxiliares, mais execução funcional federal e EFGG anual por esfera em conjuntos próprios; revisões, proveniência e coleta controlada | Definir cobertura mínima do catálogo; qualidade/termos e operação persistente |
| Referência fiscal | Governo Central, ano fechado; primário RTN/PIB, composição, juros/nominal, execução funcional e EFGG por esfera separados | Agregados observados, cobertura municipal estimada explícita; granularidade por ente e catálogo mínimo futuros |
| Simulação | Impactos incrementais; compatibilidade histórica; cenário futuro opcional declarado, revisado e preservado nos planos | Novos recortes no motor exigem contrato separado; sem previsão causal |
| Explicações | Definições/fontes/metodologia, contrato/API e interface de contextos, edição e revisão autorizada/publicação imutável (DATA-05A/B/C) | Primeiro rascunho pesquisado entregue na interface (C); revisão humana efetiva e publicação real pendentes |
| Grafos e evidências | GRAPH-01A/B/C: contrato, API de curadoria, WebGL 3D/lista, explicação e versões públicas | Primeiro mapa real exige pesquisa/revisão; magnitudes causais e curadoria por IA pendentes |
| Criação acessível | IDEIA/COMPLETA com entradas distintas (captura rápida/preparação), guiado/manual, revisão humana da saída da IA (prompt 4.0.0), checklist, compartilhamento/cópia/sugestões e moderação | Gemini 3.5 Flash-Lite configurado e chamada autenticada real conferida; disponibilidade externa e avaliação sistemática pendentes; sem revisão técnica de propostas |
| Análise da proposta | Sensibilidade fiscal DECLARED_SENSITIVITY_1 da COMPLETA publicada estimada, pelo motor e com premissas ajustáveis | Estimativa declarada; sem probabilidade, previsão causal ou cálculo de IDEIA |
| Operação local | Launchers nativos e Compose completo, banco persistente, migrations até 0017, backup/restauração e cópia conferidos | Supervisão pública, HTTPS e lançamento separados; coleta oficial opcional não iniciada |

## O que ainda não prometemos

O saldo das medidas **não é uma previsão do saldo do Brasil**. A base histórica contextualiza as publicações; o motor 1.0.0 agrega efeitos incrementais. Novas parcelas carregam declarações de ente, critério, preços, componente e período; dados ausentes não são inferidos. A avaliação verifica esses recortes contra a referência histórica preservada, sem validar o custo; a comparação com premissas futuras é um método adicional separado.

Há cenário opcional nos planos para combinar premissas futuras anuais declaradas com medidas compatíveis. A confirmação humana evita alegar exclusão não revista; não detecta sobreposições semânticas. Não há cálculo causal de emprego/pobreza/PIB ou orçamento de todos os governos. A assistência opcional Gemini organiza palavras; não avalia o mérito da proposta nem calcula impactos. O explorador do grafo permite investigar alegações e não calcula esses efeitos. Nenhum indicador isolado demonstra causa, significância ou avaliação de governo. A renda real da PNAD não é receita fiscal.

## Verificação e operação

**Conferência atual de 2026-10-19:** fluxo novo e operação local descritos no fechamento abaixo; contagens finais e resultados de QA em [VERIFICATION](../development/VERIFICATION.md). Os números e estados operacionais dos parágrafos datados/anteriores são históricos, não uma nova execução de hoje.

### Registro histórico da curadoria do grafo — 2026-10-14

1.237 testes backend passaram com PostgreSQL exclusivo de integração: 107 novos testes de transporte e 94 integrações de grafos, além da suíte anterior. Ruff/formatação de 162 arquivos e links locais passaram. Migration 0014 revertida para 0013/reaplicada apenas em integração; Alembic sem drift. Demo recebeu somente upgrade após backup; checkpoint preservou integralmente dois contextos/quatro versões/uma revisão/uma publicação anteriores, um conjunto funcional B2, um EFGG B3, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados.

Operação local conferida: health/ready/site/proxy e listas de grafos/nós/arestas HTTP 200, escrita anônima 401. Demo sem seed do grafo. Pesquisa real de desemprego preservada em duas versões privadas, zero revisões/publicações; leitura pública 404. PostgreSQL nativo/API/Next.js/worker retomados em loopback, sem inicialização automática com o computador. Última coleta em estado `PARTIAL` na conferência; houve falhas de conexão URLError em fontes externas, mantendo históricos. Não foi determinada a causa externa nem alterado o coletor. Operação supervisionada segue pendente.

Registros abaixo conservam o estado das entregas anteriores; não substituem o fechamento de 2026-10-19.

DATA-05B: 918 testes backend passaram com PostgreSQL de integração, incluindo 46 integrações de contextos. Ruff/formatação de 150 arquivos e links locais passaram. Migration 0013 revertida/reaplicada somente em integração; Alembic sem drift. Demo recebeu somente upgrade após backup, e checkpoint preservou todos os conjuntos/publicações/execuções anteriores. Sem frontend alterado, testes/build/navegador não foram repetidos; 197 testes frontend/build de DATA-07B3 permanecem evidência anterior. [VERIFICATION](../development/VERIFICATION.md).

DATA-07B3 tem coleta real 2025: 64 valores de oito grupos/métricas em revisão 1 imutável, validação contra extração independente da planilha e oito referências internas da tabela 3.1. Consolidação e competência modificada GFSM próprias, termos STN, cobertura municipal aproximadamente 90% com extrapolação oficial explícita. Maior resíduo R$ 0,01, tolerância R$ 0,03. Não é soma de DCA nem resultado RTN/BCB. Repetição idempotente; arquivo/link/hash e origem das células preservados.

Oito combinações de 360/768/1280/1920 e claro/escuro, quatro recortes no celular, teclado/foco e console conferidos. Nenhuma rolagem horizontal da página; tabelas rolam internamente. 38 pares de contraste passaram, mínimo 10,18:1. Auditoria aprofundada de acessibilidade continua F2-01.

Na entrega DATA-07B3, coleta registrada completa SUCCESS; EFGG não altera base fiscal, motor ou snapshots. A consulta diária atualizou legitimamente a data da Selic de 11/10 para 12/10/2026 e o contexto corrente, sem alterar dados fiscais ou publicações. Checkpoint preservou um conjunto B2, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados.

Next.js, FastAPI, PostgreSQL nativo isolado e worker diário retomados em loopback; leituras usam dados salvos e worker aguarda a janela. Ele não inicia sozinho com o computador. Compose completo, operação supervisionada e lançamento público permanecem pendentes; comunicação do produto à STN rastreada em [PUBLICATION](../governance/PUBLICATION.md). Não houve commit/push/deploy.

Operação conferida em 2026-10-13: API/site/proxy HTTP 200, escrita anônima 401, zero contextos reais criados. Worker diário retomado terminou PARTIAL: consultas de dívida bruta e renda real falharam, conservando seus históricos. Não foi determinada a causa externa exata nem alterado o conector. Checkpoint posterior confirmou preservação das publicações/execuções/conjuntos anteriores; operação supervisionada mantém pendências.

## Caminho até o produto completo

1. Abrir colaboração: publicar o código revisado, executar CI no remoto, definir canais e proteção de branch. [Preparação](../governance/PUBLICATION.md).
2. DATA-06 entregue no recorte restrito: compatibilidade histórica e cenário declarado opcional, com autorização, versões/snapshots e interface. Publicações legadas preservadas. [Cenários](../data/FISCAL_SCENARIOS.md).
3. DATA-07A/B1/B2/B3 entregues: composição primária, juros/nominal, execução funcional federal e Governo Geral por esfera separados. Definir cobertura mínima F1-03 e granularidade individual futura, sem dupla contagem ou mistura de métodos. [Composição](../data/FISCAL_COMPOSITION.md) · [Juros](../data/FISCAL_INTEREST.md) · [Funções](../data/FISCAL_SPENDING.md) · [Esferas](../data/GENERAL_GOVERNMENT.md).
4. DATA-05: contextos e hipóteses revisadas, contrapartidas e evidências, distinguindo observação de explicação causal.
5. GRAPH-01: contratos de nós/arestas e revisão/publicação; página explicativa pública e explorador interativo com fontes, incertezas, celular e alternativa por teclado/lista. Uma aresta visual não produz efeito numérico automaticamente.
6. IA como apoio de análise sobre dados/evidências rastreáveis, com avaliações e revisão humana. Participação social depende de regras, persistência e moderação.
7. Lançar serviço quando termos/privacidade, HTTPS, backups/restauração, monitoramento, worker persistente e limites estiverem verificados. Esse trabalho pode avançar em paralelo; não exige esperar por IA/grafos.

Esta sequência é orientação, não promessa de datas ou autorização para implementar tudo de uma vez. Estados e critérios de aceite permanecem no [backlog](BACKLOG.md).

## Último avanço do roadmap — 2026-10-15

GRAPH-01C concluído: `/grafos` ensina a ler a rede e oferece profundidade, rotação, zoom, filtros, lista equivalente e inspeção de nós/relações/fontes/contrapontos/revisão. Detalhes e versões exatas consultam a API pública. Sem mapa real publicado, um exemplo explicitamente fictício ensina a navegação; falha de uma versão solicitada não vira demonstração automaticamente. Primeiro mapa real (FGTS) ainda precisa de pesquisa e curadoria. GRAPH-01 permanece Preparado no escopo ampliado D/E; DATA-05C continua aguardando revisão humana/termos e UI-06 planejado. [Explorador](../product/GRAPH_EXPLORER.md).

## Estimativa de avanço — 2026-10-10

Estimativa comunicada ao mantenedor: cerca de 60% do produto completo planejado e 85% da V1 local. Julgamento de escopo, não proporção exata de tarefas nem previsão de prazo. Núcleo local e cenários integrados já funcionam; composição fiscal adicional, evidências/grafos, criação guiada por IA e operação pública ainda representam trabalho relevante. Reavaliar quando escopo e marcos mudarem; não interpretar testes/documentos como serviço lançado.


## DATA-05C preparado — 2026-10-13

Interface pública e privada implementada, integrada aos indicadores e à Metodologia. Desemprego com contrapartidas e fontes oficiais foi preparado privadamente, sem aceitar ou publicar análise real automaticamente. Um exemplo fictício separado testa os fluxos locais. [Pesquisa e revisão pendente](../data/FIRST_CONTEXT_RESEARCH.md).

943 testes backend (incluindo 25 de descoberta nova) e 232 frontend passaram; Ruff/formatação de 151 arquivos, Alembic sem drift, lint/types/build passaram. QA final e operação constam em VERIFICATION ao encerrar. Nenhuma alteração em coletores, base/motor fiscal ou snapshots; nenhum commit/push/deploy. Revisão humana pendente mantém DATA-05C/DATA-05 Preparados.


Fechamento DATA-05C: editor/detalhe conferidos nas quatro larguras e dois temas sem overflow, 13 pares AA (mín. 6,13:1), teclado, drawer, vazio/erro/retry e publicação/edição de exemplo fictício. Primeira pesquisa real revisão 2 privada, zero revisões/publicações reais. API/ready/site/proxy 200, escrita anônima 401, rascunho real público 404, checkpoint integral preservado e worker vivo. PARTIAL da coleta anterior permanece explícito. DATA-05C Preparado, sem lançamento ou grafo. [Verificação](../development/VERIFICATION.md).


## Base técnica dos grafos — 2026-10-14

GRAPH-01A concluído como biblioteca pura: versões imutáveis de nós/arestas, fotografias de referências, hash por aresta/conjunto, correspondência de revisão declarada e diagnósticos de duplicatas/direções opostas/ciclos/isolados. 93 testes específicos e 795 unitários backend passaram; Ruff/formatação de 154 arquivos e links locais passaram. Não foi alterado runtime, schema, frontend, motor ou dado real. Testes PostgreSQL/build/navegador não foram repetidos; as verificações de 2026-10-13 são históricas, não uma nova conferência de operação hoje.

GRAPH-01 fica Preparado. Próximo desenvolvimento B, curadoria/persistência/autorização; C entrega página explicativa e explorador/lista. Magnitudes e IA são D/E separados. DATA-05C continua Preparado com a pesquisa real privada aguardando revisão humana/termos; não foi marcada concluída nem promovida como grafo. [Contrato](../data/GRAPH_CONTRACT.md) · [Backlog](BACKLOG.md).

## Curadoria do grafo entregue — 2026-10-14

GRAPH-01B concluído com migration 0014 e API integrada; regras/evidências atuais na seção Verificação acima e no contrato. A rede ainda não aparece no site: página explicativa e explorador/lista fazem parte de C, próximo item. Testes de curadoria fictícia não equivalem à revisão humana da pesquisa real. Nenhum conteúdo real de grafo foi semeado ou publicado.

## Exploração em profundidade — 2026-10-15

272 testes frontend passaram, incluindo 34 de geometria/filtros/referências e seis regressões de abertura de versões; lint, TypeScript da compilação e build passaram. Oito combinações de 360/768/1280/1920 px e claro/escuro sem rolagem lateral. 42 pares de texto/superfície em lista, detalhe e guia atenderam AA (mínimo 5,70:1), incluindo os fundos vetoriais dos símbolos. Medição não é auditoria completa de acessibilidade.

No navegador: rotação por arraste/teclado, zoom, visão plana, seleção, leitura no celular, busca vazia e catálogo vazio conferidos. Fluxos de versão, disputa, evidência, histórico e falha/recuperação foram testados com API fictícia isolada, sem inserir registros no banco; teste também encontrou/corrigiu abertura de versão válida sem catálogo e título da revisão antiga no seletor. API real continua com zero redes publicadas. Base, contextos, publicações e simulações anteriores preservados. Nenhum backend/migration/motor/coletor alterado.

Site/API/PostgreSQL retomados em loopback; worker diário não foi retomado nesta entrega de interface e a última coleta parcial permanece registrada. Não houve nova pesquisa, revisão humana, coleta forçada, lançamento, commit/push/deploy. D/E e primeira curadoria real permanecem pendentes; a interface C não depende de inventar relações para preencher a rede.

## Mapa WebGL implementado — 2026-10-18

GRAPH-01C1 implementa o refinamento solicitado em `/grafos`: Three.js carregado sob demanda, posições estáveis, voo de câmera, destaque/mergulho, legenda, painel sobreposto, teclado e alternativa automática em lista. Dados, backend, contrato 200/400, rotas, revisão e explicação anterior preservados. Demonstração continua 18/24 sem seed real. 282 testes frontend, lint, TypeScript/build passaram; quadro de QA e limites em VERIFICATION.

Pacote 3D lazy: aproximadamente 149 kB gzip local de JS+CSS; sem esse módulo no manifesto lazy da Home. Teste de renderização isolado 200/500 e ciclo de descarte/recriação disponíveis. GRAPH-01C1 fica Preparado quanto ao aceite de qualidade completo: validação de toque/pinça, leitor de tela e perfil de 60 fps em dispositivos representativos permanecem pendentes. GRAPH-01D/E e primeiro mapa real continuam separados.

## Qualidade do mapa — continuação de 2026-10-18

300 testes frontend, lint e build/TypeScript passaram após corrigir foco do Escape, seleção acidental por gestos e redesenho ocioso de relação incerta. Teclado móvel aproxima o palco imediatamente; oito combinações de largura/tema confirmaram painel e foco sem overflow. Teste isolado agora mede chamadas reais de desenho e invalida capturas interrompidas. Pacote lazy atual: 149.012 bytes gzip local; Home continua sem esse módulo no manifesto lazy. GRAPH-01C1 mantém os aceites físicos/leitor de tela/desempenho representativo pendentes, sem avançar magnitude/IA nem publicar conteúdo real.


## Criação acessível e operação local — 2026-10-19

Entregue o fluxo local de IDEIA até COMPLETA publicada: entrada guiada ou manual, confirmação explícita, troca/retomada, cópia atribuída, sugestão de fonte, compartilhamento intencional e moderação. Checklist é validado no servidor; IDEIA não entra em motor/planos/ranking. Legado mantém contratos e snapshots anteriores. DOC_COMPLETENESS1 mostra presença de fontes/financiamento e revisão não avaliada, sem alegar nota técnica.

A análise comum usa sensibilidade fiscal declarada com multiplicadores explícitos; o motor calcula e o usuário escolhe premissas. Sem valores/recortes compatíveis não calcula faixa. Não há magnitude causal ou confiança estatística nova. Teste fictício de navegador em banco QA separado conferiu promoção/publicação e análise −100/−60/−20, além de confirmação, troca, retomada, compartilhamento, cópia e privacidade anônima.

Gemini é o provedor escolhido, com interface trocável, consentimento, quota, logs privados e apagamento. A chave ainda será fornecida: integração real permanece desligada; UI-06C/F e o épico ficam Preparados. Oito perguntas públicas fixas e preenchimento manual/guiado sem IA já funcionam. Testes controlados de imparcialidade não substituem avaliar o modelo real. Não houve chamada Gemini nesta entrega.

Scripts Windows iniciam/verificam/encerram somente a aplicação identificada, preservam PostgreSQL e não iniciam coletor. Build/migration exigem flags explícitas, banco útil recebe só upgrade com backup. Restauração foi exercitada isoladamente, preservando conteúdo anterior. Uso local não depende de abrir GitHub ou hospedar; operação pública, termos vigentes, coleta supervisionada, acessibilidade aprofundada e hardware representativo continuam pendentes. Sem commit/push/deploy e sem promover pesquisa real por testes. [Como executar](../development/DEVELOPMENT.md) · [Aceite](BACKLOG.md#épico-ui-06--criar-proposta-acessível).


Fechamento local em 2026-10-20: início/consulta/encerramento/reinício reais em PowerShell 5.1 conferidos, banco preservado, aplicação e limpeza de logs ativas. Checks finais, QA e limites registrados em [VERIFICATION](../development/VERIFICATION.md). Chave e avaliação Gemini continuam pendentes; não houve lançamento público.


## Operação atual em Docker — 2026-10-20

A pedido do mantenedor, a aplicação passou a rodar no Compose local. Containers do site/API/banco saudáveis, migrations concluídas e limpeza ativa; processos nativos gerenciados encerrados, PostgreSQL nativo preservado. Banco Docker é cópia independente conferida dos dados anteriores, sem sincronização posterior. A porta Docker do banco usa 55434 por restrição de bind 5432 neste Windows. [Guia](../development/DOCKER_LOCAL.md). Pendências antigas de “Compose completo” nos registros datados são históricas; operação pública, coleta supervisionada e gates de conteúdo/IA continuam separados.


Conexão atual do PostgreSQL Docker: 127.0.0.1:5433, banco brasil_portodos, usuário brasil. Porta e senha personalizada configuradas no ambiente privado por solicitação do mantenedor; o backend nativo também aponta agora ao Docker. Banco nativo anterior permanece preservado. Valores de senha/chave não pertencem a este documento.


Modelo local atual solicitado: gemini-2.5-flash. Containers reiniciados em 2026-10-20; teste de geração retornou404 NOT_FOUND, apesar do nome constar no catálogo. Não há confirmação de geração com esse modelo. O sucesso fictício anterior usava3.1 Flash-Lite e não valida o novo modelo.


Modelo local atual: gemini-3.5-flash-lite. Em 2026-10-20, geração direta (8,64 s) e organização autenticada pela aplicação (7,47 s) passaram com conteúdo fictício, rótulo de assistência e preservação literal. Substitui a configuração 2.5 anterior; não altera registros históricos.

## Revisão da escrita no guiado — 2026-10-20

A assistência agora pode corrigir a escrita e melhorar clareza (prompt 2.0.0), com comparação original/sugestão, identificação explícita quando não há mudanças e confirmação antes de preencher. Corrige a limitação anterior que só repetia palavras. Roteiro 1.0.0 e modelo local gemini-3.5-flash-lite preservados. Verificações automáticas não comprovam equivalência de sentido; avaliação sistemática real de imparcialidade continua pendente em UI-06C/F.

## Assistente de desenvolvimento de propostas — 2026-10-20

O contrato atual (prompt 3.0.0) substitui o corretor literal/gramatical por desenvolvimento da intenção informal: redação principal, sugestões opcionais de implantação/contrapartidas e lacunas. Seleção e confirmação preservam autoria; sugestões são pontos a avaliar. Roteiro 1.0.0, modelo local e motor preservados. Registro privado da chamada pode ser consultado pelo autor no editor, sujeito a retenção/apagamento. Checagens Docker não chamam mais /ready periodicamente; usam TCP, com limite de verificar só conexão. Avaliação sistemática real de imparcialidade continua pendente.

## Verificação do assistente — 2026-10-22

Prompt atual 3.0.1: elaboração de proposta, sugestões opt-in e lacunas, com registro privado consultável pelo autor. Teste real fictício e confirmação seletiva conferidos; 122 testes específicos backend/317 frontend aprovados, builds Docker/TypeScript e documentação verificados. Aplicação Docker ativa; checagens TCP sem consultas HTTP periódicas. Roteiro/modelo e motor preservados. Evidências e limites em [VERIFICATION](../development/VERIFICATION.md); avaliação sistemática de imparcialidade ainda pendente.
