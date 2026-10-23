# Roadmap

Sem datas prometidas. As fases avançam pelos critérios de aceite do [backlog](../project/BACKLOG.md).

| Fase | Objetivo | Critério de passagem |
| --- | --- | --- |
| 0 — Fundação | Documentação, monorepo, ambiente local, CI e decisão de licença | Instalação reprodutível; checks passam; licença e remoto definidos antes da abertura a contribuições |
| 1 — Núcleo V1 | Banco, autenticação, indicadores, fontes, propostas, planos e motor fiscal | Fluxo de ponta a ponta do V1_SCOPE executado localmente; permissões, imutabilidade e cálculo cobertos |
| 2 — Validação e lançamento | Acessibilidade, segurança, operação, qualidade dos dados e demonstração pública | Revisão de fontes, fluxo completo validado, backup/restauração e implantação documentados |
| 3 — Evolução | Melhorar participação e evidências conforme uso real | Escopo aprovado separadamente, com metodologia e decisões registradas |

## Ordem da Fase 1

Modelo e migrations → contas e autorização → fontes/indicadores → propostas e publicação → planos com versões fixadas → persistência das simulações → navegação pública e painel → teste do fluxo completo.

Frontend e backend podem evoluir por fatias verticais quando os contratos estiverem definidos. O motor fiscal puro já pode ser testado sem banco; sua integração foi concluída na Fase 1.

## Estado inicial

Fundação local preparada, licença MIT adotada; configuração do GitHub e validação do ambiente Docker ainda podem estar pendentes. Consulte os estados detalhados em [docs/project/BACKLOG.md](../project/BACKLOG.md).

## Mudanças de escopo

Toda inclusão na V1 precisa registrar problema, impacto sobre o fluxo principal e custo de manutenção. Features sociais e modelos macroeconômicos permanecem em evolução futura até nova decisão explícita.

## Prioridades verificadas — 2026-10-23

Antes de ampliar funcionalidades: corrigir o alerta crítico de dependência do Next.js (F2-02), retomar a coleta parcial antiga (F2-04/F2-03), concluir revisão/publicação do primeiro conteúdo real do grafo e avaliar imparcialidade do modelo real (UI-06C/F). Registro local em Git não encerra CI remota, termos ou operação pública. [Auditoria](../project/REPOSITORY_AUDIT.md). Registros datados abaixo preservam a evolução; o [STATUS](../project/STATUS.md) resume a capacidade atual.

## Estado após a primeira implementação

Fluxo local de contas, fontes, propostas, planos, simulação, Brasil Atual e administração implementado e verificado. Catálogo oficial iniciou com duas séries; expansão permanece em F1-03. Preparação de lançamento depende de remoto/canais e termos/privacidade, sem alterar a disponibilidade do protótipo local. Ver BACKLOG para evidências e próximos itens.

## Próximos itens da Fase 2

| ID | Estado | Entrega |
| --- | --- | --- |
| F2-01 | A fazer | Auditoria aprofundada de acessibilidade e leitores de tela; regressão automatizada do navegador |
| F2-02 | A fazer | Corrigir alerta crítico do Next.js e repetir auditoria/build; proxy confiável/IP de cliente, limites de carga e limpeza de sessões/contadores vencidos |
| F2-03 | A fazer | HTTPS, secrets, backups/restauração, monitoramento e implantação |
| F2-04 | A fazer | Revisão de qualidade/cobertura e atualização das séries oficiais; política de exportação/licenças |

## Grafos — estado atual

GRAPH-01A/B/C entregues localmente: contrato, curadoria/revisão/publicação e explorador WebGL/lista explicativa. Primeiro mapa real exige pesquisa e revisão humana; demonstração segue fictícia. Magnitudes causais D e assistência de curadoria E continuam separadas e pendentes. [Explorador](GRAPH_EXPLORER.md) · [Backlog](../project/BACKLOG.md).

## Criar proposta acessível — decisão original de 2026-10-10

Decisão de 2026-10-10: entrada simples e rigor ao publicar como completa. “Me ajuda a montar” e “Eu preencho” chegam ao mesmo molde/análise e permitem alternância sem perda. IDEIA exige título/uma frase e pode ser compartilhada explicitamente como “ideia em construção”, com ajuda por duplicação/sugestão de fontes; não entra no cálculo, planos nem ranking. COMPLETA exige problema, medida, financiamento, beneficiados/prejudicados, riscos, fontes e campos fiscais, com checklist de progresso.

Ordem de trabalho do épico: contrato de níveis/checklist/visibilidade (UI-06A) → dois caminhos e retomada (UI-06B) → roteiro fixo neutro e integração trocável (UI-06C) → análise comum pelo motor e critérios dos selos/faixas (UI-06D). Preparar limites, denúncia/moderação e ranking de solidez (UI-06E) antes de abrir participação compartilhável; avaliações de imparcialidade (UI-06F) acompanham o trabalho e bloqueiam a disponibilização do guiado até passarem. Estas fatias pertencem ao UI-06 existente, não são novos épicos duplicados.

Perguntas fixas, uma por vez, iguais para todos os temas/posições, versionadas e publicadas em Metodologia; confirmação antes de preencher, “não sei” válido e texto assistido identificado. A IA não decide a posição da pessoa nem calcula. Decisão atual de 2026-10-20 permite desenvolver a proposta e sugerir desenho/implantação e contrapartidas em blocos separados, com seleção e confirmação do autor, sem inventar números/fontes. Prompt atual 4.0.0, sem rejeição semântica no código e com confirmação humana; roteiro 1.0.0 preservado. Testes com visões opostas registram tom/perguntas e não admitem perguntas diferentes. Método das faixas/selos, custos, limites, logs privados e privacidade precisam ser definidos antes de operar.

**Registro histórico de 2026-10-10.** O estado atual da implementação está no fechamento de 2026-10-19 abaixo. [Requisito completo](PROPOSAL_CREATION.md) · [Aceite e dependências](../project/BACKLOG.md#épico-ui-06--criar-proposta-acessível).

## Composição fiscal — DATA-07

DATA-07A: receita total/transferências e composição primária do Governo Central, mesmo ano fechado do RTN; coleta auxiliar e leitura pública sem mudar bases congeladas. Entrega local verificada em 2026-10-11; DATA-07A concluído, DATA-07 Preparado. DATA-07B mantém gastos por função, juros e outros entes com fontes/contratos próprios. Não apresentar uma fatia primária como orçamento completo. [Contrato](../data/FISCAL_COMPOSITION.md) e aceite no backlog.

## Ampliações observadas — DATA-07B, 2026-10-11

B1: juros e nominal do Governo Central, com primário abaixo da linha, regime misto e conjunto auxiliar próprio. B2: gasto federal por função, natureza e estágio, coleta oficial, revisões imutáveis, API/painel e verificação local concluídos. B3: outras abrangências e correspondência. Estas fatias refinam o DATA-07 existente; uma entrega B1 não encerra o conjunto B. [Juros](../data/FISCAL_INTEREST.md) · [Execução funcional](../data/FISCAL_SPENDING.md) · [Backlog](../project/BACKLOG.md).

DATA-07B1 concluído localmente em 2026-10-11; DATA-07B2 concluído com execução funcional federal, B3 A fazer. Coleta real/painel/testes e preservação verificados; DATA-07 completo permanece Preparado.


## DATA-07 concluído no recorte observado — 2026-10-12

A/B1/B2/B3 entregues localmente: composição primária, juros/nominal, execução funcional federal e EFGG anual por esfera, respectivamente. B3 usa a consolidação oficial STN e cobertura municipal estimada explícita; não habilita milhares de declarações SICONFI, soma própria de NFSP, ponte COFOG inferida ou cálculo de políticas estaduais/municipais no motor. [Contrato](../data/GENERAL_GOVERNMENT.md) · [Evidência](../development/VERIFICATION.md).

Próximo tópico: DATA-05, contextos e evidências com hipóteses/contrapartidas e revisão humana, antes de GRAPH-01. Catálogo mínimo F1-03 e granularidade futura precisam de definição de cobertura/termos; operação pública mantém F2 e requisitos de PUBLICATION. UI-06 continua planejado. Registros anteriores do roadmap preservam o estado de cada data.


## Contextos e evidências — DATA-05 iniciado, 2026-10-13

DATA-05A concluído como biblioteca de contrato/validação e correspondência de revisão ao conteúdo. DATA-05B fará resolução confiável, autorização, persistência e publicação; DATA-05C fará apresentação e primeiros contextos efetivamente pesquisados/revisados. Não interpretar testes fictícios como análise do país. GRAPH-01 vem depois; UI-06/IA continuam futuros. [Contrato](../data/CONTEXT_EVIDENCE.md) e estados no backlog.


## DATA-05B concluído — 2026-10-13

Persistência/API com referências reais, privacidade/autoria, revisão administrativa distinta e publicação/histórico imutáveis verificados. Não há contexto real automaticamente revisado nem interface de análise nova. Próximo DATA-05C: leitura/edição/revisão na interface, seleção/pesquisa e primeiro conteúdo conferido por pessoas. DATA-05 permanece Preparado; grafos e IA ainda futuros. [Contrato](../data/CONTEXT_EVIDENCE.md).


## DATA-05C preparado — 2026-10-13

Interface e primeiro rascunho pesquisado entregues: leitura pública/histórico, editor manual, observações salvas e revisão/publicação separadas. Conteúdo de desemprego permanece privado e assistido por IA até revisão humana efetiva; publicação fictícia de QA não conclui DATA-05. [Pesquisa](../data/FIRST_CONTEXT_RESEARCH.md). GRAPH-01 é o próximo desenvolvimento após essa validação, com contratos antes do explorador, sem converter arestas em efeitos fiscais automáticos.


## GRAPH-01A concluído — 2026-10-14

Base pura de nós/arestas/evidências, revisão declarada e topologia entregue. B fará curadoria persistida/autorização/publicação; C fará a página explicativa e explorador/lista; D/E reservam magnitudes verificadas e curadoria assistida. Nenhuma propagação automática ao motor. A preparação técnica não substitui a revisão humana da pesquisa DATA-05C, que continua Preparado. [Contrato](../data/GRAPH_CONTRACT.md) · [Backlog](../project/BACKLOG.md).

## GRAPH-01B concluído — 2026-10-14

Curadoria persistida/API, resolução de referências e revisão distinta/publicação explícita entregues. Relações aceitas ou em disputa só aparecem após ato do autor; coleções preservam versões previamente publicadas. Próximo desenvolvimento GRAPH-01C: página explicativa e rede interativa com inspeção de evidências/premissas/limites e alternativa em lista/teclado, conforme requisito existente. D/E continuam futuros; sem integração numérica automática. DATA-05C ainda aguarda revisão humana efetiva e termos da pesquisa real. [Contrato](../data/GRAPH_CONTRACT.md).

## GRAPH-01C concluído — 2026-10-15

Página explicativa e explorador qualitativo entregues: perspectiva 3D, lista, inspeção/evidências/contrapontos/revisão, histórico e versões públicas exatas. A/B/C estão concluídos localmente; D/E não foram antecipados. Próximo conteúdo real depende de pesquisar/curar o caso FGTS e conferir termos/alegações, sem fabricar relações para preencher a cena. A demonstração é explicitamente fictícia. DATA-05C ainda depende de revisão humana da pesquisa; IA/magnitude/abertura pública continuam trabalhos separados. [Explorador](GRAPH_EXPLORER.md).


## Entrega para uso local — 2026-10-19

Prioridade autorizada pelo mantenedor: concluir o fluxo utilizável no próprio computador; sem roteiro de apresentação ou necessidade de link público. A/B/E de UI-06 entregues e D concluído no recorte de sensibilidade declarada pelo motor. Guiado/manual preservam confirmação/retomada; IDEIA compartilhável não entra em planos/cálculos; COMPLETA passa checklist rigoroso. Gemini é opcional: integração, controles e roteiro fixo prontos, mas C/F continuam Preparados até chave e avaliação real. [Contrato atualizado](PROPOSAL_CREATION.md).

Launchers Windows, banco existente, upgrade aditivo até 0017 e backup/restauração local sustentam a entrega. Não encerrar F2-03 inteiro: operação pública, Compose completo e supervisão continuam pendentes. Próximos gates externos são a chave/avaliação Gemini, revisões humanas de conteúdo real e critérios de lançamento/acessibilidade. Grafo continua qualitativo; sensibilidade fiscal não implementa GRAPH-01D. O produto local pode ser usado sem essas integrações externas, com limitações visíveis. [Estado e verificações](../project/STATUS.md).


Em 2026-10-20, o recorte Docker local de F2-03 foi concluído: Compose completo validado com dados preservados, autenticação e migrations. Não encerra F2-03 de operação pública. [Docker local](../development/DOCKER_LOCAL.md).


Consolidação local UI-07 em 2026-10-22: painel, editores, leitura pública e consentimento único por criação entregues; ver [auditoria](../design/WORKSPACE_AUDIT.md) e [estado dos itens](../project/BACKLOG.md). Essa entrega não encerra avaliação sistemática do Gemini, acessibilidade aprofundada nem operação pública.
