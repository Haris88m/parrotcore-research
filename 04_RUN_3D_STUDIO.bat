@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  set PY=.venv\Scripts\python.exe
) else (
  set PY=python
)
set PYTHONPATH=%CD%\src
start "" http://127.0.0.1:8765
%PY% -m parrotcore.cli studio --host 127.0.0.1 --port 8765
pause
