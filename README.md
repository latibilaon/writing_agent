# Uoffer Portable Application

A portable, migration-friendly desktop app that removes hardcoded local paths and embedded sensitive settings.

## Included workflows

- Offer Appeal (minimal-input mode)
- Lease Direct Generation
- Lease Template Rewrite
- Settings panel (key/model/data root)

## Quick start (local)

```bash
cd "<repo-root>"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python launch_app.py
```

## Why this is portable

- No absolute user-specific paths in code
- No hardcoded API keys
- Settings saved to per-user config directory
- Runtime data stored in configurable data root

## Packaging

- macOS DMG: `./build/build_mac.sh`
- Windows EXE: `./build/build_win.ps1`
- GitHub Actions CI build: `.github/workflows/ci-build.yml`

See:

- `docs/DEPLOYMENT.md`
- `docs/KEYS_AND_SETTINGS.md`
- `docs/TROUBLESHOOTING.md`

## Notes

- First launch: configure OpenRouter key in `Settings`.
- Models can be edited directly in each workflow tab.
