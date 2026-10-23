# Auditoria da interface — 2026-10-22

Inventário do código realizado antes da implementação e apresentado ao mantenedor. “Antes” descreve o estado auditado, não a versão final. Rotas aprovadas foram preservadas; compartilhados novos usam os mesmos tokens e componentes, em CSS Modules isolados.

| Rota | Antes: sistema novo? | Problema encontrado / intervenção |
| --- | --- | --- |
| `/` | Sim | Preservada |
| `/brasil` | Sim | Explorador preservado |
| `/brasil/[code]` | Parcial | Leitura do detalhe com índice, valor compacto e valor exato |
| `/fontes` | Sim | Preservada |
| `/grafos`, `/grafos/[id]`, `/grafos/[id]/versoes/[revision]` | Sim | Preservadas |
| `/cadastro`, `/entrar` | Sim | Preservadas |
| `/propostas` | Sim | Catálogo preservado |
| `/propostas/[slug]` | Parcial | Capítulos, autoria/versão, resultado e referências |
| `/planos` | Parcial | Hero, orientação de leitura, vazio e catálogo |
| `/planos/[slug]` | Parcial | Composição por versões, leitura e saldo existente |
| `/ideias` | Não | Identidade de rascunho, autoria e lista compacta |
| `/ideias/[id]` | Não | Lacunas, conteúdo e ações de ajuda separados |
| `/contextos` | Parcial | Jornada dados → hipóteses → evidências e cards |
| `/contextos/[id]` | Parcial | Índice de leitura e histórico |
| `/contextos/[id]/versoes/[revision]` | Parcial | Leitura e versão preservada, estado indisponível |
| `/metodologia` | Não | Índice, capítulos e resumos; texto/âncoras preservados |
| `/transparencia` | Não | Índice, estado atual e blocos de leitura |
| `/painel` | Parcial | Abas, totais reais, retomada e atalhos |
| `/painel/ideias` | Parcial | Cards e estados de lista |
| `/painel/propostas` | Não | Status/versão, filtros locais e paginação |
| `/painel/planos` | Não | Status/versão, filtros locais e paginação |
| `/painel/fontes` | Não | Lista compacta e cadastro lateral |
| `/painel/propostas/nova` | Parcial | Escolha → consentimento único → guiado/manual |
| `/painel/ideias/[id]` | Parcial | Mesmo editor, checklist salvo, prévia e confirmação |
| `/painel/propostas/[id]` | Parcial | Editor da completa, etapas e prévia |
| `/painel/planos/novo`, `/painel/planos/[id]` | Parcial | Etapas/âncoras e balanço existente |
| `/painel/contextos` | Parcial | Cards, estado e navegação |
| `/painel/contextos/novo`, `/painel/contextos/[id]` | Parcial | Editor em etapas e salvamento destacado |
| `/painel/contextos/revisao` | Parcial | Fila, status e leitura para revisão |
| `/painel/admin` | Não | Hero compacto, navegação por seções, formulários e estados |
| `/painel/ideias/moderacao` | Parcial | Fila e alternativas de decisão |
| Erro, carregamento e 404 | Parcial | Estados com identidade e ações existentes |

`/api/v1/[...path]` é proxy de API, não tela; contrato preservado.

## Componentes e decisões

ModeChoiceCard, GuidedStepper, AiConsentCard, AiResponseCard, AiLoadingCard e ProgressSidebar organizam o editor. PanelTabs, cartões do painel e ReadingLayout reaproveitam PageHero, Button, ícones, skeletons e estados vazios. Button ganha variante terciária isolada; páginas existentes não passam a usá-la automaticamente. Nenhuma biblioteca nova.

Consentimento explícito por criação/sessão, em memória; sem localStorage. Envia resposta e trechos confirmados ao Gemini, com retenção privada informada pelo backend (7 dias no ambiente atual). Aceitar uma vez libera as perguntas; “mudar” permite revogar/seguir sem IA. Salvamento transfere o aceite para o ID salvo; nova criação ou nova sessão exige aceite. A API continua exigindo consentimento em cada chamada real; a UI o transporta sem pedir novo clique.

Modo manual: Problema → Solução → Impacto → Fontes → Revisar. O checklist usa a revisão salva no servidor; não calcula porcentagem inventada enquanto se digita. Prévia mostra texto atual e selo de ideia. Estado “salvo no servidor” substitui cronologia não disponível. Retomada considera as 20 ideias consultadas, explicitamente rotulada. Filtros locais dizem “nesta página”. Ações indisponíveis no domínio não são simuladas como botões funcionais.

Roteiro 1.0.0, prompt 3.0.1, verificações de saída, limites, logs, permissões, publicação e motor fiscal permanecem com os contratos anteriores. Consentir não desativa as verificações do retorno. Avaliação sistemática de imparcialidade e auditoria aprofundada de acessibilidade permanecem em seus itens próprios.

Verificações e limites em [VERIFICATION](../development/VERIFICATION.md); acompanhamento em [BACKLOG](../project/BACKLOG.md).


## Atualização posterior — 2026-10-22

ADR-044 substitui o bloqueio semântico referido no inventário histórico: o conteúdo da IA segue instruções do prompt 4.0.0 e revisão humana, mantendo somente contrato técnico no código. Nova rota /painel/ideias/nova oferece título/frase e salvamento privado, distinta de /painel/propostas/nova (preparação completa). Navbar agrupada com Explorar, Ideias/Propostas/Planos e Meu espaço; CTA Criar ideia abre a entrada rápida. Sem alteração das rotas públicas ou regras fiscais.
