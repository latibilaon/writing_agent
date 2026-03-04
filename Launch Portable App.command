#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PY=""
if [ -x "$DIR/.venv/bin/python" ]; then
  PY="$DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  osascript -e 'display alert "Python 3 not found" message "Please install Python 3 and retry." as critical'
  exit 1
fi

if [ ! -x "$DIR/.venv/bin/python" ]; then
  "$PY" -m venv "$DIR/.venv"
  "$DIR/.venv/bin/python" -m pip install -U pip
  "$DIR/.venv/bin/python" -m pip install -r "$DIR/requirements.txt"
fi

exec "$DIR/.venv/bin/python" "$DIR/launch_app.py"
