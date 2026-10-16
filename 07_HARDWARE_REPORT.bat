@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe scripts\report_hardware_baseline.py
) else (
  python scripts\report_hardware_baseline.py
)
pause
