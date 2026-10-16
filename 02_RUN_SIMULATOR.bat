@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run 01_SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m parrotcore.cli demo
pause
