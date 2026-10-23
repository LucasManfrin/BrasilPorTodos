# Scripts de manutenção e operação local

O site pode funcionar inteiramente no computador, com Node.js 22, Python 3.12/uv e PostgreSQL 17+. Os launchers abaixo são para Windows PowerShell 5.1 ou PowerShell 7, executados da raiz do repositório. Não usam caminhos pessoais nem contas padrão.

## Preparar uma instalação

```powershell
powershell -NoProfile -File scripts/setup-local.ps1
npm ci
# Em backend/:
uv sync --frozen --group dev
```

O setup cria somente ambientes ausentes, com segredo JWT aleatório, e preserva ambientes existentes. Configure `DATABASE_URL` em `backend/.env` para um banco **local já criado**. Para HTTP local, use `COOKIE_SECURE=false`; mantenha `JWT_SECRET` com pelo menos 32 caracteres. `frontend/.env.local` deve apontar `API_INTERNAL_URL` para `http://127.0.0.1:8000`. Nunca envie esses arquivos ao GitHub.

Inicie seu PostgreSQL nativo ou `docker compose up -d postgres`. O arquivo é [compose.yaml](../compose.yaml); seu serviço de banco é uma alternativa. O fluxo completo em containers não é iniciado por estes scripts. Consulte [desenvolvimento](../docs/development/DEVELOPMENT.md) para pré-requisitos e [publicação](../docs/governance/PUBLICATION.md) para os requisitos de produção.

Se existir um cluster nativo **já inicializado** em `.local/postgres-tests/data`, o launcher pode iniciá-lo com o `pg_ctl.exe` da mesma versão, na porta configurada em `DATABASE_URL`. Procura `pg_ctl` no PATH e depois em `Program Files/PostgreSQL/<versão>/bin`; se necessário, informe `-PostgresBin`. Ele não cria cluster, usuário, senha ou banco, não remove `postmaster.pid` e não executa restore/downgrade.

## Iniciar, consultar e encerrar

```powershell
# Primeira execução: faça backup antes de aplicar migrations em dados úteis.
powershell -NoProfile -File scripts/start-local.ps1 -Build -Migrate

# Demais execuções, quando o código e o schema não mudaram:
powershell -NoProfile -File scripts/start-local.ps1
powershell -NoProfile -File scripts/status-local.ps1
powershell -NoProfile -File scripts/status-local.ps1 -Json
powershell -NoProfile -File scripts/stop-local.ps1

# Simular início/encerramento sem modificar o ambiente:
powershell -NoProfile -File scripts/start-local.ps1 -WhatIf
powershell -NoProfile -File scripts/stop-local.ps1 -WhatIf
```

Abra **http://127.0.0.1:3000**. A API atende em `http://127.0.0.1:8000`, e `/api/v1/ready` verifica sua conexão SQL. Não é necessário manter terminais abertos. Os processos são ocultos; logs e registro de identidade ficam em `.local/`, ignorado pelo Git. O launcher não abre o navegador automaticamente.

- `start-local.ps1`: valida versões, ambiente, disponibilidade das portas, acesso ao banco e migrations. Reutiliza serviços saudáveis já ativos; build e migrations só ocorrem com `-Build`/`-Migrate` e exigem os respectivos serviços parados. Após a API ficar pronta, inicia a manutenção de logs expirados de IA, identificada por módulo/instalação e sem duplicar processo existente. Não inicia coletor de dados oficiais nem cria/publica conteúdo. Se faltar dependência, schema ou build, informa o próximo passo. Sem mudanças no código, executar novamente reutiliza os serviços.
- `status-local.ps1`: apresenta prontidão do site/API, porta do banco, serviços gerenciados e erros de configuração sem revelar credenciais. `database_listening` sozinho não confirma o acesso ao banco: confira `api_ready`. `guidance_cleanup_process_running` indica somente processo vivo; consulte o log para saber se as execuções tiveram êxito.
- `stop-local.ps1`: encerra apenas os processos registrados em `.local/local-services.json` cujo executável, nascimento e assinatura de comando ainda correspondem aos originais. Processos iniciados manualmente e o banco são preservados. Não confiar em PIDs antigos de outros registros.
- `local-common.ps1`: funções internas compartilhadas; não executar isoladamente. Trava de operação evita início/encerramento concorrentes pelo launcher.
- `local-runtime.py`: verificações somente de leitura de configuração, conexão SQL e schema, chamadas pelos launchers. Evita diferenças de aspas entre PowerShell 5.1 e 7; falhas não imprimem DSN, segredos ou traceback. Não aplica migrations nem altera dados.
- `check-docs.mjs`: valida documentos/guias e links Markdown locais com `npm run check:docs`; não verifica sites externos ou validade estatística.

Após alterar o código, encerre os serviços gerenciados e inicie com `-Build`. Após novas migrations, faça backup e use também `-Migrate`. O launcher preserva a última versão construída quando não recebe `-Build`; ele não afirma que esse build contém alterações posteriores. Não execute dois builds em paralelo. Um serviço iniciado fora do launcher precisa ser encerrado pelo operador antes de rebuild/migration; o launcher não o assume para encerramento.

Se uma inicialização falhar, serviços já iniciados permanecem registrados para diagnóstico e podem ser encerrados com `stop-local.ps1`. O banco permanece ativo. Em uma porta ocupada por serviço não reconhecido, o script falha sem encerrar o ocupante.

## Dados e coleta

A manutenção `backend/app/guidance_cleanup.py` remove somente registros privados de assistência cuja expiração já ocorreu. Não depende de chave Gemini, não chama modelo, não altera ideias/propostas e preserva registros ativos que sustentam limites de uso. O launcher a inicia com `--watch`, a cada 300 segundos, sem reinício automático do Windows. Para executar uma vez, em `backend/`, use `uv run python -m app.guidance_cleanup --once`. Os logs de operação exibem apenas contagem ou mensagem genérica de falha, sem respostas, prompts ou credenciais.

O prazo configurado define quando o registro se torna elegível à exclusão; a execução seguinte remove os expirados enquanto o computador, o banco e o worker estiverem ativos. Computador desligado, processo parado ou banco indisponível atrasam a limpeza. Backups têm ciclo próprio e não são alterados por este worker. Encerrar pelo launcher também encerra o worker que ele próprio iniciou, preservando processos externos e o banco.

O uso normal lê os dados salvos e funciona sem disparar consultas oficiais a cada visita. Coleta (`app.collect_indicators`), cadastro oficial (`app.seed_indicators`) e administração (`app.manage`) são operações separadas com autorização e configuração em [INDICATORS](../docs/data/INDICATORS.md). Não importar valores sem proveniência, criar revisão humana fictícia ou elevar permissões implicitamente. Gemini e outras integrações externas exigem configuração própria; iniciar o site não fornece chave nem acesso a serviços externos.

Estes scripts atendem operação local. Supervisão pública, HTTPS, backup automático e disponibilidade pública continuam requisitos de lançamento. O Compose completo local foi validado separadamente: [guia Docker](../docs/development/DOCKER_LOCAL.md).


`setup-docker.ps1` prepara os ambientes ausentes, gera senha aleatória no `.env` da raiz e preserva arquivos existentes. Não inicia serviços, não copia bancos e não executa migrations. O Compose executa essas migrations ao iniciar; [guia completo](../docs/development/DOCKER_LOCAL.md).
