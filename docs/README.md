# Documentação

[Voltar ao projeto](../README.md). Comece pelo [estado atual](project/STATUS.md); escolha a área e depois o item do [backlog](project/BACKLOG.md).

| Área | Documentos |
| --- | --- |
| Produto | [Visão](product/VISION.md), [escopo V1](product/V1_SCOPE.md), [roadmap](product/ROADMAP.md), [requisito do explorador de grafos](product/GRAPH_EXPLORER.md), [criação manual/guiada de propostas](product/PROPOSAL_CREATION.md) |
| Arquitetura | [Arquitetura](architecture/ARCHITECTURE.md), [decisões](architecture/DECISIONS.md), [modelo de dados](architecture/DATA_MODEL.md), [autenticação](architecture/AUTHENTICATION.md) |
| Dados e cálculo | [Metodologia](data/METHODOLOGY.md), [contextos e evidências](data/CONTEXT_EVIDENCE.md), [contrato do grafo](data/GRAPH_CONTRACT.md), [pesquisa do primeiro contexto](data/FIRST_CONTEXT_RESEARCH.md), [fontes candidatas e selecionadas](data/DATA_SOURCES.md), [indicadores/coleta](data/INDICATORS.md), [base fiscal](data/FISCAL_BASELINE.md), [composição primária](data/FISCAL_COMPOSITION.md), [juros e nominal](data/FISCAL_INTEREST.md), [gasto por função](data/FISCAL_SPENDING.md), [outros governos e consolidação](data/GENERAL_GOVERNMENT.md), [pesquisa SICONFI](data/SICONFI_RESEARCH.md), [pesquisa NFSP](data/PUBLIC_SECTOR_RESEARCH.md), [pesquisa original](data/FEDERAL_SPENDING_RESEARCH.md), [compatibilidade de impactos](data/FISCAL_COMPATIBILITY.md), [cenários fiscais declarados](data/FISCAL_SCENARIOS.md), [emprego e renda](data/EMPLOYMENT_INDICATORS.md), [roteiro de pesquisa](data/RESEARCH_BRIEF.md) |
| Design | [Sistema visual](design/DESIGN.md), [exploração de dados](design/DATA_EXPLORER.md), [auditoria e interface do painel](design/WORKSPACE_AUDIT.md) |
| Desenvolvimento | [Ambiente e checks](development/DEVELOPMENT.md), [Docker local](development/DOCKER_LOCAL.md), [fluxo completo](development/E2E.md), [evidências de verificação](development/VERIFICATION.md) |
| Projeto | [Estado atual](project/STATUS.md), [backlog e entregas](project/BACKLOG.md), [auditoria do repositório](project/REPOSITORY_AUDIT.md), [histórico do estado](project/STATUS_HISTORY.md) |
| Governança | [Publicação do repositório e lançamento](governance/PUBLICATION.md), [auditoria de segurança](governance/SECURITY_AUDIT.md), [alcance das licenças](governance/LICENSING.md), [política de conteúdo em proposta](governance/CONTENT_POLICY_DRAFT.md) |

## Padrão dos documentos

- Português claro. Arquivos Markdown em UPPER_SNAKE_CASE; índices README.md e instruções AGENTS.md.
- Cada assunto tem um documento principal; apontar para ele, sem copiar regras em vários lugares.
- Estado atual em STATUS; trabalho e aceite em BACKLOG; justificativas aceitas/pendentes em DECISIONS; histórico em CHANGELOG/VERIFICATION.
- Registros antigos com data são evidência histórica, não catálogo atual. Preservá-los e acrescentar o novo estado com referência.
- Links relativos e caminhos portáveis. Não incluir caminhos pessoais, logs, credenciais ou bancos locais em novos guias públicos.
- Mudança fiscal documenta escopo, unidade, preços, período, transformação, fonte e limites. Dados de terceiros mantêm termos próprios.
- Requisitos futuros são identificados como futuros; política em proposta não vira termo vigente.

Ao mover arquivos, atualizar todos os links/referências e `scripts/check-docs.mjs`; executar `npm run check:docs`.
