# Página explicativa e explorador do grafo de causas

## Estado atual — 2026-10-23

O explorador público está implementado em `/grafos`, com WebGL 3D carregado sob demanda, inspeção de relações e lista equivalente. O catálogo local conferido tem zero mapas publicados; o exemplo didático contém 18 nós e 24 relações explicitamente fictícias. Não há geração automática de conexões a partir dos indicadores ou propostas.

Serviços desligados impedem o carregamento da API. Movimento reduzido, ausência de WebGL2, economia de dados ou capacidade limitada podem ativar a lista por decisão do cliente; isso é diferente de falta de mapas publicados. Diagnóstico e evidências atuais no [relatório do repositório](../project/REPOSITORY_AUDIT.md). Os pedidos e entregas datados abaixo são históricos.

## Pedido registrado — 2026-10-09

Quando começar a implementação dos grafos, entregar também uma página pública que explique como funcionam e permita explorar seus nós e conexões. Esta é uma exigência do mantenedor para a etapa futura, não uma implementação iniciada.

A referência visual enviada mostra uma rede de pontos ligados por linhas, formando grupos conectados entre si. Usar essa composição como inspiração para a rede interativa, adaptada à identidade visual já aprovada do BrasilPorTodos. Os pontos e linhas devem representar entidades e relações reais do grafo; a posição ou proximidade visual não constitui evidência causal. Não gerar ligações decorativas que possam ser interpretadas como relações documentadas.

## O que a página deve explicar

- Nós são as entidades: medidas, indicadores, mecanismos e grupos afetados.
- Arestas são relações documentadas entre dois nós, com direção, significado, fontes e condições.
- Mostrar um exemplo guiado que ensine a ler origem, destino e sentido da ligação.
- Distinguir efeito direto contábil, efeito indireto estimado e relação qualitativa.
- Explicar o que sustenta cada relação e onde a evidência acaba; uma conexão não garante que o efeito acontecerá nem fornece automaticamente uma estimativa numérica.
- Apresentar limites, premissas, revisão e incertezas em linguagem cotidiana. A referência anterior sobre arestas e curadoria permanece contexto para a futura especificação de domínio; não autoriza executar seus passos de implementação agora.

## Interação esperada

1. Ao selecionar um nó, abrir um painel com nome, tipo, explicação e conexões de entrada e saída. Destacar seus vizinhos na rede.
2. Ao selecionar uma aresta, mostrar origem e destino, sentido, tipo de efeito, prazo, premissas, evidências com links, contrapontos quando disponíveis, estado de revisão e histórico. Mostrar magnitude e unidade somente quando sustentadas por evidência; ausência deve ser explícita.
3. Permitir percorrer uma cadeia de relações e entender por que cada conexão existe, sem transformar automaticamente o percurso em soma de efeitos.
4. Oferecer busca, filtros, aproximação/afastamento, deslocamento da rede e retorno à visão inicial. Legenda explica pontos, linhas e direção; não depender apenas da cor.
5. Diferenciar relações documentadas de exemplos didáticos. Lacunas não viram linhas ou valores fictícios.

## Celular, acessibilidade e apresentação

Manter leitura pública sem login e a identidade visual aprovada. No celular, nós e arestas selecionados precisam de controles fáceis de tocar e painel de detalhes adequado à tela; evitar exigir precisão sobre uma linha muito fina. Oferecer também uma lista navegável de conexões, com acesso por teclado, equivalente à exploração visual.

Respeitar temas claro/escuro, contraste e preferência por movimento reduzido. Movimento da rede não deve impedir leitura ou seleção. Definir limites de quantidade de elementos e desempenho a partir do grafo real, antes de escolher uma biblioteca. A imagem é referência de composição, não uma decisão de tecnologia ou autorização para mudar a UX atual.

## Critérios de aceite

- Página pública com explicação, legenda e exemplo guiado, acessível a partir da metodologia ou navegação do grafo.
- Nós e arestas selecionáveis, com significado e evidências consultáveis.
- Busca/filtros e navegação das conexões de um nó, com direção verificável.
- Tratamento explícito de lacunas, ausência de estimativa, carregamento e erros.
- Experiência funcional em celular e desktop, por teclado e com alternativa em lista.
- Privacidade de rascunhos preservada; políticas de publicação/revisão definidas antes de expor dados do grafo.
- Nenhum efeito numérico inserido no motor fiscal apenas por existir uma ligação visual.

GRAPH-01 está **Preparado**: o contrato puro GRAPH-01A foi entregue em 2026-10-14. A primeira interface continua futura, com esta página explicativa obrigatória e explorador/lista equivalente. Rota e tecnologia visual serão definidas com o conjunto real; não houve mudança de UX nesta fatia. [Contrato](../data/GRAPH_CONTRACT.md) · [Backlog](../project/BACKLOG.md).


## Contrato iniciado — 2026-10-14

GRAPH-01A define nós e arestas versionados, sentido do aumento/adoção da origem, fontes/contrapontos e revisão declarada, além de diagnósticos de duplicatas/conflitos/ciclos. Não inclui consulta pública, curadoria persistida, magnitude ou propagação de efeitos. B resolve autorização/persistência/publicação; C entrega a primeira tela do grafo com esta explicação. O contexto real de desemprego ainda aguarda pessoa revisora, e FGTS continua caso de pesquisa futura do grafo, sem seed de afirmações não conferidas.

## Interface entregue — GRAPH-01C, 2026-10-15

Rota `/grafos`, detalhe por UUID e versão preservada. Perspectiva 3D por projeção matemática em SVG, sem biblioteca pesada ou dependência de WebGL; visão plana e lista dão acesso ao mesmo conteúdo. Arrastar gira, modo Mover desloca, controles aproximam/restauram e teclado usa setas, +/− e Home. Giro automático é opcional e pausa na seleção; movimento reduzido desliga animações. No celular, detalhe segue abaixo da rede e ganha foco quando aberto; ao fechar, o foco volta à rede.

Há quatro formas/tipos, busca com debounce, filtros que preservam pontas necessárias, vizinhos e ligações de entrada/saída, fontes/justificativas/contrapontos, estado da publicação e histórico. O percurso mostra nós visitados, sem alegar cadeia causal válida. Posição, tamanho e distância não são magnitude/importância/certeza. Limite de 200 nós/400 arestas com rejeição explícita, sem corte silencioso; algoritmo de layout separado e limitado. Rótulos compactos não substituem nomes completos no inspector/lista.

Guia público em três passos em `#como-funciona`, com significado dos pontos, sentido do aumento/adoção, evidência e limites; acessos pela navegação, rodapé e Metodologia. Catálogo vazio confirmado pode abrir uma demonstração destacada de 18 nós/24 ligações, toda fictícia e local, sem fonte real, revisão ou publicação simulada no banco. Erro de API/versão solicitada mostra erro/recuperação; não é substituído automaticamente pelo exemplo. Leitura real usa apenas publicações e a revisão exata congelada de cada relação.

Primeiro conteúdo real FGTS continua sem seed ou aprovação fabricada. Pesquisa humana e termos continuam pendentes antes da primeira rede real; dimensão numérica e IA são contratos D/E separados. C entrega a interface qualitativa, sem converter conexão em resultado fiscal. [Evidências](../development/VERIFICATION.md).

## Refinamento WebGL — 2026-10-18

A implementação visual anterior foi substituída, por pedido do mantenedor, por Three.js 0.186.1/OrbitControls com WebGL real. A biblioteca é importada em um componente cliente dinâmico, sem SSR, somente quando o palco se aproxima da tela e as capacidades permitem. Nenhum texto do guia, contrato, conteúdo de demonstração, regra de revisão ou rota mudou.

- Coordenadas da simulação visual determinística são pré-calculadas e mantidas em cache limitado; não há física contínua. Esferas têm o mesmo tamanho. Cor identifica tipo: medida/amarelo, indicador/verde, mecanismo/azul claro e grupo/branco, usando tokens existentes.
- Câmera interpola posição/alvo em 1.050 ms com easing; seleção enquadra nó/vizinhos ou pontas da relação, compensando o espaço do painel. Clique no vazio, Escape e Ver tudo restauram a rede. Duplo clique mergulha um nível; expansão acrescenta um nível visual, sem alterar arestas.
- Nós/setas usam instâncias e linhas são agrupadas por consenso. Contínua/debatida/especulativa correspondem a linha contínua/tracejada/pontilhada, inclusive no destaque. Setas/partículas indicam origem e destino; sentido incerto recebe `?`. Nada disso quantifica efeito ou valida a alegação.
- Sprites encaram a câmera, priorizam seleção/vizinhos e passam por empacotamento de retângulos na tela. Textos secundários podem ser omitidos quando falta espaço; nomes completos e relações permanecem no painel e na lista. Essa limitação não elimina dados.
- Painel sobreposto lateral no desktop, folha inferior no celular, cabeçalho fora do scroll e conteúdo rolável. A posição acompanha a área visível da página. O modo imersivo mantém o aviso fictício e o aviso de neutralidade dentro do mapa.
- Teclado percorre nós por nome; Enter seleciona, setas chegam a vizinhos, Escape restaura; região viva anuncia seleção/conexões. Lista preserva toda a leitura. Movimento reduzido, WebGL indisponível, economia de dados, até 2 GB/2 núcleos declarados ou falha do módulo/contexto ativam a Lista com explicação. Ausência de informação de hardware não é interpretada como incapacidade.
- Dicas iniciais dispensáveis guardam somente essa preferência em localStorage. Renderização pausa fora da tela/aba oculta, DPR é limitado a 1,5 e montagem libera observadores, eventos, controles, geometrias, materiais, texturas, instâncias e contexto.

O teste [WebGL isolado](../../frontend/tests/webgl/README.md) usa 200 nós/500 arestas sintéticos somente na fábrica de renderização. O contrato público continua em **200 nós/400 arestas**, sem alteração no backend. O exemplo do site conserva exatamente 18 nós/24 relações. Peso lazy medido: 598.026 bytes sem compressão / 148.729 bytes gzip local, incluindo JS e CSS; o manifesto lazy da Home permanece vazio. Não é uma medição de transferência real nem do delta de toda a rota.

Implementação funcional entregue; permanecem validação de toque/pinça em hardware móvel, leitor de tela e medição contínua de 60 fps em dispositivos representativos. O navegador de verificação limitou animações em segundo plano; uma amostra rápida não encerra esse aceite. Primeiro grafo real e quantificação/IA continuam pendentes. [Verificação](../development/VERIFICATION.md).

## Continuação de qualidade — 2026-10-18

Escape sem painel aberto conserva o foco da busca. Navegação por teclado no celular traz o palco imediatamente à área útil; fechamento continua devolvendo o foco. Um gesto que se afasta mais de 8 px não vira toque mesmo voltando ao início; sobreposição de dedos impede seleção até todos serem liberados, inclusive após cancelamento. São proteções de interação, sem alterar relações.

Relação incerta selecionada para de redesenhar após o voo quando não há giro ou outra animação visível. O teste isolado passa a contar chamadas reais de desenho e invalida automaticamente capturas interrompidas; cadência não equivale à conclusão GPU ou à validação de aparelhos. As pendências de qualidade física e leitor de tela continuam no backlog.

## Como levar um mapa real à publicação — 2026-10-25

“Publicados 0” significa ausência de coleções reais publicadas; a demonstração é inventada. O aviso de 3D indisponível é outro assunto: o navegador não disponibilizou o contexto gráfico ou houve falha de inicialização. Sem diagnóstico do dispositivo, não atribuir automaticamente à GPU, ao Docker ou à falta de revisão. A lista permite a mesma consulta das conexões.

Hoje a **curadoria privada de grafos existe pela API**, sem formulário privado pronto. Falta construir essa tela com fila de revisão, ações por papel e erros claros; está registrada no GRAPH-01. A página `/grafos` é o explorador público, não a ferramenta de revisão. A documentação interativa local da API fica em `http://localhost:8000/docs`; não é necessário inventar/aprovar conteúdo para preencher o mapa.

Fluxo efetivo:

1. O autor pesquisa um recorte pequeno e cria nós/relações privadas. Cada relação precisa de enunciado, sentido, condições, fontes verificáveis, contrapontos e limitações; “fonte pendente” não é evidência. Usar versões exatas dos vínculos.
2. **Outro ADMIN ativo, diferente do autor**, revisa a versão: confere afirmação/escopo, documento e trecho de suporte, contrapontos e limitações. Registra justificativa e decisão (aceitar, pedir mudanças, contestar ou rejeitar) e as verificações exigidas. Uma revisão de versão antiga não aprova a nova.
3. O autor publica explicitamente a relação na revisão esperada e estado permitido pelo contrato, REVIEWED ou DISPUTED; discordância não vira consenso silenciosamente.
4. O autor monta a coleção com versões públicas das relações e publica o mapa. Só então ele aparece em “Publicados”. Editar depois não reescreve publicações anteriores.

Rotas de curadoria sob `/api/v1/graphs`: `/nodes`, `/edges`, `/edges/review-queue`, `/edges/{id}/review`, `/edges/{id}/publish`, criação da coleção e `/{id}/publish`. Ações validam sessão, autoria, role e revisão no backend; não basta mudar um botão na interface. Ver [contrato](../data/GRAPH_CONTRACT.md) e [permissões](../architecture/AUTHENTICATION.md).

Para **contextos explicativos** já há interface distinta: `/painel/contextos` (autor) e `/painel/contextos/revisao` (outro ADMIN). Revisar/publicar um contexto não publica automaticamente um grafo. O primeiro rascunho pesquisado ainda precisa de revisão humana; nenhuma conta foi promovida, revisão registrada ou pesquisa real publicada automaticamente nesta entrega.
