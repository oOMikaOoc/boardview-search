@echo off
setlocal
cd /d "%~dp0"

echo Installation de Boardview Search pour le PC d'atelier...

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3.11 -m venv .venv
) else (
    python -m venv .venv
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Impossible de creer l'environnement virtuel .venv.
    echo Verifie que Python 3.11 est installe et accessible.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo Fichier .env cree depuis .env.example. Pense a renseigner Telegram si besoin.
)

echo.
echo Installation terminee.
echo Lance ensuite start_atelier.bat pour demarrer l'application.
pause
