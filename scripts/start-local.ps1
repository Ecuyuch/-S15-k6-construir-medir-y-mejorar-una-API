param([switch]$SinNavegador, [switch]$SinPausa)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$exitCode = 0
$transcriptStarted = $false
try {
    $logs = Join-Path $projectRoot 'logs'
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    $logPath = Join-Path $logs ('inicio-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
    Start-Transcript -LiteralPath $logPath | Out-Null
    $transcriptStarted = $true
    Write-Host '=== ReservaFlow: inicio automatico de API y PostgreSQL ==='
    $dockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
    $docker = if ($dockerCommand) { $dockerCommand.Source } else {
        Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe'
    }
    if (-not (Test-Path -LiteralPath $docker)) {
        throw 'No se encontro Docker Desktop. Instalalo con el motor Linux y vuelve a ejecutar este archivo.'
    }
    $env:Path = (Split-Path -Parent $docker) + ';' + $env:Path
    function Test-DockerReady {
        try {
            $engine = & $docker info --format '{{.OSType}}' 2>$null
            return ($LASTEXITCODE -eq 0 -and $engine -eq 'linux')
        } catch { return $false }
    }
    if (-not (Test-DockerReady)) {
        $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (-not (Test-Path -LiteralPath $desktop)) { throw 'No se encontro Docker Desktop.exe.' }
        Write-Host 'Abriendo Docker Desktop; se esperan hasta cuatro minutos...'
        Start-Process -FilePath $desktop -WindowStyle Hidden
        $deadline = (Get-Date).AddMinutes(4)
        while (-not (Test-DockerReady)) {
            if ((Get-Date) -ge $deadline) {
                throw 'Docker no quedo listo. Abre Docker Desktop, activa Linux containers y vuelve a intentar.'
            }
            Start-Sleep -Seconds 2
        }
    }
    & $docker compose version
    if ($LASTEXITCODE -ne 0) { throw 'Se requiere Docker Compose 2.24.4 o posterior.' }
    # Seleccionar la version corregida sin modificar configuraciones persistentes.
    $env:APP_VERSION = 'v2'
    Write-Host 'Iniciando los servicios de este proyecto...'
    & $docker compose up -d --build --wait --wait-timeout 180
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron iniciar los contenedores. Revisa Docker, los puertos 3001/5433 y el registro.' }
    Write-Host 'Comprobando los indices de v2 (operacion idempotente)...'
    & $docker compose exec -T db psql -U reserva -d reservaflow -v ON_ERROR_STOP=1 -f /db/v2_fix.sql
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar PostgreSQL para v2.' }
    $url = 'http://localhost:3001'
    $ready = $false
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod ($url + '/health') -TimeoutSec 4
            $availability = Invoke-RestMethod ($url + '/availability?resourceId=1&date=2026-12-01') -TimeoutSec 4
            if ($health.status -eq 'ok' -and $health.version -eq 'v2' -and $null -ne $availability) {
                $ready = $true
                break
            }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'La API o su consulta a PostgreSQL no respondieron correctamente dentro del tiempo limite.' }
    Write-Host ''
    Write-Host 'ReservaFlow esta lista.' -ForegroundColor Green
    Write-Host ('Salud:          ' + $url + '/health')
    Write-Host ('Disponibilidad: ' + $url + '/availability?resourceId=1&date=2026-12-01')
    Write-Host ('Reservas:       ' + $url + '/reservations?page=1&pageSize=5')
    Write-Host 'Puedes cerrar esta ventana; los contenedores continuaran activos.'
    Write-Host ('Registro: ' + $logPath)
    if (-not $SinNavegador) { Start-Process ($url + '/health') }
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    if ($logPath) { Write-Host ('Revisa el registro: ' + $logPath) }
    $exitCode = 1
} finally {
    if ($transcriptStarted) { Stop-Transcript | Out-Null }
    if (-not $SinPausa) { Read-Host 'Presiona Enter para cerrar' | Out-Null }
}
exit $exitCode
