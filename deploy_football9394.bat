@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%b

echo === Estado actual del repo (%BRANCH%) ===
git status --short
echo.

set /p MSG=Mensaje de commit (vacio = cancelar):
if "%MSG%"=="" (
    echo No se ha indicado mensaje de commit. Cancelado.
    pause
    exit /b 1
)

echo.
echo === git add ===
git add -A
if errorlevel 1 goto :git_error

echo === git commit ===
git commit -m "%MSG%"
if errorlevel 1 (
    echo.
    echo No hay cambios que commitear, o el commit ha fallado. Continuo sin commitear.
)

echo === git push (%BRANCH%) ===
git push origin %BRANCH%
if errorlevel 1 goto :git_error

echo.
echo === Compilando frontend ===
call npm --prefix frontend run build
if errorlevel 1 (
    echo.
    echo La compilacion del frontend ha fallado. Revisa los errores anteriores.
    pause
    exit /b 1
)

echo.
echo === Preparando dist para subir, sin assets ^(historical9394^) ===
if exist deploy_dist rd /s /q deploy_dist
robocopy frontend\dist deploy_dist /E /XD historical9394 >nul
if %ERRORLEVEL% GEQ 8 goto :robocopy_error

echo.
echo Listo. Carpeta preparada para subir: deploy_dist
echo   (no incluye frontend\dist\historical9394 - fotos/escudos, se asume ya subidos)
pause
exit /b 0

:git_error
echo.
echo Ha fallado un paso de git. Revisa el mensaje anterior.
pause
exit /b 1

:robocopy_error
echo.
echo Ha fallado la copia a deploy_dist. Revisa el mensaje anterior.
pause
exit /b 1
