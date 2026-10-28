param([switch]$Offline)
$ErrorActionPreference = 'Stop'
$telemetriaPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $telemetriaPython)) {
    $telemetriaBase = Get-Command python -ErrorAction Stop
    & $telemetriaBase.Source -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'Instale Python 3.10 ou superior antes de preparar o kit.' }
    & $telemetriaBase.Source -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o ambiente Python.' }
}
$telemetriaWheels = Join-Path $PSScriptRoot 'offline'
if ($Offline -or (Test-Path -LiteralPath $telemetriaWheels)) {
    & $telemetriaPython -m pip install --no-index --find-links $telemetriaWheels -r (Join-Path $PSScriptRoot 'requirements.txt') --disable-pip-version-check
} else {
    & $telemetriaPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt') --disable-pip-version-check
}
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias. Confira as wheels offline ou a conexao.' }
& (Join-Path $PSScriptRoot 'Verificar.ps1')
exit $LASTEXITCODE
