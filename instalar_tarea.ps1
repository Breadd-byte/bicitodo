# instalar_tarea.ps1
# Ejecutar como Administrador para registrar la tarea programada

Write-Host "=== BiciTodo - Instalador de Tarea Automatica ===" -ForegroundColor Cyan
Write-Host ""

$taskName = "BiciTodo_Scraper"
$scriptPath = "c:\Users\basti\Desktop\bicitodo\run_scraper.bat"
$workDir = "c:\Users\basti\Desktop\bicitodo"

# Verificar si ya existe
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[WARN] La tarea '$taskName' ya existe. Eliminando..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Crear accion
$action = New-ScheduledTaskAction `
    -Execute $scriptPath `
    -WorkingDirectory $workDir

# Crear trigger: todos los dias a las 3am
$trigger = New-ScheduledTaskTrigger -Daily -At "03:00AM"

# Configuracion
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries

# Registrar
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Actualiza catalogo de bicicletas BiciTodo cada noche" `
    -RunLevel Highest

Write-Host ""
Write-Host "[OK] Tarea '$taskName' registrada exitosamente!" -ForegroundColor Green
Write-Host "     Correra todos los dias a las 3:00 AM" -ForegroundColor Green
Write-Host ""
Write-Host "Para correr manualmente ahora:" -ForegroundColor White
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "Para ver el estado:" -ForegroundColor White  
Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo" -ForegroundColor Gray
