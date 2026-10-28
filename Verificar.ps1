param([switch]$Inventario)
$ErrorActionPreference = 'Stop'
$telemetriaPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $telemetriaPython)) { throw 'Execute Preparar.ps1 primeiro.' }
$telemetriaArgs = @((Join-Path $PSScriptRoot 'scripts\06_verificar_kit.py'))
if ($Inventario) { $telemetriaArgs += '--inventory' }
$telemetriaEncodingAnterior = $env:PYTHONIOENCODING
try {
    $env:PYTHONIOENCODING = 'utf-8'
    & $telemetriaPython @telemetriaArgs
    $telemetriaExitCode = $LASTEXITCODE
} finally {
    $env:PYTHONIOENCODING = $telemetriaEncodingAnterior
}
exit $telemetriaExitCode
