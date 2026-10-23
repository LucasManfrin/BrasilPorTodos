# Changelog

## Auditoria e preparação do histórico local — 2026-10-23

- Limpeza restrita de card/CSS sem uso e onze marcadores vazios; gráfico usado preservado.
- STATUS atual separado do histórico; documentação de módulos, IA e publicação corrigida.
- Relatório com diagnóstico dos grafos, coleta parcial e alerta crítico de dependência; pendências preservadas no backlog.
- Histórico Git local iniciado após revisão; sem remoto, push ou lançamento público.

## Não lançado — 2026-10-06

- Monorepo, visão, escopo, arquitetura, decisões, metodologia, guias e licença MIT.
- Modelos SQLAlchemy e migrations 0001–0006, com proteção de publicações, execuções, revisões e auditoria.
- Contas/sessões, hash Argon2id, JWT em memória, refresh/CSRF rotativos, revogação e rate limit persistente.
- Fontes por URL, rascunhos privados, propostas versionadas, financiamento explícito e histórico público.
- Planos com versões fixadas, ordem/ativação de medidas e resultados fiscais persistidos por ano/acumulado.
- Catálogos públicos com busca, filtros e paginação; painel com cadastro, editores e publicação.
- Brasil Atual com metadados, fontes, histórico/revisões e importador manual restrito às séries BCB 432 e 13762, com termos registrados.
- Administração de indicadores/observações/usuários e arquivamento com autoria/data/motivo.
- Metodologia/transparência públicas, CI/templates e roteiro de validação ponta a ponta.

O lançamento público depende de remoto/canais, operação, termos para contribuições e expansão/revisão do catálogo. Estado detalhado em [docs/project/BACKLOG.md](docs/project/BACKLOG.md).

## Redesign — 2026-10-06

- Home com motivação eleitoral, escolhas e compensações, simulador interativo fictício, bento e exemplos sinalizados.
- Tokens das cores nacionais, temas claro/escuro, fontes next/font e componentes compartilhados em todas as telas.
- Navbar fixa, menu de celular/teclado, CTA, rodapé e estados de loading/erro/404.
- Cards com autor, área, período, saldo incremental e avisos; cálculo visual em centavos exatos.
- Duplicação autenticada de propostas/planos como rascunhos privados com atribuição e versões preservadas.
- Apoios/comentários sinalizados como futuros; canais públicos ainda dependem de configuração.

## 2026-10-07 — Brasil de referência e páginas internas

- Sete séries oficiais BCB/IBGE, histórico, revisão idempotente e coletor diário com estado por fonte.
- Base contextual congelada por versão e vinculada ao snapshot/hash da simulação; atualização explícita de rascunhos e exemplos ocultos em produção.
- Páginas internas com gráficos, filtros, fontes compactas, auth dividida, editor em etapas/autosave e balanço de plano ao vivo. Home aprovada preservada.
- Roteiro de pesquisa fiscal/social com separação entre dado, hipótese causal e consequência. Base nacional calculável e IA seguem pendentes.

## 2026-10-09 — Base fiscal observada

- Três séries mensais RTN e PIB nominal trimestral SIDRA, ampliando o coletor diário para onze séries oficiais, com origem, escala, precisão e termos rastreáveis.
- Referência pública do Governo Central no último ano fechado completo: receita líquida, despesa primária, resultado publicado, cálculo dos componentes e reconciliação. Percentuais somente com quatro trimestres do PIB nacional do mesmo ano.
- Coletas fiscal/PIB atômicas e independentes, preservação em falhas e correção de colisões de fontes privadas por URL.
- Base fiscal e PIB preservados nas novas versões e nos snapshots/hash; atualizações explícitas de rascunho e contratos legados mantidos. Motor incremental inalterado.
- Painel fiscal em Brasil Atual e nas referências preservadas, com fontes e limitações. Documentação fiscal, ADR-024 e backlog DATA-04/06/07 atualizados; 214 testes backend e verificações frontend passaram.

- Proteção contra respostas truncadas de um PIB anual já completo; seleção dos gráficos por meses de calendário e montantes legíveis no celular. Suíte final: 214 testes.

## 2026-10-10 — Exploração de dados, PNAD e colaboração

- Brasil Atual/Fontes com números compactos, comparações neutras, fontes agrupadas e detalhes acessíveis; seções completas com grade equilibrada, faixa compacta e offsets de rolagem.
- Renda real habitual, informalidade e participação PNAD: 14 séries oficiais no catálogo, revisões/proveniência e histórico de renda com base de preços coerente.
- Documentação agrupada por domínio com índice, estado atual e preparação de publicação; guias especializados em .agents e instruções locais para colaboradores/agentes.
- CI frontend inclui testes existentes de exploração. Organização preserva interface, API, schema e cálculo; GitHub e lançamento público permanecem etapas próprias.

## 2026-10-10 — Metadados e compatibilidade fiscal histórica

- Parcelas de impacto com ente, caixa/competência, preços/ano-base, componente e cobertura anual; validação API/banco e preservação em rascunhos/cópias/versões.
- Avaliação de recortes contra a referência congelada do plano, com motivos/cobertura/versão no snapshot e hash das novas execuções; resultados antigos preservados sem avaliação retroativa.
- Editores, prévias e leitura pública informam metadados ausentes/misturados e limites do somatório; motor aritmético permanece 1.0.0.
- Migration 0009 aditiva e contrato DATA-06A documentado. Cenários futuros e soma base/impactos continuam pendentes em DATA-06.

## 2026-10-10 — Contrato e biblioteca de cenário futuro declarado

- Método puro separado para premissas anuais explícitas de receita/despesa do Governo Central, com recorte restrito, Decimal e dataclasses imutáveis.
- Compatibilidade contra cenário, dupla contagem declarada e bloqueio global em ausência/divergência/estimativa desconhecida ou componentes inválidos; nenhuma projeção/indexação automática.
- DATA-06B1 concluído; ligação com planos/API/persistência/interface permanece em DATA-06B2. Motor atual e publicações preservados.
- Preferência por criação manual ou guiada por IA registrada em UI-06; reformulação adiada pelo mantenedor, sem mudança do editor.


## Cenário fiscal opcional — 2026-10-10

- Premissas anuais declaradas nos planos, com revisão humana vinculada a contexto/período/composição e nova revisão após alterações ou cópia.
- Migration 0010 aditiva, autorização, snapshots/hash e publicação imutável; cenário e resultado conjunto opcionais sem reescrever legado.
- Editor de plano e leitura pública distinguem observado, cenário, impactos e comparação bloqueada; ausência nunca vira zero.
- 426 testes backend com PostgreSQL de integração e 116 testes frontend passaram; Ruff/formatação (114 arquivos), ESLint, TypeScript e build final passaram. Migration 0010 revertida/reaplicada no banco de integração e Alembic sem drift; links locais verificados. 32 combinações em 360/768/1280/1920 e temas claro/escuro: editor de cenário, resultado público com premissas abertas, campos de metadados da proposta e resultado legado, sem overflow da página. Tabelas têm rolagem interna no celular. Salvamento/reabertura, configuração incompleta, bloqueio sem revisão, combinação confirmada, revogação por composição, cópia sem confirmação e leitura anônima conferidos. Ano-base obrigatório em preços constantes e removido em nominal; foco por teclado visível. Nenhum erro de console na conferência final. Auditoria aprofundada de acessibilidade permanece F2-01.
- Criação manual/conversacional por IA segue requisito futuro adiado; grafos e lançamento público mantêm dependências.

## 2026-10-11 — Composição primária do Governo Central

- Receita total/transferências e quatro grupos diretos de receita/despesa RTN, no mesmo ano fechado da referência fiscal.
- Dez séries auxiliares, coleta atômica independente, revisões e reconciliação com valores assinados; catálogo público mantém os 14 indicadores.
- Painel expansível em Brasil Atual com valores compactos/exatos, proporções de despesa, fonte/licença/coleta e limitações.
- API separada e comparação de âncoras impedem misturar atualizações; contextos/snapshots/métodos e resultados anteriores preservados.
- DATA-07A concluído; gastos por função, juros e outros entes permanecem DATA-07B. UI-06 ainda planejado. [Verificação](docs/development/VERIFICATION.md).

## 2026-10-11 — Juros e resultado nominal observados

- Três séries RTN apuradas pelo BCB, primário abaixo da linha + juros assinados = nominal; regime misto e fonte explícitos.
- Coleta auxiliar atômica e endpoint público separados; 36 observações reais de 2025, idempotentes, sem alterar contexto/snapshots/motor.
- Painel expansível em Brasil Atual, valores compactos/exatos, critérios, atribuição, datas e reconciliação. Leitura de centavos normaliza zeros adicionais do NUMERIC sem arredondar dados.
- DATA-07B1 concluído; pesquisa funcional B2 verificada, pipeline pendente; B3 outras abrangências A fazer. [Verificação](docs/development/VERIFICATION.md).


## 2026-10-11 — Gasto federal por função (DATA-07B2)

- Coleta oficial limitada do arquivo anual OFSS/Tesouro, normalização Decimal por linha, sinais e rótulos 99 distintos, cobertura e reconciliação explícitos.
- Migration 0011 com revisões completas imutáveis, endpoint público e painel expansível em Brasil Atual; natureza/estágio, valores compactos/exatos e método.
- Fontes apresenta licença e estado de coleta comprovados, sem promover URLs privadas. Baseline, catálogo principal, publicações e motor preservados.
- Verificação local completa; DATA-07B3/outros entes e operação pública continuam pendentes.


## 2026-10-12 — Governo Geral por esfera (DATA-07B3)

- EFGG anual STN: oito grupos/métricas, consolidação publicada, competência modificada e cobertura municipal estimada explícita; pesquisa SICONFI/NFSP preservada sem novos coletores.
- Revisões próprias append-only, migration 0012, importação idempotente/atômica e download oficial limitado; fonte/termos, células, valores originais e diferenças preservados.
- Consulta pública e painel em Brasil Atual com Governo Geral/Central/estados/municípios, método, exatos e recurso da revisão; base congelada e motor preservados.
- Coleta real 2025 e coleta completa SUCCESS; 719 testes backend/197 frontend, checks/build, migration e oito combinações responsivas verificados. DATA-07 encerrado no recorte observado; catálogo mínimo, granularidade individual e operação pública permanecem futuros. [Evidência](docs/development/VERIFICATION.md).


## 2026-10-13 — Contrato de contextos e evidências (DATA-05A)

- Biblioteca isolada/imutável 1.0.0 para observações e recortes, hipóteses alternativas, evidências por afirmação, contrapartidas, consequências observadas/projetadas e lacunas.
- Validação estrita, hash completo e correspondência de revisão declarada; edição/cópia exige novo registro. Não autoriza publicação nem produz causalidade, coeficientes ou efeitos fiscais.
- 77 testes específicos/626 unitários backend e checks de código passaram; documentação e backlog atualizados. DATA-05B/C permanecem pendentes, sem alterações de API/banco/interface/grafo/IA. [Contrato](docs/data/CONTEXT_EVIDENCE.md).


## 2026-10-13 — Contextos persistidos e revisão autorizada (DATA-05B)

- Migration 0013: identidade, versões, decisões de revisão e publicações append-only; API pública lê apenas versões publicadas.
- Autor escreve/publica, administrador distinto revisa; referências oficiais resolvidas no servidor, privacidade por ID, metadados congelados e controle de edição/aceitação correspondente.
- Termos conflitantes/invalidade de proveniência e exemplos posteriores bloqueados; base de preços da renda preservada, sem IA/grafo/efeito fiscal novo.
- 918 testes backend com integração passaram; checks/migration/checkpoint verificados, backlog atualizado. UI e primeiros contextos reais permanecem DATA-05C. [Contrato](docs/data/CONTEXT_EVIDENCE.md).


## 2026-10-13 — Contextos na interface (DATA-05C preparado)

- Leitura pública com histórico, hipóteses/contrapartidas/evidências/lacunas; integração nos indicadores e Metodologia.
- Editor manual de rascunho e revisão administrativa distinta/publicação pelo autor, confirmação de descarte e checklist vinculado ao alvo.
- Descoberta por última publicação e opções confiáveis de observações históricas.
- Primeiro contexto pesquisado sobre desemprego, assistido por IA e privado; revisão humana real ainda pendente. Sem grafos/modelos/motor fiscal novo.


## 2026-10-14 — Base do grafo (GRAPH-01A)

- Contrato puro de nós/arestas versionados, referências congeladas e hash por aresta/conjunto.
- Conferência declarada com alvo exato, contrapontos e lacunas; nenhuma autorização/publicação automática.
- Diagnósticos de duplicatas, direções opostas, ciclos e nós isolados, sem propagação fiscal.
- Persistência/curadoria e página explicativa/explorador permanecem próximas fatias; conteúdo real de desemprego continua aguardando revisão humana.

## 2026-10-14 — Curadoria persistida do grafo (GRAPH-01B)

- Nós, relações e coleções com versões/fontes preservadas, nove tabelas append-only e migration 0014.
- API com autoria e revisão por outro administrador; publicação explícita revisada/em disputa, bloqueio por rejeição/pedido de alteração e coleções só de relações já públicas.
- Resolução de referências por ID, privacidade do cadastro de fontes, exemplos restritos a desenvolvimento e versões públicas exatas de nós.
- Listas/históricos compactos por projeção SQL e limites de bytes; 1.237 testes backend passaram, migração/Alembic/checkpoint verificados.
- Página explicativa/rede interativa continuam GRAPH-01C; contexto real aguarda revisão humana, sem efeitos numéricos ou IA.

## 2026-10-15 — Explorador de conexões em perspectiva (GRAPH-01C)

- Página pública `/grafos`, detalhes e versões exatas, integrada à navegação/Metodologia.
- Rede em perspectiva 3D com rotação, zoom, mover, visão plana e lista equivalente; seleção de nós e relações com evidências/contrapontos/revisão e histórico.
- Guia interativo e demonstração local explícita, sem inventar curadoria real ou impacto numérico.
- 272 testes frontend, lint/types/build; quatro larguras/dois temas, leitura por teclado e recuperação de falha conferidos. Dados e motor preservados.

## 2026-10-18

- Mapa de grafos com WebGL 3D opcional, câmera até a seleção, mergulho, sprites, estilos por consenso, painel sobreposto e lista automática conforme capacidades/preferências.
- Dicas iniciais, navegação por teclado, recursos gráficos liberados e teste isolado 200/500; contratos/dados/revisões preservados.
- Validação móvel física e perfil representativo de 60 fps permanecem pendentes em GRAPH-01C1.

## Qualidade do explorador WebGL — 2026-10-18

- Escape preserva foco sem painel; seleção por teclado no celular aproxima o mapa imediatamente.
- Arraste, múltiplos dedos e cancelamento não viram seleção acidental; relação incerta repousa após a câmera assentar.
- Teste isolado conta desenhos reais, invalida capturas interrompidas e permite conferir repouso/descarte. 300 testes frontend, lint e build passaram; aceites físicos/leitor de tela/desempenho representativo continuam pendentes.


## 2026-10-19/20 — Ideias acessíveis e operação local

- Criação guiada/manual com campos comuns e confirmação; IDEIA privada exige título e frase, COMPLETA passa por checklist antes de publicação versionada. Compartilhamento explícito, duplicação atribuída e sugestões de fontes.
- Conta, quotas, denúncia e moderação com fotografia do conteúdo; ordenação documental transparente, preservando versões e propostas legadas, sem alegar revisão técnica inexistente.
- Gemini opcional por interface trocável, chave no servidor, consentimento, logs privados/retidos e apagamento; modo guiado literal funciona sem chave. Avaliação real permanece pendente.
- Sensibilidade fiscal declarada das propostas completas publicadas, calculada pelo motor com Decimal e premissas ajustáveis. Ideias e recortes incompletos não geram resultados fictícios.
- Launchers Windows para iniciar/verificar/encerrar serviços identificados, manutenção de logs expirados e helper compatível com PowerShell 5.1. Backup/restauração e preservação do banco local verificados.
- Migrations 0015–0017, testes/regressões e documentação/backlog atualizados. [Verificação](docs/development/VERIFICATION.md) e [estado atual](docs/project/STATUS.md). Sem lançamento público.


## 2026-10-20 — Docker local completo

- Compose com frontend Next standalone, API, PostgreSQL persistente, migrations com dependência de sucesso e limpeza de logs expirados.
- Setup Docker preservando ambientes, senha aleatória, portas loopback e segredos excluídos do build; usuários sem privilégio nas imagens de aplicação.
- Build Linux, migrations em banco vazio, cópia conferida do banco anterior e autenticação pelo proxy validados. Dados nativos preservados; coleta e Gemini não iniciados. [Guia](docs/development/DOCKER_LOCAL.md).

## 2026-10-20 — Revisão útil de escrita no modo guiado

- Gemini pode corrigir escrita/clareza, com prompt versionado 2.0.0 e verificações de detalhes protegidos. As oito perguntas continuam fixas.
- Original e sugestão comparados antes de confirmar; saída sem mudança identificada e opção para manter texto original. Sem preenchimento, salvamento ou publicação automáticos.
- Metodologia e backlog atualizados com limites da validação e avaliação real sistemática pendente.

## 2026-10-22 — Desenvolvimento de propostas com IA e registros privados

- Assistente desenvolve a intenção informal e apresenta sugestões de implantação/contrapartidas e lacunas separadas; somente opções escolhidas e confirmadas entram como pontos a avaliar.
- Registro por chamada e última chamada disponíveis apenas ao autor, com retenção/apagamento respeitados, sem chaves nos logs.
- Corrigidas rejeições de expressões coloquiais e ordenação da última chamada. Docker deixa de consultar /ready periodicamente e verifica conexão TCP.
- Teste real fictício, confirmação seletiva, regressões e backlog atualizados; avaliação sistemática real de imparcialidade continua pendente.


## Interface do painel e consentimento — 2026-10-22

- Auditoria de todas as telas, preservando as aprovadas; painel, listas, editores e leitura pública alinhados aos tokens existentes.
- Aceite único de envio/retenção do Gemini por criação/sessão, revogável pelo indicador do guiado. API, verificações da saída e retenção permanecem.
- Escolha de caminho, cinco etapas manuais, pergunta focada, original/sugestões separados, ações com hierarquia e progresso/checklist do servidor.
- Sem nova dependência, alteração de schema ou cálculo fiscal. [Auditoria e limites](docs/design/WORKSPACE_AUDIT.md).


## Revisão humana, captura de ideia e navegação — 2026-10-22

- Removidas rejeições semânticas da saída do Gemini: orientação no prompt 4.0.0 e confirmação humana. Contratos técnicos, autoria, consentimento e logs preservados.
- Criar ideia agora tem entrada rápida de título/frase; preparar proposta completa mantém suas etapas e exigências de publicação.
- Navbar com agrupamentos Explorar/Meu espaço, estado ativo discreto e drawer mobile.
