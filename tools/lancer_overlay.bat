@echo off
rem Double-clic pour lancer l'overlay Queens (Windows).
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
    echo Environnement .venv introuvable : suis d'abord docs\overlay_windows.md
    pause
    exit /b 1
)
".venv\Scripts\python.exe" tools\queens_overlay.py %*
pause
