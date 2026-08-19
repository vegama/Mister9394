$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = if (Get-Command py -ErrorAction SilentlyContinue) { @("py", "-3") } else { @("python") }
function Run-Python([string[]]$Args) {
    if ($python.Count -eq 2) { & $python[0] $python[1] @Args } else { & $python[0] @Args }
    if ($LASTEXITCODE -ne 0) { throw "Python termino con codigo $LASTEXITCODE" }
}

Write-Host "Instalando dependencias de herramientas..."
Run-Python @("-m", "pip", "install", "-r", "backend/requirements-dev.txt")

Write-Host "Inventariando assets que faltan..."
Run-Python @("backend/tools/build_missing_asset_manifest.py")

Write-Host "Recuperando y normalizando imagenes (proceso resumible)..."
Run-Python @("backend/tools/recover_missing_assets.py", "--delay", "0.35", "--timeout", "20", "--report", "data/football9394/missing_assets_download_report.json")
Run-Python @("backend/tools/build_missing_asset_manifest.py")

Write-Host "Auditando clubes, ligas, competiciones y estadios contra OpenFootball..."
Run-Python @("backend/tools/audit_openfootball_1993_94.py", "--refresh", "--timeout", "30", "--output", "data/football9394/openfootball_audit_1993_94.json")

Write-Host "Terminado. Los JSON de resultados estan en data/football9394/."
