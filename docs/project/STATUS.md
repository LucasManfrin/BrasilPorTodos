# Estado do BrasilPorTodos

Atualizado em 2026-10-25. Este documento é a visão atual; evidências anteriores permanecem no [histórico de verificação](../development/VERIFICATION.md) e no [backlog](BACKLOG.md).

## Onde estamos

**V1 funcional localmente, preparada para organizar contribuições.** Código público e serviço público são marcos separados. A arquitetura e o núcleo estão alinhados à visão: entender o país, propor medidas com custos/fontes e combinar planos comparáveis, com histórico preservado.

| Área | Implementado | Limite ou próximo trabalho |
| --- | --- | --- |
| Produto e interface | Home, Brasil Atual, Fontes, propostas, planos, cadastro; painel/editor/detalhes públicos consolidados em UI-07; consentimento único por criação/sessão e navbar agrupada; celular e dois temas | Auditoria completa de acessibilidade e regressão automatizada do navegador |
| Contas e publicação | Autenticação, autorização/autoria, rascunhos privados, versões imutáveis, cópias com atribuição | Auditoria local entregue em 25/10; operação pública exige termos/privacidade, proxy, proteção/recuperação de contas e privilégios mínimos do banco |
| Dados oficiais | 14 indicadores BCB/IBGE/Tesouro e treze séries fiscais auxiliares, mais execução funcional federal e EFGG anual por esfera em conjuntos próprios; revisões, proveniência e coleta controlada | Agenda local persistente entregue; coleta de 25/10: 14 grupos disponíveis, 4 falhas de transporte preservando histórico; cobertura/qualidade/termos e supervisão pública pendentes |
| Referência fiscal | Governo Central, ano fechado; primário RTN/PIB, composição, juros/nominal, execução funcional e EFGG por esfera separados | Agregados observados, cobertura municipal estimada explícita; granularidade por ente e catálogo mínimo futuros |
| Simulação | Impactos incrementais; compatibilidade histórica; cenário futuro opcional declarado, revisado e preservado nos planos | Novos recortes no motor exigem contrato separado; sem previsão causal |
| Explicações | Definições/fontes/metodologia, contrato/API e interface de contextos, edição e revisão autorizada/publicação imutável (DATA-05A/B/C) | Primeiro rascunho pesquisado entregue na interface (C); revisão humana efetiva e publicação real pendentes |
| Grafos e evidências | GRAPH-01A/B/C: contrato, API de curadoria, WebGL 3D/lista, explicação e versões públicas | Primeiro mapa real exige pesquisa/revisão humana; falta tela privada de curadoria (API existe), magnitudes causais e apoio de IA |
| Criação acessível | IDEIA/COMPLETA com entradas distintas (captura rápida/preparação), guiado/manual, revisão humana da saída da IA (prompt 4.0.0), checklist, compartilhamento/cópia/sugestões e moderação | Ideia abre com título/frase; desenvolvimento completo é escolha explícita, sem perder detalhes. Gemini 3.5 Flash-Lite configurado e chamada autenticada real conferida anteriormente; disponibilidade externa e avaliação sistemática pendentes; sem revisão técnica de propostas |
| Análise da proposta | Sensibilidade fiscal DECLARED_SENSITIVITY_1 da COMPLETA publicada estimada, pelo motor e com premissas ajustáveis | Estimativa declarada; sem probabilidade, previsão causal ou cálculo de IDEIA |
| Operação local | Launchers nativos e Compose completo, banco persistente, migrations até 0017, backup/restauração e cópia conferidos | Supervisão pública, HTTPS e lançamento separados; coletor diário ativo às 00:00 de São Paulo; resultado parcial de 25/10 exige acompanhamento |

## O que ainda não prometemos

O saldo das medidas **não é uma previsão do saldo do Brasil**. A base histórica contextualiza as publicações; o motor 1.0.0 agrega efeitos incrementais. Novas parcelas carregam declarações de ente, critério, preços, componente e período; dados ausentes não são inferidos. A avaliação verifica esses recortes contra a referência histórica preservada, sem validar o custo; a comparação com premissas futuras é um método adicional separado.

Há cenário opcional nos planos para combinar premissas futuras anuais declaradas com medidas compatíveis. A confirmação humana evita alegar exclusão não revista; não detecta sobreposições semânticas. Não há cálculo causal de emprego/pobreza/PIB ou orçamento de todos os governos. A assistência opcional Gemini desenvolve o texto e oferece possibilidades separadas, sempre sujeitas à confirmação do autor; não avalia o mérito da proposta nem calcula impactos. O explorador do grafo permite investigar alegações e não calcula esses efeitos. Nenhum indicador isolado demonstra causa, significância ou avaliação de governo. A renda real da PNAD não é receita fiscal.

## Verificação e próximos passos

Git local em `main`, snapshot inicial `d1bee6f`, sem remoto ou push. A auditoria de 2026-10-23 e seu diagnóstico de grafos estão em [REPOSITORY_AUDIT](REPOSITORY_AUDIT.md). O histórico anterior foi preservado em [STATUS_HISTORY](STATUS_HISTORY.md); testes datados em [VERIFICATION](../development/VERIFICATION.md).

Auditoria local de autenticação/roles e correções entregues em 25/10: [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md). Next.js 16.4.3, build aprovado e scanners sem alertas conhecidos nos conjuntos conferidos; não equivale a serviço público seguro. Agenda local e diagnóstico da coleta entregues: faltava coletor persistente no Compose; falhas de transporte externas continuam explícitas. Próxima frente é acompanhar a retentativa e discutir a análise final por IA/grafos antes de implementar. Lista completa e gates públicos no início do [BACKLOG](BACKLOG.md).

Prioridades operacionais, começando pelos riscos já verificados:

1. Acompanhar as quatro fontes indisponíveis após a retomada da coleta e supervisionar o job diário (F2-04/F2-03); a auditoria local F2-02 foi entregue, mas suas pendências de operação pública continuam abertas.
2. Pesquisar, revisar e publicar o primeiro mapa real e o primeiro contexto. Exploração visual não substitui curadoria; nenhum exemplo foi promovido como pesquisa real.
3. Avaliar sistematicamente o modelo real com intenções opostas e registrar limitações; a confirmação humana continua necessária.
4. Conferir atualização/cobertura dos dados e supervisionar o coletor quando a operação exigir atualização contínua.
5. Publicar o código no remoto escolhido pelo mantenedor, executar CI e definir canais. Commits locais não lançam serviço público.
6. Antes de abrir o serviço: termos/privacidade vigentes, HTTPS, proxy/IP confiável, backups, monitoramento, acessibilidade aprofundada e testes em hardware representativo.

A V1 local está alinhada ao objetivo acadêmico e ao núcleo do produto. Não há necessidade demonstrada de reescrever a arquitetura ou adicionar serviços para essa finalidade. O produto público completo mantém os gates do [backlog](BACKLOG.md).
