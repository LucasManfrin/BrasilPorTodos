# Auditoria do repositório — 2026-10-23

## Parecer

A V1 local está alinhada à proposta: compreender dados, transformar ideias em propostas e comparar planos com custos, fontes e histórico preservados. O monorepo e o monólito modular atendem esse recorte; não há necessidade demonstrada de reescrever a arquitetura ou acrescentar serviços.

O código pode ser organizado para colaboração pública, mas **há alerta crítico de dependência a resolver antes de expor o serviço à internet**. Publicar o código e operar uma plataforma com cadastro público são entregas distintas. Esta auditoria não conclui todo o roadmap nem valida eficácia de propostas.

## Arquivos sem uso e organização

Removidos após busca de referências:

- O antigo `IndicatorCard`, substituído pelos componentes de `features/data-explorer`. O gráfico `Sparkline` era usado pelo detalhe de indicador e foi preservado em [sparkline.tsx](../../frontend/src/components/sparkline.tsx); o import do `IndicatorChart` foi atualizado.
- Estilos exclusivos desse card em `internal.css`, preservando os estilos do gráfico e do método usados na tela de detalhe.
- Onze `.gitkeep` vazios: migrations, public, components, lib, auth e seis pastas de features que ficaram apenas como estrutura inicial. As implementações atuais permanecem nas features efetivamente utilizadas.

Não foi identificado documento inteiro que devesse ser descartado com segurança. Pesquisas, contratos, decisões, licenças, migrations, testes, fixtures, lockfiles e harness WebGL foram preservados. Dois helpers com uso apenas em testes (`positivePage` e `scenarioAmountState`) foram mantidos; eliminá-los não traz benefício relevante nesta entrega.

O antigo STATUS foi preservado integralmente em [STATUS_HISTORY](STATUS_HISTORY.md); [STATUS](STATUS.md) passa a resumir a situação atual. Corrigidas referências antigas ao card, índices de módulos/features, prompt da IA, configuração real do Gemini e preparação para publicação. Não se deve interpretar registros datados como operação atual.

`.gitignore` também exclui bancos, backups e arquivos de chaves. Ambientes, logs, caches, credenciais e dados locais continuam fora do versionamento. A inspeção de candidatos não apontou correspondências com segredos locais nem padrões comuns de tokens/chaves privadas. É uma verificação limitada, não garantia de ausência de vulnerabilidades ou segredos.

## Por que os grafos pareciam não funcionar

Foram separados três casos:

1. **Serviços desligados:** no início da auditoria, Docker não estava disponível e as portas 3000/8000 recusavam conexão. Docker Desktop e o Compose existente foram iniciados, sem apagar volumes, sem semear ou publicar conteúdo. Depois disso, site e API responderam HTTP 200.
2. **Nenhum mapa real publicado:** `/api/v1/graphs`, `/graphs/nodes` e `/graphs/edges` responderam com `total: 0`. O catálogo público mostra versões publicadas e relações revisadas, não rascunhos privados. Dados de Brasil Atual e propostas não geram conexões automaticamente. O primeiro mapa real ainda exige pesquisa, revisão por outra pessoa autorizada e publicação. Existe API de curadoria; falta uma interface privada específica para esse trabalho.
3. **Alternativa em lista:** o cliente escolhe Lista quando há preferência por movimento reduzido, WebGL2 indisponível, economia de dados, capacidade limitada ou falha do renderer. Isso está implementado em [scene.tsx](../../frontend/src/features/graphs/scene.tsx) e [spatial.ts](../../frontend/src/features/graphs/spatial.ts). Não foi constatado que o navegador pessoal do mantenedor esteja nessa condição.

**Resultado observado:** no navegador de teste, o exemplo WebGL renderizou 18 nós e 24 relações; selecionar um nó por teclado abriu seus detalhes e conexões. Não foi reproduzido defeito no renderer nesta checagem. O exemplo é fictício e não constitui um mapa causal real. Catálogo vazio confirmado carrega o exemplo; falha da API mantém erro e permite abrir o exemplo explicitamente. Uma versão pública solicitada nunca é substituída silenciosamente por demonstração.

A API pública não apresenta relações privadas só para preencher a tela. Faltam conteúdo real revisado e operação ativa; magnitudes causais e IA de curadoria são trabalhos separados (GRAPH-01D/E).

## Pendências e pontos de atenção

| Prioridade | Evidência | Ação proporcional |
| --- | --- | --- |
| Crítica antes de exposição pública | `npm audit --omit=dev` apontou uma dependência com severidade crítica: Next.js 16.4.0. O build também encerrou com alerta de segurança, embora tenha compilado e gerado as rotas. | Atualizar Next.js para uma versão corrigida compatível, revisar o lockfile, repetir auditoria/build/testes e reconstruir a imagem. Não afirmar que o build está aprovado. |
| Alta para atualidade dos dados | Última coleta salva consultada em 23/10: 14/10/2026, `PARTIAL`, com falhas em seis séries IBGE e preservação dos históricos anteriores. Compose não executa um coletor contínuo. | Diagnosticar as falhas externas e retomar a coleta controlada; supervisionar sua execução quando for exigida atualização contínua. Não confundir data de acesso à página com data do dado. |
| Alta para conteúdo real | Catálogo público do grafo vazio; primeiro contexto pesquisado e primeiro mapa real ainda dependem de revisão humana. | Concluir pesquisa e revisão/publicação. Começar com um mapa pequeno e defensável; não preencher com relações inventadas. |
| Antes de ampliar o modo IA | Prompt 4.0.0 e confirmação humana implementados; avaliação sistemática real UI-06C/F permanece preparada. | Comparar casos equivalentes de posições opostas, registrar modelo/prompt/resultados e verificar preservação de intenção. Não restaurar bloqueios semânticos removidos por decisão do mantenedor. |
| Antes de vários usuários públicos | Limites de autenticação usam `request.client.host`; proxy Next não transmite uma identidade de cliente confiável. Usuários via proxy podem compartilhar um bucket de limite. | Definir e testar contrato de proxy confiável (F2-02); não aceitar livremente um cabeçalho de IP informado pelo cliente. |
| Antes de lançamento público | Termos/privacidade ainda são proposta; faltam canais, HTTPS/cookies seguros, supervisão, política de backup e restauração no ambiente final. | Concluir gates de lançamento já registrados, sem tratar Compose local como produção pública. Conferir se credenciais anteriormente compartilhadas fora do `.env` ainda precisam de rotação. |
| Qualidade e colaboração | CI preparada, ainda sem execução remota/proteção de branch; faltam auditoria aprofundada de acessibilidade e testes em GPU/toque representativos. | Executar CI após o push autorizado e conferir um fluxo principal automatizado no navegador; manter alternativa em lista e revisão com leitor de tela. |

Os alertas do registro npm abrangem otimização de imagem com SVG, Server Actions e `use cache` com typed arrays. A auditoria local de dependências não demonstra exploração nem comprova quais caminhos vulneráveis são alcançáveis nesta configuração. Referências retornadas pelo registro: [GHSA-2464-fhr4-w9xw](https://github.com/advisories/GHSA-2464-fhr4-w9xw), [GHSA-p3m5-59mp-jv5r](https://github.com/advisories/GHSA-p3m5-59mp-jv5r), [GHSA-673q-mjm6-r5xr](https://github.com/advisories/GHSA-673q-mjm6-r5xr). Não foi feita atualização de dependências nesta revisão de inventário e commits.

Logs de IA têm expiração e limpeza implementadas. O processo só executa enquanto o computador/serviço está ativo; backups possuem retenção própria. A IA não faz cálculo fiscal nem comprova fatos. O saldo do motor é incremental; não é previsão do Brasil ou efeito causal calculado pelo desenho da rede.

## Melhorias que valem a pena

1. Resolver a dependência de segurança e a atualização dos dados antes de adicionar funcionalidades.
2. Publicar um primeiro mapa/contexto bem documentado; depois, se necessário, oferecer uma tela simples de curadoria sobre a API existente.
3. Automatizar uma regressão curta de criar ideia → preparar completa → publicar → incluir em plano, preservando versões anteriores.
4. Manter STATUS curto e histórico separado; seguir o backlog existente e fazer commits locais pequenos a cada entrega verificada.

Não há recomendação de novos microsserviços, banco de grafos, fila externa ou troca de stack para a V1 local.

## Verificações desta auditoria

- Backend: **1.410 testes passaram**, incluindo integrações em PostgreSQL temporário exclusivo; migrations aplicadas até o head antes dos testes. O banco temporário foi removido ao final; o volume local foi preservado.
- Frontend: **320 testes passaram**, ESLint e TypeScript passaram. Os 68 testes específicos de grafos também passaram na investigação.
- Ruff: check passou; 188 arquivos atendem à formatação. A checagem de whitespace do Git passou excluindo migrations e licenças tipográficas, cujos espaços históricos em SQL/textos de terceiros foram preservados; linha vazia final de um componente autoral foi normalizada.
- Build: compilação/TypeScript/geração das rotas concluídos, mas o comando terminou com código 1 devido ao alerta de segurança. **Build não aprovado** até resolver a dependência e repetir o check.
- npm: uma dependência de produção com severidade crítica; não representa análise completa de todas as dependências Python nem teste de intrusão.
- Navegador: exemplo 3D e seleção de nó conferidos; em 360/768/1280/1920 px, largura do documento igual à área útil, sem overflow horizontal. Isso não substitui teste em celular físico, leitor de tela ou benchmark representativo.
- API/site: rotas públicas do grafo HTTP 200, três catálogos vazios confirmados; nenhuma curadoria real criada/publicada, nenhuma coleta forçada e nenhuma chamada real de IA nesta auditoria.

## Git e alcance da entrega

O repositório já tinha `.git`, branch `main`, sem commits ou remoto. O snapshot inicial foi registrado no commit `d1bee6f`: 476 arquivos, branch `main`, após a revisão dos arquivos. O commit seguinte registra o fechamento documental desta auditoria. A árvore estava limpa após o snapshot inicial; nenhum arquivo privado/local foi incluído. `.env`, `.local`, bancos, backups e payloads privados não devem entrar nos commits. O mantenedor escolherá o remoto; nenhum push, publicação de código ou abertura de serviço foi realizado.

As pendências acima continuam no [BACKLOG](BACKLOG.md). A V1 local é uma base funcional para o case acadêmico; ela não deve ser apresentada como serviço público finalizado, catálogo causal real ou modelo de previsão nacional.
