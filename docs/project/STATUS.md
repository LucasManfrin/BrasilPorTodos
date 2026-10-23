# Estado do BrasilPorTodos

Atualizado em 2026-10-23. Este documento é a visão atual; evidências anteriores permanecem no [histórico de verificação](../development/VERIFICATION.md) e no [backlog](BACKLOG.md).

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

Há cenário opcional nos planos para combinar premissas futuras anuais declaradas com medidas compatíveis. A confirmação humana evita alegar exclusão não revista; não detecta sobreposições semânticas. Não há cálculo causal de emprego/pobreza/PIB ou orçamento de todos os governos. A assistência opcional Gemini desenvolve o texto e oferece possibilidades separadas, sempre sujeitas à confirmação do autor; não avalia o mérito da proposta nem calcula impactos. O explorador do grafo permite investigar alegações e não calcula esses efeitos. Nenhum indicador isolado demonstra causa, significância ou avaliação de governo. A renda real da PNAD não é receita fiscal.

## Verificação e próximos passos

Git local em `main`, snapshot inicial `d1bee6f`, sem remoto ou push. A auditoria de 2026-10-23 e seu diagnóstico de grafos estão em [REPOSITORY_AUDIT](REPOSITORY_AUDIT.md). O histórico anterior foi preservado em [STATUS_HISTORY](STATUS_HISTORY.md); testes datados em [VERIFICATION](../development/VERIFICATION.md).

Prioridades sem ampliar o escopo:

1. Pesquisar, revisar e publicar o primeiro mapa real e o primeiro contexto. Exploração visual não substitui curadoria; nenhum exemplo foi promovido como pesquisa real.
2. Avaliar sistematicamente o modelo real com intenções opostas e registrar limitações; a confirmação humana continua necessária.
3. Conferir atualização/cobertura dos dados e supervisionar o coletor quando a operação exigir atualização contínua.
4. Publicar o código no remoto escolhido pelo mantenedor, executar CI e definir canais. Commits locais não lançam serviço público.
5. Antes de abrir o serviço: termos/privacidade vigentes, HTTPS, proxy/IP confiável, backups, monitoramento, acessibilidade aprofundada e testes em hardware representativo.

A V1 local está alinhada ao objetivo acadêmico e ao núcleo do produto. Não há necessidade demonstrada de reescrever a arquitetura ou adicionar serviços para essa finalidade. O produto público completo mantém os gates do [backlog](BACKLOG.md).
