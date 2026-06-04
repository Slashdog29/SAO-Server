#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Uso: $0 <token>"
  exit 2
fi

TOKEN="$1"
TARGET="$HOME/.sao_server_token"
mkdir -p "$(dirname "$TARGET")"
printf "%s" "$TOKEN" > "$TARGET"
chmod 600 "$TARGET"
echo "Token guardado en $TARGET (modo 600)."
