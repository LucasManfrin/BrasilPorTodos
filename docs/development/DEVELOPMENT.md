# Desenvolvimento local

## Alternativa completa em Docker

O fluxo Docker dispensa Node/Python no host e inclui migrations, banco persistente, API, site e limpeza de logs. Consulte [DOCKER_LOCAL](DOCKER_LOCAL.md). As instruções abaixo são para desenvolvimento nativo.

## Dependências e ambiente

Node 22, npm, Python 3.12 e uv. PostgreSQL 17+ pode rodar em Docker ou instância local isolada. Não usar banco com dados pessoais/de produção para testes. Arquivos `.env`, `.local` e dados de teste ficam fora do Git.

```powershell
# Raiz; cria apenas ambientes ausentes e um segredo aleatório.
powershell -File scripts/setup-local.ps1
npm ci
# Se usar somente o banco Docker: prepare .env raiz e confira porta/senha
powershell -File scripts/setup-docker.ps1
docker compose up -d postgres
```

No Linux/macOS, copie os dois exemplos de ambiente e forneça JWT_SECRET aleatório de pelo menos 32 caracteres. Nunca use uma chave do repositório. Ajuste DATABASE_URL, CORS_ORIGINS e COOKIE_SECURE em `backend/.env`. O setup preserva ambientes existentes; se um arquivo antigo tiver JWT_SECRET vazio, configure-o antes de testar contas.

Em `frontend/.env.local`, API_INTERNAL_URL aponta à API interna (padrão `http://127.0.0.1:8000`). O browser usa `/api/v1` na mesma origem, via Route Handler Next.js, que encaminha cookies/CSRF e Authorization. NEXT_PUBLIC_REPOSITORY_URL é opcional enquanto não há remoto público.

## Iniciar no Windows com os launchers

Depois de instalar dependências, configurar os ambientes e disponibilizar um banco PostgreSQL existente, execute na raiz:

```powershell
powershell -File scripts/start-local.ps1
powershell -File scripts/status-local.ps1
powershell -File scripts/stop-local.ps1
```

O primeiro comando usa o build existente e verifica o schema; é idempotente com serviços desta instalação já ativos. Primeiro uso ou código alterado exige `-Build`. Migration é explícita com `-Migrate`, **depois de backup**. Ambos exigem API/frontend parados: `powershell -File scripts/start-local.ps1 -Build -Migrate`. Não há criação, reset ou exclusão de banco. O launcher pode retomar o cluster nativo local existente; outro PostgreSQL deve estar disponível com DATABASE_URL configurado. Se necessário, informe `-PostgresBin` da mesma versão do cluster.

Processos são conferidos por identidade/instalação; porta ocupada por serviço alheio gera erro. Stop só encerra processos registrados ainda correspondentes e preserva PostgreSQL. Serviços iniciados fora do launcher não são encerrados por ele. Logs/estado ficam em `.local` ignorado, sem DSN/segredos no status. O coletor não é iniciado: leitura usa dados salvos; atualização oficial permanece operação separada. Esses launchers não instalam supervisor nem executam no boot. Backup/restauração desta entrega foi exercitado separadamente, não é efeito automático de `-Migrate`.

## Iniciar manualmente (alternativa)

```sh
# backend/
uv sync --frozen --group dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1
```

```sh
# Raiz, outro terminal
npm run dev
```

Site: http://127.0.0.1:3000. API: http://127.0.0.1:8000/docs. `health` verifica processo; `ready` testa conectividade com PostgreSQL. O Compose completo também está disponível e validado localmente em [DOCKER_LOCAL](DOCKER_LOCAL.md); ele tem configurações e volume próprios. Operação pública exige [PUBLICATION](../governance/PUBLICATION.md).

Cadastro/login e contribuições podem ser testados com contas fictícias nesse ambiente. Conteúdo publicado é aberto, rascunhos são privados. Administração e importação das séries BCB: [docs/data/INDICATORS.md](../data/INDICATORS.md). Roteiro de validação: [docs/development/E2E.md](E2E.md).

## Migrations

0001/0002: domínio e integridade de publicação; 0003: sessões e rate limit; 0004/0005: snapshots/execuções imutáveis; 0006: auditoria e revisões de indicadores append-only. Execute Alembic antes dos testes de integração. Não usar create_all no startup.

```sh
uv run alembic check
# Para uma nova mudança de schema:
uv run alembic revision --autogenerate -m "describe change"
```

Revise migrations geradas, especialmente chaves compostas, ciclos e triggers. Importe modelos em `app/database/models.py`. Reversão destrutiva de migrations só é verificada em banco exclusivo de teste; não aplicar em banco com conteúdo útil.

## Checks

```sh
# Raiz
npm run check:docs
npm run test:data-explorer
npm run lint
npm run typecheck
npm run build
# backend/
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Testes unitários e de saúde rodam sem banco. Integração exige PostgreSQL vazio, migrations aplicadas e RUN_DATABASE_TESTS=1. Fixtures usam transação externa e savepoints, revertendo suas contas/conteúdo fictícios ao final de cada teste. Não misturar o banco de integração com a demonstração do navegador.

```powershell
# backend/; ajuste DATABASE_URL ao banco exclusivo de integração
$env:RUN_DATABASE_TESTS='1'
uv run alembic upgrade head
uv run pytest
uv run alembic check
```

CI prepara PostgreSQL, aplica migrations antes de pytest e verifica drift. Ainda não executada no GitHub. Lockfiles: npm no frontend, uv no backend; ambos com instalação congelada na CI.

## Operação antes de lançamento

Produção exige HTTPS, COOKIE_SECURE=true, secrets gerenciados, backups/restauração, canais de manutenção e termos para conteúdo/dados. O rate limit usa IP da conexão; com o proxy Next.js local, a API vê o IP do proxy. Configurar identificação de cliente apenas por proxy confiável antes de abrir o serviço, sem aceitar cabeçalhos arbitrários. Limpeza de sessões/contadores vencidos e limites de carga ficam na Fase 2.

Docker Desktop não estava ativo na validação local. O PostgreSQL 18 instalado foi usado em cluster independente, loopback e porta 55432; os dados da instalação existente foram preservados. Essa instalação é exclusiva da máquina de verificação, não requisito portátil do projeto.

## Interface e execução atual do protótipo

Identidade e componentes em [docs/design/DESIGN.md](../design/DESIGN.md). Canais opcionais do rodapé: NEXT_PUBLIC_REPOSITORY_URL e NEXT_PUBLIC_CONTACT_EMAIL, no ambiente do frontend. Por serem públicos e incorporados ao bundle, alterações exigem reiniciar o desenvolvimento ou gerar outro build.

Na verificação fiscal de 2026-10-09, Next.js roda em 127.0.0.1:3000 usando `next start` sobre o build, FastAPI em 127.0.0.1:8000 e o cluster nativo de demonstração/testes em 127.0.0.1:55433, dentro de .local (ignorado pelo Git). A porta 55432 usada anteriormente recusou o bind nesta sessão; o mesmo cluster isolado foi iniciado em 55433 e DATABASE_URL local foi ajustado. Os bancos de demonstração e integração são separados. Isso não usa os containers de outro projeto existentes no computador. O Docker estava inativo no primeiro setup; agora está disponível, mas o Compose do BrasilPorTodos ainda precisa de validação e configuração de autenticação/portas antes de ser usado para esse fluxo completo.

Brasil Atual consulta nossa API e PostgreSQL. O coletor BCB/IBGE/Tesouro consulta uma vez por dia quando o processo está ativo; visitas só leem dados salvos. Nesta verificação o coletor local está ativo em processo oculto, com logs em `.local/collection-fiscal.out.log` e `.local/collection-fiscal.err.log`. API e frontend usam `.local/api-fiscal.*.log` e `.local/frontend-fiscal.*.log`; PIDs desta execução estão em `.local/fiscal-processes.json`. Ele não inicia sozinho após reiniciar o computador. Em produção, configurar supervisor ou tarefa agendada. Comandos e limites em [docs/data/INDICATORS.md](../data/INDICATORS.md).

## Ambiente e migrations da base contextual

Aplicar `alembic upgrade head`: 0007 acrescenta snapshots contextuais e registro de coletas; 0008 identifica exemplos; 0009 acrescenta metadados fiscais dos impactos com defaults de ausência e constraints; 0010 acrescenta cenário JSONB opcional nos planos, sem reescrever publicações/execuções antigas. `ENVIRONMENT=development` permite exemplos explicitamente marcados no banco local. O padrão do backend é `production`, que exclui exemplos dos catálogos, detalhes e históricos públicos. Rascunhos seguem privados. Não atualizar publicações antigas com uma base capturada depois.

O botão de administrador usa tarefa em segundo plano no processo FastAPI. Reinício do processo pode interromper a tarefa; o próximo coletor pode retomá-la após o intervalo mínimo. Para operação pública, supervisionar o worker e monitorar execuções interrompidas. Não é uma fila durável distribuída.

A entrega fiscal reutiliza as tabelas e snapshots existentes, sem nova migration. Testes de integração forçam configurações de produção e cookie seguro em fixtures, mantendo DATABASE_URL do banco isolado; isso evita que o `.env` de demonstração altere os testes de privacidade/exemplos. O build local é uma prévia; para editar a interface use o comando de desenvolvimento acima, após encerrar somente o processo correspondente deste projeto.

## Testes da exploração de dados

Execute npm run test:data-explorer na raiz para os testes puros de formatação, variação, recorte temporal, grade responsiva, diretório de fontes e metadados/agregação fiscal. Critérios de apresentação e confiança em [docs/design/DATA_EXPLORER.md](../design/DATA_EXPLORER.md); evidências de interface em [docs/development/VERIFICATION.md](VERIFICATION.md).

## Compatibilidade fiscal — 2026-10-10

Aplicar migration 0009 antes de usar os novos campos. Para conferir a interface, abrir um rascunho fictício e a etapa Impacto: selecionar governo, caixa/competência, preços, componente e cobertura anual; preços constantes devem exigir ano-base, retornar a nominal deve limpá-lo. Conferir autosave/reabertura, cópia e leitura pública, razões na simulação e ausência explícita em resultados legados. Revisar 360/768/1280/1920, dois temas, foco/teclado. A conferência visual foi retomada junto a DATA-06B2; veja evidências atuais em VERIFICATION.md. Testes automatizados não a substituem. [Contrato](../data/FISCAL_COMPATIBILITY.md).


## Conferir cenário futuro opcional

Aplicar migration 0010. Em plano fictício, escolher comparação com cenário, informar título/explicação e cada receita/despesa/justificativa anual; nenhum histórico será copiado. Salvar parcial, reabrir e conferir que campos vazios continuam ausentes. Simular configuração incompleta deve explicar o erro. Confirmar exclusão das propostas salva primeiro e vincula revisão às entradas. Simular antes/depois da confirmação; alterar composição/premissa exige nova revisão. Ajustar anos/adotar referência exige ação explícita. Conferir cópia sem revisão, publicação e leitura anônima com premissas/fontes/limites. Nunca editar publicações existentes para este teste. [Contrato](../data/FISCAL_SCENARIOS.md).

## Conjuntos funcionais — migration 0011

Aplicar upgrade antes da nova coleta/endpoints funcionais. A tabela de conjuntos é append-only; só agregados/proveniência ficam no banco. Não fazer downgrade em banco de demonstração ou conteúdo útil. Verificar reversão/reaplicação em banco exclusivo de integração. O coletor baixa somente o recurso do catálogo oficial revisado, com limites, sem Excel ou dependências pesadas. [Contrato](../data/FISCAL_SPENDING.md).


## Governo Geral — migration 0012

Upgrade antes da coleta/consulta EFGG; backup do demo e nenhuma reversão com conteúdo útil. Testar downgrade0011/upgradehead exclusivamente no banco de integração. Parser não executa Excel/conexões externas; pipeline valida ano e conjunto antes da transação. Worker diário lê apenas o recurso oficial revisado. [Contrato](../data/GENERAL_GOVERNMENT.md).


## Contextos revisados — migration 0013

Aplicar upgrade antes de utilizar `/api/v1/contexts`; backup do banco com conteúdo útil e downgrade apenas em banco exclusivo de integração. Interface continua DATA-05C: API permite criar/salvar próprio contexto, outro administrador revisar, autor publicar e visitante ler versão congelada. Detalhes/DTOs/rotas e estados em [CONTEXT_EVIDENCE](../data/CONTEXT_EVIDENCE.md); exemplos de testes são fictícios e revertidos, não pesquisa real.

Rodar `uv run pytest tests/unit/test_context.py tests/unit/test_context_schemas.py tests/unit/test_context_resolver.py` e `RUN_DATABASE_TESTS=1 uv run pytest tests/integration/test_contexts.py` somente com DATABASE_URL de integração. Full pytest, Ruff/formatação e Alembic check fazem parte da entrega. Não passar revisor/hash/aprovação de cliente como autorização, nem substituir observações revisadas automaticamente.


DATA-05C acrescenta `tests/integration/test_context_discovery.py` (última publicação/seleção concorrente, referências históricas e privacidade) e helpers frontend `tests/context-helpers.test.mjs`/`context-editor-state.test.mjs`. Os checks completos incluem banco exclusivo de integração, `npm run test:data-explorer`, lint, typecheck e build. Browser: público vazio/erro/histórico, proprietário salvar/publicar, revisão distinta/conflito, descarte explícito, chips/seletores e teclado nos quatro tamanhos/dois temas. Contexto de teste com revisão automatizada precisa de selo fictício; pesquisa real fica pendente de pessoa revisora.


GRAPH-01A: `uv run pytest tests/unit/test_graph.py` verifica contrato, fontes, snapshots, revisão e topologia sem banco. Antes de integrar/entregar: suíte unitária, Ruff/formatação e check:docs. Enquanto a biblioteca permanecer sem uso em runtime, essa alteração não exige reiniciar serviços, aplicar migrations ou repetir QA do frontend; a entrega registra explicitamente quais verificações são históricas. Futura API/persistência exigirá testes reais de autorização/privacidade/transação em PostgreSQL exclusivo.

## Curadoria do grafo — migration 0014

Aplicar upgrade com backup antes de utilizar `/api/v1/graphs`. O módulo tem nó/aresta/conjunto, revisão distinta e publicação explícita, sem interface gráfica nesta etapa. Não testar curadoria sobre a pesquisa real nem usar testes fictícios como revisão humana. Contratos/DTOs/listas resumidas em [GRAPH_CONTRACT](../data/GRAPH_CONTRACT.md).

Verificar `uv run pytest tests/unit/test_graph.py tests/unit/test_graph_schemas.py` e, com DATABASE_URL exclusivamente de integração, `RUN_DATABASE_TESTS=1 uv run pytest tests/integration/test_graphs.py`. Completar suíte backend, Ruff/formatação e Alembic check. Downgrade 0014→0013 e reaplicação somente no banco descartável de integração. Demo recebe apenas upgrade após backup/checkpoint. Testes cobrem papéis, fontes privadas por ID, exemplos, última revisão, publicação em disputa, versões públicas exatas, SQL imutável e rollback. Não há mudança frontend que exija repetir build/QA nesta entrega.

## Exploração visual do grafo — GRAPH-01C

`/grafos` consulta somente lista/detalhe/histórico públicos de `/api/v1/graphs`; IDs de payload e UUIDs de rotas são distintos. `features/graphs` separa contrato, helpers/layout, demonstração, inicialização, cena, inspector e guia. Sem novas dependências. `graph-helpers.test.mjs` verifica geometria/filtros/versões/limites, `graph-state.test.mjs` protege abertura exata independente do catálogo e não confunde falha com ausência/demonstração. Executar test:data-explorer, lint, typecheck/build e check:docs.

QA de tela cobre quatro larguras/dois temas, zoom/rotação/arraste/2D/reset, busca/filtros, nó→relação→vizinho, lista por teclado, fontes/limites e versão preservada/disputa/histórico/erro/retry. Respostas fictícias de QA são infraestrutura temporária separada, não seed ou revisão humana real. Não criar registros reais no banco para testar a interface. [Verificação](VERIFICATION.md).


## Assistência opcional Gemini

O guiado fixo e o modo manual funcionam sem chave. Para habilitar organização por Gemini após avaliação do modelo, configure **somente** `backend/.env`:

```dotenv
GEMINI_API_KEY=
GUIDANCE_AI_ENABLED=false
GUIDANCE_MODEL=gemini-3.5-flash-lite
GUIDANCE_DAILY_LIMIT=20
GUIDANCE_LOG_RETENTION_DAYS=7
```

Preencha a chave localmente, sem enviar ao chat/Git/frontend, e altere a flag para `true` somente ao validar a assistência. Reinicie a API depois de mudar configurações. O backend usa REST Gemini com saída estruturada e interface de provedor substituível; [modelo configurado](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite.md). Não há chamadas reais validadas sem chave do mantenedor. Falha/limite/rejeição preserva resposta e permite continuar sem IA.

Envio exige consentimento. Perguntas não mudam e o modelo não calcula. O prompt 3.0.1 desenvolve a redação de proposta e traz sugestões opcionais/lacunas separadas. Contexto inclui somente trechos confirmados, com consentimento e limites. Sugestões só entram selecionadas e confirmadas, rotuladas como ponto a avaliar. Não deve inventar fatos, números, legislação ou fontes. Servidor verifica estrutura/detalhes, sem provar sentido ou neutralidade. O autor pode consultar GET /api/v1/guidance/calls/{id} pelo botão no editor; outra conta, registro apagado ou expirado recebe 404. Logs privados incluem prompt/retorno/uso e duração quando disponíveis, sem chaves/headers. Quota padrão 20/dia UTC e cinco/minuto; falhas contam. Registros privados com prazo padrão sete dias, apagamento de conteúdo pelo proprietário e quota preservada. Expiração só remove quando a limpeza roda: aplicação/operação ativa necessária, não garantia de remoção em computador desligado ou em backups. Não colocar logs reais em fixtures. [Método/privacidade](../product/PROPOSAL_CREATION.md).

Limites opcionais da participação no backend: `IDEAS_DAILY_LIMIT=10`, `IDEAS_SUGGESTIONS_DAILY_LIMIT=20`, `IDEAS_REPORTS_DAILY_LIMIT=10`. Mudar exige reinício; não substitui segurança/proxy e política do lançamento público.

## Novo fluxo de ideias — migrations 0015–0017

Aplicar `alembic upgrade head` somente depois de backup do banco útil. Migrations aditivas introduzem IDEIA, metadados de origem/nível, compartilhamento, sugestões, denúncias e registros privados de assistência; legado permanece sem reclassificação retroativa. Downgrade/reaplicação e conteúdo de QA apenas no banco exclusivo de integração. Testar promoção incompleta/bloqueios, fotografia compartilhada separada, duplicação atribuída, autorização/denúncia/moderação, logs/quotas, imparcialidade, falha/timeout/apagamento concorrente e análise Decimal.

`GET /api/v1/guidance/impact/{slug}` recebe versão publicada opcional e `cost_low`, `cost_high`, `gain_low`, `gain_high` como strings decimais de até quatro casas. Mínimos 0–1, máximos 1–2, padrão 1. A resposta identifica `DECLARED_SENSITIVITY_1` e motor `1.0.0`; recortes incompatíveis/ausentes ou versão sem novo nível completo não geram faixa. Ajustar premissas é análise somente de leitura, sem modificar publicação/plano. [Metodologia](../data/METHODOLOGY.md#criação-guiada-e-sensibilidade-declarada--2026-10-19).

Rodar os checks completos acima incluindo PostgreSQL exclusivo. As suítes de ideias/guidance e os testes frontend `ideas-state.test.mjs`/`ideas-impact.test.mjs` cobrem regras novas. QA de navegador e restauração real devem ser registrados em [VERIFICATION](VERIFICATION.md), sem usar testes fictícios como revisão humana de conteúdos reais.


## Limpeza dos registros de assistência

Na pasta `backend`, `uv run python -m app.guidance_cleanup --once` remove registros expirados em uma execução; `--watch` verifica a cada 300 segundos enquanto ativo. O launcher Windows inicia esse processo junto da aplicação e registra sua identidade para o stop. O processo não chama Gemini nem dispara coleta oficial. Com o computador desligado não há execução; conteúdo apagado em backups depende da política de retenção desses backups. Verifique status/logs ao operar, sem expor prompts ou respostas privadas.


Na assistência, GUIDANCE_TIMEOUT_SECONDS é 30 s por padrão (2–45s). O proxy aguarda 60 s exclusivamente no POST guidance/organize. HTTP 503 do Gemini indica indisponibilidade externa; a mensagem preserva a entrada e permite tentativa manual ou modo sem IA. Não confundir ready 200 (API/banco) ou ai_available (configuração presente) com resposta do modelo validada.
