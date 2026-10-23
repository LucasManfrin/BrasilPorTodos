# Como contribuir

BrasilPorTodos é open source sob [MIT](LICENSE). Ao contribuir código ou documentação autoral, você concorda em disponibilizar sua contribuição sob a mesma licença. [docs/governance/LICENSING.md](docs/governance/LICENSING.md) explica o alcance.

## Antes de começar

Leia [docs/product/VISION.md](docs/product/VISION.md), [docs/product/V1_SCOPE.md](docs/product/V1_SCOPE.md), [docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md) e [docs/project/BACKLOG.md](docs/project/BACKLOG.md). Escolha um item pequeno e discuta mudanças de escopo em uma issue quando o remoto estiver disponível.

Use português na documentação e na experiência do produto; identificadores de código em inglês. Cite referências e diferencie observação, estimativa e opinião. Debata ideias com respeito, sem ataques pessoais.

## Fluxo

1. Crie branch `feat/...`, `fix/...` ou `docs/...` a partir de `main`.
2. Implemente uma alteração coerente e atualize os documentos afetados.
3. Execute os checks do [guia de desenvolvimento](docs/development/DEVELOPMENT.md).
4. Abra PR explicando problema, comportamento resultante, validação e limitações.
5. Aguarde revisão e CI. A configuração de proteção de `main` será feita no GitHub.

Commits podem seguir Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`). Não versionar `.env`, tokens, senhas, dados pessoais reais, caches ou ambientes locais.

## Regras de implementação

- Leitura pública só para conteúdo publicado; autenticação e ownership validados no backend.
- Versões publicadas e composição de planos são imutáveis.
- Fontes por URL, sem upload ou fetch arbitrário.
- Cálculo fiscal usa Decimal/NUMERIC, nunca float.
- Migrations com Alembic; não usar criação automática de tabelas como fluxo operacional.
- Testar regras de negócio, permissões, versionamento e cálculo; evitar testes que apenas reproduzem a implementação.
- Atualizar lockfiles ao mudar dependências; documentar decisões relevantes.

## Dados e metodologia

Toda alteração de série deve informar origem, definição, unidade, referência, transformação e condições de uso. Exemplos fictícios devem ser identificados. Mudança de regra fiscal exige versão do motor e teste com resultado explicável manualmente.

## Problemas e vulnerabilidades

Use os templates de issue para bugs e entregas. Não publique segredos ou dados de conta em issues. O canal privado de segurança será definido com o remoto; consulte [SECURITY.md](SECURITY.md).
