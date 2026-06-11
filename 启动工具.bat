@echo off
cd /d "%~dp0"
if exist "%~dp0runtime\python\pythonw.exe" (
  wscript "%~dp0启动工具.vbs"
) else (
  python -m src.app
)
