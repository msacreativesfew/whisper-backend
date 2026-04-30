Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
' The 0 at the end makes the window invisible
WshShell.Run "uv run desktop_app.py", 0, False
