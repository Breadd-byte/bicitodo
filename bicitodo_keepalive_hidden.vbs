Option Explicit

Dim shell, fso, root, powershell, keepAlive, command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

root = fso.GetParentFolderName(WScript.ScriptFullName)
powershell = "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe"
keepAlive = fso.BuildPath(root, "bicitodo_keepalive.ps1")

shell.CurrentDirectory = root
command = """" & powershell & """ -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & keepAlive & """"

' Run with window style 0 so Windows never creates a visible console for the monitor.
shell.Run command, 0, False
