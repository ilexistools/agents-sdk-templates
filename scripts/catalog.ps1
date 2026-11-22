<#
.SYNOPSIS
  Start, stop or check the catalog dashboard on Windows.

.DESCRIPTION
  start   Installs dependencies on first use, starts the dashboard + API in the
          background, waits until it answers and opens the browser.
  stop    Stops the dashboard started by this script.
  status  Shows whether it is running.
  restart Stops and starts again.

  The port comes from the PORT environment variable (default 8787).
  Logs: .run\catalog.log and .run\catalog.err.log. PID: .run\catalog.pid.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\catalog.ps1 start
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'restart')]
    [string]$Command = 'start',
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $Root '.run'
$PidFile = Join-Path $RunDir 'catalog.pid'
$LogFile = Join-Path $RunDir 'catalog.log'
$ErrFile = Join-Path $RunDir 'catalog.err.log'
$Port = if ($env:PORT) { $env:PORT } else { '8787' }
$Url = "http://127.0.0.1:$Port"
$Python = Join-Path $Root '.venv\Scripts\python.exe'

function Get-RunningProcess {
    if (-not (Test-Path $PidFile)) { return $null }
    $id = (Get-Content $PidFile -Raw).Trim()
    if (-not $id) { return $null }
    $process = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($process) { return $process }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    return $null
}

function Test-Healthy {
    try {
        $response = Invoke-WebRequest -Uri "$Url/health" -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Start-Catalog {
    $running = Get-RunningProcess
    if ($running) {
        Write-Host "Already running (PID $($running.Id)) at $Url"
        if (-not $NoBrowser) { Start-Process $Url }
        return
    }
    if (Test-Healthy) {
        Write-Host "Something is already answering at $Url (not started by this script)."
        Write-Host "Stop it, or choose another port: `$env:PORT = '8790'; scripts\start.cmd"
        exit 1
    }
    if (-not (Test-Path $Python)) {
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            Write-Host 'uv is required and was not found. Install it, then run this again:'
            Write-Host '  https://docs.astral.sh/uv/getting-started/installation/'
            exit 1
        }
        Write-Host 'Installing dependencies (first run)...'
        Push-Location $Root
        try { uv sync --locked } finally { Pop-Location }
        if ($LASTEXITCODE -ne 0) { Write-Host 'uv sync failed.'; exit 1 }
    }
    New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
    $process = Start-Process -FilePath $Python -ArgumentList '-m', 'app', 'serve', '--port', $Port `
        -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $LogFile -RedirectStandardError $ErrFile
    Set-Content -Path $PidFile -Value $process.Id -Encoding ascii
    Write-Host -NoNewline "Starting at $Url "
    for ($i = 0; $i -lt 60; $i++) {
        if (Test-Healthy) {
            Write-Host ''
            Write-Host "Running (PID $($process.Id)). Stop it with scripts\stop.cmd"
            if (-not $NoBrowser) { Start-Process $Url }
            return
        }
        if ($process.HasExited) { break }
        Write-Host -NoNewline '.'
        Start-Sleep -Milliseconds 500
    }
    Write-Host ''
    Write-Host "It did not start. Last lines of $ErrFile`:"
    if (Test-Path $ErrFile) { Get-Content $ErrFile -Tail 15 }
    Stop-Catalog -Quiet
    exit 1
}

function Stop-Catalog {
    param([switch]$Quiet)
    $running = Get-RunningProcess
    if (-not $running) {
        if (-not $Quiet) {
            Write-Host 'Not running (no process started by this script).'
            if (Test-Healthy) { Write-Host "Note: something else is answering at $Url." }
        }
        return
    }
    # /T also stops child processes (uvicorn reloaders, workers).
    & taskkill.exe /PID $running.Id /T /F | Out-Null
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    if (-not $Quiet) { Write-Host "Stopped (PID $($running.Id))." }
}

function Show-Status {
    $running = Get-RunningProcess
    if ($running -and (Test-Healthy)) { Write-Host "Running (PID $($running.Id)) at $Url" }
    elseif ($running) { Write-Host "Process $($running.Id) exists but $Url is not answering yet. See $ErrFile" }
    else { Write-Host 'Not running.' }
}

switch ($Command) {
    'start' { Start-Catalog }
    'stop' { Stop-Catalog }
    'status' { Show-Status }
    'restart' { Stop-Catalog -Quiet; Start-Catalog }
}
