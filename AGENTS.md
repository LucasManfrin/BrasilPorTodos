# Instruções para agentes e colaboradores automatizados

Antes de implementar, leia [README](README.md), [estado atual](docs/project/STATUS.md), [escopo V1](docs/product/V1_SCOPE.md) e [decisões](docs/architecture/DECISIONS.md). Escolha o [guia da especialidade](.agents/README.md) e leia as instruções AGENTS.md da pasta editada.

## Regras comuns

- Preserve leitura pública de publicações, privacidade de rascunhos e escrita autenticada/autorizada.
- Não altere versões publicadas nem atualize automaticamente propostas dentro de planos publicados.
- Não adicione upload ou busca de URLs arbitrárias na V1.
- Use Decimal/NUMERIC para dinheiro e UTC para timestamps; cálculo incremental não é previsão nacional.
- Domínio em services; motor fiscal independente de HTTP/banco; fontes e hipóteses rastreáveis.
- Exemplos explicitamente fictícios. Ausência de dado não vira zero; dados revisados preservam história.
- Respeite o escopo e as telas aprovadas. Tokens e componentes existentes antes de novas soluções/dependências.
- Não publique, faça push, implante ou crie issues externas sem autorização correspondente. O backlog local pode ser atualizado.
- Código/documentação autoral MIT; preservar avisos e termos de dados/fontes externos. Não registrar segredos ou payloads privados.

## Organização e trabalho paralelo

Padrão documental em [docs/README.md](docs/README.md). Guias .agents são contexto de trabalho, não configuração automática de execução. Delegar quando autorizado e útil; delimitar arquivos e contratos, evitar escritores concorrentes e integrar/testar antes de encerrar. Consulte [COORDINATOR](.agents/COORDINATOR.md).

Ao concluir uma entrega, atualize imediatamente [BACKLOG](docs/project/BACKLOG.md) com estado e evidência. Preserve pendências; entrega parcial não é concluída. Atualize STATUS/DECISIONS quando capacidade/decisão mudar. Execute os checks pertinentes do [guia de desenvolvimento](docs/development/DEVELOPMENT.md), sem afirmar verificações não executadas.

Ao começar grafos, leia [GRAPH_EXPLORER](docs/product/GRAPH_EXPLORER.md): página explicativa pública, rede interativa de nós/arestas, inspeção de conexões/evidências, celular e alternativa por teclado/lista. GRAPH-01 é requisito futuro; esta anotação não autoriza implementação automática.
