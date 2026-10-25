# Backlog do projeto

Estados: **concluído** (entrega local verificada), **preparado** (implementação parcial ou dependência externa pendente), **a fazer**. Itens estão registrados localmente; não foram criadas issues no GitHub.

## Pauta de retomada — pedido de 2026-10-23

Ao retomar o projeto, apresentar estas frentes, seus estados e o que ainda falta. Pedido registrado em 23/10; estado atualizado em 25/10: auditoria local de autenticação e correções entregues, com pendências públicas explícitas. Diagnóstico/agendamento local da coleta entregues, com resultado parcial e supervisão pendentes; discussão da análise por IA continua a fazer. Ordem prática sugerida: segurança → coleta → discussão da análise com grafos. A discussão de produto pode ocorrer antes, a pedido do mantenedor.

| Frente / referência | Estado | Próxima entrega verificável |
| --- | --- | --- |
| GRAPH-01F — Debater análise final da proposta por IA e grafos | A fazer — discussão de método | Definir como examinar viabilidade, possíveis benefícios, riscos e lacunas contra objetivos declarados, com evidências do grafo; registrar alternativas, limites e decisão antes de implementar. Não prometer previsão ou percentual de sucesso. |
| F2-04 / F2-03 — Atualização e supervisão da coleta | Preparado — diagnóstico e agenda local entregues | Compose sem coletor persistente corrigido; job 00:00 São Paulo, retomada e retentativa de uma hora ativos. Coleta real de 25/10: 14 grupos SUCCESS, 4 falhas de transporte com histórico preservado. Acompanhar nova tentativa; disponibilidade externa, cobertura e supervisão pública continuam abertas. |
| F2-02 — Segurança, autenticação e roles | Preparado — auditoria local entregue | [Relatório de 25/10](../governance/SECURITY_AUDIT.md): Next.js corrigido, suspensão revoga sessões, configuração/logs endurecidos e regressões. Pendências públicas: proxy/limites, privilégios mínimos no banco, recuperação/MFA/administração de contas e limpeza de sessões. |
| Fechamento das pendências | Em aberto | Retornar lista atualizada do que falta para a V1 local e, separadamente, para lançamento público. Não estimar porcentagem de conclusão apenas pelo número de testes. |

### GRAPH-01F — Pauta da discussão, sem implementação agora

- Objetivo: ao concluir uma proposta, ajudar a pessoa a entender em quais condições ela pode atingir o objetivo declarado e quais consequências/contrapartidas precisam ser consideradas. “Boa” depende de objetivos e escolhas explícitos, não de uma preferência política atribuída à IA.
- Debater a IA consultando conexões/evidências revisadas e acionando ferramentas de cálculo verificáveis; aritmética financeira continua em motor determinístico com Decimal, premissas, fontes, versões e resultado reproduzível. A IA explica resultados e limites; texto gerado não vira valor fiscal automaticamente.
- Separar custo/financiamento e consistência contábil de viabilidade de implantação, efeitos sociais/econômicos e força da evidência. Mostrar beneficiados/prejudicados, riscos, condições, contrapontos e o que não se sabe.
- Usar base do Brasil e versões identificadas das propostas, nós, arestas e fontes. Definir cobertura mínima, atualidade e comportamento sem grafo real/dados suficientes; exemplo fictício não sustenta análise real.
- Depender de GRAPH-01D para magnitudes/composição: tratar unidades, cenários/faixas, ciclos, sobreposição e dupla contagem antes de quantificar caminhos. GRAPH-01E permanece apoio à curadoria, tarefa diferente desta análise final.
- Não afirmar probabilidade de sucesso ou previsão causal sem método/evidência e validação adequados. Avaliação qualitativa condicional é alternativa a discutir; número de conexões ou classificação da aresta não vira chance de funcionar.
- Definir revisão humana, apresentação da incerteza, critérios públicos, avaliação com propostas de posições opostas e controle de custo/privacidade. Decidir depois quais cálculos já cabem no motor e o que exige pesquisa/modelo novo.
- Aceite desta fatia de planejamento: discussão com o mantenedor, proposta de método e recorte inicial documentados, questões em aberto e decisão registrada. Não equivale à entrega da análise automática nem altera o contrato atual de UI-06D.

### F2-04 / F2-03 — Coleta: diagnóstico e agenda local entregues

Em 25/10 foi demonstrada a ausência de coletor persistente no Compose. A consulta antiga de 15/10 02:47 UTC corresponde a 14/10 23:47 em São Paulo; a interface agora informa horário/fuso e “última tentativa”. Os seis conectores IBGE anteriormente indisponíveis responderam aos testes de leitura, sem troca de IDs, parser ou TLS; não foi possível atribuir causa exata às falhas antigas.

Job `indicator-collector` ativo às 00:00 America/Sao_Paulo, retomada ao iniciar, lock global, mínimo de uma hora e retentativa de resultado parcial. Recarregar continua lendo dados salvos. Backup privado anterior conferido; coleta de 25/10 12:48–12:49 São Paulo terminou PARTIAL: 14 grupos SUCCESS e quatro FAILED (participação/URLError, composição RTN/timeout, execução funcional/RemoteDisconnected, Governo Geral/RemoteDisconnected). Leituras adicionais da participação responderam, compatível com intermitência, sem comprovar causa externa. Próxima tentativa automática após uma hora; não foi forçada coleta adicional para ocultar o resultado parcial.

Conferência preservou hashes de quatro versões publicadas de propostas, duas de planos, seis execuções, doze resultados e todos os contextos/publicações anteriores. Pendências: observar a retomada das fontes, cobertura/qualidade/termos e supervisão/alertas de operação pública. Configuração de agenda não comprova vida do processo. [Operação](../development/DOCKER_LOCAL.md) · [Método](../data/INDICATORS.md).

### F2-02 — Autenticação e autorização: auditoria local entregue, operação pendente

Inventário de permissões em [AUTHENTICATION](../architecture/AUTHENTICATION.md#papéis-e-permissões--inventário-de-2026-10-23); auditoria local, achados, correções, criptografia e evidências em [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md). A auditoria não fecha operação pública, proxy/IP, privilégios do banco, MFA/recuperação/administração de contas ou limpeza de sessões. Escopo e critérios de referência:

- Cadastro/login, normalização, hash de senha, enumeração de contas, força bruta e recuperação de acesso disponível ou ausente.
- Claims/assinatura/expiração de JWT, consulta da sessão/conta, refresh rotativo/reuso/concorrência, logout/revogação e efeito de desativação de conta ou mudança de papel.
- Cookies, CSRF, origens/CORS, cache, transporte de tokens, proxy/IP confiável e limites por cliente sem confiar em cabeçalhos arbitrários.
- Matriz visitante/USER/ADMIN aplicada no backend: acesso horizontal por IDs, elevação de privilégio, campos extras como role no cadastro, rascunhos/ideias/logs privados, operações administrativas e imutabilidade das publicações.
- Privilégios amplos de ADMIN em propostas/planos versus autoria estrita em ideias/contextos/grafos; avaliar se o alcance atual é o desejado e registrar divergências antes de alterar permissões. Revisão própria, contas administrativas e procedimento de concessão/revogação de ADMIN.
- Secrets e logs sanitizados, dependências relevantes, alerta crítico do Next.js, limpeza/retenção de sessões e contadores. Fazer testes em ambiente/banco isolado, sem ataque ao serviço de terceiros ou exposição de dados reais.
- Entrega: achados por severidade com localização, evidência/reprodução, impacto, correção recomendada/aplicada e regressão; limitações e riscos residuais explícitos. Não rotular a autenticação como segura apenas por testes anteriores terem passado.

### O que falta — lista de retomada

1. **Segurança:** auditoria local entregue, Next.js corrigido e build/auditorias aprovados; fechar proxy/IP/limites, privilégios mínimos do banco, recuperação/proteção de contas administrativas e limpeza operacional de sessões (F2-02). Sem afirmar segurança absoluta.
2. **Dados:** agenda local/retomada entregues; acompanhar fontes ainda indisponíveis, supervisionar atualização e fechar cobertura/qualidade/termos do catálogo (F2-04/F2-03/F1-03).
3. **Conteúdo real:** revisar/publicar o primeiro contexto e mapa reais; exploração visual já existe, mas o catálogo público conferido estava vazio (DATA-05C/GRAPH-01).
4. **IA atual:** avaliação sistemática real de imparcialidade e preservação da intenção; IA na análise final com grafos é discussão futura, não capacidade entregue (UI-06C/F, GRAPH-01F; magnitudes D e curadoria E separadas).
5. **Qualidade:** auditoria de acessibilidade/leitor de tela, toque/GPU representativos e regressão automatizada do fluxo principal (F2-01/GRAPH-01C1).
6. **Código público:** remoto, push autorizado, CI executada, proteção de branch e canais de manutenção/segurança (F0-04/F0-06/F1-11/UI-05).
7. **Serviço público:** termos/privacidade vigentes, moderação responsável, HTTPS/cookies seguros, secrets, proxy, supervisão/monitoramento e backup/restauração no ambiente final (F1-14/F2-02/F2-03). Uso acadêmico no próprio computador não exige hospedar o serviço.

## Fase 0 — Fundação

| ID | Estado | Entrega | Critério de aceite | Dependência |
| --- | --- | --- | --- | --- |
| F0-01 | Concluído | Visão, escopo, arquitetura, decisões, metodologia e fontes | Documentos relacionados e limites da V1 explícitos | — |
| F0-02 | Concluído | Estrutura monorepo e guias | frontend/backend/docs/scripts/.github; instruções de instalação | F0-01 |
| F0-03 | Concluído | Ambiente local e lockfiles | Frontend/API iniciam; PostgreSQL responde; Alembic executa sem drift | F0-02; PostgreSQL local |
| F0-04 | Preparado | CI e templates | Checks executam no remoto; proteção de main configurada | F0-03; remoto |
| F0-05 | Concluído | Licença do repositório | LICENSE MIT integral, metadados atualizados e ADR-014 aceita | Orientação do mantenedor em 2026-10-06 |
| F0-06 | Preparado | Remoto e governança | Repositório público, canais, reporte privado de segurança, regras de revisão | F0-05; conta GitHub |

## Fase 1 — Núcleo da V1

| ID | Estado | Entrega | Critério de aceite | Dependência |
| --- | --- | --- | --- | --- |
| F1-01 | Concluído | Modelos e migrations PostgreSQL | Entidades de DATA_MODEL, constraints, timestamps UTC, migração em banco vazio e upgrade verificados | F0-03 |
| F1-02 | Concluído | Contas e sessões | Cadastro/login/me/refresh/logout; senha com hash; expiração, revogação, rate limit e transporte de sessão documentados; sem segredo nos logs | F1-01; ADR-015 |
| F1-03 | Preparado | Catálogo inicial de indicadores | Séries e termos verificados; seed idempotente; unidade, recorte, data, fonte e histórico; nenhum dado fictício apresentado como real | F1-01; ADR-018 |
| F1-04 | Concluído | Fontes por URL | Cadastro autenticado; HTTP/HTTPS validado; sem fetch/upload; descrição de uso; privacidade de vínculos em rascunho | F1-02 |
| F1-05 | Concluído | Propostas e publicação | CRUD de rascunhos próprios; requisitos de publicação; impactos e financiamento; v1 imutável, edição cria v2 draft; catálogo e histórico públicos | F1-02; F1-04 |
| F1-06 | Concluído | Planos com versões fixadas | Período válido; incluir/ordenar/ativar versões publicadas; sem duplicação; composição congelada; nova proposta v2 não muda plano v1 | F1-05 |
| F1-07 | Concluído | Simulações persistidas | Integrar motor puro; snapshots e versão; resultado anual/acumulado; aviso de não estimado, não financiado e sobreposição; reprodução de execução anterior | F1-06 |
| F1-08 | Concluído | Brasil Atual público | Lista e detalhe/histórico com fontes, datas e estados vazios; uso por teclado e telas pequenas | F1-03 |
| F1-09 | Concluído | Catálogos públicos | Propostas/planos/fontes com busca, paginação e filtros; rascunhos invisíveis; links históricos estáveis | F1-04; F1-05; F1-06; F1-07 |
| F1-10 | Concluído | Painel de contribuição | Fluxo cadastro → proposta → publicação → plano → simulação → publicação; erros de formulário claros | F1-02; F1-04; F1-05; F1-06; F1-07 |
| F1-11 | Preparado | Metodologia e transparência no site | Método, limitações, fontes, licença, roadmap, changelog e repositório acessíveis sem conta | F0-05; F0-06 |
| F1-12 | Concluído | Administração mínima | Indicadores, usuários e arquivamento com autoria/data/motivo; snapshots publicados preservados | F1-02; F1-03; F1-05; F1-06 |
| F1-13 | Concluído | Validação ponta a ponta | Cenário completo do V1_SCOPE; testes de 401/403 e privacidade; regressão de imutabilidade; integração PostgreSQL; revisão de acessibilidade | F1-08 a F1-12 |
| F1-14 | Preparado | Termos de conteúdo e dados | Termos para propostas/planos e atribuições de fontes definidos antes do cadastro público | ADR-019; F1-03 |

## Detalhes dos itens prioritários

### F1-01 — Banco

- Implementar as 14 entidades conceituais e suporte necessário a sessões/snapshots.
- Garantir unicidade de slug, número de versão e proposta por versão de plano; limitar a um rascunho ativo por identidade.
- Validar estado/ponteiro público, valores não negativos e períodos coerentes.
- Não criar tabelas para uploads, votos ou Claims.

### F1-05 — Publicação

- Rascunho pode estar incompleto; publicação valida campos obrigatórios e estado fiscal explícito.
- Nova despesa/redução de receita exige declaração de financiamento, inclusive UNFUNDED.
- Publicar em transação, preservando autor/data e snapshot de fontes.
- Provar que impactos, financiamento e referências de uma versão publicada não podem ser alterados, inclusive por admin.

### F1-07 — Motor e integração

- A biblioteca fiscal inicial já possui testes; a entrega abrange API, persistência e UI.
- Usar valores Decimal/string; somar apenas impactos anuais de versões habilitadas.
- Não estimado gera resultado parcial. Declarar financiamento não duplica receita/economia.
- Armazenar snapshot/hash de entrada e versão do motor; nova execução preserva execução anterior.

## Definição de pronto por item

Critérios de aceite demonstrados, verificações pertinentes passando, docs atualizados, nenhum segredo ou dado privado publicado. Um item com dependência externa pendente permanece preparado ou a fazer.

## Auditoria e versionamento local — 2026-10-23

Inventário e limpeza concluídos: card antigo sem consumidores e seus estilos removidos, Sparkline em uso preservado, onze marcadores vazios removidos. STATUS atual separado do histórico sem apagar evidências; guias de módulos/IA/publicação sincronizados. Revisão de candidatos ao Git sem segredos detectados nos padrões conferidos; `.env`, dados locais, bancos, backups e chaves excluídos. Commit inicial `d1bee6f`, 476 arquivos em `main`, sem remoto; fechamento documental em commit próprio. F0-06 fica Preparado pelo histórico local; remoto/canais/governança continuam pendentes, F0-04 não é encerrado sem CI remota.

Checks: 1.410 testes backend com banco temporário exclusivo, 320 frontend, Ruff (188 arquivos), ESLint, TypeScript e links passaram. **Build não aprovado:** terminou com alerta de segurança após compilar; `npm audit --omit=dev` apontou Next.js 16.4.0 como dependência de severidade crítica. Atualizar versão/lock e repetir build/auditoria é prioridade de F2-02 antes de expor o serviço; não houve atualização de dependências nesta revisão.

Docker iniciado sem apagar volumes. Grafo didático 3D com 18/24 e detalhe por teclado conferidos, quatro larguras sem overflow; API respondeu 200 com zero mapas/nós/arestas públicos. GRAPH-01 mantém conteúdo real/revisão e D/E pendentes. Última coleta salva de 14/10, PARTIAL com seis falhas IBGE; retomar/diagnosticar e supervisionar atualização em F2-04/F2-03, sem forçar coleta nesta auditoria. Avaliação real da IA UI-06C/F e gates públicos continuam abertos. [Relatório completo](REPOSITORY_AUDIT.md).

## Registro de entregas

- 2026-10-25 — F2-02 Preparado: auditoria local de autenticação/autorização entregue, com correções de Next.js/dependências, revogação na suspensão, serialização do login/rehash, cookies seguros fora de desenvolvimento, limites sem identidade vazia, identificação JWT e sanitização de erros SQL/configuração. Sem alterar as permissões amplas de ADMIN por conta própria. 1.447 testes backend/320 frontend passaram; lint/types/build nativo e Docker aprovados, scanners npm/Python sem alertas conhecidos nos conjuntos conferidos. Regressões de roles, suspensão/reativação e sigilo; experimento isolado de concorrência passou. Evidências e pendências públicas em [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md); operação útil preservada e nenhum push. Coleta e GRAPH-01F não foram executados nesta fatia.

- 2026-10-23 — Pauta de retomada registrada a pedido do mantenedor: GRAPH-01F para discussão da análise final com IA/grafos, diagnóstico da coleta em F2-04/F2-03 e auditoria específica de autenticação/roles em F2-02. Matriz de permissões documentada a partir do código; checklist geral de pendências e instruções de retomada sincronizados. Apenas documentação/planejamento: sem coleta, auditoria de segurança concluída ou análise causal implementada.

- 2026-10-06 — F1-01 concluído: 14 tabelas, migrations 0001/0002, constraints e triggers de imutabilidade; 29 testes passaram com PostgreSQL 18 isolado; downgrade para base, upgrade e Alembic sem drift verificados.

- 2026-10-06 — F1-02 concluído no backend: cadastro/login/me/refresh/logout, Argon2id, JWT, refresh/CSRF rotativos, revogação, CORS e limite persistente de tentativas. 39 testes passaram com PostgreSQL; migration 0003, reversão/reaplicação e Alembic sem drift verificados. Interface pertence a F1-10.

- 2026-10-06 — F1-04 concluído no backend: cadastro autenticado de fontes HTTP/HTTPS, validação sem credenciais, catálogo e detalhe públicos somente quando referenciados por publicação/indicador, listagem privada por autor e paginação. 45 testes passaram; interface permanece em F1-09/F1-10.

- 2026-10-06 — F1-05 concluído no backend: CRUD de rascunhos próprios, publicação com validação de campos/fontes/financiamento, snapshots, nova versão após edição, catálogo paginado, histórico e arquivamento. 55 testes passaram com PostgreSQL; remoção de rascunho preserva versões publicadas. Interface em F1-09/F1-10.

- 2026-10-06 — F1-06 concluído no backend: criação/edição/publicação/arquivamento de planos, ordem e ativação dos itens, versões específicas, recusa de múltiplas versões da mesma proposta e histórico público. 62 testes passaram.
- 2026-10-06 — F1-07 preparado: API e persistência da simulação concluídas, snapshots/hash, versão do motor, avisos e resultados imutáveis testados. Falta a exibição na interface para encerrar a entrega. Migrations 0004/0005 e roundtrip completo sem drift verificados.

- 2026-10-06 — F1-07/F1-09/F1-10 concluídos: telas públicas de propostas/planos/fontes, histórico, busca, paginação, categoria/autor/ano; painel, cadastro/login e renovação de sessão, editores com impactos/financiamento/fontes, composição e simulação. Fluxo completo verificado no navegador com dados fictícios restritos ao banco isolado. Proposta v2 com R$ 9.999,99 preservou o plano v1 em − R$ 1.234,56. Lint, tipos e build passaram. Revisão em tela pequena permanece em F1-13 após timeout do navegador.

- 2026-10-06 — F0-03 concluído com PostgreSQL nativo em cluster isolado, frontend/API iniciados, migrations e ausência de drift. Docker continua pendente como alternativa de execução.
- 2026-10-06 — F1-08/F1-12 concluídos: Brasil Atual, detalhe/histórico/revisões, fontes e datas, estados sem dados; administração de indicadores/observações/usuários e arquivamento, com auditoria append-only. 70 testes passaram; migration 0006 revertida/reaplicada sem drift.
- 2026-10-06 — F1-03 preparado: duas séries BCB verificadas, importador restrito e idempotente, 36 observações da meta Selic e 8 de DBGG/PIB importadas duas vezes sem duplicação (máxima revisão 1). Restante do catálogo candidato depende de verificar série, recorte e termos. Ver docs/data/INDICATORS.md.
- 2026-10-06 — F1-13 concluído localmente: fluxo completo, sessões após reload, leitura anônima e plano v1 preservado; backend 401/403/privacidade/imutabilidade e integração PostgreSQL. Navegador recuperado; revisão básica de teclado e tela pequena passou após corrigir foco. Ver docs/development/E2E.md. Auditoria aprofundada de acessibilidade e regressão automatizada do navegador ficam na Fase 2.
- 2026-10-06 — F1-11 preparado: metodologia/transparência públicas, licença e roadmap; URL de repositório/canais ainda ausentes. F1-14 preparado: docs/governance/CONTENT_POLICY_DRAFT.md contém proposta concreta e decisões de operação/privacidade pendentes; não há termos vigentes ou cadastro público aberto.

- 2026-10-06 — Verificação final: 70 testes backend passaram, Ruff/lint/formatação e Alembic sem drift; documentos/links, ESLint, TypeScript e build das rotas públicas/privadas passaram. Guias, changelog e roadmap sincronizados. Regra de atualizar backlog após cada entrega registrada em AGENTS.md.

- 2026-10-06 — Ajuste de acesso local concluído: frontend restrito a 127.0.0.1, origens localhost/127.0.0.1 explicitamente permitidas em desenvolvimento e guias corrigidos. 11 testes de autenticação passaram, incluindo CSRF e rejeição de origem para ambos os endereços; Ruff e links dos documentos passaram. Login no navegador em 127.0.0.1 abriu o painel da conta fictícia.

## Redesign solicitado em 2026-10-06

| ID | Estado | Entrega | Evidência / pendência |
| --- | --- | --- | --- |
| UI-01 | Concluído | Home com motivação, escolhas e simulador ilustrativo | Teclado gerou saldo negativo, positivo e zero; temas claro/escuro; 360/768/1280/1920 sem overflow; contraste de 113 elementos de texto sem falhas nos pares verificados |
| UI-02 | Concluído | Sistema visual em todas as páginas | 17 telas em 360/768/1280/1920, 68 combinações sem overflow; contraste claro/escuro nas 12 telas públicas e revisão nas privadas; teclado, menu e pular conteúdo verificados; lint/tipos/build/docs passaram |
| UI-03 | Concluído | Duplicar proposta/plano em rascunho próprio | Navegador criou cópias privadas com crédito ao autor e versão original; fontes/valores preservados; plano copiado manteve proposta v1 e simulação − R$ 1.234,56; originais continuaram publicados |
| UI-04 | A fazer | Apoios e comentários | Ações desabilitadas e sinalizadas “em breve”; exigem regras de domínio, persistência, autorização e moderação antes de habilitar |
| UI-05 | Preparado | Código aberto e contato no rodapé | Links de transparência e metodologia funcionam; URL pública do repo e canal de contato ainda não fornecidos |

- 2026-10-06 — UI-01/UI-03 concluídos: home reconstruída com geometria abstrata, bento, explicação da motivação eleitoral e limites do cálculo; cópia autenticada para rascunho com atribuição. ESLint, TypeScript e build passaram antes dos últimos refinamentos do painel. Validação final de UI-02 segue em andamento.
- 2026-10-06 — UI-02 concluído: ESLint, TypeScript, build de todas as rotas e links dos documentos passaram. 68 combinações de página/largura sem overflow; 12 telas públicas verificadas nos dois temas, com contraste sem falhas nos textos verificados. Menu abre por Enter, fecha por Escape com foco no summary, e pular conteúdo foca MAIN. Cópias revalidadas após buscar a versão somente ao clicar (menor payload inicial dos cards). Plano original v1 segue público com − R$ 1.234,56; cópias seguem privadas. Fontes tipográficas com avisos/licenças preservados. UI-04/UI-05 e validação do fluxo completo em Docker permanecem pendentes.

- 2026-10-06 — Refinamentos finais do redesign concluídos: espaço reservado para contagem animada e sessão, unidades com tamanho mínimo de 16 px e ícones próprios também no celular. Build final passou; home/indicador rechecados nas 4 larguras sem overflow; passos em 360 px com 3 ilustrações visíveis e documento 345/345 px. Overrides de viewport removidos ao terminar a revisão.

## Dados e base do Brasil — 2026-10-07

| ID | Estado | Entrega | Evidência / pendência |
| --- | --- | --- | --- |
| DATA-01 | Concluído | Base contextual congelada em novas versões de propostas e planos | Migration 0007; testes de revisão do indicador, base preservada e hash de simulação inalterado. Versões anteriores mantêm ausência explícita; base fiscal nacional completa ainda pendente. |
| DATA-02 | Concluído | Coletor diário BCB/IBGE e histórico | Sete séries oficiais e histórico real coletados com SUCCESS; worker diário local ativo. 85 testes passaram, incluindo lock entre processos, cooldown, permissões e solicitação em background. Supervisor/agendamento de produção continua pendente. |
| DATA-03 | Concluído | Lista de métricas e roteiro para pesquisa do mantenedor | docs/data/RESEARCH_BRIEF.md: fontes, unidades, recortes e formulário para separar dado, hipótese causal e consequência. Nenhum valor inventado. |
| UX-01 | Concluído | Redesign das páginas internas e editores | Home preservada; páginas internas, gráficos, filtros, fontes, auth e editores verificados. 14 telas em quatro larguras e dois temas: 112 combinações sem overflow; contraste dos textos conferidos, autosave, base explícita, balanço e teclado verificados. Lint, tipos e build passaram. |
| DATA-04 | Concluído | Base fiscal observada calculável do Governo Central | Três séries RTN reconciliadas em 12 meses de um ano fechado; PIB nominal de quatro trimestres do mesmo ano e proporções condicionais. Coleta real, snapshots, API e tela verificados. Não inclui soma de impactos a cenários futuros. |
| DATA-05 | Preparado | Contextos revisados e análise futura por IA | DATA-05A/B concluídos: contrato, referências reais e API de revisão/publicação imutável. DATA-05C Preparado: interface e primeiro rascunho pesquisado entregues; revisão humana efetiva do conteúdo real ainda pendente. Sem IA ou grafo nesta entrega. [Contrato](../data/CONTEXT_EVIDENCE.md). |
| DATA-06 | Concluído | Compatibilidade fiscal de impactos e cenários futuros | DATA-06A e DATA-06B1/B2 verificados localmente no recorte restrito; premissas explícitas, revisão vinculada e combinação condicional. Outros recortes em DATA-07. |
| DATA-07 | Concluído | Composição fiscal e outras abrangências | A/B1/B2/B3 entregues no recorte observado e documentado: composição primária, juros/nominal, execução federal por função e EFGG anual por esfera. Não conclui todo o catálogo F1-03 nem amplia o motor. [Evidência](../development/VERIFICATION.md). |

- 2026-10-07 — DATA-01 concluído: base por versão e inclusão no snapshot/hash da simulação, atualização explícita de rascunho e aviso de bases distintas. 79 testes backend passaram, incluindo novos contratos IBGE e preservação de publicações após revisão do dado. DATA-03 concluído com roteiro de pesquisa; DATA-02 e UX-01 seguem em verificação final.

- 2026-10-07 — DATA-02 concluído: 575 observações preservadas no banco de demonstração, sete séries com coleta SUCCESS e processo diário ativo. 85 testes backend, Ruff/formatação e Alembic sem drift passaram; ESLint, tipos, build e links dos documentos passaram. Operação de produção e base fiscal nacional seguem pendentes.


- 2026-10-07 — UX-01 concluído e aprovado pelo mantenedor: 112 combinações de tela/largura/tema sem overflow, contraste dos textos conferidos após ajuste de controle desabilitado, menu por Enter/Escape, períodos de gráfico, filtros/estado vazio, disponibilidade de usuário e mostrar senha. Rascunho fictício salvo automaticamente e reaberto com texto/fonte/base preservados; balanço atualizado ao selecionar/desativar medidas e mudar anos. 85 testes backend, Ruff, Alembic sem drift, lint/tipos/build passaram. Apoios/comentários, Google login, termos vigentes, base fiscal nacional e operação de produção seguem pendentes. Novo contexto sobre arestas recebido apenas como referência; nenhuma implementação de grafo foi iniciada.


## Base fiscal — entrega de 2026-10-09

- DATA-04 concluído com trabalho paralelo de pesquisa oficial, conectores e revisão de arquitetura/testes, integrado pelo coordenador. Onze séries com coleta real SUCCESS; três séries RTN com 68 meses cada e PIB com 22 trimestres. A base anual selecionada é 2025: doze meses fiscais e quatro trimestres do PIB, com valores publicados, cálculo e diferença de reconciliação visíveis.
- Coletas fiscal/PIB atômicas, falhas preservando a base anterior, privacidade de fontes com URL coincidente e HTTP limitado verificados. Novas bases incluem o denominador no hash/snapshot; revisões e atualização explícita de rascunho não alteram publicações ou o resultado incremental original.
- 214 testes backend passaram com PostgreSQL isolado; Ruff/formatação, Alembic sem drift, ESLint, TypeScript, build e links dos documentos passaram. Brasil Atual conferido em 360/768/1280/1920 nos dois temas, com detalhes abertos e sem overflow; fontes, precisão e fórmula conferidas. Ver [docs/development/VERIFICATION.md](../development/VERIFICATION.md).
- F1-03 continua preparado: onze séries automatizadas não encerram o catálogo fiscal/social previsto. DATA-06/DATA-07, evidências causais/IA, operação persistente, Docker completo, termos e lançamento público permanecem pendentes.

- Revisão final da entrega fiscal: proteção contra truncamento de ano previamente completo do PIB e três regressões adicionais, suíte final com 214 testes. Valores longos no celular e períodos de calendário do gráfico trimestral corrigidos; build final passou.

## Grafos — evolução em preparação

| ID | Estado | Entrega | Critério de aceite / dependência |
| --- | --- | --- | --- |
| GRAPH-01 | Preparado | Página explicativa com explorador interativo do grafo de causas | Rede de nós e arestas inspirada na referência visual do mantenedor; selecionar entidades e relações para entender conexões, direção, fontes, premissas e incertezas. Explicação guiada, busca/filtros, zoom/deslocamento, celular/teclado e alternativa em lista. A/B/C concluídos no recorte qualitativo; primeira rede real, magnitudes e IA continuam pendentes. Depende dos contratos e políticas de revisão/publicação do grafo. Ver [docs/product/GRAPH_EXPLORER.md](../product/GRAPH_EXPLORER.md). |

- 2026-10-09 — Preferência do mantenedor registrada para quando começar a implementação dos grafos: página que ensina o funcionamento e rede interativa de pontos/conexões, com inspeção dos nós e das arestas. Requisito documentado; implementação continua a fazer. Não inicia o grafo nem altera a UX atual ou o cálculo fiscal. Links locais da documentação verificados.

## Brasil Atual e Fontes — entrega de 2026-10-10

| ID | Estado | Entrega | Evidência / pendência |
| --- | --- | --- | --- |
| UX-02 | Concluído | Redesign restrito a Brasil Atual e Fontes | 44 testes de formatação, variação, calendário, fontes e estado de consulta; lint, tipos e build passaram. Duas telas em quatro larguras e dois temas: 16 combinações sem overflow ou falhas nos contrastes de texto medidos. Drawer, filtros, gráficos e foco conferidos. Ver [docs/design/DATA_EXPLORER.md](../design/DATA_EXPLORER.md) e [docs/development/VERIFICATION.md](../development/VERIFICATION.md). |

- Destaques fixos e equilibrados: desemprego, IPCA mensal, dívida bruta/PIB e resultado primário. Bento por tema, valores compactos, comparações neutras e detalhe lateral/no celular. Base fiscal anual visual com memória do cálculo; painel de referência duplicado removido apenas desta página.
- Fontes oficiais agrupadas por instituição em tabela responsiva. Doze registros oficiais históricos resultam em nove fontes distintas de três instituições: duplicatas reais de Selic, DBGG e RTN agrupadas sem alterar seus IDs; variáveis mensal/acumulada do IPCA preservadas. Exemplos somente em desenvolvimento. Estado da consulta automática separado da referência e da data de acesso.
- Home, páginas aprovadas, componentes compartilhados e tokens globais preservados. A regra dos destaques aparece em Brasil Atual e na documentação; Metodologia não foi alterada para respeitar o limite de duas telas.
- Dados complementares de renda, informalidade, participação e crescimento real permanecem em DATA-05/F1-03 e aparecem como “Em breve”. Grafos, cenários fiscais futuros e operação pública mantêm suas dependências anteriores.

## Seções de tema e emprego — entrega de 2026-10-10

| ID | Estado | Entrega | Evidência / pendência |
| --- | --- | --- | --- |
| UX-03 | Concluído | Grade completa por tema abaixo dos Destaques | Todos os indicadores, selo, linhas equilibradas e variante horizontal; busca única, faixa compacta e offsets. 56 combinações sem overflow/vãos; teclado e contraste conferidos. Fontes e demais telas aprovadas preservadas. |
| DATA-08 | Concluído | Renda real habitual, informalidade e participação PNAD | SIDRA 6390/5933, 8513/12466 e 5944/4096 verificados/coletados; 35 observações por série. Renda atômica, histórico salvo inteiro reconsultado, preços/proveniência/revisões. 14 indicadores, 12 fontes distintas. |

- 234 testes backend e 76 frontend passaram; Ruff/formatação, Alembic sem drift, ESLint, tipos, build e links locais passaram. [Fontes e limitações](../data/EMPLOYMENT_INDICATORS.md), [verificação](../development/VERIFICATION.md).
- Nenhum dos três novos indicadores ficou em preparação. PIB em volume continua em preparação. Subutilização SIDRA 6441/4118 é sugestão verificada, sem implementação; endividamento/inadimplência dependem de seleção/verificação antes de eventual autorização.
- IBC-Br e dívida líquida falharam por HTTP na última coleta; dados preservados e status explícito. Operação persistente de produção permanece pendente. DATA-05/06/07, GRAPH-01 e dependências de lançamento mantêm seu estado; esta ampliação não conclui todo o catálogo F1-03 nem prevê efeitos causais.

## Organização para colaboração pública — 2026-10-10

| ID | Estado | Entrega | Evidência / pendência |
| --- | --- | --- | --- |
| REPO-01 | Concluído | Documentação organizada e guias de agentes | Raiz com entradas GitHub; docs por domínio, índice/estado/publicação; perfis fiscal/frontend/backend/QA/docs/coordenador e AGENTS locais. Links/checker atualizados; checks pertinentes verificados. |

- Migração conserva documentos e registros históricos; sem mudanças de UX/API/schema/cálculo. CI frontend agora executa os 76 testes de exploração já existentes. READMEs de módulos/scripts atualizados ao estado real.
- Revisão de publicação e alinhamento somente leitura com agentes especializados. V1 local alinhada à visão, com limite incremental explícito; próxima etapa de produto DATA-06. Código público e serviço lançado separados em [STATUS](STATUS.md) e [PUBLICATION](../governance/PUBLICATION.md).
- Primeiro commit/remoto/push, CI remota, proteção/main e canais de segurança continuam pendentes; nenhuma ação externa feita. Compose completo, termos vigentes e operação de produção mantêm as dependências anteriores. Não marcar F0-06/F0-04/F1-11/F1-14/F2 como concluídos pela organização.

## Compatibilidade fiscal — 2026-10-10

| ID | Estado | Entrega | Evidência / pendência |
| --- | --- | --- | --- |
| DATA-06A | Concluído | Metadados e compatibilidade com a referência histórica | Verificação visual retomada e concluída junto a DATA-06B2; registros automatizados preservados e regressão reexecutada. [Contrato](../data/FISCAL_COMPATIBILITY.md), [evidências](../development/VERIFICATION.md). |
| DATA-06B | Concluído | Cenário futuro e combinação de referência/medidas | Motor puro e integração opcional aos planos; premissas anuais explícitas, revisão vinculada, bloqueios e resultados preservados. Não depende de grafos/IA. |

- Metadados por parcela com ausência explícita, validação de ano-base e preservação em rascunhos/publicações/cópias. Nova avaliação versionada compara somente recortes declarados com o snapshot fiscal do plano; metadados ausentes/misturados e ano futuro têm motivos claros. Não soma base histórica nem valida custos/causas.
- Revisão fiscal somente leitura encontrou e corrigiu um parágrafo que interpretava o sinal de somas heterogêneas. Motor aritmético permanece 1.0.0; avaliação tem versão própria e participa do snapshot/hash das novas execuções.
- Backup local antes da migration demo; checkpoint conferiu duas versões publicadas de proposta, uma de plano, dois impactos antigos, três execuções concluídas e seis resultados anuais sem alterações. Seis rotas HTTP passaram, incluindo leitura pública e avisos do legado no HTML servido. Nenhum conteúdo de demonstração novo publicado.
- API/frontend/coletor retomados no ambiente local isolado. Coleta atual PARTIAL: 13 séries SUCCESS; renda real FAILED com histórico anterior preservado. Supervisor de produção segue pendente.
- DATA-06 geral permanece Preparado; DATA-06A não é marcado Concluído sem a conferência visual pendente. Nenhum push, publicação no GitHub, grafo ou cenário futuro nesta entrega. [Verificação](../development/VERIFICATION.md).

- 2026-10-10 — Conta comum fictícia criada no banco local de demonstração para validação manual de DATA-06A. Cadastro, login e logout conferidos pela API; conta administrativa preservada. Senha/tokens não registrados no repositório. Verificação visual segue pendente.

## Próximas fatias de produto — 2026-10-10

| ID | Estado | Entrega | Aceite / dependências |
| --- | --- | --- | --- |
| UI-06 | Preparado | **Épico: Criar proposta acessível — modo guiado e manual** | Fluxo local, níveis, modos, sensibilidade fiscal e proteções implementados; Gemini real configurado e chamado com exemplos fictícios; avaliação sistemática ainda pendente. Operação pública mantém gates próprios. [Requisito](../product/PROPOSAL_CREATION.md), [fatias e aceite](#épico-ui-06--criar-proposta-acessível). |
| DATA-06B1 | Concluído | Contrato e motor puro de cenário fiscal declarado | 87 testes específicos e 282 unitários backend passaram; Ruff/formatação e links. Recorte restrito, anos/premissas explícitos, combinação condicional e bloqueios globais; sem API/banco/interface. [Contrato](../data/FISCAL_SCENARIOS.md). |
| DATA-06B2 | Concluído | Integrar cenário declarado aos planos | Migration 0010, autoria/revisão vinculada, snapshot/hash, publicação imutável, editor opcional e leitura pública. [Verificação](../development/VERIFICATION.md). |

As pendências registradas nesta primeira fatia foram resolvidas pela integração e verificação DATA-06B2 abaixo; o motor isolado não as encerrava. A preferência por IA não antecipa implementação nem bloqueia o fundamento fiscal.

- 2026-10-10 — DATA-06B1 concluído: motor puro de cenário anual declarado, avaliação contra o cenário separada da referência histórica, composição de receitas/despesas e bloqueios globais de ausência/divergência/estimativa desconhecida/dupla contagem/componente negativo ou acima do limite. 87 testes específicos e 282 unitários backend passaram; Ruff/formatação e links verificados. Revisão fiscal independente, sem migração, consulta externa, alteração do editor ou de execução legada. DATA-06B2, DATA-06A visual e DATA-06 geral preservam suas pendências. UI-06 registrado conforme feedback do mantenedor, implementação adiada.


## Integração do cenário aos planos — 2026-10-10

- DATA-06B2 concluído: cenário opcional por versão, premissas anuais manuais, confirmação autoral vinculada ao hash de contexto/horizonte/premissas/composição, reset após mudanças fiscais/cópias e resultado conjunto condicional persistido. Incremental padrão e leitura legada preservados.
- 426 testes backend com PostgreSQL de integração e 116 testes frontend passaram; Ruff/formatação (114 arquivos), ESLint, TypeScript e build final passaram. Migration 0010 revertida/reaplicada no banco de integração e Alembic sem drift; links locais verificados.
- 32 combinações em 360/768/1280/1920 e temas claro/escuro: editor de cenário, resultado público com premissas abertas, campos de metadados da proposta e resultado legado, sem overflow da página. Tabelas têm rolagem interna no celular. Salvamento/reabertura, configuração incompleta, bloqueio sem revisão, combinação confirmada, revogação por composição, cópia sem confirmação e leitura anônima conferidos. Ano-base obrigatório em preços constantes e removido em nominal; foco por teclado visível. Nenhum erro de console na conferência final. Auditoria aprofundada de acessibilidade permanece F2-01.
- Backup/checkpoint demonstraram publicações e execuções anteriores intactas. Dados novos de QA explícitos e development-only. Nenhuma publicação no GitHub/deploy; editor guiado por IA continua adiado em UI-06.
- DATA-06A, DATA-06B e DATA-06 encerrados no recorte documentado. DATA-07, catálogo mínimo F1-03, DATA-05/GRAPH-01/IA e operação pública permanecem pendentes. Estimativa de escopo: cerca de 60% do produto completo e 85% da V1 local, sem precisão de prazo.


## Épico UI-06 — Criar proposta acessível

Decisão do mantenedor registrada em 2026-10-10: **separar entrar de publicar**. Conta continua obrigatória para contribuir; começar não exige chegar com pesquisa pronta. O rigor está em publicar como proposta completa. Esta seção detalha o UI-06 existente, sem criar um segundo épico. Estados abaixo atualizados em **2026-10-19**, após implementação e validação local. Registros datados de 2026-10-10 conservam a decisão original.

| ID | Estado | Entrega | Critério de aceite | Dependências |
| --- | --- | --- | --- | --- |
| UI-06A | Concluído | Molde comum e dois níveis de proposta | IDEIA salva com título/uma frase, anos/valores/período opcionais; compartilhamento explícito com selo “ideia em construção”, duplicação e sugestão de fontes. Excluída no backend do cálculo, planos e ranking. COMPLETA exige problema, medida, financiamento, quem ganha/perde, riscos, fontes e campos fiscais obrigatórios; checklist mostra faltas. Privacidade, autoria e publicações anteriores preservadas. | F1-02/F1-05; contrato de estados/visibilidade e regras de promoção; termos e UI-06E antes de abrir compartilhamento |
| UI-06B | Concluído | “Me ajuda a montar” e “Eu preencho” | Guiado por IA ou manual por etapas; mesmo molde e tela final. Trocar modo e interromper/retomar sem perder campos confirmados, fontes ou origem assistida; falha/limite da IA permite seguir manualmente. Em 25/10, criação e edição de IDEIA abrem só título/frase; “Desenvolver” abre preparação completa no mesmo ID, com detalhes preservados e guiado começando após respostas já salvas. Explicação curta no topo de Ideias/Propostas/Planos; sugestões opcionais recolhidas. Stepper/prévia/consentimento mantidos (ADR-043/044/047). | UI-06A; UI-06C para conversa; UI-06D para análise comum |
| UI-06C | Preparado | Condução neutra por roteiro fixo e integração trocável | Uma pergunta simples por vez; texto/ordem iguais para todos os temas/posições, versionados e publicados em Metodologia. Incluir “Quem poderia perder com isso?”/“O que poderia dar errado?”. Prompt 4.0.0 instrui a IA a desenvolver a intenção sem escolher posição política; revisão de conteúdo é humana, sem rejeições semânticas no código; opções de implantação/contrapartidas e lacunas separadas, sugestões desmarcadas e incorporadas somente por seleção/confirmação, como ponto a avaliar; original e sugestão comparados, saída sem alteração identificada, opção de manter original e preenchimento só após confirmação. “Não sei” válido, sem inventar valor/ano/fonte: catálogo oficial opcional com fonte/data ou “sem estimativa”, incompleta. Todo texto gerado rotulado “assistido por IA”. Interface de modelo trocável/barato, limite por usuário configurável, logs prompt/resposta/versões com acesso/retenção definidos e chave só em variável de ambiente. | UI-06A; roteiro revisado, provedor/custo/privacidade definidos; catálogo oficial; aprovação nos testes UI-06F antes de disponibilizar |
| UI-06D | Concluído no recorte declarado | Análise de impacto comum e ajustável | Mesma análise e checklist nos dois modos. COMPLETA publicada estimada usa DECLARED_SENSITIVITY_1, multiplicadores explícitos e Decimal/motor 1.0.0; padrão 1 sem faixa inventada. Recortes ausentes/mistos bloqueiam conta. Rótulo “estimativa declarada”; não há selo causal/estatístico ou cálculo de IDEIA. | UI-06A; método documentado para faixas/selos, recortes do motor e evidências pertinentes; não assumir que DATA-06 já cobre todos os efeitos |
| UI-06E | Concluído localmente | Participação com proteção contra spam e abuso | Conta obrigatória; limite diário de ideias e limites de IA aplicados no servidor; denúncia, tratamento/moderação e proteção de dados. Ranking padrão de COMPLETAS por solidez (fontes, financiamento definido, revisão), com critérios transparentes; nunca popularidade, nunca IDEIAs. Necessário antes de abrir o novo fluxo compartilhável. | F1-02; UI-06A; política de conteúdo/privacidade F1-14 e regras de operação; sem duplicar o rate limit de login existente |
| UI-06F | Preparado | Imparcialidade e regressão registradas | Mesmo roteiro em casos equivalentes de visões opostas; comparar tom e perguntas, registrar versões/casos/resultados. Nenhuma pergunta do roteiro varia por tema/posição; opções de desenvolvimento devem ser equilibradas e identificadas como hipóteses, sem mérito político ou adesão inferidos. Testar confirmação, “não sei”, alternância, exclusões, limites, sigilo e falhas; repetir após mudança de roteiro, prompt ou modelo; conferir preservação de sentido nas reformulações de escrita. | Casos/oposições e critérios definidos; UI-06A/B/C/D/E implementados para aceite final; avaliação é gate do modo guiado |

O [requisito principal](../product/PROPOSAL_CREATION.md) concentra as regras do épico. Perguntas adaptativas do planejamento anterior foram substituídas por roteiro fixo; ajustes de premissas não permitem à IA calcular nem decidir política. Logs privados não são arquivos públicos do repositório. Compartilhar uma IDEIA exige decisão do autor; salvar rascunho não abre dados privados automaticamente.

- 2026-10-10 — UI-06 reescrito e detalhado conforme decisão de produto; roadmap/requisito/escopo/estado/decisões sincronizados. Apenas documentação e verificação de links; nenhuma implementação, mudança de banco, chamada de IA ou teste de produção executados. UI-06 e suas fatias permanecem A fazer.

## Composição fiscal — DATA-07

| ID | Estado | Entrega | Critério de aceite / pendência |
| --- | --- | --- | --- |
| DATA-07A | Concluído | Receita bruta, transferências e composição primária RTN do Governo Central | Coleta real de 120 observações, 12 meses/mesmo ano, sinais, revisões, fonte, transação e reconciliação; API/painel públicos separados da base congelada. 457 testes backend/134 frontend, checks/build e 8 combinações de tela passaram. [Evidência](../development/VERIFICATION.md). |
| DATA-07B | Concluído | Função de gasto, juros e outros entes | B1–B3 verificadas localmente, com critérios próprios, cobertura e correspondência explícitas. Outros entes em agregados oficiais por esfera; granularidade individual futura, sem soma própria de declarações. |
| DATA-07B1 | Concluído | Juros e resultado nominal observados do Governo Central | 36 observações reais idempotentes de 2025; API/painel, doze meses, sinais e regime misto. 503 testes backend/157 frontend e oito combinações de tela passaram; contexto/publicações preservados. [Contrato](../data/FISCAL_INTEREST.md) · [Evidência](../development/VERIFICATION.md). |
| DATA-07B2 | Concluído | Gasto federal por função e estágio | Coleta real 2025, revisão imutável/idempotente, API e painel com natureza/estágio/cobertura. 609 testes backend/177 frontend, migration 0011 e oito combinações de tela passaram. Base e publicações preservadas. [Contrato](../data/FISCAL_SPENDING.md) · [Evidência](../development/VERIFICATION.md). |
| DATA-07B3 | Concluído | Outros entes e correspondência entre classificações | EFGG real 2025: 64 valores em revisão imutável/idempotente, consolidação oficial e cobertura municipal estimada explícitas; API/painel e termos próprios. 719 testes backend/197 frontend, migration 0012 e oito combinações de tela passaram. Publicações preservadas. [Contrato](../data/GENERAL_GOVERNMENT.md) · [Evidência](../development/VERIFICATION.md). |

- 2026-10-10 — DATA-07A iniciada: hierarquia e sinais verificados em API/manual/planilha oficiais, com 180 pares API/XLSX de 2025 e diferenças mensais explícitas. Integração backend/frontend e verificação em andamento; DATA-07 ainda não concluído.

## DATA-07A concluído — 2026-10-11

457 testes backend passaram com PostgreSQL de integração; 134 testes frontend, ESLint, TypeScript e build final passaram. Ruff e formatação de 118 arquivos passaram; Alembic sem drift, sem nova migration. Oito combinações de 360/768/1280/1920 nos temas claro/escuro, composição e detalhes abertos, sem overflow da página; tabela exata com rolagem interna no celular. Expansão por Enter, foco visível de 3px e ausência de erros/avisos de console conferidos. Auditoria aprofundada de acessibilidade permanece F2-01.

Coleta real de 2025 importou 120 observações auxiliares. Nova coleta registrada confirmou idempotência: 120 registros, máxima revisão 1, composição AVAILABLE. Receita e ponte líquida reconciliaram com diferença 0; despesa com diferença anual R$ 0,01, preservada. A coleta completa terminou SUCCESS nos 14 indicadores e no grupo de composição; renda real voltou a ter sucesso. Acrescentar composição preservou exatamente o hash/contexto corrente, e checkpoint final preservou quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados anteriores. Backup local anterior conservado; nenhum commit/push/deploy.

Revisão independente corrigiu a exclusão indevida das séries auxiliares do catálogo administrativo: público mantém os 14 indicadores, administração permite gerir as dez séries adicionais. Testes cobrem valores assinados/escala/limites, lacunas, revisão mais recente, âncoras revisadas, reconciliação, privacidade de fonte, idempotência, rollback por falha intermediária/truncamento/indisponibilidade e preservação de snapshots. Allowlist e fingerprint do trio original mantidos; parser compartilhado privado, métodos de simulação inalterados.

DATA-07 permanece Preparado: DATA-07B ainda A fazer. UI-06 continua planejado, sem implementação de IA ou novo editor.

## DATA-07B1 concluído — 2026-10-11

503 testes backend passaram com PostgreSQL de integração; 157 testes frontend, ESLint, TypeScript e build final passaram. Ruff e formatação de 123 arquivos passaram; Alembic sem drift, sem nova migration. Oito combinações de 360/768/1280/1920 nos temas claro/escuro com painel de juros e método abertos, sem overflow da página; teclado e foco visível conferidos. Auditoria aprofundada permanece F2-01.

Coleta real de 2025 importou 36 observações auxiliares de primário abaixo da linha, juros e nominal. Repetição preservou os mesmos registros, máxima revisão 1; AVAILABLE, doze meses e residual anual R$ 0,00. Valores da API conferidos em 36 pares da planilha oficial. Acrescentar o conjunto preservou exatamente o contexto corrente. Coleta completa registrada terminou SUCCESS nos 14 indicadores, composição e juros; worker diário local restaurado e aguardando a janela.

Checkpoint posterior preservou quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados anteriores. Backup anterior conservado; motor, fingerprints legados e snapshots intactos. Nenhum commit/push/deploy. Revisão independente por leitura sem achado bloqueante.

Navegador encontrou formato NUMERIC de seis casas com zeros adicionais: helper corrigido para aceitar zeros subcentavo sem arredondar frações reais; teste de contrato real e casos assinados adicionados. Interface mostra competência, sinais e método abaixo da linha, sem chamar juros de pagamentos orçamentários. Pesquisa de funções leu arquivo oficial completo (155.738 linhas, 37 colunas), preservou naturezas/99 distintos e residual anual +R$ 0,01 do resumo. Pipeline funcional ainda não implementado.

DATA-07 e DATA-07B permanecem Preparados. DATA-07B2 tem pesquisa/contrato, pipeline pendente; DATA-07B3 ainda A fazer. UI-06 e grafos continuam planejados.


## DATA-07B2 concluído — 2026-10-11

609 testes backend passaram com PostgreSQL de integração, incluindo rollback da primeira coleta, revisões, imutabilidade por SQL e privacidade. 177 testes frontend, ESLint, TypeScript e build passaram. Ruff e formatação de 131 arquivos passaram; migration 0011 revertida/reaplicada somente em integração, Alembic sem drift. Demo recebeu apenas upgrade após backup.

Coleta oficial registrada terminou SUCCESS e importou uma revisão íntegra de 2025: 155.738 registros, 37 colunas, doze meses, 753 grupos mensais e 64 combinações anuais de natureza/função; 29 funções e dois rótulos sem classificação distintos. Os 2.259 valores mensais conferiram com a agregação independente da pesquisa. Pago + RAP = total em centavos; resumo publicado do subconjunto conciliou os doze meses e preservou diferença anual +R$ 0,01. Nova gravação do mesmo payload preservou ID, revisão 1 e referência corrente; nenhuma observação artificial foi adicionada ao catálogo.

Oito combinações de 360/768/1280/1920 nos temas claro/escuro com painel e método abertos passaram sem overflow da página. Tabela exata tem rolagem interna no celular; nove combinações de natureza/estágio em 360 px, sinais, grupos 99, teclado/foco de 3px e console sem erros/avisos conferidos. 46 pares visíveis de contraste passaram (23 por tema, mínimo 8,83:1); cabeçalho de 1×1 px recortado visualmente e mantido para leitores de tela excluído da medição visual. Fonte oficial mostrou licença ODbL e consulta atualizada, sem criar indicadores fictícios. Auditoria aprofundada permanece F2-01.

Checkpoint preservou quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados. API/site/worker diário local retomados. Não há atualização por visita, integração ao motor ou implantação pública; DATA-07B3 e operação supervisionada continuam pendentes.

Na verificação real, o primeiro processamento foi recusado pelo scanner de um metadado ignorado UTF-16 da própria planilha; suporte estrito de varredura UTF-16 foi acrescentado somente aos XML ignorados, sem execução, mantendo bloqueio de DTD/entidades e planilhas ativas UTF-8. Testes de regressão e arquivo completo passaram após o reparo. Última coleta registrada verificada conforme evidência desta entrega; sem alteração nos snapshots anteriores.

DATA-07 e DATA-07B permanecem Preparados; DATA-07B3 ainda A fazer. UI-06 e grafos continuam planejados.


## Governo Geral por esfera DATA-07B3 — 2026-10-12

719 testes backend passaram com PostgreSQL exclusivo de integração; Ruff e formatação de 138 arquivos passaram. Migration 0012 foi revertida/reaplicada somente em integração, com 18 testes focados, e Alembic não detectou novas operações. Demo recebeu apenas upgrade após backup. 197 testes frontend passaram; ESLint, TypeScript e build final passaram novamente após o ajuste textual e do destino do link da planilha.

Coleta real EFGG de 2025 produziu revisão 1 AVAILABLE: oito grupos por oito métricas, 64 valores conferidos com a extração independente da pesquisa da mesma planilha. O SHA-256 do arquivo também conferiu; repetir a gravação preservou ID, revisão e data de coleta do conjunto. A tabela 3.1 confere oito agregados do Governo Geral dentro do próprio arquivo, sem alegação de fonte externa independente. Diferenças das identidades/partições preservadas, máximo absoluto R$ 0,01 para tolerância R$ 0,03. Valores originais em milhões, normalização a centavos por célula agregada, sinais, termos e metadados de cobertura preservados.

Coleta registrada completa terminou SUCCESS, incluindo `general-government` com 64 observações, sem adicionar indicadores artificiais. Inserir apenas EFGG preservou a referência corrente. A coleta diária completa atualizou a data de referência da Selic de 11/10 para 12/10/2026; comparação dos contextos isolou essa mudança e sua proveniência, sem alteração fiscal. Essa atualização legítima muda o contexto corrente, mas não reescreve publicações. Checkpoint posterior preservou integralmente um conjunto funcional B2, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções concluídas e doze resultados.

Oito combinações de 360/768/1280/1920 e claro/escuro, com painel, método e células originais abertos, passaram sem rolagem horizontal da página. Tabelas têm rolagem interna. Quatro recortes em 360 px, valores/sinais/cobertura, expansão por Enter e foco de 3px conferidos. 38 pares de contraste passaram (19 por tema, mínimo 10,18:1); console sem erros/avisos. Após o ajuste do link, a página foi conferida novamente: recurso resolvido da revisão, fonte oficial em /fontes, ausência de overflow/erros. Auditoria aprofundada permanece F2-01.

Dois comportamentos HTTP reais exigiram reparo: redirecionamento oficial revisado agora é tratado manualmente sem seguir URLs arbitrárias; recurso thot recusa HEAD, então a verificação usa duas leituras GET limitadas, conferindo URL/cabeçalhos/hash e metadados da publicação antes/depois. Regressões e coleta completa passaram. Não há consulta por visita, alteração do motor/base congelada ou coletor SICONFI/NFSP habilitado.

API/site/worker diário local retomados; worker aguarda janela. Código/documentos continuam locais, sem commit/push/deploy. Licença desta EFGG são os termos do Tesouro Transparente com atribuição, não ODbL inferida. Comunicação do produto à STN permanece rastreada em PUBLICATION; operação persistente e lançamento público continuam pendentes.

DATA-07 e DATA-07B encerrados no recorte agregado observado. Próximo tópico: DATA-05, contextos/evidências revisados antes de grafos; UI-06 permanece planejado. Catálogo mínimo F1-03, granularidade SICONFI por ente, correspondência COFOG validada e operação pública mantêm seus critérios próprios. Os estados pendentes nas seções datadas anteriores são história, superada por esta entrega.


## Contextos e evidências — DATA-05, 2026-10-13

Fatias do DATA-05 existente, sem duplicar épico. Objetivo: observações, hipóteses alternativas, contrapartidas, consequências e incertezas rastreáveis; revisão não comprova causalidade. [Contrato](../data/CONTEXT_EVIDENCE.md).

| ID | Estado | Entrega | Critério / evidência |
| --- | --- | --- | --- |
| DATA-05A | Concluído | Contrato isolado e revisão vinculada ao conteúdo | Biblioteca estrita/imutável 1.0.0, lacunas explícitas, fontes/recortes/evidências, hash completo e correspondência de revisão declarada; 77 testes específicos e 626 unitários backend, Ruff/formatação de 141 arquivos passaram. Não autoriza publicação. |
| DATA-05B | Concluído | Persistência, revisão autorizada e publicação | Migration 0013, quatro tabelas append-only, API/autoria/revisor distinto, referências reais/frozenpayload e gates de publicação; 918 testes backend incluindo 46 integrações de contextos passaram; Ruff/formatação de 150 arquivos e Alembic sem drift. Demo com backup/upgrade/checkpoint; interface permanece C. [Evidência](../development/VERIFICATION.md). |
| DATA-05C | Preparado | Contextos nos indicadores e primeiro conteúdo revisado | Leitura pública/histórico, editor manual, seleção de observações, revisão distinta/publicação e integração nos indicadores entregues. Primeiro contexto de desemprego pesquisado e privado, assistido por IA; falta revisão humana efetiva e publicação pelo autor. 943 backend, 232 frontend, lint/types/build passaram; editor e detalhe conferidos em 360/768/1280/1920 e dois temas, sem overflow; 13 pares de contraste AA. API/privacidade/checkpoint conferidos. [Pesquisa](../data/FIRST_CONTEXT_RESEARCH.md). |

DATA-05 permanece Preparado: nenhum contexto real, endpoint, banco ou interface habilitado nesta fatia. A revisão paralela do contrato reforçou a distinção entre correspondência declarada e autorização; avaliações da biblioteca não são usadas como gate HTTP. Sem alterações nos coletores, base fiscal, motor, publicações ou telas aprovadas. Integração PostgreSQL/frontend não foi repetida por biblioteca sem uso em runtime; verificação anterior permanece histórica. Próximo passo: DATA-05B. GRAPH-01 e UI-06 continuam futuros.


## Contextos persistidos DATA-05B — 2026-10-13

918 testes backend passaram com PostgreSQL exclusivo de integração, incluindo 46 integrações de contextos, 51 novos testes de entrada e 25 testes do resolvedor. Ruff completo e formatação de 150 arquivos passaram. Migration 0013 revertida para 0012/reaplicada exclusivamente em integração; Alembic não detectou novas operações. As quatro tabelas recusam UPDATE/DELETE; alvo/hash/checklist e última aceitação conferidos por gates SQL/FKs.

Fluxo de criar/salvar, revisão administrativa distinta, publicar e ler versões históricas verificado com conteúdo fictício na transação de rollback. Testes cobrem anonimato/autoria/privacidade, identidades forjadas e tipos estritos, metadados/números do servidor, fonte privada de terceiro por URL coincidente, pedido de mudanças, revisão antiga, cópia sem aceitação, revisor inativo/rebaixado, alteração de referência e conflitos de edição. Definições históricas e base de preços da renda preservadas; consequência/hipótese não gera cálculo. Publicação anterior e busca pública não revelam título/dados de rascunho posterior.

Termos históricos conflitantes são recusados e proveniência malformada gera erro limitado; fontes próprias sem licença ficam explicitamente desconhecidas, sem atribuição inferida. Caso de exemplo marcado após ACCEPT em development bloqueia publicação de contexto real. Revisão independente final por leitura sem achado bloqueante; revisão não comprova conteúdo/causalidade.

O primeiro teste de publicação SQL recusada encontrou o bloqueio esperado, mas a exceção genérica da função era ProgrammingError em vez de erro de integridade. Gates passaram a SQLSTATE 23514; roundtrip de migration/testes confirmaram a correção. Serialização JSON estrita do contrato e resposta antes do commit corrigidas durante integração; erros anteriores ao commit revertem transação.

Demo recebeu somente upgrade após backup; checkpoint preservou um conjunto funcional B2, um conjunto EFGG B3, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados anteriores. Nenhum contexto real foi cadastrado/revisado automaticamente. API/site local conferidos; sem alteração de frontend/motor/coletor/snapshots. Não foram repetidos testes frontend/build/navegador: 197 frontend/build da entrega B3 são evidência anterior. Não houve teste de carga, lançamento, commit/push/deploy. DATA-05C/GRAPH-01/UI-06 continuam pendentes.

DATA-05 permanece Preparado; próximo tópico DATA-05C: interface e primeiro conteúdo com pesquisa e revisão humana efetiva. Grafos/IA ainda não iniciados.


## Operação local após DATA-05B — 2026-10-13

API/site/proxy responderam HTTP 200; OpenAPI registra as rotas de contextos, lista pública vazia e escrita anônima recusada com 401. Nenhum contexto ou publicação real foi criado. PostgreSQL/worker diário retomados com o mesmo operador da coleta anterior e cooldown existente, sem forçar atualização por visita.

A coleta diária retomada terminou PARTIAL: dívida bruta/PIB (`divida-bruta-pib`) falhou por timeout e renda real (`renda-trabalho-real`) por erro de conexão. Não foi determinada a causa externa exata nem alterado o conector nesta fatia. Históricos anteriores conservados; worker continua a política de nova tentativa. Checkpoint posterior à coleta preservou os conjuntos fiscais/publicações/execuções anteriores. Essa pendência operacional não é uma validação adicional de fontes ou uma mudança na API de contextos.


## Interface e primeira pesquisa DATA-05C — 2026-10-13

Leitura em `/contextos`, detalhe/links por revisão e integração no drawer/página do indicador. Painel tem lista própria, editor manual em quatro etapas e fila administrativa. Seleção usa observações já salvas, metadados/termos/períodos congelados e IDs, sem URL fetch, upload, modelo IA ou número gerado. Publicação permanece exclusiva do autor após revisão distinta; edição cria nova revisão e mantém a anterior pública.

Checklist local zera ao aplicar outro registro; conflito preserva a entrada. Links internos exigem confirmação para descartar texto. Referências citadas abrem o trecho e foco por teclado. Descoberta usa última publicação selecionada na mesma consulta (título/principal), sem trocar resultado caso outra versão seja publicada durante a renderização. Fontes privadas/exemplos e revisões históricas mantêm proteção.

Primeira pesquisa: desemprego, participação, informalidade e renda no mesmo trimestre móvel; documentos metodológicos oficiais conferidos e hipóteses só como possibilidades. Rascunho privado rotulado assistido por IA; termos específicos dos dois PDFs e revisão humana efetiva pendentes. O contexto fictício de QA publicado localmente **não encerra** esse aceite. Não houve revisão humana simulada sobre o contexto real. DATA-05C/DATA-05 ficam Preparados, GRAPH-01 e UI-06 futuros. [Pesquisa para revisão](../data/FIRST_CONTEXT_RESEARCH.md).


Fechamento C: 943 backend/232 frontend, lint/types/build/check:docs passaram. Editor/detalhe em quatro larguras/dois temas sem overflow; 13 pares renderizados AA. Fluxo fictício de revisão/publicação/edição verificado, rascunho/histórico separados e recuperação de falha da API conferida. Backup/checkpoint preservam todos os conjuntos/publicações/execuções anteriores; API/ready/site/proxy 200 e worker vivo. Pesquisa real revisão 2 continua sem revisão/publicação: C fica Preparado. [Verificação](../development/VERIFICATION.md).


## Base do grafo GRAPH-01A — 2026-10-14

Fatias do GRAPH-01 existente, sem duplicar épico. A preparação técnica avança enquanto a pesquisa de desemprego continua privada, sem revisão/publicação humana real. DATA-05C/DATA-05 ficam Preparados.

| ID | Estado | Entrega | Critério / evidência |
| --- | --- | --- | --- |
| GRAPH-01A | Concluído | Contrato puro de nós/arestas e diagnóstico | Versões exatas, hash por aresta/conjunto, evidências/contrapontos, correspondência de revisão declarada; duplicatas/conflitos/ciclos/isolados. 93 testes específicos e 795 unitários backend, Ruff/formatação de 154 arquivos e links locais passaram. Sem HTTP/banco/UI/IA/motor. [Contrato](../data/GRAPH_CONTRACT.md). |
| GRAPH-01B | Concluído | Curadoria persistida e publicação autorizada | Migration 0014, referências reais/privacidade, revisão por outro admin, publicação explícita REVIEWED/DISPUTED pelo autor, histórico e coleções de versões públicas. 1.237 backend (107 transporte e 94 integrações novos), Ruff/formatação, Alembic e links passaram. [Contrato](../data/GRAPH_CONTRACT.md). |
| GRAPH-01C | Concluído | Página que ensina e explorador público | `/grafos`, perspectiva 3D em SVG, nós/arestas inspecionáveis, lista equivalente, busca/filtros/zoom, fontes/contrapontos/revisão/histórico. 272 frontend, lint/types/build, quatro larguras/dois temas e fluxo fictício de versões/disputa/retry passaram. Sem seed real. [Requisito e limites](../product/GRAPH_EXPLORER.md). |
| GRAPH-01C1 | Preparado | Refinar mapa com WebGL real e câmera imersiva | Implementação funcional e QA responsivo/teclado entregues; Three.js lazy, layout estável, seleção/mergulho, painel sobreposto, lista/fallback e dicas. 300 frontend/lint/types/build passaram; regressões de gestos/foco e repouso de relação incerta, captura de desenhos reais com invalidação automática e oito combinações responsivas conferidas. Toque/pinça física, leitor de tela e 60 fps representativos pendentes. [Explorador](../product/GRAPH_EXPLORER.md). |
| GRAPH-01D | A fazer | Magnitudes verificadas e eventual composição | Decimal/faixas/unidade/base/condições e vínculo literal/documental confiável, revisão e método próprio para composição/recortes/ciclos/dupla contagem antes de integrar ao motor. Não usar classificação de efeito como número. |
| GRAPH-01E | A fazer | Apoio de IA à curadoria | Interface trocável, verificação por código, contrapontos e lacunas, limites/logs/chave em ambiente; IA cria candidata privada, nunca publica. Depende de B e método de verificação aprovado. |
| GRAPH-01F | A fazer — discussão | Debater análise final da proposta por IA e grafos | Definir objetivos, critérios de viabilidade, evidências/contrapontos, cálculo por ferramentas verificáveis e limites; discutir com o mantenedor antes de implementar. Sem previsão ou percentual de sucesso inventado; depende de método próprio para magnitudes de D e conteúdo real revisado. Ver pauta de retomada no início do backlog. |

GRAPH-01 permanece Preparado; **falta interface privada de curadoria/revisão de nós, relações e coleções**, com filas/ações por autor e outro ADMIN, preservando o contrato de B. A API existe; não orientar a pessoa como se houvesse formulário pronto. Primeiro conteúdo real continua dependente de pesquisa/revisão humanas. [Fluxo atual](../product/GRAPH_EXPLORER.md#como-levar-um-mapa-real-à-publicação--2026-10-25). A não entrega a rede interativa. Primeiro caso FGTS mantém pesquisa/seed real pendentes: “fonte pendente” não vira aresta. Dados atuais, contextos reais, snapshots, fontes privadas e cálculo fiscal não foram alterados. Contratos de quantificação/operação continuam próprios. Não houve revisão humana de conteúdo por executar os testes.

## Curadoria do grafo GRAPH-01B — 2026-10-14

Concluído localmente: resolução confiável de referências, nove tabelas append-only, API de nós/arestas/coleções, autoria, revisão administrativa distinta e publicação explícita com estado revisado/em disputa. Última decisão rejeitada/pedido de alteração bloqueia; nova versão não herda aceite. Coleções preservam relações históricas já públicas e seus metadados; fontes privadas não viram catálogo público por URL coincidente ou reuso. Versões exatas de nós só ficam públicas por testemunha de relação publicada; coleção real recusa testemunha de exemplo inclusive em desenvolvimento.

1.237 testes backend passaram com PostgreSQL exclusivo de integração: 107 novos testes de transporte e 94 integrações de grafos, além da suíte anterior. Ruff/formatação de 162 arquivos e links locais passaram. Migration 0014 revertida para 0013/reaplicada apenas em integração; Alembic sem drift. Demo recebeu somente upgrade após backup; checkpoint preservou integralmente dois contextos/quatro versões/uma revisão/uma publicação anteriores, um conjunto funcional B2, um EFGG B3, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados.

Testes verificam versões/fontes privadas, reuso por terceiro autor, revisão inativa/desatualizada/checklist, disputa explícita, 18 tentativas de UPDATE/DELETE nas nove tabelas, gates de publicação SQL, rollback de criação/edição/revisão/publicação e limites de payload. Listas/históricos usam projeções compactas, detalhes preservam conteúdo completo; snapshots de conjunto até 4 MiB/200 nós/400 relações. Sem benchmark de carga.

Operação local conferida: health/ready/site/proxy e listas de grafos/nós/arestas HTTP 200, escrita anônima 401. Demo sem seed do grafo. Pesquisa real de desemprego preservada em duas versões privadas, zero revisões/publicações; leitura pública 404. PostgreSQL nativo/API/Next.js/worker retomados em loopback, sem inicialização automática com o computador. Última coleta em estado `PARTIAL` na conferência; houve falhas de conexão URLError em fontes externas, mantendo históricos. Não foi determinada a causa externa nem alterado o coletor. Operação supervisionada segue pendente.

GRAPH-01 permanece Preparado: próximo C entrega a página explicativa e rede interativa com inspeção/lista/teclado. FGTS real e revisão humana da pesquisa DATA-05C continuam pendentes. Sem alteração frontend/motor/snapshots, magnitudes, IA, commit/push/deploy. Não repetidos build/QA do navegador: 232 testes frontend/build/QA de DATA-05C são evidência histórica, não conferência nova. [Verificação](../development/VERIFICATION.md).

## Explorador GRAPH-01C — 2026-10-15

Concluído o recorte de interface: `/grafos`, `/grafos/[id]` e `/grafos/[id]/versoes/[revision]`; SVG com coordenadas 3D/projeção em perspectiva, rotação/arraste/teclado, zoom, mover, visão plana e reset. Giro lento apenas sob ação, pausa ao selecionar e respeita movimento reduzido. Busca/filtros, quatro formas/tipos, contadores, legendas e percurso de nós visitados sem composição numérica. Inspector apresenta versões exatas, sentido alegado, prazo, efeito/consenso autorais, fontes/trechos/termos, contrapontos, premissas/lacunas, autoria assistida, revisão/disputa e histórico público. Lista equivalente e guia interativo em três passos.

272 testes frontend passaram, incluindo 34 de geometria/filtros/referências e seis regressões de abertura de versões; lint, TypeScript da compilação e build passaram. Oito combinações de 360/768/1280/1920 px e claro/escuro sem rolagem lateral. 42 pares de texto/superfície em lista, detalhe e guia atenderam AA (mínimo 5,70:1), incluindo os fundos vetoriais dos símbolos. Medição não é auditoria completa de acessibilidade.

API real sem redes publicadas: demonstração local com 18 nós/24 relações, aviso permanente, fontes fictícias não clicáveis e zero revisão humana/publicação inventada. Filtros não criam arestas nem truncam rede; guard de 200 nós/400 ligações, identidades/referências e versões exatas. Layout estável por conteúdo, captions sem sobreposição; medidas de tempo são locais, sem alegar desempenho de produção. Limite sintético 200/400 calculou layout em cerca de 133 ms na primeira execução desta máquina após otimização; não é garantia de FPS/dispositivo.

QA isolado com respostas HTTP fictícias verificou duas versões, título exato, disputa, evidência, revisão/histórico e recuperação da API preservando versão; nenhuma fixture foi salva no banco. Regressão de versão compartilhada válida com catálogo ausente corrigida e testada. Celular sem overflow, controle por teclado e arraste reais conferidos; leitor de tela e emulação de movimento reduzido não foram auditados integralmente. Zero alteração de backend, schema, motor, coletor, contextos reais ou snapshots. 1.237 backend de GRAPH-01B são evidência anterior, não repetidos por esta mudança de frontend.

GRAPH-01 permanece Preparado no escopo ampliado: D/E e pesquisa/curadoria do primeiro mapa real (FGTS) continuam pendentes. DATA-05C mantém a pesquisa de desemprego privada, sem revisão/publicação humana simulada. Nenhum commit/push/deploy. [Verificação](../development/VERIFICATION.md).

## Refinamento GRAPH-01C1 — 2026-10-18

WebGL real com Three.js/OrbitControls substitui a projeção SVG somente no mapa. Câmara com voo de 1.050 ms, vizinhos/pontas destacados, tipo por tokens, consenso por estilo de linha, sentido incerto com `?`, mergulho/expansão, retorno, zoom e modo imersivo. Painel sobreposto mantém título visível ao rolar; conteúdo preserva fontes, contrapontos, revisão e histórico. Lista, teclado, aviso do exemplo, explicação abaixo, rotas e regras públicas continuam preservados.

282 testes frontend, lint e build/TypeScript passaram. QA em 360/768/1280/1920 e dois temas sem overflow; seleção por teclado anuncia conexões e mantém foco; correção de cabeçalho repetida nas oito combinações. Teste isolado exercita 200 nós/500 arestas sem mudar limite 200/400, descarte/recriação e alternativas puras. Peso JS+CSS adiado: 598.026 bytes / 148.729 bytes gzip local, separado de outras páginas; não é delta total da rota ou transferência real.

**Preparado, não encerrado como aceite total:** toque/pinça em aparelho físico, leitor de tela e medição contínua representativa de 60 fps permanecem pendentes. Medições variaram com visibilidade/limitação do navegador de verificação; não tratar uma amostra curta como garantia. Filtros/dados/contratos não foram alterados para satisfazer o teste; nenhuma publicação humana real foi fabricada. D/E e pesquisa FGTS continuam pendentes.

## Continuação de qualidade GRAPH-01C1 — 2026-10-18

Corrigidos Escape sem seleção que retirava foco da busca, renderização contínua desnecessária de relação incerta e reconhecimento de toque que podia aceitar arraste de ida/volta ou sequência de vários dedos. Seleção por teclado no celular aproxima o palco sem rolagem animada concorrente. Helper puro de gesto cobre 12 regressões; amostrador de desenhos reais tem seis testes e invalida capturas interrompidas sem publicar FPS parcial.

300 testes frontend, lint e build/TypeScript passaram. Navegador confirmou foco/fechamento e cabeçalho visível em 360/768/1280/1920, claro/escuro, sem overflow. Teste isolado 200/500 confirmou contador parado em relação incerta após voo, descarte/recriação e invalidação ao redimensionar. A amostra local não encerra desempenho representativo. GRAPH-01C1 continua **Preparado**; toque/pinça física, leitor de tela e 60 fps em dispositivos representativos permanecem pendentes. Sem alteração de backend, contrato 200/400, dados, revisão ou motor. [Verificação](../development/VERIFICATION.md).


## Participação acessível e entrega local — 2026-10-19

UI-06A/B/E concluídos no ambiente local: ideias privadas, compartilhamento explícito de fotografia, cópia atribuída, sugestões, denúncias e moderação administrativa; checklist/promoção transacionais, exclusões de motor/planos e preservação de legado. Modos guiado/manual compartilham campos confirmados, retomada e análise; “não sei” não fabrica dados. Catálogo usa DOC_COMPLETENESS1, com revisão explicitamente não avaliada. Não implica abertura do cadastro público.

UI-06D concluído no recorte de sensibilidade fiscal declarada, distinto de magnitudes causais GRAPH-01D: resultado anual/acumulado pelo motor, faixas escolhidas pelo usuário, limites e recortes validados, sem receita extra pelo texto de financiamento. Ensaio fictício isolado no navegador confirmou valores −100/−60/−20, publicação completa e análise real da API, sem editar publicações úteis.

UI-06C/F Preparados: roteiro público 1.0.0 com oito perguntas, confirmação literal, provedor Gemini trocável, consentimento, chave só no servidor, quotas, logs privados com retenção/apagamento e testes de posições opostas implementados. **Falta chave do mantenedor e avaliação com Gemini real**; assistência permanece desativada por padrão, e o guiado sem IA funciona. Provedores controlados nos testes não comprovam comportamento do modelo externo.

Launchers Windows start/stop/status entregam operação local com validação de identidade, banco existente e flags explícitas de build/migration, sem iniciar coleta automaticamente. Backup/restauração exercitados e upgrade até 0017 preservam legado. F2-03 tem esse recorte local entregue; HTTPS, hospedagem, supervisão, monitoramento e Compose completo continuam pendentes. Nenhum push, deploy, revisão humana simulada ou grafo real publicado. Evidências finais e contagens de checks em [VERIFICATION](../development/VERIFICATION.md); limites atuais em [STATUS](STATUS.md).


Fechamento local em 2026-10-20: início/consulta/encerramento/reinício reais em PowerShell 5.1 conferidos, banco preservado, aplicação e limpeza de logs ativas. Checks finais, QA e limites registrados em [VERIFICATION](../development/VERIFICATION.md). Chave e avaliação Gemini continuam pendentes; não houve lançamento público.


## Docker local completo — 2026-10-20

Recorte Docker de F2-03 concluído localmente: imagens Linux do frontend/API, PostgreSQL persistente, migrations antes da API, prontidão e limpeza de logs. Setup preserva ambientes e gera senha; segredos não entram no frontend/build. Migrations 0001–0017 exercitadas em banco Docker temporário vazio; cópia do banco nativo conferida em 39 tabelas/3.796 registros com hashes UTC, preservando a origem. Login/renovação/logout pelo proxy, leitura e schema sem drift conferidos. Coleta oficial e Gemini não chamados. Hospedagem/HTTPS/monitoramento público continuam pendentes. [Guia](../development/DOCKER_LOCAL.md) · [Verificação](../development/VERIFICATION.md).


## Ajuste da conexão Docker — 2026-10-20

Concluído a pedido do mantenedor: porta publicada 5433, usuário brasil e senha local personalizada no ambiente privado; senha aplicada também ao papel PostgreSQL já existente. DATABASE_URL do backend nativo alinhada à conexão Docker, sem alterar configuração de assistência. Backup antes da troca, autenticação TCP e comparação integral de 39 tabelas/3.805 registros passaram. Compose/guia/exemplo de porta atualizados; aplicação retomada sem recriar o volume.


## Diagnóstico e espera do Gemini — 2026-10-20

Corrigido limite concorrente de 15s: provedor com 30 s por padrão (configurável até 45), proxy com 60 s somente para POST guidance/organize; demais chamadas mantêm 15 s. Erros do guiado aparecem perto do botão; HTTP 503/429/autenticação/modelo recebem mensagens específicas, com status sanitizado no registro privado. Google aceitou chave/modelo (GET 200); uma chamada fictícia real passou em 7,58 s e outras retornaram 503 UNAVAILABLE. Disponibilidade externa não é garantida; sem repetição automática nem preenchimento sem confirmação. 37 testes específicos backend (incl integração em banco exclusivo), 312 frontend, lint e buildDocker passaram. UI-06C/F continuam Preparados quanto à avaliação real sistemática de imparcialidade, sem reclassificar sondagem de conexão como aceite completo.


## Modelo solicitado gemini-2.5-flash — 2026-10-20

GUIDANCE_MODEL alterado para gemini-2.5-flash no ambiente local, exemplo e padrão do backend, a pedido do mantenedor. Imagem reconstruída e API/limpeza recriadas; containers saudáveis. Chamada real com frase fictícia recebeu HTTP404 NOT_FOUND em 0,45s. O modelo consta na listagem de modelos, mas a geração não foi aceita nesta configuração; não declarar a assistência funcionando. Google informa restrição de acesso aos modelos 2.5 para usuários que já os utilizavam, o que é compatível com a falha, sem comprovar o motivo específico da conta. Mantido o modelo solicitado; não houve troca silenciosa, alteração de chave, banco, roteiro ou publicação. Avaliação real sistemática permanece pendente.

Referência: [Gemini 2.5 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash).


## Gemini 3.5 Flash-Lite — 2026-10-20

A pedido do mantenedor, GUIDANCE_MODEL passou para gemini-3.5-flash-lite no ambiente local, exemplo e padrão do backend. API e limpeza recriadas com a nova imagem, mantendo banco e chave. Chamada real direta com frase fictícia passou pela validação literal em 8,64 s. Chamada autenticada pelo proxy Next em /api/v1/guidance/organize também passou: assisted_by_ai=true, texto literal validado e resposta em 7,47 s. Conta fictícia existente usada e sessão encerrada; nenhuma ideia/proposta real publicada ou modificada. Configuração/documentação e backlog atualizados. A disponibilidade externa e a avaliação sistemática de imparcialidade continuam separadas deste teste funcional; UI-06C/F não são encerrados somente por uma chamada bem-sucedida.

## Revisão de escrita do guiado — 2026-10-20

Corrigida a restrição literal que fazia o Gemini repetir a resposta. Prompt 2.0.0 permite revisar ortografia, concordância e clareza preservando ideia/ressalvas; roteiro 1.0.0 e modelo gemini-3.5-flash-lite mantidos. API inclui original_text/rewritten; tela compara original/sugestão, informa ausência de mudança, oferece manter original e só preenche após confirmação. Sem IA e “não sei” preservam comportamento anterior. Verificações de estrutura/tamanho e detalhes protegidos são conservadoras; não provam equivalência semântica.

Verificação: 82 testes específicos de guidance passaram (68 unitários/14 integrações em PostgreSQL temporário exclusivo criado/removido), 315 frontend, ESLint, Ruff check/format dos cinco arquivos backend, documentação e build Docker com TypeScript aprovados. API/site/PostgreSQL saudáveis e limpeza ativa após atualização dos containers. Não foi repetida a suíte inteira do backend nem alterado schema/motor fiscal.

Teste real pelo navegador, conta fictícia existente, consentimento e Gemini: “neste exemplo ficticio quero q o texto fique mais facil de entender” recebeu “Neste exemplo fictício, quero que o texto fique mais fácil de entender.” Original/sugestão e rótulo visíveis; resumo não preenchido antes da confirmação. Confirmação por teclado avançou para pergunta 3 e modo manual preservou o texto revisado e a origem assistida. Nenhuma ideia salva/compartilhada/publicada; sessão encerrada. Comparação medida em 360/768/1280/1920 sem rolagem horizontal; foco visível no tema escuro. Não equivale a auditoria completa de acessibilidade nem avaliação sistemática real de imparcialidade, ainda pendente em UI-06C/F.

## Desenvolvimento assistido da proposta e rastreio privado — 2026-10-22

Concluída a fatia solicitada pelo mantenedor: prompt 3.0.1 desenvolve a intenção informal em objetivo/mecanismo, com sugestões opcionais de desenho/implantação/contrapartidas e lacunas separadas. Substitui a restrição de apenas formatar/corrigir. Contexto enviado inclui trechos textuais confirmados e consentidos; sugestões começam desmarcadas e somente as selecionadas entram após confirmação, com rótulo de ponto a avaliar. Sem IA/“não sei” mantidos; roteiro 1.0.0/modelo configurado preservados. Não equivale a verificação de sentido, análise causal ou fatos comprovados.

Expressões coloquiais de frequência não são tratadas como duração técnica; paráfrases de ausência/condição/incerteza aceitas sem exigir palavras idênticas. Números/URLs/unidades técnicas e reversões diretas selecionadas continuam com verificações conservadoras. Prefixo de sugestão normalizado para não duplicar rótulos. Data de criação atribuída em UTC na reserva de cada chamada, evitando confundir chamadas da mesma transação no acesso à última.

GET /guidance/calls/{id} e /guidance/calls/latest exigem autor autenticado, prazo vigente e ausência de apagamento. A UI consulta por ação explícita, inclusive após falha. Mostra pedido registrado, resposta/uso/duração disponíveis e versões, sem chave/headers; não registra payload privado no console HTTP. A exportação histórica foi limitada à conta explicitamente identificada pelo mantenedor, em pasta privada ignorada pelo Git; nenhum conteúdo real entrou nos documentos/testes públicos.

Compose passou de consultas HTTP periódicas a /ready para checagens TCP. Em 2026-10-22, API/site/PostgreSQL saudáveis, limpeza ativa e zero acessos a /ready na janela de 60 segundos conferida. TCP confirma conexão, não prontidão do banco; endpoint continua disponível para diagnóstico manual. Volume existente preservado; nenhuma alteração de schema/motor/publicações.

Verificação atual: 122 testes guidance (93 unitários/29 integrações em PostgreSQL temporário exclusivo criado/removido), 317 frontend, Ruff/formatação dos arquivos guidance, documentação e builds Docker/TypeScript passaram. Não foi repetida a suíte inteira de domínio. Teste fictício real pelo navegador/Gemini passou em 5.197,94 ms, uso informado de 724 tokens, prompt 3.0.1: frase informal sobre consultar fila recebeu redação com objetivo/mecanismo, duas sugestões e duas lacunas. Registro privado SUCCEEDED consultado na UI. Somente uma opção selecionada entrou no modo manual após confirmação por teclado; a outra sugestão e as perguntas não entraram. Nenhuma ideia salva/compartilhada/publicada, sessão encerrada. Larguras 360/768/1280/1920 sem overflow horizontal; foco visível no tema escuro. Avaliação sistemática real de imparcialidade e auditoria aprofundada de acessibilidade continuam pendentes; UI-06C/F permanecem Preparados.


## Consolidação visual e consentimento — 2026-10-22

| ID | Estado | Entrega | Aceite / limite |
| --- | --- | --- | --- |
| UI-07 | Concluído na implementação local | Auditoria de todas as rotas e consolidação do painel/editor/detalhes públicos | [Inventário antes/depois e decisões](../design/WORKSPACE_AUDIT.md). CSS isolado e componentes atuais; sem alteração de backend/schema/motor. Verificações em [VERIFICATION](../development/VERIFICATION.md). Auditoria aprofundada de acessibilidade e regressão integral de publicações permanecem F2-01; avaliação real sistemática permanece UI-06C/F. |

UI-06B atualizado em vez de criar um segundo épico de criação. Consentimento de envio/retenção é pedido uma vez por criação/sessão, revogável e sem armazenamento persistente no navegador. O aceite não corrige nem suprime rejeições das verificações de saída do Gemini. Nenhum conteúdo real foi enviado ao modelo nesta verificação visual.


## Ajustes de revisão humana e entradas — 2026-10-22

Concluída a fatia solicitada, atualizando UI-06B/C e UI-07 sem duplicar o épico: removidos bloqueios semânticos de revisão; prompt 4.0.0 orienta e a pessoa confirma. Formato/tamanho, consentimento/autoria, limite e logs permanecem. Nova captura rápida de ideia com título/frase, distinta da preparação completa. Navbar agrupada com menus Explorar/Meu espaço, CTA Criar ideia e alternativa mobile. [ADR-044](../architecture/DECISIONS.md) e [verificação](../development/VERIFICATION.md).

Avaliação sistemática real de imparcialidade continua UI-06C/F; revisão humana da saída não significa verificação técnica de mérito ou dados. Requisitos de publicação completa e motor fiscal permanecem inalterados.

## Retomada da coleta e ideia simples — 2026-10-25

F2-04/F2-03 atualizados com diagnóstico e agenda local, mantendo fontes indisponíveis e operação pública pendentes. UI-06B/07 recebem edição simples de ideia, desenvolvimento explícito, explicação no topo dos três catálogos e sugestões opcionais recolhidas. Sem novo épico nem alteração na Home ou nas permissões.

1.469 testes backend e 329 frontend, Ruff/lint/types/build, Compose/imagens passaram. QA isolado verificou criação/edição, compartilhar/recolher, preservar detalhes e guiado na pergunta 3; 32 combinações de quatro larguras/dois temas nas quatro telas sem overflow. Nenhuma chamada Gemini ou revisão humana real foi simulada. Evidências operacionais e limitações em [VERIFICATION](../development/VERIFICATION.md). Próximos: acompanhar fontes, curadoria privada do grafo/conteúdo real e discussão GRAPH-01F; acessibilidade aprofundada e leitura de tela continuam pendentes.
