# Deployment Guide

This project supports local packaging for:

- macOS `.dmg`
- Windows `.exe`

## Prerequisites

- Python 3.11+ recommended
- internet access for dependency installation

## Build macOS DMG

Run on macOS:

```bash
cd "<repo-root>"
./build/build_mac.sh
```

Expected output:

- `dist/UofferPortable.app`
- `dist/UofferPortable.dmg`

## Build Windows EXE

Run on Windows PowerShell:

```powershell
cd "<repo-root>"
.\build\build_win.ps1
```

Expected output:

- `dist/UofferPortable.exe`
- `dist/UofferPortable-win.zip`

## Why two build machines

Native GUI binaries should be built on their target OS:

- Build `.dmg` on macOS
- Build `.exe` on Windows

## Distribution

You can upload `dist/UofferPortable.dmg` and `dist/UofferPortable.exe` to any file host or release page.

## CI / GitHub Actions

This repository includes `.github/workflows/ci-build.yml`:

- installs Python dependencies automatically
- runs compile checks
- builds macOS and Windows artifacts
- uploads build artifacts to the workflow run
