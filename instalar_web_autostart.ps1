$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$KeepAlive = Join-Path $Root "bicitodo_keepalive.ps1"
$TaskName = "BiciTodo_Web_KeepAlive"

Write-Host "=== BiciTodo - Instalador Web KeepAlive ===" -ForegroundColor Cyan
Write-Host ""

try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "La tarea '$TaskName' ya existe. Reemplazando..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$KeepAlive`"" `
        -WorkingDirectory $Root

    $trigger = New-ScheduledTaskTrigger -AtLogOn

    $settings = New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -RestartCount 999 `
        -Hidden

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Mantiene arriba la API y la web local de BiciTodo"

    Start-ScheduledTask -TaskName $TaskName
    Write-Host "[OK] Tarea '$TaskName' registrada y arrancada." -ForegroundColor Green
} catch {
    Write-Host "No se pudo registrar la tarea programada. Usando Inicio de Windows..." -ForegroundColor Yellow

    $startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
    New-Item -ItemType Directory -Force -Path $startupDir | Out-Null

    $shortcutPath = Join-Path $startupDir "BiciTodo Web KeepAlive.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$KeepAlive`""
    $shortcut.WorkingDirectory = $Root
    $shortcut.WindowStyle = 7
    $shortcut.Description = "Mantiene arriba la API y la web local de BiciTodo"
    $shortcut.Save()

    Start-Process `
        -FilePath powershell.exe `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", $KeepAlive) `
        -WorkingDirectory $Root `
        -WindowStyle Hidden

    Write-Host "[OK] Acceso directo de autoinicio creado:" -ForegroundColor Green
    Write-Host "     $shortcutPath" -ForegroundColor Gray
}

Write-Host "Web: http://127.0.0.1:8080/" -ForegroundColor Cyan
Write-Host "API: http://127.0.0.1:8000/api/stats" -ForegroundColor Cyan
