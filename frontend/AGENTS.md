# Instruções do frontend

Aplicam-se as [instruções comuns](../AGENTS.md). Antes de editar, leia [.agents/FRONTEND.md](../.agents/FRONTEND.md) e [DESIGN](../docs/design/DESIGN.md). Respeite escopo/telas aprovadas, tokens, contratos públicos/privados e verificação proporcional. Os guias da versão instalada do Next.js abaixo prevalecem sobre suposições de APIs antigas.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
