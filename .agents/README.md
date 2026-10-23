# Guias de agentes por especialidade

Estes arquivos são instruções reutilizáveis para agentes e colaboradores. **Não registram agentes executáveis nem criam processos automaticamente.** O coordenador deve fornecer o guia correspondente ao delegar uma tarefa, junto do [AGENTS.md](../AGENTS.md) e das instruções locais da pasta.

| Guia | Responsabilidade |
| --- | --- |
| [COORDINATOR.md](COORDINATOR.md) | Escopo, contratos, divisão de trabalho, integração e backlog |
| [FISCAL.md](FISCAL.md) | Fontes oficiais, coleta, precisão, base fiscal e coerência econômica |
| [FRONTEND.md](FRONTEND.md) | Interface, acessibilidade, responsividade e contratos da API |
| [BACKEND.md](BACKEND.md) | Domínio, API, autoria, persistência e migrations |
| [QA.md](QA.md) | Verificação independente, regressões, segurança e evidência |
| [DOCS.md](DOCS.md) | Documentação, estado, organização e contribuição pública |

## Delegação

Delegar quando autorizado pela pessoa mantenedora e quando houver tarefas independentes. Não criar agentes apenas para aumentar paralelismo. Definir: ID do backlog, resultado, arquivos que pode editar, contrato de entrada/saída, verificações e dependências. Evitar dois agentes escrevendo o mesmo arquivo. Pesquisa/revisão pode avançar em paralelo; mudanças com contrato dependente esperam sua definição.

Modelo de passagem: **item e objetivo → guia relevante → arquivos permitidos → contratos/limites → verificações → evidência de conclusão**. O coordenador integra, resolve conflitos e registra a entrega. Agentes não marcam trabalho de outro agente como concluído por inferência.

Relatório de retorno: o que mudou, arquivos, fontes/contratos, checks executados/resultados, riscos reais e pendências. Nunca incluir segredos, payloads privados ou dizer que um teste passou sem execução.
