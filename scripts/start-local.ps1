[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [switch] $Build,
    [switch] $Migrate,
    [string] $PostgresBin
)
. (Join-Path $PSScriptRoot 'local-common.ps1')

$config = Get-LocalConfiguration
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
if (-not $nodeCommand) { throw 'Instale Node.js 22 para executar o frontend.' }
$node = $nodeCommand.Source
if ((& $node --version) -notmatch '^v22\.') { throw 'Este projeto requer Node.js 22.' }
$next = Join-Path $script:RepoPath 'node_modules\next\dist\bin\next'
if (-not (Test-Path -LiteralPath $next)) { throw 'Dependências frontend ausentes. Execute npm ci na raiz.' }
$frontend = Join-Path $script:RepoPath 'frontend'
$backend = Join-Path $script:RepoPath 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$apiOccupied = Test-LocalPort '127.0.0.1' 8000
$frontendOccupied = Test-LocalPort '127.0.0.1' 3000
if ($apiOccupied -and (-not (Test-LocalHttp 'http://127.0.0.1:8000/openapi.json' 'BrasilPorTodos API') -or -not (Test-ServiceRepository 8000))) { throw 'A porta 8000 está ocupada por outro serviço ou instalação não identificada. Libere-a manualmente; nenhum processo foi encerrado.' }
if ($frontendOccupied -and (-not (Test-LocalHttp 'http://127.0.0.1:3000/' 'BrasilPorTodos') -or -not (Test-ServiceRepository 3000))) { throw 'A porta 3000 está ocupada por outro serviço ou instalação não identificada. Libere-a manualmente; nenhum processo foi encerrado.' }
if (($Build -and $frontendOccupied) -or ($Migrate -and ($apiOccupied -or $frontendOccupied))) {
    throw 'Build/migration exigem os serviços parados para evitar arquivos/schema concorrentes. Pare somente esta instalação primeiro.'
}
if (-not $Build -and -not (Test-Path -LiteralPath (Join-Path $frontend '.next\BUILD_ID')) -and -not $frontendOccupied) {
    throw 'Frontend sem build. Execute scripts/start-local.ps1 -Build na primeira vez ou após alterar o código.'
}
if (-not $PSCmdlet.ShouldProcess($script:RepoPath, 'Iniciar banco existente e serviços locais; build/migration somente com as flags informadas')) { return }
$operationLock = Enter-LocalOperation
try {
    $services = @(Read-ServiceState | Where-Object { Test-ProcessFingerprint $_ })
    if (-not (Test-LocalPort $config.db_host $config.db_port)) {
        $data = Join-Path $script:LocalPath 'postgres-tests\data'
        $versionFile = Join-Path $data 'PG_VERSION'
        if (-not (Test-Path -LiteralPath $versionFile)) {
            throw 'PostgreSQL indisponível. Inicie sua instância local (ou docker compose up -d postgres) e ajuste DATABASE_URL. Este script não cria nem apaga bancos.'
        }
        $major = (Get-Content -LiteralPath $versionFile -Raw).Trim()
        if (-not $PostgresBin) {
            $onPath = Get-Command pg_ctl.exe -ErrorAction SilentlyContinue
            $PostgresBin = if ($onPath) { Split-Path $onPath.Source } else { Join-Path $env:ProgramFiles "PostgreSQL\$major\bin" }
        }
        $pgctl = Join-Path $PostgresBin 'pg_ctl.exe'
        if (-not (Test-Path -LiteralPath $pgctl)) { throw 'pg_ctl.exe não encontrado. Informe -PostgresBin com a pasta bin da mesma versão do cluster.' }
        if ((& $pgctl --version) -notmatch ('\s' + [regex]::Escape($major) + '\.')) { throw 'A versão de pg_ctl não corresponde ao cluster existente.' }
        $port = [int]$config.db_port
        & $pgctl start -D $data -l (Join-Path $script:LocalPath 'postgres-local.log') -o "-h 127.0.0.1 -p $port" -w -t 30
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL não iniciou. Consulte .local/postgres-local.log; nenhum arquivo do cluster foi removido.' }
    }
    Push-Location $backend
    try {
        # Prontidão SQL verifica a base configurada sem mostrar DSN/credenciais.
        & $python -B (Join-Path $PSScriptRoot 'local-runtime.py') database
        if ($LASTEXITCODE -ne 0) { throw 'Banco não acessível com a configuração atual. Confira DATABASE_URL e a existência do banco; detalhes sensíveis foram omitidos.' }
        if ($Migrate) {
            & $python -m alembic upgrade head
            if ($LASTEXITCODE -ne 0) { throw 'Migration falhou. Serviços não foram iniciados.' }
        }
        & $python -B (Join-Path $PSScriptRoot 'local-runtime.py') schema
        if ($LASTEXITCODE -ne 0) { throw 'Banco sem todas as migrations. Faça backup e execute scripts/start-local.ps1 -Migrate com serviços parados.' }
    } finally { Pop-Location }
    if ($Build) {
        Push-Location $script:RepoPath
        try { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw 'Build falhou; frontend não foi iniciado.' } }
        finally { Pop-Location }
    }
    if (-not $apiOccupied) {
        $services += @(Start-LocalService 'api' $python @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000') $backend)
        Save-ServiceState $services
    }
    Wait-LocalService 'http://127.0.0.1:8000/api/v1/ready'
    $janitors = @(Find-GuidanceCleanup)
    if (-not $janitors.Count) {
        $services += @(Start-LocalService 'guidance_cleanup' $python @('-m','app.guidance_cleanup','--watch') $backend)
        Save-ServiceState $services
    }
    if (-not $frontendOccupied) {
        $services += @(Start-LocalService 'frontend' $node @((Quote-ProcessPath $next),'start',(Quote-ProcessPath $frontend),'--hostname','127.0.0.1','--port','3000') $script:RepoPath)
        Save-ServiceState $services
    }
    Wait-LocalService 'http://127.0.0.1:3000/'
    Save-ServiceState $services
    Write-Output 'BrasilPorTodos pronto: http://127.0.0.1:3000'
    Write-Output 'API e banco acessíveis. Serviços já ativos foram preservados. O banco permanece ativo ao encerrar a aplicação.'
    Write-Output 'Manutenção de logs de IA ativa em processo próprio (verificação a cada 300 segundos; sem chamadas ao Gemini).'
    Write-Output 'Coletor não iniciado: a página usa os dados já salvos. A coleta oficial é uma operação separada de administrador.'
} finally { $operationLock.Dispose() }
