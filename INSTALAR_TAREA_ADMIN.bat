@echo off
echo Instalando tarea automatica de BiciTodo...
echo Necesita permisos de Administrador.
echo.
powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File ""c:\Users\basti\Desktop\bicitodo\instalar_tarea.ps1""' -Verb RunAs"
pause
