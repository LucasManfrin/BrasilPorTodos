$ErrorActionPreference = 'Stop'
$repoPath = Split-Path $PSScriptRoot
& (Join-Path $PSScriptRoot 'setup-local.ps1')
$dockerEnvironment = Join-Path $repoPath '.env'
if (Test-Path -LiteralPath $dockerEnvironment) {
    Write-Output 'Ambiente Docker existente preservado. Confira POSTGRES_PASSWORD e as portas no .env da raiz.'
} else {
    $secretBytes = New-Object byte[] 32
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($secretBytes) } finally { $generator.Dispose() }
    # Hex evita caracteres especiais na URL SQL e na interpolacao do Compose.
    $databasePassword = -join ($secretBytes | ForEach-Object { $_.ToString('x2') })
    $template = [IO.File]::ReadAllText((Join-Path $repoPath '.env.example'))
    $template = $template.Replace('POSTGRES_PASSWORD=', "POSTGRES_PASSWORD=$databasePassword")
    [IO.File]::WriteAllText($dockerEnvironment,$template,[Text.UTF8Encoding]::new($false))
    Write-Output 'Ambiente Docker criado com senha aleatoria; arquivos locais anteriores preservados.'
}
Write-Output 'JWT_SECRET e Gemini: backend/.env. Senha do banco e portas Docker: .env da raiz.'
Write-Output 'Inicie com docker compose up -d --build. Nunca versione arquivos .env.'
