# Registro de decisões

Data da fundação: 2026-10-06. **Aceita** indica decisão já incorporada ao projeto; **pendente** indica questão ainda aberta. Uma decisão aceita não implica feature implementada.

| ID | Estado | Decisão e consequência |
| --- | --- | --- |
| ADR-001 | Aceita | Leitura de conteúdo publicado sem login; escrita autenticada e autorizada. Rascunhos continuam privados. |
| ADR-002 | Aceita | Monorepo com monólito modular. Frontend e backend separados, sem microsserviços na V1. |
| ADR-003 | Aceita | Next.js + TypeScript e FastAPI + SQLAlchemy + Alembic + PostgreSQL. |
| ADR-004 | Aceita | Propostas e planos versionados desde o início. Publicações imutáveis; edição abre novo rascunho. |
| ADR-005 | Aceita | Cada versão do plano referencia versões específicas de propostas. Atualizar proposta não altera plano publicado. |
| ADR-006 | Aceita | Sem upload de arquivos/estudos na V1. Fontes por URL com contexto de uso; sem fetch de URL arbitrária. |
| ADR-007 | Aceita | Simulação fiscal aditiva por ano, um Cenário Base, motor independente e versionado. |
| ADR-008 | Aceita | Dinheiro com Decimal/NUMERIC; magnitudes não negativas e sinal determinado pelo tipo. |
| ADR-009 | Aceita | Não estimado difere de zero. Avisos acompanham resultados incompletos e medidas não financiadas. |
| ADR-010 | Aceita | Código, decisões e metodologia abertos; licença específica definida separadamente. |
| ADR-011 | Aceita | Fundação usa npm workspaces, uv, Node 22 e Python 3.12, com lockfiles. Escolha operacional revisável. |
| ADR-012 | Aceita | Financiamento declarativo não é somado ao resultado; efeito fiscal entra apenas nos impactos anuais. |
| ADR-013 | Aceita | Snapshot de fontes e entradas protege reprodutibilidade de publicações e execuções. Especificação em DATA_MODEL. |
| ADR-014 | Aceita | MIT para código e documentação autoral, seguindo a orientação de permitir uso e contribuição. Ver LICENSE e docs/governance/LICENSING.md. |
| ADR-015 | Aceita | JWT em Authorization, refresh opaco em cookie HttpOnly/SameSite Strict/Secure, nonce CSRF vinculado ao token, rotação e revogação de sessão em PostgreSQL. Produção usa origem única por proxy. Ver docs/architecture/AUTHENTICATION.md. |
| ADR-016 | Pendente | Hospedagem, domínio, remoto GitHub e canais de manutenção. |
| ADR-017 | Aceita | Em 2026-10-06: CSS nativo com tokens únicos, componentes React, Bricolage Grotesque + DM Sans via next/font, temas claro/escuro e geometria própria. Sem biblioteca visual/animação adicional. Ver docs/design/DESIGN.md. |
| ADR-018 | Pendente | Séries oficiais, recortes fiscais/sociais e política de atualização; verificar em F1-03. |
| ADR-019 | Pendente | Termos para propostas e planos contribuídos na plataforma; registrar termos de fontes/dados externos antes de usá-los. |

## Regra para novas decisões

Registrar ID, estado, contexto, escolha, alternativas relevantes e consequência. Não substituir uma decisão histórica sem indicar a nova decisão que a supera. Decisões de domínio precisam atualizar escopo, metodologia e critérios de aceite afetados.

## Implementação incremental de ADR-018/019

Meta Selic (SGS 432) e DBGG/PIB (SGS 13762) foram verificadas como primeiras séries, com termos ODbL em INDICATORS. O restante do catálogo e a política de atualização mantêm ADR-018 pendente. ADR-019 possui proposta revisável em docs/governance/CONTENT_POLICY_DRAFT.md; não está aceita nem implementada como termo vigente.

## ADR-020 — Cópia privada a pedido do mantenedor (2026-10-06)

Aceita. O redesign inclui duplicar propostas e planos publicados para um novo rascunho próprio, com crédito ao autor/versão e revisão antes de publicar. Usar os contratos existentes de criação, preservar referências às versões de propostas nos planos e não copiar a execução fiscal como resultado atual. Essa cópia independente amplia o escopo anterior; grafo/sincronização de forks, apoios e comentários seguem pendentes. Ver docs/design/DESIGN.md e UI-03/UI-04.

## ADR-021 — Coleta periódica de fontes revisadas (2026-10-07)

Aceita. Define a parte de atualização antes aberta em ADR-018: sete séries BCB/IBGE, consulta diária por worker, limite de repetição manual, lock PostgreSQL, histórico idempotente e preservação em falhas. Evita chamadas externas por visitante. Hospedagem/supervisão e a expansão fiscal/social seguem pendentes. Fontes arbitrárias contribuídas não são consultadas.

## ADR-022 — Brasil de referência por versão (2026-10-07)

Aceita. Criar proposta/plano captura os indicadores atuais disponíveis com unidade, referência, abrangência, fontes e proveniência. Rascunho só troca de base por ação explícita. Publicação e simulação preservam snapshot/hash, inclusive quando os dados oficiais são revisados depois. A base inicial é contextual e parcial; não soma taxas/índices ao resultado em reais, não prevê efeitos macroeconômicos e não reconstitui retrospectivamente versões antigas. Bases diferentes geram aviso.

## ADR-023 — Exemplos locais e dados ausentes (2026-10-07)

Aceita. Identidade explícita de exemplos; exclusão de publicações/fontes fictícias em produção e da base contextual em qualquer ambiente. A interface não fabrica popularidade, comentários, estimativa fiscal ou justificativa causal. Recursos sociais, login Google e termos vigentes dependem de implementação/decisões próprias.

## ADR-024 — Referência fiscal observada e denominador nominal (2026-10-09)

Aceita. Expandir ADR-021/022 com o RTN acima da linha: receita primária líquida, despesa primária e resultado primário do Governo Central, em caixa e reais nominais. Selecionar o último ano fechado com doze meses completos e reconciliados; conservar valores publicados separados dos calculados. Os valores em milhões são convertidos com Decimal, com tolerância mensal explícita de R$ 0,03 após arredondamento aos centavos, sem ajuste artificial dos agregados.

Para proporções, usar PIB nominal nacional do mesmo ano pela soma dos quatro trimestres das CNT/SIDRA 1846, variável 585, categoria 90707. Preservar a precisão de R$ 10 mil e a natureza revisável dessa soma; não confundir com divulgação anual definitiva. PIB ausente/incompleto não bloqueia valores fiscais absolutos e não permite usar outro ano ou trimestre estimado. PIB nacional não amplia Governo Central para Governo Geral nem equivale a receita disponível.

Coleta fiscal e coleta de PIB são atômicas e independentes. Referências capturadas preservam observações/revisões, fontes e conjuntos; dados novos não reescrevem publicações. Rejeitamos usar IBC-Br como PIB, anualizar o ano parcial ou somar automaticamente medidas à referência histórica. A compatibilidade dos impactos e premissas de cenários futuros fica em DATA-06. Outras abrangências e composição de receitas/despesas permanecem etapas posteriores. Ver [contrato e fontes](../data/FISCAL_BASELINE.md).

## ADR-025 — Organização documental e guias de agentes — 2026-10-10

Aceita por orientação do mantenedor para organizar o repositório antes da publicação. Raiz conserva entradas GitHub (README, AGENTS, CONTRIBUTING, SECURITY, CHANGELOG, LICENSE) e configuração; documentos por domínio em docs com índice e estado atual. Perfis .agents são guias fornecidos na delegação, sem registro automático de processos. AGENTS locais aplicam instruções por escopo; trabalho paralelo depende de autorização e contratos/arquivos sem sobreposição.

Documentos históricos preservados com links atualizados. Publicar código não equivale a lançar serviço; pendências explícitas em [PUBLICATION](../governance/PUBLICATION.md). CI inclui os testes frontend existentes. Nenhuma mudança de API/schema/método fiscal ou UX faz parte desta organização.

## ADR-026 — Metadados e compatibilidade histórica separados da aritmética — 2026-10-10

Aceita. Informar recorte fiscal por impacto, sem inferir campos legados. Avaliar novas execuções contra o snapshot fiscal do plano, preservando motivos/cobertura/versão no hash. COMPATIBLE identifica correspondência das declarações com o ano histórico, não qualidade da estimativa. Valores futuros exigem premissas próprias; não somar a base automaticamente.

Motor aritmético 1.0.0 preservado; avaliação adicional com versão própria 1.0.0. Metadados ausentes/misturados geram avisos e interpretação explícita, sem mudar resultados antigos. Migration 0009 aditiva; modelos validam preços constantes/ano-base. DATA-06A cobre o contrato histórico; DATA-06 continua preparado para cenários futuros. [Detalhes](../data/FISCAL_COMPATIBILITY.md).

## ADR-027 — Cenário anual declarado separado do observado — 2026-10-10

Aceita para a fatia de contrato/motor puro DATA-06B1. Antes de combinar medidas futuras, exigir receita/despesa primárias declaradas para cada ano e explicação das premissas. Primeiro recorte: Governo Central, caixa, BRL nominal, ano inteiro, até 30 anos. Nenhuma taxa/indexação automática ou repetição da base histórica.

Compatibilidade adicional com cenário futuro não altera o assessment histórico DATA-06A. Ausências, divergências, medida não estimada, dupla contagem não revista ou componente negativo impedem combinação global. A exclusão dos efeitos do plano na base futura é declaração humana, sem detector semântico de sobreposições.

Método de cenário versionado separado do motor incremental. Integração de rascunhos/API/persistência/interface fica em DATA-06B2; execuções e snapshots publicados atuais não mudam. [Contrato](../data/FISCAL_SCENARIOS.md).

## ADR-028 — Cenário opcional por versão e revisão vinculada às entradas — 2026-10-10

Aceita para a integração DATA-06B2. Guardar premissas do cenário em PlanVersion, opcionais, protegidas pela mesma imutabilidade da publicação. Ausência preserva modo incremental e legado; nova execução com cenário preserva insumos/revisão/método no hash e resultado separado em assumptions.

Confirmação de exclusão de efeitos exige endpoint específico e hash atual, sessão/autoria e rascunho. Vincular à referência preservada, premissas, horizonte e composição; alteração real invalida, salvamento idêntico não invalida. Novo rascunho/cópia exige nova revisão. Configuração ativa inválida não faz fallback silencioso. Compatibilidade histórica e com cenário declarado são avaliações distintas. [Contrato](../data/FISCAL_SCENARIOS.md).


## ADR-029 — Entrada acessível e rigor na proposta completa — 2026-10-10

Decisão de produto aceita por instrução do mantenedor; implementação ainda A fazer no épico UI-06. Separar começar de publicar como completa: conta obrigatória, IDEIA com título/uma frase e compartilhamento explícito identificado, sem cálculo/planos/ranking; COMPLETA com problema, medida, financiamento, beneficiados/prejudicados, riscos, fontes e requisitos fiscais/checklist. Não expor rascunhos existentes automaticamente nem alterar versões/planos publicados.

Modos “Me ajuda a montar” e “Eu preencho” usam um único molde e análise, com alternância sem perda. Substitui a orientação anterior de perguntas adaptativas por roteiro **fixo**, texto/ordem iguais para todos os temas/posições, versionado e publicado em Metodologia. Uma pergunta por vez, sempre quem perde/riscos; IA só organiza, confirma antes de preencher, aceita “não sei”, não inventa nem opina, texto identificado como assistido. Referências oficiais do catálogo são opcionais, com fonte/data. Motor calcula, nunca a IA; faixas/selos/lacunas exigem método público.

Integração de modelo trocável/barato, limite de uso configurável, log de prompt/resposta/versões com acesso restrito/retenção definidos e chave só em variável de ambiente. Limite diário, denúncia/moderação e ranking por solidez são condições da abertura do novo fluxo. Testes registrados com visões opostas exigem o mesmo roteiro e tom neutro, sem perguntas variáveis por tema/posição. Não escolher provedor, pesos do ranking ou valores de quotas nesta tarefa. [Requisito e fatias](../product/PROPOSAL_CREATION.md).

## ADR-030 — Composição RTN separada da referência fiscal — 2026-10-10

Aceita para DATA-07A. Usar quatro filhos diretos da receita/despesa e ponte receita total menos transferências, com valores assinados, mesma fonte/ano/critério. Não confundir com função orçamentária, renúncia total, discricionárias totais ou orçamento de todos os governos. API/XLSX/manuais verificam códigos e escala; tolerância mensal R$ 0,03 e diferenças publicadas sem forçar igualdade.

Catálogo/fingerprint/coleta próprios reutilizam observações existentes. Dez séries auxiliares ficam fora do catálogo principal e da base contextual; endpoint separado ancorado nos três totais/ano da base corrente. Coerência e transação impedem lote parcial; frontend bloqueia mistura entre consultas. Preservar métodos/hashes/snapshots publicados e resultado incremental. Outras funções, juros e entes continuam DATA-07B. [Contrato](../data/FISCAL_COMPOSITION.md).

## ADR-031 — Juros e nominal com primário abaixo da linha — 2026-10-11

Aceita para DATA-07B1. Usar três séries RTN apuradas pelo BCB, sinais publicados e regime misto explícito: primário em caixa, juros líquidos por competência. Nominal é a soma assinada com o primário abaixo da linha, nunca com o acima da linha existente. Mesmo ano/ente não elimina a diferença metodológica.

Catálogo/fingerprint/coleta auxiliares próprios, transação, doze meses e tolerância mensal R$ 0,03; residual anual divulgado. API e painel separados, sem alteração do motor, snapshots, hashes ou contratos anteriores. Funções de gasto/Extra-Siafi e outros entes continuam em B2/B3. [Contrato](../data/FISCAL_INTEREST.md).

## ADR-032 — Conjunto funcional completo e imutável — 2026-10-11

Aceita para DATA-07B2. Arquivo federal por função contém três naturezas e pagamentos do exercício/RAP, incluindo ajustes Extra-Siafi assinados e código 99 com rótulos distintos. Normalização Decimal por linha a centavos half-even versionada; dados brutos e diferenças preservados como proveniência agregada, sem inventar zero ou função.

Persistir cada arquivo validado como conjunto append-only próprio, via migration 0011, em vez de criar indicador-sentinela com valor fictício. Revisão por ano/hash/parser/precisão, fonte congelada e transação; último conjunto incompatível não faz fallback silencioso. Somente agregados monetários string em JSONB, sem arquivo bruto no git. Fonte pública depende de vínculo real; URLs privadas coincidentes não são promovidas.

Consulta/painel auxiliares, fora da base contextual, snapshots e motor. Classificação funcional não equivale à despesa RTN, mínimos constitucionais ou margem para cortes; resumo da planilha tem recorte próprio. [Contrato](../data/FISCAL_SPENDING.md).


## ADR-033 — Governo Geral com consolidação publicada pela STN — 2026-10-11

Aceita para DATA-07B3. Usar EFGG/GFSM anual por esfera, competência modificada, termos/atribuição da publicação, cobertura municipal extrapolada explícita e ajustes de consolidação originais. Não produzir soma própria de DCA, juntar NFSP/RTN/OFSS ou substituir a base primária. Preservar grupos, sinais, cálculos/resíduos e recurso completo em revisão append-only própria (0012), API/painel auxiliares, nenhum efeito em snapshots/motor.

SICONFI por ente e NFSP foram verificados como alternativas com contratos distintos; não importar todos os municípios nem tratar setor público consolidado como Governo Geral. Não inferir ponte entre função nacional e COFOG. [Contrato](../data/GENERAL_GOVERNMENT.md).


## ADR-034 — Contexto distingue explicação possível de observação — 2026-10-13

Aceita para DATA-05A. Contrato isolado/imutável 1.0.0 em módulo contexts, sem HTTP, banco, IA ou dependência do motor. Observações com IDs/revisões e recortes congelados, evidências sobre afirmações específicas, hipóteses alternativas, contrapartidas e consequências observadas/projetadas separadas. Incompletude e incertezas explícitas; nenhum coeficiente numérico.

Hash do conteúdo validado completo e registro de revisão com alvo/versão/checklist/data. Correspondência declarada não autentica revisor nem autoriza publicar; futura camada confiável resolve referências e permissões e persiste publicação em transação. Não criar selo de causalidade ou ranking automático a partir de metadados. [Contrato e limites](../data/CONTEXT_EVIDENCE.md).


## ADR-035 — Contextos publicados exigem revisão autorizada distinta — 2026-10-13

Aceita para DATA-05B. Autor ativo cria/salva/publica; administrador ativo diferente do autor revisa, inclusive quando autor é administrador. Sem bypass para editar/publicar contexto alheio ou usar fonte privada de terceiro. Cliente informa referências/textos, servidor resolve dados e atribui identidade/revisão/data/hash; publicação depende da última aceitação correspondente e elegibilidade atual do revisor.

Cada salvamento é append-only, não apenas versões publicadas; identidade/selo de exemplo, decisões e publicação também são imutáveis. Locks, expected_revision, FKs compostas e gates SQL estruturais preservam alvos/imutabilidade. Leitura pública sempre parte de publicação e de metadados congelados; nenhuma integração retroativa ao motor/snapshots. A API não valida causalidade nem converte checklist em selo de verdade. [Contrato](../data/CONTEXT_EVIDENCE.md).


## ADR-036 — Relações versionadas e grafo separado do cálculo — 2026-10-14

Aceita para GRAPH-01A, contrato puro sem HTTP, persistência ou UI. Nó tem identidade/revisão e dimensão explícita; aresta incorpora versões exatas dos nós/fontes/evidências e conserva seu próprio hash/autoria/revisão. Snapshot seleciona versões exatas. Aumento/adoção da origem define o sentido alegado no destino; classificação de efeito/consenso é declaração autoral, sem comprovação ou número inferido.

Sem fonte/evidência vinculada não existe aresta. Só apoio declarado permite encaminhar à conferência; consolidado/debatido exige contraponto documentado ou busca declarada sem resultado (nota, registro de busca e data). Busca não realizada fica distinta e não cumpre esse requisito. Humano/assistido exigem revisão distinta vinculada ao conteúdo; estados correspondentes continuam sem autenticação/autorização. Publicação/disputa/rejeição exigem política e serviço próprios na fatia B, sem flag que exponha rascunho.

Duplicatas, direções opostas e ciclos são diagnósticos; feedback pode existir, mas nenhum percurso gera soma/coeficiente. Magnitudes/IA ficam em contratos posteriores. Não impor uniformidade global a fotografias históricas de um cadastro de fonte mutável; preservar cada fotografia no hash da aresta. Não mudar motor, snapshots ou contextos já publicados. [Contrato](../data/GRAPH_CONTRACT.md).

## ADR-037 — Publicação explícita por aresta e reuso de versões públicas — 2026-10-14

Aceita para GRAPH-01B. Serviço resolve referências reais e visibilidade e atribui identidades/datas/hash; autor ativo escreve/publica, outro admin ativo revisa. Última aceitação permite publicar `REVIEWED`; última disputa com conferências completas permite somente `DISPUTED`, escolhido explicitamente pelo autor. Pedido de alteração/rejeição bloqueiam; nenhum estado puro ou flag do cliente concede autorização.

Coleção congela versões de relações já publicadas e seus metadados de revisão. Nó só é público pela publicação da versão exata numa aresta; nó isolado selecionado exige testemunha pública anterior. Conjunto real exige testemunha real, inclusive em desenvolvimento, sem vazamento por exemplos. Publicações históricas mantêm suas fontes/revisões e podem ser reutilizadas por outro autor; isto não torna o cadastro privado da fonte um item do diretório público.

Nove tabelas append-only/migration 0014, FKs/gates e transação com locks preservam alvos e autoria. Listagens/históricos projetam metadados, detalhes carregam conteúdo congelado; limites de bytes complementam limites de nós/arestas. Não modificar observações, contextos reais, base fiscal ou snapshots. Página explicativa/explorador são C; magnitude/IA continuam D/E. [Contrato](../data/GRAPH_CONTRACT.md).

## ADR-038 — Perspectiva 3D com alternativa textual equivalente — 2026-10-15

Aceita para GRAPH-01C. O pedido de profundidade visual é atendido com coordenadas 3D, câmera/projeção e SVG próprio, sem adicionar WebGL ou pacote de grafos. Layout é determinístico, limitado e separado dos dados; posição/tamanho/distância não representam evidência ou impacto. Arraste, zoom, visão plana, controles por teclado e lista equivalente preservam acesso quando a perspectiva não ajuda. Layout calcula uma vez por conjunto/recorte, sem executar a simulação física em cada frame.

Publicações são lidas como versões exatas, inclusive fontes/revisão por aresta. Demonstração local explicitamente fictícia só é uma origem distinta; não conta como publicação ou revisão real, nem substitui erro de uma versão solicitada. Uma versão válida abre independentemente da disponibilidade do catálogo. Não escrever contextos, grafo real ou cálculo fiscal para preencher a interface. [Contrato](../data/GRAPH_CONTRACT.md) · [Explorador](../product/GRAPH_EXPLORER.md).

## ADR-039 — WebGL opcional e câmera centrada na seleção — 2026-10-18

Substitui apenas a decisão de renderização SVG da ADR-038, a pedido do mantenedor. Usar Three.js diretamente com OrbitControls, sem wrapper de grafos adicional: o layout determinístico existente já fornece as coordenadas e o renderer precisa controlar rótulos, consenso e câmera de forma específica. [Three.js](https://threejs.org/docs/) e seus avisos MIT são preservados.

Módulo cliente dinâmico sem SSR e adiado por interseção/capacidade; nenhuma importação de Three no shell global. Lista pública é alternativa de conteúdo equivalente e fallback para preferência de movimento reduzido, capacidade limitada ou erro. Não manter dados privados em localStorage: somente preferência de dicas.

Câmera/enquadramento/instâncias/sprites são geometria visual e usam Number, sem aritmética fiscal. Layout fica estável e cacheado, física para após pré-cálculo, seleção não modifica conteúdo ou posições. Destaques são somente seleção/tipo. Consenso é declarado pelo autor e não ganha magnitude, ranking ou certeza visual. Fullscreen mantém identificação do exemplo. Limite 200/400, versões e gates de revisão/publicação continuam intactos; 200/500 existe somente no teste isolado de renderização. Perfil em hardware móvel/60 fps e leitor de tela permanecem verificações próprias.


## ADR-040 — Participação local acessível e assistência opcional Gemini — 2026-10-19

Implementa ADR-029 após autorização do mantenedor para concluir o projeto para uso no próprio computador. A entrega é o produto local funcionando, sem roteiro acadêmico, publicação externa ou alegação de concluir a operação pública.

Separar IDEIA de PROPOSTA COMPLETA. Ideia começa privada com título/frase; compartilhar é ação explícita com fotografia. Editar retira a fotografia pública e exige novo compartilhamento. Duplicação conserva atribuição; sugestões dependem de incorporação autoral. Checklist do servidor e publicação transacional impedem levar ideia incompleta ao motor/planos. Contratos novos preservam publicações/planos legados e seu tratamento fiscal anterior. Migrations 0015–0017 são aditivas; backup antes de upgrade, sem downgrade no banco útil.

Guiado e manual compartilham contrato, confirmações, retomada e análise. Roteiro fixo `1.0.0` público; nenhuma pergunta varia por tema. Gemini é o provedor escolhido pelo mantenedor, atrás de interface trocável, sem SDK pesado adicional ou OpenAI integrado. Modelo configurável, padrão `gemini-3.1-flash-lite`; [documentação do modelo](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite.md). Assistência desativada por padrão, chave `GEMINI_API_KEY` só no servidor e envio com consentimento. Sem chave o roteiro funciona sem IA. Não afirmar teste com Gemini real até a chave e a avaliação efetiva.

O modelo apenas organiza parágrafos com palavras literais e mesma ordem; o servidor rejeita inserção/omissão. Texto não entra em campo sem confirmação. “Não sei” preserva ausência. Logs privados registram prompt/resposta/versões por sete dias por padrão; usuário apaga conteúdo, quota permanece e resposta tardia não restaura conteúdo apagado. Limpeza exige operação ativa e não apaga backups automaticamente. Quota padrão 20/dia UTC e cinco/minuto, incluindo falhas. Conta, limites de participação e moderação são controles de backend, não permissões inferidas da interface.

Análise `DECLARED_SENSITIVITY_1` usa Decimal e motor `1.0.0` sobre COMPLETA pública estimada com recortes compatíveis. Multiplicadores explícitos até quatro casas, mínimos 0–1/máximos 1–2 e padrão 1, sem fabricar faixa. Rótulo “estimativa declarada”; não atribuir confiança estatística, efeito causal ou cálculo ao Gemini. Financiamento não duplica receita. [Método](../data/METHODOLOGY.md#criação-guiada-e-sensibilidade-declarada--2026-10-19).

Solidez vira completude documental transparente `DOC_COMPLETENESS1`, fonte/financiamento/revisão, sem popularidade. Revisão de proposta não existe neste fluxo: zero e `NOT_ASSESSED`, sem selo fictício; legado sem nota. Não confundir revisão de contextos/grafos com revisão de propostas.

Launchers Windows usam instância/banco existentes, validam identidade de processos e preservam serviços alheios. Build/migration são flags explícitas; encerramento preserva PostgreSQL. Não iniciar coletor ou criar pesquisa/publicação real automaticamente. Backup/restauração local verificados não encerram HTTPS, operação supervisionada ou lançamento público. [Desenvolvimento](../development/DEVELOPMENT.md) · [Contrato do editor](../product/PROPOSAL_CREATION.md).

## ADR-041 — Revisão de escrita com comparação e confirmação — 2026-10-20

Substitui somente a restrição de palavras literais da ADR-040: a implementação anterior impedia a ajuda de escrita esperada pelo mantenedor. O prompt 2.0.0 permite corrigir ortografia, concordância e clareza sem mudar ideia/posição/ressalvas ou acrescentar medidas, fontes ou números. Roteiro público 1.0.0 permanece fixo. Provedor mantém formato de parágrafos e retorna original_text/rewritten; UI compara os textos, identifica ausência de alteração, permite manter original e exige confirmação. Sem IA usa o original, sem alegar revisão.

Validação local é conservadora sobre estrutura, tamanho e detalhes protegidos (números/sinais/unidades/URLs e marcadores selecionados). Não é verificador de verdade ou prova de equivalência semântica; confirmação humana continua essencial. Prompt/modelo exigem nova avaliação real de imparcialidade. Logs/quota/consentimento/retenção, cálculo fiscal e publicação permanecem com os contratos anteriores.

## ADR-042 — Desenvolver a intenção, com opções autorais e rastreio privado — 2026-10-20

Substitui o limite de revisão de escrita da ADR-041 por pedido explícito do mantenedor: a pessoa escreve do próprio jeito e o assistente ajuda a elaborar uma proposta de política pública. Prompt 3.0.0 separa redação principal, sugestões de desenho/implantação/contrapartidas e lacunas. Sugestões podem ir além do dito, mas não se tornam afirmações do autor: começam desmarcadas e só entram por seleção e confirmação, rotuladas como pontos a avaliar. Sem fatos/valores/legislação/fontes inventados, escolha ideológica pelo assistente, cálculo ou publicação autônoma. Perguntas fixas 1.0.0 preservadas; lacunas são conteúdo auxiliar, não substituição do roteiro. Essa mudança exige nova avaliação real de imparcialidade.

Contexto limitado às respostas textuais confirmadas e consentidas, sem parcelas fiscais, sugestões pendentes ou consulta automática a dados externos. Logs existentes suportam contexto/saída estruturada sem nova tabela; consulta privada por ID exige autor, prazo vigente e não apagamento. Resposta pública não contém chave ou autenticação. HTTP detalhado do provedor não é salvo indiscriminadamente. Código não prova fidelidade semântica: revisão humana continua necessária.

Healthchecks Docker de API/frontend passam de HTTP /ready a conexão TCP a pedido do mantenedor, eliminando sondagens periódicas ao endpoint. Não equivalem mais a prontidão do banco; migration e diagnóstico manual continuam separados. Limpeza de registros privados continua ativa e não é a origem das chamadas /ready.


## ADR-043 — Consentimento único por criação e interface do painel — 2026-10-22

Por pedido do mantenedor, o consentimento deixa de ser uma confirmação repetida por pergunta. Aceite explícito no início do modo guiado é guardado somente na memória da sessão autenticada, associado à criação. Transferência para o ID salvo preserva a decisão; nova criação, recarregamento ou encerramento da sessão removem o aceite. A opção “mudar” permite seguir sem IA. A interface envia consentimento em cada chamada ao modelo; não remove o gate da API, a retenção configurada nem verificações da saída. Não é uma autorização global persistente da conta.

Consolidação visual usa os tokens e componentes atuais, com módulos CSS locais; páginas aprovadas não são redesenhadas. Contadores, checklist e ações refletem contratos existentes, sem inventar completude, ranking, histórico ou permissões para atender a um mockup. [Auditoria](../design/WORKSPACE_AUDIT.md).


## ADR-044 — Autor decide sobre a sugestão da IA; entradas distintas — 2026-10-22

Pedido explícito do mantenedor substitui as verificações semânticas conservadoras das ADR-041/042. Comparação de números, URLs, unidades, palavras de direção, negações, ressalvas e extensão relativa ao original deixa de rejeitar a saída. Prompt 4.0.0 orienta a geração; revisão humana compara e confirma antes de escrever campos. Código valida apenas contrato de transporte/tamanho (incluindo limites reais dos campos), sem certificar fatos ou equivalência. Erros técnicos distinguem formato inválido de falha do provedor. Mantidos roteiro 1.0.0, consentimento, quotas, logs privados e publicação explícita. Nenhum conteúdo da IA passa a alimentar o cálculo diretamente.

Nova entrada rápida `/painel/ideias/nova` recebe título e uma frase e salva privadamente. O fluxo existente `/painel/propostas/nova` passa a comunicar preparação completa. Salvar e desenvolver com IA encaminha ao editor da ideia salva, sem envio ao Gemini antes do aceite. Navbar agrupa leitura em Explorar, mantém Ideias/Propostas/Planos visíveis e conta em Meu espaço, preservando os destinos existentes.


## ADR-045 — Suspensão revoga sessões e configuração falha de forma segura — 2026-10-25

A auditoria local confirmou que apenas is_active=false bloqueava acesso durante a suspensão, mas a reativação restaurava sessões antigas. Desativar USER passa a revogar todas as sessões na mesma transação; reativar exige novo login. Login bloqueia exclusivamente a própria conta durante verificação/rehash/criação de sessão, ordenando concorrência com a suspensão sem promoção de lock de leitura para escrita.

COOKIE_SECURE=false fica restrito a ENVIRONMENT=development; outras configurações inseguras são recusadas. Erros SQL e de configuração não devem ecoar entradas privadas: engine oculta parâmetros, handler SQL registra só classe/request_id e settings ocultam input em mensagens de validação. JWT continua HS256, com IDs tipados e sessão/role consultados no banco. Bucket de oito por identidade só existe quando há identificador; limite por IP e pendência de proxy confiável permanecem.

Não muda o acesso amplo de ADMIN a rascunhos de propostas/planos, autoria estrita dos outros módulos ou imutabilidade. Não implica criptografia em repouso, HTTPS local, MFA ou lançamento público. Patch de framework/dependências é manutenção de segurança, sem mudança de stack ou telas. Achados, evidências e limites em [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md).

## ADR-046 — Coleta diária por calendário no Compose — 2026-10-25

Pedido de 12:00 A.M. interpretado como 00:00 em America/Sao_Paulo. Serviço dedicado executa a rotina diretamente, sem sondagem HTTP da aplicação e sem coleta por visitante. Calendário e mínimo de uma hora são reavaliados dentro do lock PostgreSQL; resultado parcial permite retentativa de uma hora, início recupera consulta vencida, sucesso volta à próxima meia-noite. Configuração pública não comprova processo vivo. Atribuição usa ADMIN ativo configurado ou primeiro por criação/ID, sem criar/promover conta. Históricos, fontes controladas e snapshots permanecem protegidos. Computador/Docker desligados adiam a consulta; alertas/supervisão pública continuam pendentes.

## ADR-047 — Capturar ideia e desenvolver proposta são momentos distintos — 2026-10-25

Criação e edição de ideia mostram só título/frase por padrão; desenvolver é ação explícita, aproveita o mesmo ID e preserva detalhes anteriores. O rigor continua na publicação completa. Catálogos explicam ideia/proposta/plano no início; sem nova aba nem redesenho da Home. Possibilidades da IA são opcionais/recolhidas e exigem seleção/confirmação; não são incorporadas silenciosamente, nem calculam efeitos. Complementa ADR-044 sem alterar autorização, compartilhamento, motor ou versionamento.
