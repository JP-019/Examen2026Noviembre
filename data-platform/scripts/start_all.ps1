# Arranca el servicio de catalogo (indice vivo de la plataforma).
# Uso: powershell -ExecutionPolicy Bypass -File scripts/start_all.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "Plataforma de datos - arranque local" -ForegroundColor Cyan
Write-Host "Raiz: $root"

Write-Host ""
Write-Host "[1/2] Verificando conexion a SQL Server..." -ForegroundColor Yellow
$check = sqlcmd -S localhost -E -C -Q "SET NOCOUNT ON; SELECT DB_ID('DataPlatform')" -h -1 -W
if ($LASTEXITCODE -ne 0) {
    Write-Host "No se pudo conectar a SQL Server. Revisar instancia y driver ODBC." -ForegroundColor Red
    exit 1
}
if ($check.Trim() -eq "NULL") {
    Write-Host "La base DataPlatform no existe. Ejecutar los scripts de database/." -ForegroundColor Red
    exit 1
}
Write-Host "SQL Server OK" -ForegroundColor Green

Write-Host ""
Write-Host "[2/2] Iniciando catalogo en http://localhost:8001 ..." -ForegroundColor Yellow
Write-Host "Indice: http://localhost:8001/index.md"
Write-Host "Swagger: http://localhost:8001/docs"
Push-Location (Join-Path $root "services/catalog")
try {
    python -m uvicorn app.main:app --port 8001
}
finally {
    Pop-Location
}
