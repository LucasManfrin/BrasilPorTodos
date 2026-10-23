# BrasilPorTodos

Entender o Brasil, transformar ideias em propostas e comparar planos com fontes, custos e escolhas visíveis.

O projeto nasceu da dificuldade de acompanhar números e propostas durante as eleições. A intenção é simplificar o entendimento sem esconder limites: ampliar uma política tem custos, financiamento e consequências que precisam ser explicados.

**Estado:** V1 funcional localmente, em preparação para colaboração pública. Contas, rascunhos privados, propostas e planos versionados, publicação, fontes e simulações persistidas já funcionam. Brasil Atual reúne **14 indicadores oficiais** do BCB, IBGE e Tesouro, com coleta controlada e histórico de revisões. A referência fiscal usada nas publicações é do **Governo Central**. Brasil Atual também apresenta composição primária, juros/nominal, execução federal por função e [Governo Geral por esfera](docs/data/GENERAL_GOVERNMENT.md), em conjuntos observados separados, com consolidação oficial e cobertura municipal estimada explícita; esses conjuntos não ampliam automaticamente o motor. O simulador calcula o efeito fiscal incremental das medidas e registra a compatibilidade dos recortes declarados com a referência histórica; o [cenário futuro declarado](docs/data/FISCAL_SCENARIOS.md) é opcional nos planos, com premissas anuais e revisão humana preservadas. A [interface/API de contextos e evidências](docs/data/CONTEXT_EVIDENCE.md) permite salvar textos privados, revisar por outro administrador e publicar versões preservadas; o primeiro contexto pesquisado aguarda revisão humana. O [grafo](docs/data/GRAPH_CONTRACT.md) tem contrato, persistência e API de curadoria com revisão distinta e publicação explícita; a [rede visual em WebGL 3D](docs/product/GRAPH_EXPLORER.md) e sua explicação estão disponíveis em `/grafos`, com lista equivalente, fontes e versões. O grafo não calcula efeitos. A [criação acessível](docs/product/PROPOSAL_CREATION.md) já oferece IDEIA/COMPLETA, guiado/manual, compartilhamento, cópias, sugestões e moderação. A análise de completas tem sensibilidade fiscal declarada pelo motor; assistência Gemini é opcional, integrada e desligada por padrão, com teste local fictício e avaliação sistemática real pendente. A comparação fiscal não é previsão oficial.

[Estado atual e próximos passos](docs/project/STATUS.md) · [Documentação](docs/README.md) · [Backlog](docs/project/BACKLOG.md) · [Contribuir](CONTRIBUTING.md)

## Princípios

- Leitura pública sem conta; contribuições autenticadas e autorizadas.
- Propostas e planos publicados preservam suas versões e fontes. Editar uma proposta não altera um plano publicado.
- Fontes por URL; sem upload de estudos ou arquivos na V1.
- Dados observados, hipóteses e estimativas identificados separadamente. Ausência de dado não vira zero.
- Ferramenta independente, sem vínculo com partidos ou candidaturas; resultados dependem das premissas.
- Código e documentação autoral sob [MIT](LICENSE). Dados externos e fontes tipográficas conservam seus próprios termos.

## Organização

```text
BrasilPorTodos/
├── frontend/       Next.js + TypeScript, App Router
├── backend/        FastAPI + SQLAlchemy + Alembic + motor fiscal
├── docs/           Produto, arquitetura, dados, design, desenvolvimento e governança
├── .agents/        Guias de especialidade para trabalho assistido
├── scripts/        Setup, launchers locais e verificação de documentação
├── .github/        CI e templates de contribuição
├── AGENTS.md       Instruções comuns para agentes
├── CONTRIBUTING.md Regras de colaboração
├── SECURITY.md     Reporte de segurança e situação do canal
├── CHANGELOG.md    Histórico de entregas
└── LICENSE         Licença MIT
```

Monorepo e monólito modular: frontend separado, uma API e PostgreSQL como fonte de verdade. Sem microsserviços. Three.js é carregado separadamente somente ao explorar o mapa 3D; a lista continua disponível. [Arquitetura](docs/architecture/ARCHITECTURE.md).

## Rodar com Docker

Com Docker Desktop ativo em containers Linux, na raiz:

```powershell
powershell -NoProfile -File scripts/setup-docker.ps1
docker compose up -d --build --wait
```

Site: http://127.0.0.1:3000. O Compose inclui banco persistente, migrations, API, frontend e limpeza de logs. Se a aplicação nativa estiver ativa, encerre-a antes com `scripts/stop-local.ps1` para liberar 3000/8000. Configurações Docker/portas ficam no `.env` da raiz; JWT e Gemini em `backend/.env`. [Guia Docker, dados e backup](docs/development/DOCKER_LOCAL.md).

## Rodar nativamente

Node.js 22, Python 3.12, [uv](https://docs.astral.sh/uv/) e PostgreSQL 17+ (nativo ou Docker).

Na raiz, instale o frontend e prepare os ambientes:

```sh
npm ci
```

No Windows, `powershell -File scripts/setup-local.ps1` cria os ambientes ausentes e gera um segredo local. Nos demais sistemas, copie `backend/.env.example` para `backend/.env` e `frontend/.env.example` para `frontend/.env.local`, configure um JWT_SECRET aleatório de pelo menos 32 caracteres e ajuste DATABASE_URL. O setup preserva ambientes existentes.

Para usar somente PostgreSQL via Docker, prepare também o ambiente Compose com `scripts/setup-docker.ps1` e execute `docker compose up -d postgres`. A API nativa deve apontar `DATABASE_URL` para a porta/senha Docker, conforme o [guia](docs/development/DOCKER_LOCAL.md). Não alterar o ambiente nativo se ele já usa outro banco.

No Windows, depois de preparar dependências e um banco existente, os launchers iniciam e conferem a aplicação:

```powershell
powershell -File scripts/start-local.ps1
powershell -File scripts/status-local.ps1
powershell -File scripts/stop-local.ps1
```

Primeiro uso/código novo: `start-local.ps1 -Build`. Schema pendente: faça backup antes e use `-Migrate`; build/migration exigem API/frontend parados. O launcher verifica identidade, não cria/apaga bancos, preserva PostgreSQL ao parar e não inicia coleta automaticamente. [Detalhes e alternativa manual](docs/development/DEVELOPMENT.md).

Para a alternativa manual, em um terminal na pasta backend:

```sh
uv sync --frozen --group dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1
```

Em outro terminal, na raiz:

```sh
npm run dev
```

Site: http://127.0.0.1:3000. API: http://127.0.0.1:8000/docs. Saúde: `/api/v1/health`; conectividade com o banco: `/api/v1/ready`. A coleta exige operador autorizado e processo ativo; visitas leem dados salvos. [Guia completo](docs/development/DEVELOPMENT.md).

O Compose completo local foi validado com migrations, leitura, login/renovação/logout e persistência. Coleta oficial e Gemini permanecem operações separadas; não há serviço público lançado.

## Assistência opcional

“Me ajuda a montar” funciona com roteiro fixo mesmo sem IA. Para usar Gemini, a chave fica somente em `GEMINI_API_KEY` de `backend/.env`, com `GUIDANCE_AI_ENABLED=true` após configuração e avaliação. Não envie chaves ao frontend, chat ou Git. A integração permanece desligada por padrão. O ambiente local já foi testado com frase fictícia; avaliação sistemática de imparcialidade do modelo real continua pendente. Manual e guiado sem IA continuam disponíveis. [Configuração e privacidade](docs/development/DEVELOPMENT.md#assistência-opcional-gemini).

## Verificar

Na raiz:

```sh
npm run check:docs
npm run test:data-explorer
npm run lint
npm run typecheck
npm run build
```

Na pasta backend:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run alembic check
```

Integração exige banco exclusivo de teste, migrations aplicadas e RUN_DATABASE_TESTS=1. Alembic exige PostgreSQL ativo. Evidências e limites em [docs/development/VERIFICATION.md](docs/development/VERIFICATION.md).

## Colaborar e publicar

Comece por [CONTRIBUTING.md](CONTRIBUTING.md), [visão](docs/product/VISION.md) e [escopo V1](docs/product/V1_SCOPE.md). Agentes devem ler [AGENTS.md](AGENTS.md) e o [guia da especialidade](.agents/README.md).

Preparação do GitHub, canais e distinção entre abrir o código e lançar o serviço: [PUBLICATION.md](docs/governance/PUBLICATION.md). [Alcance da licença](docs/governance/LICENSING.md). Políticas de conteúdo da plataforma continuam em proposta; publicar este código não abre o cadastro público.
