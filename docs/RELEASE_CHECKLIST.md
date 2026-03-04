# Release Checklist

## Pre-release

- [ ] Update app version in release notes.
- [ ] Verify no real API key in source code.
- [ ] Verify `settings.json` is not bundled.
- [ ] Run local smoke test (`python launch_app.py`).

## Build artifacts

- [ ] Build macOS DMG (`./build/build_mac.sh`).
- [ ] Build Windows EXE (`./build/build_win.ps1`).
- [ ] Confirm generated files in `dist/`:
  - `UofferPortable.dmg`
  - `UofferPortable.exe`

## Validation

- [ ] Fresh machine test: launch app without pre-existing config.
- [ ] Confirm Settings tab prompts for API key.
- [ ] Confirm model field accepts manual model id.
- [ ] Confirm Offer workflow runs with minimal input.

## Release package

- [ ] Upload artifacts and docs.
- [ ] Include `KEYS_AND_SETTINGS.md` for end users.
