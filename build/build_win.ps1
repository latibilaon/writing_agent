$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = $env:PYTHON_BIN
if (-not $Python) { $Python = "python" }

& $Python -m venv .venv-build
& .\.venv-build\Scripts\python -m pip install -U pip
& .\.venv-build\Scripts\python -m pip install -r requirements.txt

& .\.venv-build\Scripts\pyinstaller --noconfirm --noconsole --onefile --name UofferPortable launch_app.py

New-Item -ItemType Directory -Path dist -Force | Out-Null
if (Test-Path ".\dist\UofferPortable.exe") {
  Compress-Archive -Path ".\dist\UofferPortable.exe" -DestinationPath ".\dist\UofferPortable-win.zip" -Force
  Write-Host "Built: dist/UofferPortable.exe"
  Write-Host "Built: dist/UofferPortable-win.zip"
} else {
  throw "Expected exe not found at dist/UofferPortable.exe"
}
