# Módulos de domínio

Implementados: auth, users, indicators, sources, policies, plans, simulations, admin, contexts, graphs, ideas e guidance. Routers/schemas fazem a fronteira HTTP; services aplicam regras/transações; models persistem entidades. Só criar camadas adicionais quando houver necessidade concreta.

Publicações, composição de planos, observações e execuções preservam história; leitura pública e escrita autenticada seguem autorização do domínio. Contratos em [arquitetura](../../../docs/architecture/ARCHITECTURE.md); instruções em [backend/AGENTS](../../AGENTS.md). Cálculo puro fica em app/simulation, fontes externas em app/integrations.
