@echo off
setlocal EnableExtensions
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

echo [1/4] Preparando dependencias...
%PY% -m pip install -r backend\requirements-dev.txt
if errorlevel 1 goto :error

echo [2/4] Reconstruyendo JSON de assets que faltan...
%PY% backend\tools\build_missing_asset_manifest.py
if errorlevel 1 goto :error

echo [3/4] Descargando y normalizando BDFutbol / Wikimedia Commons...
%PY% backend\tools\recover_missing_assets.py --delay 0.35 --timeout 20 --report data\football9394\missing_assets_download_report.json
if errorlevel 1 goto :error

echo [4/4] Actualizando JSON final de huecos restantes...
%PY% backend\tools\build_missing_asset_manifest.py
if errorlevel 1 goto :error

echo.
echo LISTO. Revisa:
echo   data\football9394\missing_assets_1993_94.json
echo   data\football9394\missing_assets_download_report.json
echo.
pause
exit /b 0

:error
echo.
echo ERROR. El proceso se puede volver a ejecutar: es resumible y no pisa assets correctos.
pause
exit /b 1
