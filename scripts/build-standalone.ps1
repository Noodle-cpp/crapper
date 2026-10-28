# Build crapper.exe (PyInstaller one-file). Requires Python 3.11+ once for the build machine.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

& $Pip install -q -e ".[dev]" pyinstaller
& $Py -m PyInstaller packaging\crapper.spec --noconfirm

Write-Host ""
Write-Host "Built: $Root\dist\crapper.exe"
Write-Host "Copy to PATH or run: dist\crapper.exe --help"
