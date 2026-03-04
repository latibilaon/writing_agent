#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY=${PYTHON_BIN:-python3}

$PY -m venv .venv-build
source .venv-build/bin/activate
pip install -U pip
pip install -r requirements.txt

pyinstaller --noconfirm --windowed --name UofferPortable launch_app.py

mkdir -p dist
if [ -d "dist/UofferPortable.app" ]; then
  hdiutil create -volname "UofferPortable" -srcfolder "dist/UofferPortable.app" -ov -format UDZO "dist/UofferPortable.dmg"
  echo "Built: dist/UofferPortable.dmg"
else
  echo "Expected app bundle not found at dist/UofferPortable.app"
  exit 1
fi
