$ErrorActionPreference = 'Stop'
$script:RepoPath = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent)).TrimEnd('\')
$script:LocalPath = Join-Path $script:RepoPath '.local'
$script:StatePath = Join-Path $script:LocalPath 'local-services.json'

function Get-LocalConfiguration {
    $python = Join-Path $script:RepoPath 'backend\.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        throw 'Ambiente Python ausente. Em backend/, execute uv sync --frozen --group dev.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $script:RepoPath 'backend\.env'))) {
        throw 'Ambiente ausente. Execute scripts/setup-local.ps1 e configure DATABASE_URL antes de iniciar.'
    }
    Push-Location (Join-Path $script:RepoPath 'backend')
    try {
        $raw = & $python -B (Join-Path $PSScriptRoot 'local-runtime.py') configuration
        if ($LASTEXITCODE -ne 0) { throw 'Configuração local inválida. Confira backend/.env; os valores foram omitidos para proteger segredos.' }
        $config = $raw | ConvertFrom-Json
    } finally { Pop-Location }
    if ($config.db_driver -notlike 'postgresql*') { throw 'DATABASE_URL precisa usar PostgreSQL.' }
    if ($config.db_host -notin @('127.0.0.1','localhost','::1')) { throw 'Estes scripts operam somente com banco local (loopback).' }
    if (-not $config.jwt_ready) { throw 'Configure JWT_SECRET com pelo menos 32 caracteres no backend/.env.' }
    if ($config.cookie_secure) { throw 'Para HTTP no computador, configure COOKIE_SECURE=false no backend/.env. Produção HTTPS deve usar true.' }
    if ($config.api_url.TrimEnd('/') -notin @('http://127.0.0.1:8000','http://localhost:8000')) {
        throw 'frontend/.env.local deve apontar API_INTERNAL_URL para http://127.0.0.1:8000 neste fluxo local.'
    }
    return $config
}

function Test-LocalPort([string] $Address, [int] $Port) {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync($Address, $Port)
        if (-not $connection.Wait(1200)) { return $false }
        return $client.Connected
    } catch { return $false } finally { $client.Dispose() }
}

function Test-LocalHttp([string] $Url, [string] $ExpectedName = '') {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4 -MaximumRedirection 0
        if ($response.StatusCode -ne 200) { return $false }
        if ($ExpectedName) { return $response.Content.Contains($ExpectedName) }
        return $true
    } catch { return $false }
}

function Test-ServiceRepository([int] $Port) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    if (-not $listeners.Count) { return $false }
    foreach ($listener in $listeners) {
        $ownerId = [int]$listener.OwningProcess
        $matched = $false
        # A instalação precisa aparecer no executável/comando do listener ou de
        # seu launcher. Um site homônimo de outra pasta não será adotado.
        for ($level=0; $level -lt 3 -and $ownerId -gt 0; $level++) {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $ownerId" -ErrorAction SilentlyContinue
            if (-not $owner) { break }
            $identity = [string]$owner.CommandLine + ' ' + [string]$owner.ExecutablePath
            if ($identity.IndexOf($script:RepoPath + '\',[StringComparison]::OrdinalIgnoreCase) -ge 0) { $matched = $true; break }
            $ownerId = [int]$owner.ParentProcessId
        }
        if (-not $matched) { return $false }
    }
    return $true
}

function Find-GuidanceCleanup {
    $moduleFile = Join-Path $script:RepoPath 'backend\app\guidance_cleanup.py'
    $modulePattern = '(?:^|\s)-m\s+app\.guidance_cleanup(?:\s|$)|' + [regex]::Escape($moduleFile)
    $candidates = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction SilentlyContinue)
    foreach ($candidate in $candidates) {
        if ([string]$candidate.CommandLine -notmatch $modulePattern) { continue }
        if ([string]$candidate.CommandLine -notmatch '(?:^|\s)--watch(?:\s|$)') { continue }
        $ownerId = [int]$candidate.ProcessId
        $belongs = $false
        for ($level=0; $level -lt 3 -and $ownerId -gt 0; $level++) {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $ownerId" -ErrorAction SilentlyContinue
            if (-not $owner) { break }
            $identity = [string]$owner.CommandLine + ' ' + [string]$owner.ExecutablePath
            if ($identity.IndexOf($script:RepoPath + '\',[StringComparison]::OrdinalIgnoreCase) -ge 0) { $belongs = $true; break }
            $ownerId = [int]$owner.ParentProcessId
        }
        if ($belongs) {
            $fingerprint = Get-ProcessFingerprint ([int]$candidate.ProcessId)
            if ($fingerprint) { $fingerprint }
        }
    }
}

function Read-ServiceState {
    if (-not (Test-Path -LiteralPath $script:StatePath)) { return @() }
    try {
        $saved = Get-Content -LiteralPath $script:StatePath -Raw | ConvertFrom-Json
        if ($saved.repository -ne $script:RepoPath -or $saved.version -ne 1) {
            throw 'Registro pertence a outra pasta ou versão.'
        }
        return @($saved.services)
    } catch { throw 'Registro .local/local-services.json inválido. Não será usado para encerrar processos.' }
}

function Save-ServiceState([object[]] $Services) {
    $state = @{version=1; repository=$script:RepoPath; services=@($Services)}
    $temp = Join-Path $script:LocalPath ('services-' + [guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllText($temp, ($state | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $temp -Destination $script:StatePath -Force
    } finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp } }
}

function Get-ProcessFingerprint([int] $ProcessId) {
    $item = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $item -or -not $item.ExecutablePath -or -not $item.CommandLine) { return $null }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $hash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($item.CommandLine))) }
    finally { $sha.Dispose() }
    return [pscustomobject]@{id=$ProcessId; executable=$item.ExecutablePath; born=$item.CreationDate.ToUniversalTime().ToString('o'); command_hash=$hash}
}

function Test-ProcessFingerprint($Saved) {
    $actual = Get-ProcessFingerprint ([int]$Saved.id)
    return ($actual -and $actual.executable -eq $Saved.executable -and $actual.born -eq $Saved.born -and $actual.command_hash -eq $Saved.command_hash)
}

function Quote-ProcessPath([string] $Path) {
    if ($Path.Contains('"') -or $Path.Contains("`n") -or $Path.Contains("`r")) { throw 'Caminho inválido para execução local.' }
    return '"' + $Path + '"'
}

function Start-LocalService([string] $Kind, [string] $Executable, [string[]] $Arguments, [string] $Directory) {
    $process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Directory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $script:LocalPath "$Kind-local.out.log") -RedirectStandardError (Join-Path $script:LocalPath "$Kind-local.err.log")
    Start-Sleep -Milliseconds 250
    $fingerprint = Get-ProcessFingerprint $process.Id
    if (-not $fingerprint) { throw "Não foi possível iniciar $Kind. Consulte os logs em .local/." }
    $fingerprint | Add-Member -NotePropertyName kind -NotePropertyValue $Kind
    # Python venv no Windows pode manter um launcher e um filho. Registra os dois,
    # com identidade e nascimento exatos, sem procurar/encerrar processos por nome.
    $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $($process.Id)" -ErrorAction SilentlyContinue)
    $entries = @($fingerprint)
    foreach ($child in $children) {
        $childIdentity = Get-ProcessFingerprint $child.ProcessId
        if ($childIdentity) { $childIdentity | Add-Member -NotePropertyName kind -NotePropertyValue $Kind; $entries += $childIdentity }
    }
    return $entries
}

function Wait-LocalService([string] $Url, [int] $Seconds = 45) {
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    do {
        if (Test-LocalHttp $Url) { return }
        Start-Sleep -Milliseconds 500
    } while ([DateTime]::UtcNow -lt $deadline)
    throw 'O serviço não ficou pronto. Consulte .local/*-local.err.log e execute scripts/status-local.ps1.'
}

function Enter-LocalOperation {
    New-Item -ItemType Directory -Path $script:LocalPath -Force | Out-Null
    try { return [IO.File]::Open((Join-Path $script:LocalPath 'services.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
    catch { throw 'Outra operação local está em andamento. Aguarde e tente novamente.' }
}
