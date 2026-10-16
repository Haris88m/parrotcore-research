@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set PY=.venv\Scripts\python.exe
) else (
  set PY=python
)
set PYTHONPATH=%CD%\src
start "ParrotCore Creature Lab" http://127.0.0.1:8770
%PY% -m parrotcore.cli creature-lab
pause
