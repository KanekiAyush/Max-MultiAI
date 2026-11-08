Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Games\MAX"
' pythonw.exe use kar rahe hain taaki black window na khule
WshShell.Run """D:\Games\MAX\venv\Scripts\pythonw.exe"" main.py", 0, False