# Registro de verificação

## Fundação — registro histórico

Data: 2026-10-06. Ambiente local: Windows, Node 22.20.0, Python 3.12.14.

| Verificação | Resultado |
| --- | --- |
| Dependências frontend e package-lock.json | Instaladas; Next.js 16.4.0, React 19.3.0, ESLint 10.12.0 e TypeScript 5.9.3 |
| Dependências backend e uv.lock | Instaladas em .venv; resolução versionada |
| Documentos obrigatórios e links locais | Passaram |
| Frontend lint | Passou sem avisos |
| Frontend typecheck | Passou |
| Frontend build | Passou; página inicial pré-renderizada |
| Backend lint e formatação | Passaram |
| Testes backend | 21 passaram; 1 teste de integração PostgreSQL foi omitido |
| Alembic offline (`upgrade head --sql`) | Configuração executou; ainda não há revisões de domínio |
| Docker Compose (`config --quiet`) | Configuração válida |
| PostgreSQL real / Alembic online / Dockerfile build | Não executados: Docker Desktop não estava em execução |
| GitHub Actions e proteção de branch | Arquivos preparados; não executados/configurados no remoto |

Os testes cobrem contratos públicos de saúde/prontidão, indisponibilidade do banco sem expor detalhes, cálculo anual/acumulado, precisão em centavos, resultado parcial, propostas desativadas, valores fora do período e rejeição de entradas inválidas/duplicadas. Permissões de domínio e publicação versionada ainda não estão implementadas.

Para concluir a verificação com banco, inicie Docker Desktop e execute na raiz `docker compose up -d postgres`. Na pasta backend, execute `uv run alembic upgrade head`, `uv run alembic check` e habilite `RUN_DATABASE_TESTS=1` ao executar pytest. A CI já prepara esse ambiente.

A fundação foi criada localmente na branch main, sem commit ou remoto GitHub. O estado do backlog distingue entregas locais concluídas de configurações que dependem de ambiente ou serviço externo.

## Avanço F1-01 e F1-02 — 2026-10-06

PostgreSQL 18 instalado foi usado em cluster isolado, porta 55432, sem acesso à instalação existente. Migrations 0001/0002/0003 aplicadas; downgrade/upgrade e Alembic sem drift passaram. A suíte passou com 39 testes, incluindo integração real, imutabilidade, ponteiros de versões, hash de senha, refresh rotativo, replay, logout, CSRF, origens, limites e expiração. Docker e CI remota continuam não executados.


## Avanço F1-04/F1-05/F1-06 e backend F1-07

62 testes passaram com PostgreSQL real. Foram verificados cadastro/privacidade de fontes, autoria, propostas v1/v2, snapshots de fontes, remoção de rascunhos, plano fixado em proposta v1 após publicação da v2, resultado por ano/acumulado, avisos de ausência de estimativa/financiamento e impactos fora do horizonte. Execuções completas e seus resultados recusam alteração/exclusão direta. Migrations até 0005 passaram por downgrade base e upgrade sem drift.


## Estado atual — protótipo local da V1

70 testes passaram com PostgreSQL real, incluindo indicadores, idempotência de revisões, administração e auditoria. Migration 0006 revertida/reaplicada e Alembic sem drift. Frontend lint/tipos/build e verificação de documentos passaram. O roteiro completo no navegador e a revisão básica de teclado/tela pequena estão em docs/development/E2E.md.

Importações BCB repetidas preservaram 36 observações de meta Selic e 8 de DBGG/PIB, com revisão máxima 1. Dados da demonstração ficaram em banco separado do banco de integração. O banco nativo existente não foi utilizado.

Ainda pendentes: Docker/Dockerfile, CI/proteção remota, expansão das séries, operação pública, termos e auditoria aprofundada de acessibilidade. A tabela da fundação acima é histórico, não o estado atual dessas funcionalidades.

## Redesign da interface — 2026-10-06

Lint/tipos/build/docs passaram após todos os ajustes. Home reconstruída e sistema aplicado ao restante do frontend; 17 telas / 68 combinações de largura verificadas no navegador. Contraste de texto, teclado, menu, exemplo fiscal e cópias privadas verificados conforme docs/development/E2E.md. Não houve alteração no motor ou schema; resultados da suíte backend acima são da etapa anterior. Docker agora está disponível no computador, mas o BrasilPorTodos segue com os processos e cluster nativo isolado; o Compose completo permanece não validado.

## Dados e páginas internas — 2026-10-07

85 testes backend passaram com PostgreSQL de integração, incluindo preservação de dados após falha externa, lock/cooldown, autorização da coleta, contratos IBGE, base congelada, revisão explícita e exemplos ocultos em produção. Ruff/formatação, Alembic sem drift e frontend lint/tipos/build passaram. Migrations 0007/0008 aplicadas; não foi verificado downgrade dessas duas migrations.

No navegador: 14 telas, quatro larguras (360/768/1280/1920) e dois temas, totalizando 112 combinações sem overflow. Textos conferidos nos dois temas; corrigido contraste transitório do botão de cópia desabilitado. Foram verificados gráficos por período, menu Enter/Escape, filtros abertos no celular/estado vazio, disponibilidade de username, mostrar senha, autosave privado reaberto, vínculo de indicador/base e prévia de plano com centavos, medidas desativadas e anos fora do intervalo. Não equivale a auditoria completa com leitor de tela. Diálogo nativo de compartilhamento não exercitado.

Coleta real de sete séries com SUCCESS; 575 observações preservadas no banco local de demonstração. API pronta e coletor diário local ativo; não é serviço persistente após reiniciar o computador. Supervisor/agendamento, Docker completo e operação pública permanecem pendentes. A Home aprovada foi preservada.


## Base fiscal observada e PIB — 2026-10-09

214 testes backend passaram com PostgreSQL real em banco isolado de integração. A suíte cobre contratos RTN/SIDRA, escala e Decimal, doze meses de ano fechado, reconciliação, quatro trimestres de PIB do mesmo ano, lacunas sem zero, proveniência/coerência dos conjuntos, idempotência e revisões, privacidade de fontes coincidentes, rollback da coleta fiscal e preservação da base anterior. Snapshots/hash de propostas, planos e simulações permanecem congelados após revisões fiscais e do PIB; atualização explícita de rascunho muda somente sua referência.

Ruff/lint e formatação do backend passaram; Alembic não detectou drift. Não foi necessária migration adicional às 0007/0008. ESLint, TypeScript e build do frontend passaram. Documentos obrigatórios e links Markdown locais passaram. Esses resultados são da versão final com o conector PIB, não somente da etapa intermediária do Tesouro.

Coleta real concluída com SUCCESS nas onze séries. RTN trouxe 68 meses em cada uma das três séries (2021–2025 e oito meses de 2026), e PIB trouxe 22 trimestres (2021–2025 e dois de 2026). A base selecionou 2025, com receita líquida de R$ 2.332.555.301.431,48, despesa primária de R$ 2.394.249.610.412,52 e resultado publicado de − R$ 61.694.308.980,99. A soma dos componentes dá − R$ 61.694.308.981,04, diferença anual de − R$ 0,05 após arredondamento mensal, exibida separadamente. A reconciliação mensal foi validada; não se aplicou ajuste artificial. O PIB CNT somado é R$ 12.738.565.620.000,00, com precisão publicada de R$ 10 mil. As proporções são 18,3110%, 18,7953% e −0,4843%, respectivamente. Referências verificadas em [docs/data/FISCAL_BASELINE.md](../data/FISCAL_BASELINE.md); números sujeitos a revisão.

Navegador: Brasil Atual conferido nas larguras 360/768/1280/1920, nos temas claro e escuro, com os detalhes de cálculo e PIB abertos: oito combinações sem rolagem horizontal. Fórmula, diferença de reconciliação, fonte, ano fechado, percentuais e limites de precisão verificados na tela. Os detalhes das séries e a navegação pública de metodologia/fontes foram conferidos. Esta revisão não equivale a auditoria completa de acessibilidade ou de todas as telas.

Prévia local: Next.js sobre build em 3000, FastAPI em 8000, PostgreSQL nativo isolado em 55433. Coletor diário ativo em processo oculto, não instalado como serviço persistente. Bancos de demonstração e integração separados; a instalação PostgreSQL e containers de outros projetos não foram usados. Docker completo e operação pública permanecem pendentes. O motor incremental 1.0.0 não projeta contas futuras nem soma automaticamente impactos ao saldo observado.

Revisão final: resposta truncada do PIB para um ano já disponível rejeita o lote antes de gravar e preserva IDs/hash da base anterior. Anos novos incompletos continuam como observações, sem denominador anual; resposta vazia conserva o cache. Três regressões PostgreSQL passaram e a suíte final totalizou 214 testes. Valores monetários não quebram no meio dos dígitos em 360 px. Gráfico do PIB conferido em 6/12/24 meses de calendário e histórico disponível; a seleção não confunde quantidade de trimestres com meses. Lint, tipos e build repetidos após esses ajustes passaram.

## Brasil Atual e diretório de fontes — 2026-10-10

44 testes frontend passaram: compactação e precisão decimal, sinal tipográfico, taxas em p.p., negativos/zero/mudança de sinal, diferenças muito pequenas, períodos de calendário e revisões; identidade oficial/deduplicação, filtros, paginação integral e estado de consulta por série. ESLint sem avisos, TypeScript e build de todas as rotas passaram. Sem alteração do backend ou de seus cálculos.

As duas rotas foram verificadas nas larguras 360/768/1280/1920 e nos dois temas: 16 combinações sem overflow. Foram medidos 287–289 elementos de texto em Brasil Atual e 139–157 em Fontes, por combinação, sem falhas nos pares renderizados. Contraste transitório dos chips foi corrigido com transição restrita a movimento. Esses testes não substituem auditoria completa com leitor de tela; a preferência por movimento reduzido foi revisada no código.

Drawer fiscal em 360 px preservou o valor exato −R$ 13.584.945.058,57 e a diferença absoluta R$ 24,4 bi. Um ano mensal vai de set/25 a ago/26; um ano de PIB trimestral vai de 3º tri/25 a 2º tri/26. Gráfico respondeu a Home, seta e clique, mostrando valores/datas distintos. Escape fechou o modal, restaurou o foco ao card e liberou a rolagem. A memória anual mostrou os componentes exatos e a diferença de reconciliação de −R$ 0,05, sem alargar a página.

Filtros: busca inexistente em Brasil Atual apresentou zero/estado vazio; limpar restaurou onze indicadores. Selecionar IBGE apresentou quatro fontes; busca sem acento por “inflacao” encontrou as duas variáveis distintas do IPCA. Metadados históricos abriram por teclado em 360 px sem overflow.

A lista de produção apresenta nove fontes oficiais distintas de três instituições, a partir de doze registros oficiais históricos; o exemplo fictício foi excluído. IDs originais não foram alterados. Hashes da Home, estilos globais/tokens, IndicatorCard, IndicatorChart, PageHero/PageKit, BaselinePanel e Metodologia coincidem com os anteriores ao redesign.

## Seções de tema e PNAD ampliada — 2026-10-10

Backend final: **234 testes passaram** com PostgreSQL isolado, incluindo 15 novos unitários e cinco de integração da renda: idempotência/nova base, histórico antigo reconsultado, âncora alterada durante leitura, mês anterior omitido e rollback após falha de sublote. Ruff/formatação passaram; Alembic sem alterações pendentes. Sem migration ou biblioteca adicional.

Frontend: **76 testes passaram**, com 29 testes da grade e três de comparação anual PNAD adicionados aos 44 anteriores. ESLint, TypeScript e build final passaram.

Navegador: **56 combinações** — seis quantidades (1/2/3/4/5/7) mais catálogo completo, em 360/768/1280/1920 e temas claro/escuro. Filtros reais produziram essas quantidades, sem dados sintéticos. Todas as linhas preencheram a largura, com alturas iguais por linha, sem overflow; 9.699 verificações de texto renderizado sem falhas nos pares de contraste medidos. Não substitui auditoria completa com leitor de tela.

Chip de emprego reúne quatro cards incluindo destacado. Busca em grade única. Drawer de renda em 360 px mostrou R$ 3.777,00, preços do trimestre encerrado em ago/26, definição/abrangência/fonte; um ano set/25–ago/26. Escape restaurou foco ao card e liberou rolagem. Estado das fontes abriu por Enter em 360 px, sem overflow/falhas de contraste. Recarregar preservou 14 indicadores. Âncora de emprego no celular terminou com título em 280,7 px, abaixo da barra encerrada em 264,6 px.

Coleta real: três novas séries SUCCESS, 35 observações cada, referência jun–ago/2026, valores 3.777 reais, 37,5% e 62,2%. Renda com preços do trimestre mais recente, proveniência e revisão; [docs/data/EMPLOYMENT_INDICATORS.md](../data/EMPLOYMENT_INDICATORS.md). Execução geral PARTIAL: IBC-Br e dívida líquida indisponíveis por HTTP; cache preservado e estados públicos corretos. Worker diário local ativo; não é serviço persistente de produção.

Fontes confirmou 12 identidades oficiais distintas, três instituições (IBGE com sete), incluindo tabela/variável e consulta dos novos registros. Hashes de Fontes (rota/componente/estilos), Home, IndicatorCard legado, tokens e estilos globais coincidiram com os anteriores à tarefa. Destaques conservam configuração e visual; somente o texto contextual do desemprego aponta para dados agora disponíveis.

## Organização documental e guias de agentes — 2026-10-10

22 documentos realocados em pastas por domínio; links relativos e referências atualizados. Índice/estado/publicação e seis perfis de especialidade criados, com instruções locais e bloco gerado do Next.js preservado. Check de documentos/guias obrigatórios e destinos Markdown locais passou. Os 76 testes frontend existentes passaram novamente e agora fazem parte da CI configurada; CI remota ainda não executada.

Sem mudanças de UI, API, banco ou regra fiscal. Não foi repetida a suíte completa backend por esta reorganização; a evidência de 234 testes pertence à entrega funcional anterior. A única referência alterada no código Python é o caminho da metodologia no docstring. Arquivos locais sensíveis e ambientes permaneceram ignorados. Revisão de padrões comuns de segredos é limitada; não equivale a auditoria completa de segurança.

Git sem commit/remoto na verificação desta entrega; nenhum push, publicação externa ou mudança de configuração GitHub. REPO-01 concluído localmente; F0-04/F0-06 e itens de lançamento mantêm pendências reais.

## 2026-10-10 — Metadados e compatibilidade fiscal (DATA-06A)

- Backend: 285 testes passaram com PostgreSQL de integração isolado. Incluem ausência/zero estimado, recortes incompatíveis, ano futuro, base malformada, receita/despesa negativas, preços constantes/ano-base, desativação/horizonte, roundtrip/cópias, snapshot/hash e preservação de execuções anteriores. Ruff completo e formatação passaram (108 arquivos).
- Migration 0009: downgrade para 0008 e upgrade head exclusivamente em integração; Alembic check sem operações novas. Demo recebeu apenas upgrade após backup; checkpoint de colunas históricas preservou duas versões publicadas de proposta, uma de plano, dois impactos, três execuções concluídas e seis resultados anuais. Verificado novamente após a coleta.
- Frontend: 93 testes passaram (17 novos de metadados/cópia/ausência/mistura). Lint, tipos e build passaram; após ajuste de texto identificado na revisão fiscal, lint/tipos/build novamente passaram. Não foi repetida suíte pura por mudança somente textual.
- Runtime: API ready e seis rotas HTTP 200: home, Brasil Atual, Fontes, Metodologia, proposta e plano publicados fictícios preexistentes. HTML servido confirmou ausência de metadados no legado e aviso de compatibilidade não avaliada no resultado antigo. Isso é conferência HTTP, não teste visual nem teste de autosave no navegador.
- Conferência visual dos novos controles em 360/768/1280/1920, temas e teclado **não executada**: ferramenta recusou vincular a aba local por política de URL/protocolo. Nenhuma tentativa de contornar o bloqueio. DATA-06A permanece Preparado até essa conferência; evidências antigas de UI não são reaproveitadas como teste destes controles.
- Ambiente local retomado: frontend build em loopback 3000, API em loopback 8000, cluster isolado 55433 e coletor diário. Coleta atual parcial: 13 sucessos e renda real falhando na origem, conservando o histórico. PID/logs/backup/checkpoints ignorados pelo Git.
- Revisão fiscal independente de código/contrato: interpretação do sinal de soma heterogênea corrigida; nenhuma outra falha material encontrada. Avaliação adicional 1.0.0 separada do motor aritmético 1.0.0; nenhuma combinação de base histórica e impactos ou cenário futuro implementado. Links/documentos verificados localmente; CI remota não executada.

## 2026-10-10 — Biblioteca isolada de cenário fiscal (DATA-06B1)

- 87 testes específicos de cenário passaram; regressão unitária backend completa: 282 testes passaram. Ruff/formatação completos e check de documentação passaram. Os 285 testes completos e 93 frontend do estágio anterior permanecem evidência anterior; integrações PostgreSQL/frontend não foram repetidas por esta biblioteca sem alterações de API/schema/UI.
- Cenário futuro com entradas anuais declaradas e recorte restrito; identidades com todos os tipos de impacto, precisão/limites, anos/IDs/URLs/valores inválidos, ausência/divergência, NOT_ESTIMATED, confirmação de exclusão, componentes negativos/overflow, desativação/horizonte e ausência de efeitos cobertos. Entradas/referência não alteradas, métodos separados.
- Revisão fiscal independente do contrato/código. Somente scenario.py/test_fiscal_scenario.py e documentação alterados nesta fatia; sem consultas oficiais adicionais, migrations, publicação de conteúdo, reinícios ou mudança de UX. Não habilita cenários na API/site: DATA-06B2 pendente.
- Feedback do editor registrado como requisito futuro: manual/conversa guiada por IA, sem exigir ideia pronta e com revisão comum. Implementação explicitamente adiada. DATA-06A visual continua pendente; nenhuma aprovação do usuário foi inferida pelo feedback de produto.


## Cenário opcional nos planos — 2026-10-10

426 testes backend com PostgreSQL de integração e 116 testes frontend passaram; Ruff/formatação (114 arquivos), ESLint, TypeScript e build final passaram. Migration 0010 revertida/reaplicada no banco de integração e Alembic sem drift; links locais verificados.

32 combinações em 360/768/1280/1920 e temas claro/escuro: editor de cenário, resultado público com premissas abertas, campos de metadados da proposta e resultado legado, sem overflow da página. Tabelas têm rolagem interna no celular. Salvamento/reabertura, configuração incompleta, bloqueio sem revisão, combinação confirmada, revogação por composição, cópia sem confirmação e leitura anônima conferidos. Ano-base obrigatório em preços constantes e removido em nominal; foco por teclado visível. Nenhum erro de console na conferência final. Auditoria aprofundada de acessibilidade permanece F2-01.

Migration 0010 roundtrip apenas no banco de integração, Alembic sem drift; backup demo anterior e atualização aditiva. Checkpoint pós-QA preservou as três versões de proposta, uma versão de plano, três impactos, três execuções e seis resultados anuais preexistentes. Novos exemplos fictícios restritos a development, sem alterações em conteúdo anterior. Confirmação/salvamento/reabertura, erro de cenário incompleto, combinação bloqueada sem revisão, revisão válida e composição alterada, publicação e leitura pública conferidos. Nenhum segredo em logs/documentos.

## Composição primária DATA-07A — 2026-10-11

457 testes backend passaram com PostgreSQL de integração; 134 testes frontend, ESLint, TypeScript e build final passaram. Ruff e formatação de 118 arquivos passaram; Alembic sem drift, sem nova migration. Oito combinações de 360/768/1280/1920 nos temas claro/escuro, composição e detalhes abertos, sem overflow da página; tabela exata com rolagem interna no celular. Expansão por Enter, foco visível de 3px e ausência de erros/avisos de console conferidos. Auditoria aprofundada de acessibilidade permanece F2-01.

Coleta real de 2025 importou 120 observações auxiliares. Nova coleta registrada confirmou idempotência: 120 registros, máxima revisão 1, composição AVAILABLE. Receita e ponte líquida reconciliaram com diferença 0; despesa com diferença anual R$ 0,01, preservada. A coleta completa terminou SUCCESS nos 14 indicadores e no grupo de composição; renda real voltou a ter sucesso. Acrescentar composição preservou exatamente o hash/contexto corrente, e checkpoint final preservou quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados anteriores. Backup local anterior conservado; nenhum commit/push/deploy.

Revisão independente corrigiu a exclusão indevida das séries auxiliares do catálogo administrativo: público mantém os 14 indicadores, administração permite gerir as dez séries adicionais. Testes cobrem valores assinados/escala/limites, lacunas, revisão mais recente, âncoras revisadas, reconciliação, privacidade de fonte, idempotência, rollback por falha intermediária/truncamento/indisponibilidade e preservação de snapshots. Allowlist e fingerprint do trio original mantidos; parser compartilhado privado, métodos de simulação inalterados.

## Juros e nominal DATA-07B1 — 2026-10-11

503 testes backend passaram com PostgreSQL de integração; 157 testes frontend, ESLint, TypeScript e build final passaram. Ruff e formatação de 123 arquivos passaram; Alembic sem drift, sem nova migration. Oito combinações de 360/768/1280/1920 nos temas claro/escuro com painel de juros e método abertos, sem overflow da página; teclado e foco visível conferidos. Auditoria aprofundada permanece F2-01.

Coleta real de 2025 importou 36 observações auxiliares de primário abaixo da linha, juros e nominal. Repetição preservou os mesmos registros, máxima revisão 1; AVAILABLE, doze meses e residual anual R$ 0,00. Valores da API conferidos em 36 pares da planilha oficial. Acrescentar o conjunto preservou exatamente o contexto corrente. Coleta completa registrada terminou SUCCESS nos 14 indicadores, composição e juros; worker diário local restaurado e aguardando a janela.

Checkpoint posterior preservou quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados anteriores. Backup anterior conservado; motor, fingerprints legados e snapshots intactos. Nenhum commit/push/deploy. Revisão independente por leitura sem achado bloqueante.

78 medições de contraste do painel (39 textos/elementos por tema) passaram nos pares verificados; foco visível de 3px e console sem erros/avisos conferidos.

Navegador encontrou formato NUMERIC de seis casas com zeros adicionais: helper corrigido para aceitar zeros subcentavo sem arredondar frações reais; teste de contrato real e casos assinados adicionados. Interface mostra competência, sinais e método abaixo da linha, sem chamar juros de pagamentos orçamentários. Pesquisa de funções leu arquivo oficial completo (155.738 linhas, 37 colunas), preservou naturezas/99 distintos e residual anual +R$ 0,01 do resumo. Pipeline funcional ainda não implementado.


## Gasto federal por função DATA-07B2 — 2026-10-11

609 testes backend passaram com PostgreSQL de integração, incluindo rollback da primeira coleta, revisões, imutabilidade por SQL e privacidade. 177 testes frontend, ESLint, TypeScript e build passaram. Ruff e formatação de 131 arquivos passaram; migration 0011 revertida/reaplicada somente em integração, Alembic sem drift. Demo recebeu apenas upgrade após backup.

Coleta oficial registrada terminou SUCCESS e importou uma revisão íntegra de 2025: 155.738 registros, 37 colunas, doze meses, 753 grupos mensais e 64 combinações anuais de natureza/função; 29 funções e dois rótulos sem classificação distintos. Os 2.259 valores mensais conferiram com a agregação independente da pesquisa. Pago + RAP = total em centavos; resumo publicado do subconjunto conciliou os doze meses e preservou diferença anual +R$ 0,01. Nova gravação do mesmo payload preservou ID, revisão 1 e referência corrente; nenhuma observação artificial foi adicionada ao catálogo.

Oito combinações de 360/768/1280/1920 nos temas claro/escuro com painel e método abertos passaram sem overflow da página. Tabela exata tem rolagem interna no celular; nove combinações de natureza/estágio em 360 px, sinais, grupos 99, teclado/foco de 3px e console sem erros/avisos conferidos. 46 pares visíveis de contraste passaram (23 por tema, mínimo 8,83:1); cabeçalho de 1×1 px recortado visualmente e mantido para leitores de tela excluído da medição visual. Fonte oficial mostrou licença ODbL e consulta atualizada, sem criar indicadores fictícios. Auditoria aprofundada permanece F2-01.

Checkpoint preservou quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados. API/site/worker diário local retomados. Não há atualização por visita, integração ao motor ou implantação pública; DATA-07B3 e operação supervisionada continuam pendentes.

Na verificação real, o primeiro processamento foi recusado pelo scanner de um metadado ignorado UTF-16 da própria planilha; suporte estrito de varredura UTF-16 foi acrescentado somente aos XML ignorados, sem execução, mantendo bloqueio de DTD/entidades e planilhas ativas UTF-8. Testes de regressão e arquivo completo passaram após o reparo. Última coleta registrada verificada conforme evidência desta entrega; sem alteração nos snapshots anteriores.


## Governo Geral por esfera DATA-07B3 — 2026-10-12

719 testes backend passaram com PostgreSQL exclusivo de integração; Ruff e formatação de 138 arquivos passaram. Migration 0012 foi revertida/reaplicada somente em integração, com 18 testes focados, e Alembic não detectou novas operações. Demo recebeu apenas upgrade após backup. 197 testes frontend passaram; ESLint, TypeScript e build final passaram novamente após o ajuste textual e do destino do link da planilha.

Coleta real EFGG de 2025 produziu revisão 1 AVAILABLE: oito grupos por oito métricas, 64 valores conferidos com a extração independente da pesquisa da mesma planilha. O SHA-256 do arquivo também conferiu; repetir a gravação preservou ID, revisão e data de coleta do conjunto. A tabela 3.1 confere oito agregados do Governo Geral dentro do próprio arquivo, sem alegação de fonte externa independente. Diferenças das identidades/partições preservadas, máximo absoluto R$ 0,01 para tolerância R$ 0,03. Valores originais em milhões, normalização a centavos por célula agregada, sinais, termos e metadados de cobertura preservados.

Coleta registrada completa terminou SUCCESS, incluindo `general-government` com 64 observações, sem adicionar indicadores artificiais. Inserir apenas EFGG preservou a referência corrente. A coleta diária completa atualizou a data de referência da Selic de 11/10 para 12/10/2026; comparação dos contextos isolou essa mudança e sua proveniência, sem alteração fiscal. Essa atualização legítima muda o contexto corrente, mas não reescreve publicações. Checkpoint posterior preservou integralmente um conjunto funcional B2, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções concluídas e doze resultados.

Oito combinações de 360/768/1280/1920 e claro/escuro, com painel, método e células originais abertos, passaram sem rolagem horizontal da página. Tabelas têm rolagem interna. Quatro recortes em 360 px, valores/sinais/cobertura, expansão por Enter e foco de 3px conferidos. 38 pares de contraste passaram (19 por tema, mínimo 10,18:1); console sem erros/avisos. Após o ajuste do link, a página foi conferida novamente: recurso resolvido da revisão, fonte oficial em /fontes, ausência de overflow/erros. Auditoria aprofundada permanece F2-01.

Dois comportamentos HTTP reais exigiram reparo: redirecionamento oficial revisado agora é tratado manualmente sem seguir URLs arbitrárias; recurso thot recusa HEAD, então a verificação usa duas leituras GET limitadas, conferindo URL/cabeçalhos/hash e metadados da publicação antes/depois. Regressões e coleta completa passaram. Não há consulta por visita, alteração do motor/base congelada ou coletor SICONFI/NFSP habilitado.

API/site/worker diário local retomados; worker aguarda janela. Código/documentos continuam locais, sem commit/push/deploy. Licença desta EFGG são os termos do Tesouro Transparente com atribuição, não ODbL inferida. Comunicação do produto à STN permanece rastreada em PUBLICATION; operação persistente e lançamento público continuam pendentes.


## Contextos/evidências DATA-05A — 2026-10-13

77 testes específicos e regressão de 626 unitários backend passaram; Ruff completo e formatação de 141 arquivos passaram. Contrato isolado 1.0.0: incompletude, órfãos/duplicatas, observação/contrapartida, alternativas, consequência observada/projetada, URL sem credenciais/controles, datas UTC, valores exatos/zero, tipos estritos, coleções imutáveis, roundtrip, hash, edição/cópia/revisão/checklist e pedido de mudanças. Fixtures explicitamente fictícias; nenhuma análise real recebeu revisão por executar testes.

Revisão paralela do contrato: correspondência de revisão não é autorização nem causalidade; identidade/visibilidade/referências exigem futura camada confiável. Nenhuma chamada HTTP, leitura/escrita de banco, migration, coletor, API, motor ou interface alterados. Integração PostgreSQL, frontend/build/navegador e operação não foram repetidos; seus resultados anteriores não são testes desta fatia. Backlog/estado/roadmap/contrato e links locais atualizados. Nenhum commit/push/deploy.


## Contextos persistidos DATA-05B — 2026-10-13

918 testes backend passaram com PostgreSQL exclusivo de integração, incluindo 46 integrações de contextos, 51 novos testes de entrada e 25 testes do resolvedor. Ruff completo e formatação de 150 arquivos passaram. Migration 0013 revertida para 0012/reaplicada exclusivamente em integração; Alembic não detectou novas operações. As quatro tabelas recusam UPDATE/DELETE; alvo/hash/checklist e última aceitação conferidos por gates SQL/FKs.

Fluxo de criar/salvar, revisão administrativa distinta, publicar e ler versões históricas verificado com conteúdo fictício na transação de rollback. Testes cobrem anonimato/autoria/privacidade, identidades forjadas e tipos estritos, metadados/números do servidor, fonte privada de terceiro por URL coincidente, pedido de mudanças, revisão antiga, cópia sem aceitação, revisor inativo/rebaixado, alteração de referência e conflitos de edição. Definições históricas e base de preços da renda preservadas; consequência/hipótese não gera cálculo. Publicação anterior e busca pública não revelam título/dados de rascunho posterior.

Termos históricos conflitantes são recusados e proveniência malformada gera erro limitado; fontes próprias sem licença ficam explicitamente desconhecidas, sem atribuição inferida. Caso de exemplo marcado após ACCEPT em development bloqueia publicação de contexto real. Revisão independente final por leitura sem achado bloqueante; revisão não comprova conteúdo/causalidade.

O primeiro teste de publicação SQL recusada encontrou o bloqueio esperado, mas a exceção genérica da função era ProgrammingError em vez de erro de integridade. Gates passaram a SQLSTATE 23514; roundtrip de migration/testes confirmaram a correção. Serialização JSON estrita do contrato e resposta antes do commit corrigidas durante integração; erros anteriores ao commit revertem transação.

Demo recebeu somente upgrade após backup; checkpoint preservou um conjunto funcional B2, um conjunto EFGG B3, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados anteriores. Nenhum contexto real foi cadastrado/revisado automaticamente. API/site local conferidos; sem alteração de frontend/motor/coletor/snapshots. Não foram repetidos testes frontend/build/navegador: 197 frontend/build da entrega B3 são evidência anterior. Não houve teste de carga, lançamento, commit/push/deploy. DATA-05C/GRAPH-01/UI-06 continuam pendentes.


## Operação local após DATA-05B — 2026-10-13

API/site/proxy responderam HTTP 200; OpenAPI registra as rotas de contextos, lista pública vazia e escrita anônima recusada com 401. Nenhum contexto ou publicação real foi criado. PostgreSQL/worker diário retomados com o mesmo operador da coleta anterior e cooldown existente, sem forçar atualização por visita.

A coleta diária retomada terminou PARTIAL: dívida bruta/PIB (`divida-bruta-pib`) falhou por timeout e renda real (`renda-trabalho-real`) por erro de conexão. Não foi determinada a causa externa exata nem alterado o conector nesta fatia. Históricos anteriores conservados; worker continua a política de nova tentativa. Checkpoint posterior à coleta preservou os conjuntos fiscais/publicações/execuções anteriores. Essa pendência operacional não é uma validação adicional de fontes ou uma mudança na API de contextos.


## DATA-05C — interface entregue; conteúdo real aguardando revisão, 2026-10-13

- Backend: 943 testes passaram com PostgreSQL exclusivo de integração, incluindo 25 de descoberta (última publicação/título/principal, seleção estável sob publicação concorrente, referências históricas/períodos/termos/exemplos/privacidade). Ruff e formatação de 151 arquivos passaram. Alembic sem drift; nenhuma migration nova ou downgrade do demo nesta entrega.
- Frontend: 232 testes passaram, incluindo 32 de helpers de contexto e três sobre estado de revisão/navegação. Lint sem avisos, TypeScript e build final Next.js 16.4 passaram. Rotas públicas de contextos/histórico e painel/editor/fila compiladas. Links Markdown locais passaram.
- Revisão paralela encontrou e corrigiu troca de resultado filtrado durante publicação concorrente, checklist local reaproveitado, perda de texto em links SPA e estado de carregamento ao limpar indicador. QA encontrou título ausente no preview do revisor e trecho de evidência fechado após clicar; corrigidos e conferidos após rebuild.
- Editor e leitura pública medidos em 360/768/1280/1920, claro/escuro: nenhuma largura documental excedeu viewport; campos 16px. Treze pares renderizados de texto na prévia/revisão dos dois temas passaram AA, mínimo 6,13:1. Não é auditoria completa de leitor de tela; captura de viewport em troca de largura pode mostrar recorte transitório, por isso as medidas DOM foram verificadas separadamente.
- Navegador: revisão distinta e publicação pelo autor usando **somente exemplo fictício**; edição posterior criou revisão 2 privada/bloqueada, mantendo publicação 1. Links/trechos abrem e recebem foco; drawer de indicador lista publicação pertinente, Escape fecha e restaura foco. Confirmação de descarte via diálogo conserva texto e Escape restaura o link. Seletor vazio encerra loading; estado vazio não revela título de rascunho; versão real privada recebe resposta pública genérica. Loading, falha controlada da API e retentativa após retomada conferidos.
- Primeira pesquisa real salva em revisão 2 privada, com quatro observações do mesmo trimestre móvel, PDFs oficiais, hipóteses alternativas e lacunas; zero revisões humanas e zero publicações reais. Texto assistido por IA rotulado. Os termos específicos dos PDFs permanecem sem identificação explícita; precisam de conferência humana antes da publicação. [Pesquisa](../data/FIRST_CONTEXT_RESEARCH.md). Aceitação automatizada de QA fictício não atende esse critério.
- Backup demo anterior e checkpoint posterior preservaram integralmente um conjunto funcional B2, um EFGG B3, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados. PostgreSQL e coletor não foram parados. API/frontend retomados somente pelos processos identificados em loopback; health/ready/site/proxy 200, escrita anônima 401 e contexto real privado 404 em leitura pública. Coleta mais recente continua PARTIAL; falhas anteriores não foram ocultadas nem houve nova consulta oficial forçada.

Não houve mudança em coletores/motor fiscal/snapshots, benchmark de concorrência/carga, CI remota, commit, push ou deploy. DATA-05C/DATA-05 permanecem Preparados até revisão humana efetiva e publicação do contexto real pelo autor. GRAPH-01/UI-06/IA permanecem futuros.


## GRAPH-01A — 2026-10-14

Contrato puro `app/modules/graphs/graph.py` e testes fictícios: 93 testes específicos e 795 unitários backend passaram. Ruff e formatação de 154 arquivos e documentos/links locais passaram. Cobertura: referências/órfãos/sem fonte, tipos estritos/imutabilidade, magnitude recusada, hashes e edições/cópias, revisão e datas/autoria, contrapontos, snapshots exatos e topologia (duplicatas, oposições, ciclos/limites/isolados).

Nenhuma autenticação ou publicação real é feita pela biblioteca. Não se verificou documento remoto, criou seed real do FGTS ou registrou revisão do contexto real de desemprego. Nenhum código do frontend, API, coletor, registro de modelos, migration, banco, motor ou snapshot anterior foi alterado. Por esse escopo isolado, PostgreSQL/Alembic, build e navegador não foram repetidos; 943 backend com integração/232 frontend e QA de 2026-10-13 continuam evidência histórica. Sem benchmark/carga, CI remota, commit/push/deploy.

GRAPH-01A concluído, GRAPH-01 Preparado e B/C/D/E A fazer. DATA-05C continua Preparado com revisão humana efetiva pendente. [Contrato](../data/GRAPH_CONTRACT.md).

## GRAPH-01B — persistência e curadoria autorizada, 2026-10-14

1.237 testes backend passaram com PostgreSQL exclusivo de integração: 107 novos testes de transporte e 94 integrações de grafos, além da suíte anterior. Ruff/formatação de 162 arquivos e links locais passaram. Migration 0014 revertida para 0013/reaplicada apenas em integração; Alembic sem drift. Demo recebeu somente upgrade após backup; checkpoint preservou integralmente dois contextos/quatro versões/uma revisão/uma publicação anteriores, um conjunto funcional B2, um EFGG B3, quatro versões publicadas de propostas, duas de planos, cinco impactos, seis execuções e doze resultados.

- Autor ativo cria/salva/publica; outro administrador ativo revisa. Testes de acesso, campos gerenciados, IDs/versões exatas, fonte privada própria/alheia/URL coincidente e reuso de publicação histórica por terceiro autor.
- Última aceitação ou disputa completa autoriza somente o estado explícito correspondente; rejeição/pedido de alteração, revisor desativado/rebaixado e conteúdo/referências alterados bloqueiam. Publicação anterior conserva revisão e fontes congeladas.
- Nove tabelas recusam UPDATE/DELETE (18 casos). SQL impede publicação com alvo/hash/autor/estado incorretos e coleção real com nó testemunhado apenas por aresta exemplo. Arrays de seleção são conferidos pelos gates, não FKs convencionais. Serviço aplica validação Pydantic/hash/referências de catálogo; não se alega que SQL sozinho valida toda semântica.
- Falha de montagem de resposta reverte criação, edição, revisão e duas publicações. Limites de bytes bloqueiam mutação sem linhas parciais e não alteram leitura histórica. Listas e históricos projetam metadados/títulos; detalhes completos preservam fotografia. Conjunto consulta metadados de revisões/publicações em um JOIN, sem N+1 por relação.

Operação local conferida: health/ready/site/proxy e listas de grafos/nós/arestas HTTP 200, escrita anônima 401. Demo sem seed do grafo. Pesquisa real de desemprego preservada em duas versões privadas, zero revisões/publicações; leitura pública 404. PostgreSQL nativo/API/Next.js/worker retomados em loopback, sem inicialização automática com o computador. Última coleta em estado `PARTIAL` na conferência; houve falhas de conexão URLError em fontes externas, mantendo históricos. Não foi determinada a causa externa nem alterado o coletor. Operação supervisionada segue pendente.

Não houve seed real de FGTS, revisão humana simulada do contexto real, efeito numérico, IA, alteração em coletores/motor/frontend ou snapshots existentes. Não repetidos frontend/build/navegador: 232 testes frontend e QA DATA-05C permanecem evidência histórica. Sem benchmark de carga/concorrência, CI remota, commit/push/deploy. GRAPH-01B concluído; GRAPH-01 e DATA-05C Preparados; C é próximo desenvolvimento.

## GRAPH-01C — explorador em perspectiva, 2026-10-15

272 testes frontend passaram, incluindo 34 de geometria/filtros/referências e seis regressões de abertura de versões; lint, TypeScript da compilação e build passaram. Oito combinações de 360/768/1280/1920 px e claro/escuro sem rolagem lateral. 42 pares de texto/superfície em lista, detalhe e guia atenderam AA (mínimo 5,70:1), incluindo os fundos vetoriais dos símbolos. Medição não é auditoria completa de acessibilidade.

- Navegador local: arraste alterou a rotação, setas giraram, zoom mudou projeção, 2D/reset funcionaram, nós abriram ligações e inspector, lista abriu relação por Enter com foco no cabeçalho. Celular 360 px mostrou detalhe legível e versão longa sem overflow; busca sem resultados, limpar e catálogo vazio conferidos.
- Oito capturas de larguras/temas confirmaram 18 nós/24 relações na demonstração e `scrollWidth == clientWidth`. Rótulos são distribuídos sem sobrepor; conteúdo completo permanece em foco/inspector/lista. Formas e textos acompanham cores. Animações respeitam a condição de movimento reduzido no código/CSS; não houve emulação completa dessa preferência nem auditoria com leitor de tela.
- Ambiente temporário separado, com a mesma compilação e respostas HTTP fictícias, verificou publicação em disputa, evidência/trecho/fonte, auditoria/justificativa, histórico da aresta e conjunto com versões 1/2, compartilhamento de versão 1 e interrupção/retomada da API. Revisão fictícia não foi persistida nem apresentada como curadoria real. O teste encontrou uma falha de inicialização de versão válida sem catálogo; corrigida com seis regressões. Título/revisão do seletor agora são os da versão aberta. Cancelamento protege consultas de coleção/histórico contra respostas atrasadas.
- Geometria é Number exclusivamente visual, layout determinístico e limitado, SVG sem WebGL/pacote adicional. Teste 200 nós/400 ligações conserva limites e finitude; execução local do layout cerca de 133 ms primeira vez, 30–76 ms aquecida, sem benchmark de frames em aparelhos reais. A demonstração preservou distância inicial mínima ~36,7 px a 850×550; no celular há zoom e lista com controles maiores.
- API real pública vazia permaneceu vazia. Site/API/ready disponíveis em loopback; nenhum schema/backend, dado real, snapshot ou motor alterado. Checkpoint preserva as publicações/contextos/conjuntos/simulações anteriores. Worker não retomado nesta entrega; coleta anterior parcial não foi ocultada.

272 frontend e build/lint não são a suíte backend: 1.237 backend de 2026-10-14 continuam evidência histórica. Sem CI remota, revisão humana real, seed FGTS, coeficientes/propagação, IA, commit/push/deploy. GRAPH-01C concluído; primeiro conteúdo real e D/E permanecem pendentes.

## 2026-10-18 — GRAPH-01C1, renderização WebGL

- 282 testes frontend passaram, incluindo dez novos testes de layout/cache/vizinhança/enquadramento/capacidades. Lint e build com TypeScript passaram. Testes backend não repetidos: sem mudança no backend/schema/motor.
- Three.js 0.186.1/OrbitControls importados apenas pelo módulo dinâmico sem SSR. Manifesto lazy de grafos contém JS 594.092 bytes e CSS 3.934 bytes; gzip local 147.530 + 1.199 = 148.729 bytes. Manifesto lazy da Home vazio. Medição não representa delta total da rota, Brotli ou transferência real.
- Oito combinações de largura 360/768/1280/1920 e claro/escuro conferidas no navegador com WebGL ativo. Nenhum overflow horizontal. Inspector aberto conserva cabeçalho visível; rolagem da página no desktop revelou corte inicial, corrigido e repetido nas oito combinações. Teclado Enter e região viva conferidos. Capturas e medições locais são evidências da entrega, sem publicação externa.
- Teste isolado persistente em [frontend/tests/webgl](../../frontend/tests/webgl/README.md): renderizador atual, 200 nós/500 relações inteiramente sintéticos, sem API/banco. Montagem, seleção, aresta incerta, mergulho/expansão, descarte/recriação exercitados; canvas é removido no descarte. Não equivale a auditoria de memória GPU.
- Cadência de animação variou com janela/aba em segundo plano no ambiente de verificação; uma amostra curta de 80,16 fps foi observada, e outras sofreram limitação. Não se declara 60 fps validado em hardware representativo. Teste real de toque/pinça e leitor de tela continuam pendentes; regras puras de fallback foram testadas, sem afirmar emulação de preferências do sistema.
- `npm audit --omit=dev`: zero vulnerabilidades reportadas. Auditoria incluindo desenvolvimento reportou cinco entradas na cadeia existente ESLint/Next/fast-glob/braces, fora da dependência Three; atualização forçada não executada. Conferência de imutabilidade preservou conjuntos fiscais, contextos, publicações e execuções anteriores.

Escopo limitado ao mapa, interação e documentação/dependência necessárias. Nenhuma alteração de guia explicativo, conteúdo demonstrativo, API, validação/revisão ou cálculo fiscal. Nenhum commit/push/deploy. GRAPH-01C1 Preparado enquanto o aceite de qualidade restante não for conferido.

Fechamento de interação: clique direto em nó/aresta, duplo clique/expansão, navegação por vizinho, troca Rede/Lista, pausa preservada após filtro e saída nativa/CSS por Escape conferidos. A saída retorna o mapa a position: relative e remove a seleção. Abertura móvel com mapa parcialmente visível mantém o cabeçalho dentro da tela e aproxima o palco da área útil. Console sem erros na conferência final. Site/API/ready em loopback, catálogo real com zero mapas; servidor de estresse encerrado e preferência temporária de viewport restaurada.

## 2026-10-18 — GRAPH-01C1, continuação de interação e medição

- 300 testes frontend passaram: 282 anteriores, 12 novos de reconhecimento de toque/arraste/multitouch/cancelamento e seis do amostrador de chamadas de desenho. Lint e build/TypeScript passaram após o último ajuste de teclado móvel. Sem dependência nova.
- Revisão paralela somente leitura identificou Escape global retirando foco da busca sem seleção e relação incerta mantendo RAF/desenho sem partículas. Correções verificadas no navegador: Escape conserva o campo; relação incerta sintética manteve exatamente 1.917 chamadas acumuladas em duas leituras após a câmera assentar, separadas por pelo menos 1,8 s. Seleção e interação retomam desenho normalmente.
- O helper de gesto acompanha todos os IDs ativos e o maior deslocamento observado: arraste de ida/volta, pinça, terceiro dedo, liberação em ambas as ordens e cancelamento não geram seleção. São regressões sintéticas unitárias, **não** validação de pinça em celular físico.
- Nova captura isolada observa somente chamadas efetivas a `renderer.render`, com 30 desenhos de aquecimento e 240 intervalos; sem RAF paralelo usado como proxy. Uma execução local completou em 1.454,50 ms, média de 165,01 submissões/s, p95 de 6,10 ms, máximo de 6,20 ms. Mede submissão do navegador, não conclusão GPU/apresentação ou hardware representativo. Não confirma aceite de 60 fps. Nova captura foi invalidada por redimensionamento após 35 intervalos, sem estatística parcial. Descarte deixou zero canvas; recriação voltou a um, sem erro de console.
- QA final em 360×900, 768×1024, 1280×900 e 1920×1080, claro/escuro: WebGL ativo, sem overflow, cabeçalho do painel visível, foco no nó após Enter e foco preservado na busca após fechar e pressionar Escape novamente. Teste revelou rolagem suave concorrente à focagem no celular; seleção por teclado agora usa aproximação imediata e as oito combinações foram repetidas com sucesso.
- Lazy JS 594.911 bytes / 147.813 gzip e CSS 3.934 / 1.199 gzip; total 598.845 / **149.012 gzip local**. Home com manifesto lazy vazio. Valores anteriores permanecem como histórico da compilação anterior.

Mudanças limitadas aos componentes de grafos, helper/testes de interação, teste isolado e documentação. Backend/schema/motor/coletores/dados reais não foram alterados; nenhuma revisão/publicação humana criada. Toque/pinça física, leitor de tela completo e desempenho contínuo representativo seguem pendentes. GRAPH-01C1 permanece Preparado; D/E e primeiro mapa real continuam separados.

Fechamento desta continuação: site e API ready responderam 200, catálogo público permaneceu com zero grafos, servidor temporário de teste foi encerrado e viewport restaurado. Console do explorador sem erros na conferência final. Worker de coleta não iniciado; nenhuma coleta forçada, commit/push/deploy ou publicação real.


## 2026-10-19/20 — Participação acessível e fechamento local

- 1.314 testes backend passaram com PostgreSQL em banco exclusivo de integração; Alembic até 0017 e verificação sem drift. Ruff e formatação de 169 arquivos passaram. O helper operacional Python também passou no padrão do backend. Não foram executados downgrade em dados úteis nem chamadas Gemini reais.
- 310 testes frontend, ESLint sem avisos e build com TypeScript de todas as rotas passaram após integrar o editor, análise, moderação e correção do endereço de resolver sugestões. Documentos obrigatórios e links Markdown locais passaram.
- IDEIA privada salva somente com título/frase; alternância manual/guiado, confirmação antes de preencher, “não sei” preservando resposta anterior, retomada, compartilhamento explícito, leitura anônima, duplicação com atribuição e proteção do rascunho conferidos no navegador. Sugestão aceita registra a decisão sem vincular automaticamente a fonte. Moderação administrativa conferida com denúncia e conteúdo congelado, justificativa e retorno de foco.
- Em banco QA separado e com referências/conteúdo explicitamente fictícios: checklist 10/10, promoção, publicação, campos de beneficiários/perdas/riscos preservados no editor de nova versão, inclusão da versão 1 no plano, simulação e publicação do plano com saldo −R$ 60,00. Nenhuma dessas publicações foi inserida no banco útil. Proposta pública com sensibilidade aberta mostrou −R$ 60,00 nos três cenários padrão; ao ajustar custos/ganhos, −R$ 100,00/−R$ 60,00/−R$ 20,00. Divergência de precisão entre percentuais da tela e multiplicadores HTTP foi corrigida e recebeu regressões unitária e HTTP. Ranking histórico usa a versão publicada exata, não o sinalizador atual do rascunho.
- Cinco telas/estados em 360×900, 768×1024, 1280×900 e 1920×1080, claro/escuro: 40 combinações sem rolagem horizontal, sobreposição da navegação ou controles cortados. Conferência por DOM e navegador; não é auditoria completa com leitor de tela, aparelho físico ou desempenho representativo. Console sem erros na conferência final da área pública de ideias.
- Integração Gemini opcional: oito perguntas fixas públicas, interface trocável, consentimento explícito, limites serializados por usuário, respostas literais e confirmação, falha sem perda da entrada, logs privados com versão e expiração. Testes incluem posições opostas, truncamento/alteração recusados, sigilo, falhas/quota e apagamento durante resposta pendente. Sem chave: guiado literal funciona e não alega assistência por modelo. UI-06C/F continuam Preparados até configuração e avaliação real.
- Limpeza de logs expirados: cinco testes unitários e um PostgreSQL, sem chamar provedor. Launcher inicia `app.guidance_cleanup --watch` após API pronta; manutenção a cada 300 segundos enquanto processo/computador/banco ativos. Apagamento solicitado mantém metadados de quota e não restaura prompt/resposta de chamada pendente. Backups têm ciclo próprio.
- Banco útil recebeu upgrade após backup de 527.826 bytes e restauração verificada em banco temporário exclusivo. Comparação de IDs/hash preservou todos os registros anteriores, incluindo oito propostas/nove versões, cinco planos/cinco versões, seis simulações/doze resultados, 27 indicadores/1.719 valores e contextos/fontes existentes. Sem seed real de grafo, revisão humana fabricada ou alteração de conteúdo anterior.
- Operação real em PowerShell 5.1: início, status, novo início idempotente, encerramento e reinício passaram. Correção de aspas substituiu Python inline por `scripts/local-runtime.py`; falhas de configuração não imprimem segredos. PostgreSQL manteve sua identidade durante o ciclo; launcher encerra somente processos registrados e conferidos. Site 3000, API 8000, prontidão SQL e manutenção de logs ativos em loopback; estado final `ready=true`. Coletor de fontes não iniciado, nenhuma coleta forçada. Área pública de ideias conferida no endereço final.

Backlog, roadmap, escopo, metodologia, ADR-040 e instruções de operação sincronizados. UI-06A/B/E concluídos localmente; D concluído no recorte de sensibilidade declarada. Permanecem separados: chave/avaliação Gemini, pesquisa e revisão humana do primeiro mapa real, magnitudes causais, auditorias aprofundadas e lançamento público/Compose completo. Não houve commit, push ou deploy. Não foi criado roteiro de apresentação.


## 2026-10-20 — Compose completo local

- Docker Engine 29.9.1/Compose 5.6.0 disponíveis. Build Linux das duas imagens passou; backend Python 3.12/uv.lock e frontend Node22/package-lock. Next16.4 standalone ativado somente no build Docker, TypeScript e rotas compilados. Imagem frontend de aproximadamente 428 MB descompactados, usuário node/UID1000; backend appuser. Contexto frontend inicial aproximadamente 1,16 MB, sem ambientes privados/dados/caches. Arquivos .env/.env.local/.local ausentes da imagem frontend.
- Compose validado com `config --quiet`; comando real `docker compose up -d --build --wait` passou, inclusive repetição com imagens em cache. PostgreSQL, API e frontend saudáveis; migrate encerrou0; limpeza em execução e log confirmou zero registros expirados removidos. Banco publica somente loopback55434, API8000 e site3000. Windows recusou bind5432; porta configurável resolveu sem encerrar serviço de outro projeto.
- Migrations 0001–0017 aplicadas em banco Docker temporário vazio, depois removido; schema do banco usado sem drift. Backup da instalação nativa restaurado somente no destino Docker vazio, em transação. Comparação de IDs/conteúdo de todas as 39 tabelas/3.796 registros passou com hashes JSONB e fuso UTC igual nos dois lados; verificação inicial sem normalizar fuso detectava apenas representações distintas dos timestamps. Origem conservada. As cópias não sincronizam alterações posteriores; login/logout de teste geraram apenas suas mutações normais de sessão no Docker.
- Navegador no endereço final: Home, Brasil Atual com 14 indicadores e referência fiscal, login de conta fictícia existente, recarregamento com renovação/cookies preservados e logout retirando acesso ao painel. Console sem erros na conferência final. Nenhuma conta nova ou publicação criada para esse teste; nenhuma coleta oficial ou chamada Gemini realizada.
- Processos nativos gerenciados encerrados pelo launcher, PostgreSQL nativo preservado. Setup Docker executado novamente conservou hashes dos três ambientes existentes. Parser PowerShell do setup, lint, 310 testes frontend e documentos/links passaram. Backend de domínio não alterado: 1.314 testes do fechamento anterior permanecem evidência desse código, sem alegar nova execução completa nesta entrega de infraestrutura.
- Guia DOCKER_LOCAL, README, arquitetura, escopo, roadmap, estado, backlog e changelog atualizados. Root .env gera senha Docker; backend/.env mantém JWT/Gemini e DATABASE_URL nativa, sobrescrita somente no Compose. Segredos não são argumentos de build ou expostos no frontend. Coletor continua operação separada autorizada.

Esse aceite encerra o recorte Docker local, não toda a operação pública de F2-03. Política de backups automáticos, HTTPS, monitoramento de hospedagem, termos e gates de conteúdo/IA continuam separados. Não houve push, publicação de imagem ou deploy externo.


## 2026-10-20 — Porta PostgreSQL 5433 e credencial local

Porta alterada de 55434 para 5433, com usuário brasil e senha definida pelo mantenedor. Role PostgreSQL alterada no banco existente via conexão local, sem senha em argumentos de processo ou em arquivos públicos. Backup prévio, volume preservado, ambientes privados e fallback/exemplo/guia atualizados. DATABASE_URL nativa alinhada ao banco Docker. Autenticação TCP com a nova senha passou; hashes UTC de todas as 39 tabelas/3.805 registros iguais ao checkpoint anterior. Compose retomado e documentos/links conferidos. Nenhum código de domínio, migration ou dependência alterado; suíte de domínio não repetida por mudança de configuração.


## 2026-10-20 — Assistência real e falhas de provedor

Metadados Gemini consultados no host e no container com 200 e modelo reconhecido; credenciais não exibidas. Uma geração com “Ideia de teste.” passou pela validação literal em 7,58 s. Testes posteriores com outra frase fictícia receberam503UNAVAILABLE do Google; nenhuma proposta real do usuário foi reenviada nesses diagnósticos. O502 de15s relatado originalmente não preservava a causa específica, portanto não é atribuído com certeza à mesma indisponibilidade observada depois.

Prazo padrão do provedor ampliado15→30s; proxy específico60s acima do teto45s suportado, preservando15s nas outras rotas. Erro do guiado movido para perto da ação e classificação de HTTP 503/429/401/403/404 sem corpo bruto do provedor nos logs. Confirmação obrigatória e texto preservado mantidos. 37 testes backend de guidance passaram com PostgreSQL em banco temporário exclusivo criado/removido para a regressão; 312 frontend, lint e builds Docker/TypeScript passaram. Não foi repetida toda a suíte de domínio nem alterado schema, cálculo ou propostas. Chave configurada localmente não equivale a disponibilidade do serviço ou avaliação completa de imparcialidade.

Conferência final do navegador: HTTP 503 recebeu a mensagem específica próxima ao botão, preservando a frase fictícia. A alternativa sem IA mostrou Entendi isso e os botões de confirmação/correção sem preencher o título ou salvar publicação. Sessão fictícia encerrada; nenhuma proposta real foi alterada.


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


## UI-07 — Painel, criação e leitura pública — 2026-10-22

Inventário de todas as rotas apresentado antes da implementação, registrado em [WORKSPACE_AUDIT](../design/WORKSPACE_AUDIT.md). Auditoria de código inclui rotas dinâmicas e fallback; não equivale a exercitar todas as versões possíveis no navegador. Home, exploradores Brasil/Fontes/Grafos, autenticação/cadastro e catálogo de propostas preservados. Componentes do painel/editor/leitura usam tokens existentes e CSS Modules locais; sem dependência nova, backend, schema ou motor alterados.

### Checks

- 320 testes frontend passaram (317 anteriores + 3 de consentimento: escopo da criação, transferência ao salvar e revogação). 35 testes existentes de contexto também conferidos separadamente pelo agente responsável. ESLint completo sem avisos, TypeScript e build de produção Docker passaram; links da documentação verificados. Não foi repetida a suíte backend por ausência de alteração nessa camada.
- Docker frontend atualizado, API/site/PostgreSQL saudáveis e limpeza ativa; volume preservado. Migrações existentes executadas pelo serviço de inicialização, sem nova migration.
- No navegador: aceite exibido antes da primeira pergunta; após aceitar, perguntas seguintes usam o indicador IA ativa e não repetem a autorização. Troca para manual preservou o título confirmado. Revogação por “mudar” levou a “Guiado sem IA”; entrada sem IA não apresenta botão de chamada ao Gemini. Logout voltou ao gate de autenticação. Transferência do aceite ao ID salvo coberta por teste unitário; não foi criado novo registro para esse teste visual.
- Duas chamadas fictícias reais ao Gemini retornaram texto desenvolvido, duas sugestões e duas lacunas cada. Original permaneceu visível. Uma opção selecionada entrou somente após confirmação por Enter; a outra e as perguntas não entraram. Nenhuma proposta real foi enviada. Nenhuma ideia foi salva, compartilhada, promovida ou publicada nesta verificação.
- Retorno da IA medido nas oito combinações de 360/768/1280/1920 e claro/escuro, sem overflow horizontal. Escolha, manual, painel, listas privadas (ideias/propostas/planos/fontes/contextos), criação de contexto/plano, catálogos públicos (ideias/planos/contextos), metodologia e transparência também conferidos nos quatro tamanhos e dois temas. Contexto fictício existente verificado em edição/leitura e link permanente. Menus/abas têm rolagem interna no celular. A versão final da barra de confirmação foi conferida fixa em 360 px, com foco visível e sem overflow.
- Amostragem dos textos/controles visíveis da escolha e do gate administrativo, nos temas, teve contraste mínimo medido de 6,69:1. Foco/Enter, labels, progresso e avisos de carregamento conferidos. Não constitui auditoria WCAG completa nem teste de leitor de tela/toque físico.

### Limites e decisões

Os catálogos de propostas/planos/ideias estavam vazios para a conta de QA: estados vazios foram verificados, sem fabricar novas publicações para preencher a tela. Detalhes desses conteúdos e editor da proposta completa passaram por revisão do código/TypeScript; regressão visual de todas as combinações de parcelas/versões segue F2-01. Administração, revisão restrita e moderação foram verificadas pelo gate; conteúdo administrativo completo exige QA com papel autorizado. Não houve promoção de papel nem simulação de revisão humana real.

Checklist só reflete revisão salva no servidor. Sem cronologia disponível, a UI diz “salvo no servidor”; retomada é a última atualizada entre 20 ideias consultadas; filtros locais dizem “nesta página”. Ações sem suporte de domínio não foram criadas artificialmente. Carregamento do roteiro, conferência literal e chamada real ao modelo têm mensagens distintas.

Consentimento único por criação/sessão é apenas uma mudança de experiência. Verificações de saída da IA continuam independentes; não se afirma que toda paráfrase passará nem que essas verificações provem fidelidade semântica. Avaliação sistemática real de imparcialidade permanece UI-06C/F; acessibilidade aprofundada/regressão integral permanecem F2-01. Sessão fictícia encerrada, tema inicial restaurado e dimensões temporárias removidas. Sem commit, push, deploy ou lançamento público.


## ADR-044 — Revisão humana, entrada rápida e navbar — 2026-10-22

Removidas as rejeições semânticas de comparação entre original e sugestão (palavras, números/URLs/unidades, negações, ressalvas e expansão proporcional). Prompt 4.0.0 orienta o modelo; aceitação é humana. Seguem somente contrato técnico e limites dos campos: listas/textos válidos, teto fixo de 5.000 caracteres do texto principal e 200 no título, limites de sugestões/lacunas e caracteres de controle. Erro técnico usa GUIDANCE_INVALID_OUTPUT/INVALID_RESPONSE_FORMAT; não afirma insegurança política ou equivalência de sentido. Auth, consentimento, quotas, registros privados e dados fiscais não mudaram.

127 testes guidance passaram em PostgreSQL temporário exclusivo criado, migrado e removido (96 unitários + 31 integrações). Após substituir o caso por um exemplo explicitamente fictício, 96 unitários passaram novamente; Ruff/check/format dos quatro arquivos alterados passou. Integrações cobrem retorno para revisão humana, erro estrutural, consentimento, limites, autenticação, logs/expiração/apagamento e nenhuma ideia criada automaticamente pela IA. 320 frontend, ESLint, TypeScript, documentação e builds Docker de API/site passaram. Sem migration nova; volume/publicações existentes preservados. Não foi repetida toda a suíte backend de domínio.

No navegador, conta fictícia existente: nova entrada rápida solicitou apenas título/frase, salvou um rascunho privado rotulado QA e abriu o guiado. As duas primeiras respostas já digitadas não foram repetidas; após aceite único, abriu pergunta 3 de 8 do roteiro 1.0.0. Chamada fictícia ao Gemini retornou paráfrase de “8 hrs” como “oito horas por dia”, duas sugestões e uma lacuna, sem rejeição semântica. Rastreio privado confirmou SUCCEEDED, prompt 4.0.0/modelo gemini-3.5-flash-lite, 1.557,15 ms e 835 tokens informados. Campo problema permaneceu vazio antes da confirmação e apareceu assistido por IA somente depois de Enter no botão de confirmar. Conteúdo não foi compartilhado, promovido ou publicado; nenhum texto real foi enviado ao modelo para QA.

Navbar agrupa Brasil/Fontes/Conexões em Explorar, mantém Ideias/Propostas/Planos e move painel/sair para Meu espaço. Entrada rápida e navbar medidas em 360/768/1280/1920 nos dois temas sem overflow horizontal. Drawer móvel aberto conferido em 360, com rolagem própria; Escape fecha e restaura foco. Rotas de ideias/preparação completa e estados ativos permanecem distintos. Confirmação humana não certifica correção da sugestão; avaliação sistemática de imparcialidade e auditoria completa de acessibilidade seguem pendentes nos itens existentes.


Complemento do mesmo QA: o botão normal “Salvar ideia privada” retornou à lista Minhas ideias com o novo registro marcado Privada; foram criados somente dois rascunhos fictícios nessa conta de teste, sem compartilhamento/publicação. Catálogo Ideias continuou sem exibir esses rascunhos; catálogo Propostas e seu CTA abriram a preparação completa, com link de volta à captura rápida. Entrada rápida e preparação completa somaram 16 combinações medidas de quatro larguras/dois temas, sem overflow. As verificações do retorno da IA não reapareceram como bloqueio de conteúdo; formato/tamanho seguem o contrato técnico documentado.


## Auditoria anterior aos commits locais — 2026-10-23

1.410 testes backend passaram em PostgreSQL temporário exclusivo, removido ao fim; migrations até head. 320 testes frontend, Ruff (188 arquivos), ESLint, TypeScript e documentos/links passaram. **Build não aprovado:** compilou/gerou rotas, mas terminou com código 1 e alerta de segurança. `npm audit --omit=dev` confirmou uma dependência de produção com severidade crítica, Next.js 16.4.0; atualização e repetição dos checks pendentes. Nenhuma dependência foi atualizada nesta auditoria.

Docker Desktop/Compose existentes iniciados, volume preservado. Site e três catálogos públicos de grafos responderam 200, `total: 0`. Navegador renderizou exemplo fictício WebGL de 18 nós/24 relações; seleção por teclado abriu detalhe e conexões. Larguras 360/768/1280/1920: documento/área útil 345/345, 753/753, 1265/1265, 1905/1905; um canvas ativo. Não foi reproduzida falha do renderer. Imagens Docker existentes usadas nessa inspeção; não houve reconstrução/publicação. Sem curadoria real, coleta forçada ou chamada Gemini.

Última coleta salva consultada: 14/10/2026, PARTIAL, seis falhas IBGE, históricos anteriores preservados. Pesquisa/revisão real, avaliação sistemática de IA, dependência de segurança, acessibilidade aprofundada e operação pública permanecem pendentes. Revisão de candidatos ao Git por segredos conhecidos/padrões comuns e caminhos pessoais sem ocorrências; não é auditoria de segurança completa. [Relatório](../project/REPOSITORY_AUDIT.md).


## Auditoria de autenticação/autorização — 2026-10-25

1.447 testes backend passaram em PostgreSQL temporário exclusivo (37 novas regressões), sem alteração do banco útil. Ruff/check e formatação de 190 arquivos passaram. 320 frontend, ESLint, TypeScript e build nativo passaram. Next.js/eslint-config-next 16.4.3, sharp 0.35.5/librsvg 2.63.2 e patch Zod 4.6.7 conferidos; auditoria npm completa e de produção zeradas. pip-audit conferiu 45 distribuições locais e 35 da imagem Linux, sem alertas conhecidos ou pacotes ignorados. Não inclui pacotes do sistema operacional.

Rodada focal de 48 testes após o ajuste de bloqueio do login passou; três casos adicionais de sigilo de configuração constam na suíte final completa. Experimento separado em banco temporário: login/suspensão concorrentes, bloqueio observado e JWT/refresh antigos recusados com 401 após reativar. Observador de estatísticas do experimento foi corrigido para não reutilizar snapshot; rodada final passou. Não equivale a teste de carga.

Imagens Docker reconstruídas, containers locais iniciados e Next 16.4.3 e flags hide_input_in_errors conferidos no runtime. Site/health/ready 200, admin anônimo 401, login fictício inválido via proxy 401, origem não permitida 403 e no-store. Sem nova conta real, coleta oficial, chamada IA ou mudanças de permissões de produto/schema/motor. Banco local com role SQL superuser e TLS off foi explicitado como limite de desenvolvimento; não houve alteração desses privilégios ou promessa de criptografia de volume.

Relatório, controles de hash/criptografia/tokens/roles e pendências públicas em [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md). F2-02 Preparado: auditoria local entregue, operação pública ainda depende de proxy/limites, privilégios mínimos no banco, proteção/recuperação de administradores, limpeza de sessões e demais gates. Documentos/links e diff passaram. Sem push, lançamento, pentest externo ou QA visual integral nesta fatia.
