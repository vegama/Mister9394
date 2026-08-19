@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (set "PY=py -3") else (set "PY=python")

echo Descargando/cacheando OpenFootball y cruzando el mundo 1993-94...
%PY% backend\tools\audit_openfootball_1993_94.py --refresh --timeout 30 --output data\football9394\openfootball_audit_1993_94.json
if errorlevel 1 goto :error

echo.
echo LISTO. Revisa data\football9394\openfootball_audit_1993_94.json
pause
exit /b 0

:error
echo.
echo No se pudo completar la descarga. Si ya existe cache, ejecuta sin --refresh:
echo   %PY% backend\tools\audit_openfootball_1993_94.py
pause
exit /b 1
