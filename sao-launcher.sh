#!/usr/bin/env bash
# Launcher wrapper for double-click execution on Linux
# Place this file next to Server.py and make it executable: chmod +x sao-launcher.sh

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$DIR/Server.py"

if [ ! -f "$PY" ]; then
  echo "Server.py not found in $DIR"
  exit 1
fi

# Run the app fully detached so double-click doesn't block the file manager.
# Use setsid and redirect stdio; exit immediately so no terminal remains.
if command -v setsid >/dev/null 2>&1; then
  setsid python3 "$PY" >/dev/null 2>&1 </dev/null &
else
  nohup python3 "$PY" >/dev/null 2>&1 &
  disown
fi

exit 0
