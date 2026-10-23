[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
param()
. (Join-Path $PSScriptRoot 'local-common.ps1')
$services = @(Read-ServiceState)
if (-not $services.Count) { Write-Output 'Nenhum serviço registrado por este launcher. Processos externos e PostgreSQL foram preservados.'; return }
if (-not $PSCmdlet.ShouldProcess($script:RepoPath, 'Encerrar somente processos registrados que ainda correspondem à identidade original (preserva PostgreSQL)')) { return }
$operationLock = Enter-LocalOperation
try {
    $services = @(Read-ServiceState)
    # Filhos primeiro: launcher Python pode sair quando seu filho termina.
    [array]::Reverse($services)
    foreach ($service in $services) {
        if ($service.kind -notin @('api','frontend','collector','guidance_cleanup')) { throw 'Tipo de processo desconhecido no registro. Nenhum processo adicional será encerrado.' }
        $moduleMatches = $service.kind -ne 'guidance_cleanup' -or @((Find-GuidanceCleanup) | Where-Object { $_.id -eq $service.id }).Count -gt 0
        if ($moduleMatches -and (Test-ProcessFingerprint $service)) {
            Stop-Process -Id ([int]$service.id) -ErrorAction Stop
            Write-Output "$($service.kind) encerrado."
        } else { Write-Output "$($service.kind): processo já encerrado ou identidade diferente; preservado." }
    }
    Save-ServiceState @()
    Write-Output 'PostgreSQL e serviços iniciados fora deste launcher foram preservados.'
} finally { $operationLock.Dispose() }
