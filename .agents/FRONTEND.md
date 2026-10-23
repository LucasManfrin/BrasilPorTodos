# Agente frontend

Leia [instruções comuns](../AGENTS.md), [instruções do frontend](../frontend/AGENTS.md), [design](../docs/design/DESIGN.md), [exploração de dados](../docs/design/DATA_EXPLORER.md) e [arquitetura](../docs/architecture/ARCHITECTURE.md).

Escopo: `frontend/src/app`, features, components, lib e testes frontend. Next.js/TypeScript/App Router; CSS nativo/tokens existentes, fontes via next/font. Leia a documentação da versão instalada quando mexer em APIs do framework. Reutilize componentes antes de criar variantes; preserve as telas aprovadas fora do pedido. Não adicionar dependência pesada sem necessidade concreta.

Interface em português simples, cores nacionais/tokens, neutralidade e distinção entre dados e ilustração. Aritmética monetária final sobre Decimal/string ou centavos inteiros; Number somente geometria quando documentado. Taxas em p.p.; valor negativo/próximo de zero sem percentual enganoso. Direção não é melhora/piora.

Brasil Atual lê API/cache, não fontes oficiais no browser. Respeite contratos públicos/privados, autenticação no servidor e cookies/CSRF; não guardar rascunhos/tokens de sessão em armazenamento persistente do browser. Backend é autoridade final para autoria/publicação.

Verifique loading/vazio/erro, 360/768/1280/1920, claro/escuro, ausência de overflow, contraste AA, foco, teclado, fechamento/restauração dos dialogs, SVG acessível e movimento reduzido. Testes puros de cálculo/formatação/filtro quando houver regra. Checks: test:data-explorer, lint, typecheck; build quando a alteração afetar compilação/rotas. Informe evidência e limitações, sem afirmar auditoria completa de acessibilidade pela inspeção visual.

GRAPH-01C: `features/graphs` e rotas `/grafos` implementam WebGL 3D com carregamento adiado e lista equivalente, com explicação obrigatória no mesmo percurso. Antes de mudar, ler GRAPH_EXPLORER/GRAPH_CONTRACT. Não inferir relações por proximidade nem magnitude por cor/tamanho; preservar versões exatas do backend e rótulo de demonstração. Uma versão pública válida não depende do catálogo carregar. Testes graph-helpers/state e QA responsivo/teclado/erro/retry são obrigatórios para alterações relacionadas.

WebGL: Three.js/OrbitControls ficam no módulo dinâmico de grafos; não importar no shell global. Layout estável, instâncias/lotes, câmera enquadrando seleção, sprites com colisão de rótulos e descarte de recursos. Movimento reduzido/ausência de WebGL/dispositivo limitado levam à lista. O teste isolado em frontend/tests/webgl usa 200/500 sintéticos, sem mudar o limite público 200/400; cadência local não é garantia em celulares.
