Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = scriptDir
cmd = "pythonw.exe \"" & scriptDir & "\main.py\""
objShell.Run cmd, 0, False
