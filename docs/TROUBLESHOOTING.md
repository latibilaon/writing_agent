# Troubleshooting

## 1) "OpenRouter API key missing"

Set key in `Settings` tab and save.

## 2) PDF cannot be parsed

Install optional parser dependencies:

```bash
pip install pymupdf pymupdf4llm pypdf
```

If still failing, place a text summary file in materials as fallback.

## 3) DOCX export skipped

Install:

```bash
pip install python-docx
```

## 4) Build fails in PyInstaller

Check:

- correct Python version
- pip dependencies installed
- build script run from repository root

## 5) Model id invalid

Use a valid OpenRouter model id, e.g.:

- `anthropic/claude-sonnet-4.6`
- `anthropic/claude-opus-4.1`
- `google/gemini-2.5-pro-preview-03-25`
