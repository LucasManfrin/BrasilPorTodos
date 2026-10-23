# Contextos e evidências — DATA-05

O objetivo é ajudar a pessoa a ler um indicador com contexto, sem tratar uma possível explicação como fato. Primeiro separar o que foi observado, as hipóteses sobre o motivo, as alternativas e o que ainda não sabemos. Dados e análise não viram efeito numérico de uma proposta por associação.

## Estado e sequência

DATA-05A entregue localmente em 2026-10-13: biblioteca isolada de contrato, validação, impressão digital e correspondência de revisão declarada. Não há persistência, endpoints, contextos publicados, nova interface, grafo ou IA nesta fatia. Biblioteca: `backend/app/modules/contexts/context.py`. A API, a base corrente, as publicações e o motor existentes não a utilizam automaticamente.

DATA-05B entregue localmente em 2026-10-13: persistência/versionamento, resolução confiável de referências, escrita autenticada/autorizada, revisão humana e publicação imutável na API. DATA-05C Preparado: interface pública/editor/revisão e primeiro rascunho pesquisado entregues; falta revisão humana efetiva e publicação desse conteúdo. DATA-05 permanece parcial até os primeiros contextos efetivamente pesquisados/revisados; análise por IA é evolução posterior. [Backlog](../project/BACKLOG.md).

## Estrutura versionada

Contrato `1.0.0`, modelos Pydantic estritos/imutáveis, coleções em tuplas e campos desconhecidos recusados. Um contexto pode estar incompleto: `assess_context` informa pendências em vez de preencher lacunas. Valores de observações são strings decimais exatas, sem conversão para float, cálculo ou arredondamento; zero observado não é ausência. Não há parâmetro para coeficiente, probabilidade ou impacto fiscal.

| Parte | Conteúdo preservado | O que não autoriza concluir |
| --- | --- | --- |
| Identidade | UUID do contexto/autor, revisão, data UTC e versão do contrato | Identidade declarada não autentica autor |
| Observação | Indicador, UUID/revisão da observação, fonte, valor/unidade, recorte, método, frequência, período, referência e coleta | Validação estrutural não comprova existência no catálogo oficial |
| Fonte | UUID, título, instituição, URL, termos/URL, consulta e publicação quando conhecida | URL não comprova argumento, não é consultada pela biblioteca e não torna fonte privada pública |
| Evidência | Afirmação específica, trecho usado, página/tabela/seção, recorte/período, fonte, limites e tipo de sustentação | Documento inteiro não endossa cada frase do contexto |
| Hipóteses | Explicação possível, evidências que apoiam/contestam/contextualizam, justificativa e incerteza | Correlação, cronologia ou hipótese revisada não demonstram causa |
| Alternativas | Pelo menos duas explicações distintas para encaminhar à revisão | Distinção de texto não garante diversidade de mecanismos ou imparcialidade |
| Contrapartidas | Outro indicador, por que ler junto, observações referenciadas ou “não coletado” explícito | Falta não vira zero nem dado conhecido |
| Consequências | OBSERVED ou PROJECTED, referências ou premissas, limitações | Projeção não é observação nem previsão produzida pelo motor |
| Lacunas | Limitações e o que não se sabe, registradas separadamente | Completar campos não elimina incertezas |

Evidências têm tipos **descrição**, **associação** e **apoio a hipótese** (`DESCRIPTION`, `ASSOCIATION`, `HYPOTHESIS_SUPPORT`). São rótulos do uso declarado, não escala automática de confiança, ranking nem selo de causalidade. Não existe tipo “causa comprovada” nesta biblioteca. Cada ligação registra `SUPPORTS`, `CHALLENGES` ou `CONTEXT` e uma justificativa. Hipótese alternativa sem evidência pode continuar explicitamente incerta; a avaliação não fabrica apoio.

Uma consequência observada precisa de observação referenciada ou evidência descritiva/de associação e não admite premissas de projeção. Apoio a hipótese, sozinho, não atende esse requisito; associação descreve o recorte, sem comprovar causa. Uma projetada exige premissas declaradas. Ambas exigem limitações. Nenhuma consequência é obrigatoriamente inventada para completar um contexto: quando não sabemos, registrar a lacuna; a revisão humana deve avaliar a pertinência do conteúdo.

## Validação e limites

IDs duplicados e referências órfãs são recusados. A observação principal precisa pertencer ao conjunto. Uma contrapartida referenciada precisa apontar para o próprio indicador; repetir o indicador principal não atende ao requisito de outro recorte. Ausência é `NOT_COLLECTED`, sem observações ou valores inventados.

Referência temporal deve pertencer ao período observado. Datas de registro exigem fuso e são normalizadas para UTC. A avaliação recebe explicitamente `assessed_at`, sem relógio ambiente: identifica contexto futuro, publicação posterior à consulta, coleta/consulta posteriores à edição e período observado posterior à coleta. Data de publicação desconhecida permanece `None`.

URLs HTTP/HTTPS com host, sem credenciais, espaços, controles ou barra invertida; tamanho e coleções limitados. As URLs são somente metadados armazenáveis, sem download, upload, scraping ou consulta ao modelo. A biblioteca não resolve DNS, valida a reputação de uma fonte ou confere o texto citado. Campos livres precisam de renderização segura na futura interface.

## Revisão vinculada ao conteúdo

`fingerprint` calcula SHA-256 do conteúdo validado completo em JSON canônico: versão, identidade/revisão/autor, datas, observações e recortes, fontes/termos, textos, evidências, alternativas, contrapartidas, consequências, limites e lacunas. Ordem das coleções faz parte do conteúdo. Espaços nas bordas dos campos textuais normalizados e fusos equivalentes não são alterações semânticas; chaves JSON têm ordem canônica.

O registro de revisão conserva UUID do revisor, data UTC, versão, ID/revisão do contexto, hash, decisão e justificativa. Checklist separado: referências, recortes, alternativas e limitações conferidos. Copiar, editar um campo semântico, adotar outra revisão da observação ou mudar a revisão do contexto exige novo registro correspondente. Revisão anterior à edição ou posterior à avaliação não corresponde. Pedido de mudanças permanece pedido de mudanças.

| Estado da biblioteca | Significado |
| --- | --- |
| INCOMPLETE | Pendências estruturais/de conteúdo explícitas; revisão não as dispensa |
| NEEDS_REVIEW | Estrutura pronta para conferência humana ou checklist incompleto |
| REVIEW_STALE | Registro não corresponde ao contexto/revisão/hash/datas avaliados |
| CHANGES_REQUESTED | Registro correspondente solicita alterações |
| REVIEW_MATCHES | Registro declarado corresponde ao conteúdo e checklist; não é autorização de publicação |

**Não tratar `REVIEW_MATCHES` como aprovação autenticada, selo de verdade, prova causal ou autorização.** UUID/hash enviados por cliente não comprovam quem revisou. DATA-05B deve atribuir identidade/data na camada confiável, conferir sessão/permissões e estado do usuário, resolver IDs e revisões contra dados reais, conferir metadados congelados e visibilidade das fontes, persistir a revisão e publicar em transação. Não aceitar flag de aprovação ou identidade de revisor fornecida pelo cliente como gate final.

A versão publicada deve preservar conteúdo, evidências, registro e autoria; revisão oficial posterior não reescreve a análise antiga. Contextos não entram nos snapshots legados nem nas contas fiscais automaticamente. Um eventual grafo pode apresentar relações, mas terá contrato próprio antes de produzir qualquer efeito numérico. [Metodologia](METHODOLOGY.md) · [Requisito futuro de grafos](../product/GRAPH_EXPLORER.md).

## Verificação desta fatia

Testes com conteúdo explicitamente fictício cobrem incompletude, sinais/zero, referências, fontes/URLs, datas, tipos estritos, mutabilidade, roundtrip JSON, hash, edição/cópia/revisão, checklist, pedido de alterações, contrapartidas e observação/projeção. Nenhuma análise real do Brasil foi publicada ou recebeu revisão humana por executar esses testes. [Evidências de execução](../development/VERIFICATION.md).



## Persistência e API — DATA-05B

Migration 0013 cria quatro tabelas append-only: `contexts` (identidade/autoria/selo de exemplo), `context_versions` (cada salvamento é uma nova revisão, payload e hash), `context_reviews` (decisões humanas sequenciais por versão) e `context_publications` (versão/revisão aceitas/data/autor da publicação). Não há alteração/exclusão silenciosa, nem atualização retroativa dos planos/simulações. Contextos incompletos podem ser salvos privadamente.

Escrita/publicação **somente pelo autor ativo**. Admin tem leitura privada para revisar, sem editar ou publicar por outra pessoa. Revisão exige administrador ativo diferente do autor; autor administrador precisa de outro administrador. Essa separação é decisão desta fatia para distinguir autoria de conferência. O servidor atribui UUIDs, autoria, revisão, data e hash. Cliente envia conteúdo e IDs de referências, nunca identidade do revisor, timestamps de revisão ou flag de aprovação.

`expected_revision` inteiro estrito é obrigatório para editar, revisar e publicar. Bloqueio na identidade serializa as operações; alvo antigo recebe conflito 409. Cada edição perde o vínculo com a aceitação anterior, mesmo após publicar. Pedido de mudanças mais recente bloqueia uma aceitação anterior. Publicação exige última revisão ACCEPT/checklist completo da versão atual, referências novamente conferidas e revisor ainda ativo/administrador. Resposta é construída antes do commit; falha anterior reverte toda a transação. Não foi executado teste de carga ou benchmark de concorrência.

Gates SQL conferem identidade/sequência, alvo/hash/revisor/checklist e a vinculação da publicação à aceitação atual, com chaves estrangeiras compostas. UPDATE/DELETE das quatro tabelas é recusado. Esses gates protegem estrutura/imutabilidade; autenticação e interpretação das referências continuam na API, sem alegar que SQL comprova o argumento. Há trilha de auditoria de revisão/publicação.

| Método e rota | Acesso / resultado |
| --- | --- |
| GET `/api/v1/contexts` | Público, paginação e busca em títulos publicados; não revela rascunhos |
| GET `/api/v1/contexts/mine` | Próprios contextos/última revisão, autenticado |
| GET `/api/v1/contexts/review-queue` | Fila de versões ainda não publicadas, administrador ativo distinto do autor |
| POST `/api/v1/contexts` | Cria identidade e primeira revisão privada, `{content: ...}` |
| PUT/PATCH `/api/v1/contexts/{id}` | Conteúdo inteiro e `expected_revision`; cria nova revisão própria |
| GET `/api/v1/contexts/{id}/draft` | Última revisão privada, autor ou administrador |
| POST `/api/v1/contexts/{id}/review` | Decisão/checklist/justificativa e `expected_revision`; revisor distinto |
| POST `/api/v1/contexts/{id}/publish` | Autor, `expected_revision`; publica versão revisada em transação |
| GET `/api/v1/contexts/{id}` | Última versão publicada, independente de rascunho posterior |
| GET `/api/v1/contexts/{id}/versions` | Histórico somente publicado |
| GET `/api/v1/contexts/{id}/versions/{revision}` | Publicação histórica congelada |

Envelope/paginação/erros seguem a API existente. Escrita de observações usa apenas `observation_ids`; `source_ids` seleciona fontes adicionais para evidências. A fonte de cada observação é incluída automaticamente. DTO não aceita números/metadados de observações fornecidos pelo cliente; conteúdo textual e relações continuam autorais e sujeitos à revisão, sem busca automática.

## Resolução real e preservação

Esta fatia aceita observações dos 14 códigos principais revisados, fontes oficiais cadastradas e definição histórica completa em `IndicatorValue.provenance.definition`. Não substitui uma definição ausente pela atual. Valor, unidade, recorte, método, frequência, revisão e coleta são copiados do registro existente. A revisão mais recente do mesmo indicador/período é exigida ao salvar, revisar e publicar; dado revisado exige nova seleção/salvamento/conferência. Publicação histórica continua legível com sua fotografia anterior.

Períodos preservam os recortes: PNAD é trimestre móvel, IPCA de 12 meses é janela de 12 meses, PIB é trimestre de calendário e demais séries seguem frequência revisada. O dia 01 não transforma esses dados em medição diária. A renda real preserva também a base de preços e o método da coleta em sua definição; falta desses metadados impede criar uma análise com base de preços inventada. Não calcular relações entre janelas diferentes automaticamente.

Contrapartida precisa ser código conhecido/ativo e apontar para observações do próprio indicador. `NOT_COLLECTED` só cabe quando não há observação salva desse indicador; não significa apenas que o autor deixou de selecionar um dado. Ausência por período e novos códigos precisam de contrato/catálogo próprios.

Fontes são resolvidas **para o autor do contexto**, por ID: próprias ou já públicas por vínculo real; administrador revisor não ganha permissão para usar a fonte privada de terceiro. URL coincidente não concede acesso. Fonte própria selecionada será divulgada no payload congelado se o autor publicar a versão revisada; não expõe descrição privada/outros rascunhos e não promove automaticamente a linha mutável no diretório Fontes. Leitura pública usa apenas o payload publicado, sem consultar metadados atuais da fonte para substituir os antigos.

Nome, instituição, URL e publicação vêm do cadastro. Consulta preserva a data cadastrada na fonte, representada em UTC, sem afirmar nova visita externa. Termos vêm da proveniência das observações selecionadas ou do registro de coleta validado da fonte. Termos históricos conflitantes na mesma fonte são recusados; dados malformados recebem erro limitado. Fonte sem termos conhecidos fica explicitamente “Termos não informados no catálogo; conferir antes de reutilizar”, com URL de origem; esse link não é apresentado como prova de licença. A publicação humana não relicencia dados externos.

Metadados/fontes e usuários recebem bloqueios compartilhados durante a transação; revisão/publicação rechecadas não atualizam o conteúdo silenciosamente. Selo de exemplo é derivado das fontes e congelado na identidade; exemplos ficam ocultos fora de development. Contexto inicialmente real não pode adotar uma referência fictícia nem publicar após a fonte passar a ser exemplo, mesmo em development; exige outro contexto identificado como exemplo. Conteúdo de testes continua exclusivamente fictício e revertido.

Nenhum contexto real ou análise causal foi cadastrado/revisado automaticamente nesta entrega. UI/primeiros contextos são DATA-05C; grafos e IA continuam futuros. Verificação e limites atuais em [VERIFICATION](../development/VERIFICATION.md).


## Interface e descoberta — DATA-05C

Leitura pública em `/contextos`, `/contextos/{id}` e `/contextos/{id}/versoes/{revision}`; rascunhos em `/painel/contextos`, `/novo`, `/{id}` e fila administrativa `/revisao`. Os indicadores oferecem contextos publicados e aviso quando a observação principal difere da corrente, sem prazo de validade causal inventado. O editor manual aceita salvamento incompleto, sem autosave ou armazenamento local do texto.

GET `/api/v1/contexts` agora filtra `indicator_code` pela observação principal da **última publicação**, assim como busca o título dessa publicação. O registro/versão/publicação selecionado na consulta é mantido na renderização; publicação concorrente não substitui o resultado pelo rascunho ou por outro filtro. GET autenticado `/api/v1/contexts/references/{code}` retorna opções salvas paginadas, uma revisão atual por período, com ancoragem e fonte. Revisão maior, depois coleta e UUID, desempata; não cai numa revisão antiga caso a atual esteja oculta/inválida. Não aceita fontes privadas de outro autor nem código auxiliar fora dos 14 principais revisados.

A interface distingue observado/projetado, descrição/associação/suporte e apoio/contestação/contexto. Checklist/rationale do revisor são zerados quando um registro é aplicado; navegação interna com conteúdo não salvo pede descarte explícito. Rascunho real preparado com [pesquisa documental](FIRST_CONTEXT_RESEARCH.md), marcado assistido por IA e sem revisão humana registrada. Só o exemplo fictício foi revisado/publicado automaticamente para QA local. DATA-05C ainda Preparado; sem grafos, chamadas a modelo ou efeito numérico adicional.
