param([ValidateSet('Stop','Start')][string]$Action)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$recordPath = Join-Path $projectRoot 'results\evaluacion-2026-11-14\servicios-windows-temporales.json'
$serviceNames = @('OracleServiceXE','MSSQLSERVER','MSSQL$SQLEXPRESS')
if ($Action -eq 'Stop') {
    $record = [ordered]@{ authorized=$true; stoppedAt=(Get-Date).ToUniversalTime().ToString('o'); services=@(); restoredAt=$null }
    foreach ($serviceName in $serviceNames) {
        $service = Get-Service -Name $serviceName
        $record.services += [pscustomobject]@{name=$serviceName; originalStatus=$service.Status.ToString()}
    }
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding utf8
    foreach ($service in $record.services) {
        if ($service.originalStatus -eq 'Running') {
            Stop-Service -Name $service.name
            (Get-Service -Name $service.name).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(60))
        }
    }
} else {
    $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
    foreach ($service in $record.services) {
        if ($service.originalStatus -eq 'Running') {
            Start-Service -Name $service.name
            (Get-Service -Name $service.name).WaitForStatus('Running',[TimeSpan]::FromSeconds(60))
        }
    }
    $record.restoredAt = (Get-Date).ToUniversalTime().ToString('o')
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding utf8
}
