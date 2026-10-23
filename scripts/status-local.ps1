[CmdletBinding()]
param([switch] $Json)
. (Join-Path $PSScriptRoot 'local-common.ps1')
$configurationError = $null
try { $config = Get-LocalConfiguration } catch { $configurationError = $_.Exception.Message }
$databaseReady = if ($config) { Test-LocalPort $config.db_host $config.db_port } else { $false }
$api = Test-LocalHttp 'http://127.0.0.1:8000/openapi.json' 'BrasilPorTodos API'
$apiReady = $api -and (Test-LocalHttp 'http://127.0.0.1:8000/api/v1/ready')
$frontendReady = Test-LocalHttp 'http://127.0.0.1:3000/' 'BrasilPorTodos'
$janitorRunning = @(Find-GuidanceCleanup).Count -gt 0
$stateError = $null
try { $services = @(Read-ServiceState); $managed = @($services | Where-Object { Test-ProcessFingerprint $_ } | ForEach-Object { $_.kind } | Select-Object -Unique) }
catch { $stateError = $_.Exception.Message; $managed = @() }
$result = [pscustomobject]@{
    repository=$script:RepoPath; site='http://127.0.0.1:3000'; frontend_ready=$frontendReady;
    api_ready=$apiReady; database_listening=$databaseReady; managed_services=$managed;
    guidance_cleanup_process_running=$janitorRunning;
    configuration_error=$configurationError; state_error=$stateError;
    ready=([bool]($frontendReady -and $apiReady -and -not $configurationError))
}
if ($Json) { $result | ConvertTo-Json -Depth 3 } else {
    $result | Format-List
    Write-Output 'database_listening verifica a porta; api_ready confirma a conexão da API com o banco configurado.'
    Write-Output 'guidance_cleanup_process_running indica somente processo vivo, não garantia de execução bem-sucedida nem retenção enquanto o computador estiver desligado.'
    Write-Output 'Logs: .local/*-local.out.log e .local/*-local.err.log. Segredos e senhas não são exibidos.'
}
