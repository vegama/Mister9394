@echo off
setlocal
cd /d "%~dp0"

echo === Compilando frontend ===
call npm --prefix frontend run build
if errorlevel 1 (
    echo.
    echo La compilacion del frontend ha fallado. Revisa los errores anteriores.
    pause
    exit /b 1
)

echo.
echo === Arrancando backend (http://127.0.0.1:8000) ===
start "Mister 93/94 - Backend" cmd /k python run_football9394.py

echo === Arrancando frontend compilado (http://127.0.0.1:4173) ===
start "Mister 93/94 - Frontend" cmd /k npm --prefix frontend run preview -- --port 4173

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:4173

endlocal
