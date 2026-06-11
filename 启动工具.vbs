Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = projectDir

runtimePython = projectDir & "\runtime\python\pythonw.exe"
If fso.FileExists(runtimePython) Then
  command = """" & runtimePython & """ -m src.app"
Else
  command = "python -m src.app"
End If

shell.Run command, 0, False
