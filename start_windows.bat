@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

start "Boardview Search" http://127.0.0.1:5000/
%PYTHON_EXE% telegram_boardview_web.py

echo.
echo Application arretee.
pause
