# Contrato do grafo — GRAPH-01A/B

## Estado

Contrato puro `1.0.0` entregue em 2026-10-14, em `backend/app/modules/graphs/graph.py`. Define versões de nós e relações, referências congeladas, correspondência de revisão declarada e diagnósticos de topologia. GRAPH-01B acrescenta persistência e API de curadoria na mesma data, com referências reais resolvidas, revisão administrativa distinta e publicação explícita. GRAPH-01C entrega a interface de leitura em 2026-10-15, com perspectiva 3D/lista e explicação pública; coletor, IA e motor fiscal permanecem separados. A rede pública interativa e sua página explicativa continuam requisitos de [GRAPH-01](../product/GRAPH_EXPLORER.md).

A preparação técnica do grafo pode avançar enquanto o primeiro contexto real aguarda conferência humana. Ela não revisa, publica ou promove esse rascunho. DATA-05C permanece Preparado; [pesquisa pendente](FIRST_CONTEXT_RESEARCH.md).

## Nós, arestas e fotografia do conjunto

Modelos Pydantic estritos e imutáveis, tuplas limitadas e campos desconhecidos recusados. Funções de hash, avaliação e topologia revalidam os dados, inclusive objetos montados sem validação. Referências continuam declaradas: um UUID ou código nesta biblioteca não comprova existência, autoria, permissão ou visibilidade.

| Objeto | Conteúdo | Limite e responsabilidade |
| --- | --- | --- |
| `GraphNodeVersion` | Slug estável, revisão, tipo, nome, definição, dimensão e unidade quando conhecida | Indicador exige código; medida exige ID/número da versão da proposta. Mecanismo/grupo não herdam referências desses tipos. Serviço B confere existência e visibilidade |
| `GraphEdgeDraft` | Slug/revisão/autor/UTC, nós de origem e destino completos, enunciado, gatilho, sentido, prazo, efeito/consenso declarados, autoria humana/assistida, evidências, recorte, premissas, contrapontos, limites e lacunas | Uma relação precisa de fonte/evidência vinculadas para existir. Continua rascunho; preencher campos não a torna verdadeira ou pública |
| `GraphSnapshot` | Identidade/revisão/autoria/data/título e versões exatas dos nós/arestas | Até 200 nós e 400 arestas; somente uma revisão por identidade. Cada nó embutido numa aresta coincide integralmente com a versão selecionada |
| `EdgeReview` | Aresta/revisão/hash, revisor/UTC, decisão/justificativa e conferências | Registro declarado, sem autenticação ou poder de publicação |

Nós representam conceitos ou medidas, não uma observação estatística atualizada automaticamente. Um grupo precisa de uma dimensão clara, como uma condição de acesso, em vez de simplesmente apontar para pessoas e dizer que elas aumentam/diminuem. Não inferir unidade quando ausente. Versão de proposta é uma referência exata, sem buscar implicitamente a mais recente.

A revisão de um nó exige nova versão; adotá-la exige revisar a aresta que o usa. Uma nova revisão da aresta não reescreve fotografias anteriores. O conjunto pode preservar nós isolados: uma lacuna de conhecimento não vira uma linha inventada.

## Como ler a direção

O sentido descreve o efeito **alegado de aumentar a dimensão de origem**, mantidas as premissas, sobre a dimensão de destino: `INCREASES`, `DECREASES` ou `UNCERTAIN`. Para medida, o gatilho é `ADOPTION`, a adoção da medida descrita; demais tipos usam `INCREASE`.

Não inverter o sinal quando a narrativa fala de redução na origem. Se uma hipótese diz que menos recursos podem acompanhar menos oferta, a relação entre aumentar recursos e oferta não deve ser cadastrada automaticamente como “reduz”. É necessário formular a alegação, conferir o contexto e pesquisar a evidência antes de registrar qualquer relação real. Isto é uma regra de leitura, não uma afirmação sobre o FGTS ou uma política.

Prazo curto/médio/longo e recorte/período são declarações textuais, sem duração numérica inferida. `ACCOUNTING_DIRECT`, `INDIRECT_ESTIMATE` e `QUALITATIVE` classificam o uso pretendido; consolidado/debatido/especulativo são classificações autorais. Nenhum desses rótulos transforma evidência em coeficiente, certeza ou previsão. Esta versão não aceita magnitude, probabilidade, elasticidade ou impacto numérico, nem mesmo com um rótulo de efeito direto.

## Evidências e contrapontos

Reutilizar `SourceReference`, `Evidence` e `EvidenceLink` de [contextos](CONTEXT_EVIDENCE.md). Cada aresta possui até 32 fontes e 64 evidências/vínculos, com IDs únicos, sem referências órfãs ou fontes/evidências sem uso. Fontes preservam título/instituição/URL/termos/data; evidências preservam afirmação, trecho, localização, recorte/período e limites. `SUPPORTS`, `CHALLENGES` e `CONTEXT` distinguem sustentação, contestação e contexto.

Para ficar estruturalmente pronta à conferência, a aresta precisa de apoio declarado, premissas, limites e lacunas. Evidência somente contrária ou contextual não sustenta a relação. `CounterpointStatus` distingue `NOT_RESEARCHED`, `NOT_FOUND` e `DOCUMENTED`. Contestação vinculada e `DOCUMENTED` precisam corresponder; não pode declarar “não encontrado” mantendo uma contestação vinculada. Consolidado/debatido com `NOT_RESEARCHED` fica incompleto. Sem contestação documentada, exige `NOT_FOUND` com nota explícita, notas de busca e data UTC; “não procurei” não atende esse caminho. A biblioteca não fabrica a frase “não encontrado”, não executa busca e não comprova a suficiência de uma pesquisa declarada. Data de busca posterior à edição/avaliação é pendência temporal.

URLs HTTP/HTTPS são metadados, com formatos inseguros e credenciais recusados pelo contrato comum. A biblioteca não visita links nem confere o trecho contra um documento obtido. Essa verificação terá um serviço próprio, com material obtido por canais autorizados, termos, limites e rastreabilidade; URL contribuída não autoriza fetch arbitrário ou upload na V1.

O mesmo UUID de fonte pode aparecer com consultas/metadados diferentes em arestas históricas. `SourceReference` identifica o cadastro, não uma revisão global imutável. Preservar cada fotografia por aresta, sem uniformizar pelo cadastro atual. A exigência de conteúdo idêntico para um nó de mesma identidade/revisão é diferente.

## Hash e revisão

`edge_fingerprint` calcula SHA-256 do JSON canônico completo da aresta validada, incluindo nós embutidos, revisões, fontes/termos, trechos, relações, autoria, datas e limites. `graph_fingerprint` inclui o conjunto completo. Ordem das coleções integra o conteúdo; normalização de espaços nas bordas e fuso UTC seguem o contrato comum. A revisão tem alvo próprio de aresta, não apenas o hash do conjunto.

`assess_edge` recebe `assessed_at` explícito. Falta de conteúdo e incoerência temporal (edição futura, consulta posterior à edição, publicação da fonte posterior à consulta) tornam a relação incompleta. A avaliação não completa campos nem transforma ausência em zero.

| Estado | Interpretação |
| --- | --- |
| `INCOMPLETE` | Pendências estruturais/de conteúdo ou tempo |
| `NEEDS_REVIEW` | Registro de revisão ausente ou conferências incompletas |
| `REVIEW_STALE` | Alvo/hash/revisão/tempo/revisor não correspondem |
| `CHANGES_REQUESTED` | Pedido correspondente de alterações |
| `DISPUTE_MATCHES` | Registro correspondente declara disputa |
| `REJECTION_MATCHES` | Registro correspondente declara rejeição |
| `REVIEW_MATCHES` | Aceitação declarada corresponde ao conteúdo e às conferências |

Revisor deve ser diferente do autor, e o registro deve estar entre a edição e a avaliação. Humano e assistido por IA exigem o mesmo registro de conferência; autoria assistida não salta a revisão. Ainda assim, **nenhum desses estados autoriza publicar**, autentica uma pessoa ou prova causalidade. A camada confiável B atribui identidade/data, confere sessão/autor/revisor ativo, resolve permissões e versões reais, preserva revisões e publica em transação. Não aceitar flags de status, hash ou revisor enviados pelo cliente como autorização.

“Em disputa aparece” não é uma flag que exponha rascunho. A política B permite `DISPUTED` somente após a última revisão distinta declarar `DISPUTE`, com checklist completo, seguida de publicação explícita pelo autor. Aceitação permite `REVIEWED`; nenhum dos estados é selo de verdade. Rejeição não publica nada. Nenhuma alteração deve reescrever silenciosamente uma publicação anterior.

## Duplicatas, conflitos e ciclos

`inspect_topology` produz diagnóstico determinístico sobre a fotografia validada:

- Duplicatas candidatas: mesma origem/destino/sentido/recorte/período. Normalizar espaços e caixa não resolve equivalência semântica; condições diferentes precisam de conferência humana.
- Direções opostas: aumento e redução declarados para o mesmo par/recorte/período. Não escolher uma narrativa automaticamente ou apagar a outra.
- Componentes com ciclos: diagnóstico estritamente estrutural que ignora recorte/período e pode reunir países ou tempos distintos. Não demonstra uma realimentação econômica válida. Registrar e expor esse limite, sem percorrer infinitamente nem somar efeitos. Autoaresta é recusada nesta versão.
- Nós isolados: visíveis como lacuna, sem inferir que o mundo real não tem outros efeitos.

Limites de tamanho são estruturais; a travessia é iterativa. Não representam benchmark nem justificam escalar a rede pública sem teste. O diagnóstico não é um detector de dupla contagem causal e não autoriza cálculo em cadeia.

## O que segue no roadmap

GRAPH-01B entregue: resolução real/autorização e persistência/versionamento/revisão/publicação, preservando cada alvo e conteúdo. GRAPH-01C entregue em 2026-10-15: página explicativa pública e explorador interativo/lista equivalente, nós/arestas/fontes/estados, busca/filtros/zoom/deslocamento, celular/teclado e desempenho. A página é parte obrigatória da primeira interface do grafo.

GRAPH-01D: contrato próprio para magnitude em faixa, Decimal/strings, unidade/base/condições, trecho literal verificado e revisão efetiva, antes de qualquer uso quantitativo. Depois, integração numérica exige método separado de composição, recortes e prevenção de dupla contagem/ciclos; não está autorizada por existir uma aresta. GRAPH-01E: interface trocável de curadoria assistida, roteiro/verificação documental, busca de contrapontos, logs protegidos, orçamento/limites e chave em ambiente; sem publicação pelo modelo.

Primeiro caso de pesquisa do grafo solicitado pelo mantenedor: FGTS. Ainda não há seed real, relação aceita ou pesquisa específica concluída para ele. Recursos do fundo, crédito, proteção, renda/risco e grupos afetados são perguntas de pesquisa a conferir, não conclusões desta entrega. “Fonte pendente” continua no backlog de pesquisa; não criar uma aresta sem fonte para preencher a rede.

[Backlog e evidências](../project/BACKLOG.md) · [Verificação](../development/VERIFICATION.md) · [Decisões](../architecture/DECISIONS.md).

## Curadoria confiável — GRAPH-01B

Autor ativo cria/salva/publica seus registros; administrador ativo distinto revisa arestas, inclusive quando o autor também é administrador. Admin lê rascunhos para revisão, mas não edita/publica conteúdo alheio nem reutiliza referências privadas de terceiros. UUID, revisão, autor, datas, hash e estado de exemplo são atribuídos/resolvidos pelo servidor; campos gerenciados enviados pelo cliente são recusados.

INDICATOR resolve um código ativo do catálogo oficial e sua unidade; definição/dimensão do nó continuam autorais. MEASURE resolve uma versão já publicada da proposta, preservando o número exato. Fontes são resolvidas por ID, próprias ou já públicas; coincidência de URL não concede acesso. A publicação divulga a fotografia da fonte dentro da aresta, sem promover seu cadastro privado ao diretório público. Nenhum link contribuído é visitado.

Cada salvamento acrescenta versão; `expected_revision` obrigatório em edição/revisão/publicação impede sobrescrita concorrente. `ACCEPT` e `DISPUTE` exigem estrutura pronta e quatro conferências verdadeiras. Última decisão `REQUEST_CHANGES` ou `REJECT` bloqueia publicação; nova versão não herda revisão. Publicar revalida referências/metadados e elegibilidade do revisor; mudança exige nova versão/revisão, sem substituir dados congelados. Revisar não publica. Uma publicação anterior permanece legível após mudança de cargo do revisor ou de metadados do cadastro.

Coleção seleciona versões exatas e publica somente relações já publicadas; conserva a revisão/estado público original de cada uma, inclusive relações históricas. Todo nó selecionado, mesmo isolado, precisa de uma publicação prévia como ponta de alguma aresta. Coleção real exige testemunha de aresta real, inclusive em development. Exemplos derivam das referências, ficam ocultos fora de development e não podem ser incorporados a identidades reais. Um conjunto novo não exige outra aceitação de todas as relações, pois elas já passaram pelo fluxo de curadoria; nenhum conjunto publica rascunhos implicitamente.

Nove tabelas append-only e gates SQL protegem identidade, sequência, FKs/alvos, checklist, autoria e dependências públicas. Locks serializam gravações por identidade e conferem usuários/referências; mutação e montagem da resposta ficam na mesma transação, com rollback em falha. O banco não reimplementa toda validação Pydantic, cálculo canônico SHA-256 ou elegibilidade dos catálogos: esses controles pertencem ao serviço, que é a fronteira de escrita autorizada. SQL direto privilegiado não é uma API de curadoria.

## API para a futura interface

Prefixo `/api/v1/graphs`. IDs da API e `version_id` são UUIDs persistidos; slugs `node-…`/`edge-…` pertencem ao payload puro, não às rotas. Para referências, sempre enviar `version_id` exato, não procurar a versão mais recente implicitamente.

| Recurso | Rotas relativas | Acesso |
| --- | --- | --- |
| Nós | `GET/POST /nodes`, `GET /nodes/mine`, `PUT/PATCH /nodes/{id}`, `GET /nodes/{id}/draft` | Lista pública só de versões com publicação; criação/edição próprias; rascunho autor/admin |
| Relações | `GET/POST /edges`, `GET /edges/mine`, `GET /edges/review-queue`, `PUT/PATCH /edges/{id}`, `GET /edges/{id}/draft`, `POST /edges/{id}/review`, `POST /edges/{id}/publish` | Revisão por outro admin; publicação pelo autor |
| Conjuntos | `GET/POST` no prefixo, `GET /mine`, `PUT/PATCH /{id}`, `GET /{id}/draft`, `POST /{id}/publish` | Autoria e dependências publicadas |
| Detalhe/histórico | `GET` no ID, no ID + `/versions` ou `/versions/{revision}` para cada recurso | Só publicações, nunca revisão privada mais recente |

Criação/edição recebe `content`; edição acrescenta `expected_revision`. Nó recebe tipo/nome/definição/dimensão e referências próprias do tipo. Aresta recebe `from_node_version_id`, `to_node_version_id`, `source_ids` e campos autorais/evidências do contrato puro; fotografias são montadas pelo servidor. Coleção recebe `title`, `node_version_ids`, `edge_version_ids`. Revisão recebe `expected_revision`, `decision`, `rationale` e quatro checklists booleanos; publicação de relação recebe também `publication_state` (`REVIEWED` ou `DISPUTED`), e de coleção somente `expected_revision`. Esquemas completos estão no OpenAPI e em `graphs/schemas.py`.

Respostas de detalhe usam `{data: registro}`; listas usam `{data: [], pagination: {page, page_size, total}}`, com página de 1 a 100 itens e busca `q` de até 120 caracteres. Lista retorna apenas `id`, `revision`, `version_id`, `content_hash`, `published_at`, `is_example` e `content` resumido (`label`, `statement` ou `title`); aresta acrescenta `publication_state`. Projeção SQL evita carregar snapshots/evidências completos por linha. Histórico também projeta metadados/título; detalhe, versão e rascunho retornam conteúdo completo. Detalhe de aresta acrescenta `assessment`, `review` e `publication_state`; conjunto acrescenta `topology` e metadados congelados das publicações selecionadas.

Tamanhos máximos do JSON canônico UTF-8 na gravação: nó 32 KiB, aresta 1 MiB, conjunto 4 MiB, além dos 200 nós/400 relações e limites de campos. Não são benchmark de carga; histórico e filas exigirão avaliação operacional antes da abertura pública. Ausência de sessão gera 401; autoria indevida 403; referência indisponível/não pública 404; revisão concorrente/referência alterada 409; incompletude, disputa sem confirmação correspondente ou limite excedido 422. As regras de privacidade também valem para fontes com URLs idênticas.

B não entregou rede visual; C acrescentou leitura em perspectiva/lista, explicação, disputa e histórico. Não há publicação real do FGTS, análise numérica ou aprovação humana simulada do contexto de desemprego. [Verificação](../development/VERIFICATION.md).
