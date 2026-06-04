#!/usr/bin/env bash
set -euo pipefail

# Asegura que la clave de github.com esté en ~/.ssh/known_hosts y luego hace git pull

KNOWN_HOSTS="$HOME/.ssh/known_hosts"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if ! ssh-keygen -F github.com >/dev/null 2>&1; then
  ssh-keyscan -t ed25519 github.com >> "$KNOWN_HOSTS" 2>/dev/null || true
  ssh-keyscan -t rsa github.com >> "$KNOWN_HOSTS" 2>/dev/null || true
  chmod 600 "$KNOWN_HOSTS"
fi

# Ejecutar git pull para la rama actual (se asume ejecutar dentro del repo)
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
git pull origin "$branch"
