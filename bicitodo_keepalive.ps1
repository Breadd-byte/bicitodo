$ErrorActionPreference = "Stop"

$ScriptPath = $PSCommandPath
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "fronted"
$LogDir = Join-Path $Root "logs"
$MonitorLog = Join-Path $LogDir "bicitodo_keepalive.log"
$ApiUrl = "http://127.0.0.1:8000/api/stats"
$WebUrl = "http://127.0.0.1:8080/"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-MonitorLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $MonitorLog -Value $line -Encoding UTF8
}

function Exit-IfAlreadyRunning {
    $others = Get-CimInstance Win32_Process |
        Where-Object {
            $_.ProcessId -ne $PID -and
            $_.CommandLine -and
            $_.CommandLine -match [regex]::Escape($ScriptPath)
        }

    if ($others) {
        Write-MonitorLog "Another keepalive process is already running. Exiting current PID $PID."
        exit 0
    }
}

function Get-PythonPath {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        return $cmd.Source
    }

    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        return $cmd.Source
    }

    return $null
}

function Test-PortOpen {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connect = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $connect.AsyncWaitHandle.WaitOne(1000, $false)) {
            return $false
        }
        $client.EndConnect($connect)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Test-HttpOk {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    } catch {
        return $false
    }
}

function Start-BiciTodoApi {
    $python = Get-PythonPath
    if (-not $python) {
        Write-MonitorLog "Python was not found in PATH. Cannot start API."
        return
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Write-MonitorLog "Starting API on http://127.0.0.1:8000"
    Start-Process `
        -FilePath $python `
        -ArgumentList @("-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $BackendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "api_$stamp.out.log") `
        -RedirectStandardError (Join-Path $LogDir "api_$stamp.err.log")
}

function Start-BiciTodoWeb {
    $python = Get-PythonPath
    if (-not $python) {
        Write-MonitorLog "Python was not found in PATH. Cannot start frontend."
        return
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Write-MonitorLog "Starting frontend on http://127.0.0.1:8080"
    Start-Process `
        -FilePath $python `
        -ArgumentList @("-m", "http.server", "8080", "--bind", "127.0.0.1") `
        -WorkingDirectory $FrontendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "frontend_$stamp.out.log") `
        -RedirectStandardError (Join-Path $LogDir "frontend_$stamp.err.log")
}

function Ensure-BiciTodoUp {
    if (-not (Test-PortOpen -Port 8000)) {
        Start-BiciTodoApi
        Start-Sleep -Seconds 3
    }

    if (-not (Test-PortOpen -Port 8080)) {
        Start-BiciTodoWeb
        Start-Sleep -Seconds 2
    }

    if (-not (Test-HttpOk -Url $ApiUrl)) {
        Write-MonitorLog "API health check failed. Waiting for next cycle."
    }

    if (-not (Test-HttpOk -Url $WebUrl)) {
        Write-MonitorLog "Frontend health check failed. Waiting for next cycle."
    }
}

Exit-IfAlreadyRunning
Write-MonitorLog "Keepalive started with PID $PID."

while ($true) {
    try {
        Ensure-BiciTodoUp
    } catch {
        Write-MonitorLog ("Keepalive cycle error: " + $_.Exception.Message)
    }
    Start-Sleep -Seconds 30
}
