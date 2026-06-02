Set WshShell = CreateObject("WScript.Shell")
' Run the batch file hidden (second argument 0 = hidden window)
WshShell.Run """%~dp0start_gui.bat""", 0, False
