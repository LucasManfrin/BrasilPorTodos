$ErrorActionPreference = 'Stop'
$repoPath = Split-Path $PSScriptRoot
$backendEnv = Join-Path $repoPath 'backend\.env'
if (-not (Test-Path -LiteralPath $backendEnv)) {
    $envText = [System.IO.File]::ReadAllText((Join-Path $repoPath 'backend\.env.example'))
    $secretBytes = New-Object byte[] 48
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($secretBytes) } finally { $generator.Dispose() }
    $secret = [Convert]::ToBase64String($secretBytes)
    $envText = $envText.Replace('JWT_SECRET=', "JWT_SECRET=$secret")
    [System.IO.File]::WriteAllText($backendEnv, $envText, [System.Text.UTF8Encoding]::new($false))
    Write-Output 'Ambiente backend criado com chave de sessão aleatória.'
} else {
    Write-Output 'Ambiente backend existente preservado.'
}
$frontendEnv = Join-Path $repoPath 'frontend\.env.local'
if (-not (Test-Path -LiteralPath $frontendEnv)) {
    Copy-Item -LiteralPath (Join-Path $repoPath 'frontend\.env.example') -Destination $frontendEnv
}
