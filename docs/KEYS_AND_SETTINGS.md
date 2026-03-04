# Keys And Settings

## Where settings are stored

The app stores settings in the user config directory (outside the app bundle):

- macOS: `~/Library/Application Support/UofferApplication/settings.json`
- Windows: `%APPDATA%\\UofferApplication\\settings.json`
- Linux: `~/.config/UofferApplication/settings.json`

## Recommended setup flow

1. Launch the app.
2. Open the `Settings` tab.
3. Fill `OpenRouter API Key`.
4. Choose a `Default Model` (you can still override per workflow).
5. Optionally set `Data Root` (materials/converted/output/templates/contracts).
6. Save settings.

## Key rotation

When your key changes:

1. Open `Settings` tab.
2. Replace `OpenRouter API Key`.
3. Click `Save Settings`.

No code change is required.

## Security notes

- Do not hardcode keys in source code.
- Do not commit `settings.json` to git.
- Keep `.env` local only.
