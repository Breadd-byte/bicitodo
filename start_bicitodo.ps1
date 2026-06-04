$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$KeepAlive = Join-Path $Root "bicitodo_keepalive.ps1"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$alreadyRunning = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine -match [regex]::Escape($KeepAlive)
    }

if (-not $alreadyRunning) {
    Start-Process `
        -FilePath powershell.exe `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $KeepAlive) `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "keepalive_start.out.log") `
        -RedirectStandardError (Join-Path $LogDir "keepalive_start.err.log")
}

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "BiciTodo local esta arriba:" -ForegroundColor Green
Write-Host "  Web: http://127.0.0.1:8080/" -ForegroundColor Cyan
Write-Host "  API: http://127.0.0.1:8000/api/stats" -ForegroundColor Cyan
Write-Host ""
Write-Host "Log del monitor:" -ForegroundColor White
Write-Host "  $LogDir\bicitodo_keepalive.log" -ForegroundColor Gray
