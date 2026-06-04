#!/usr/bin/env bash
set -euo pipefail

# Asegura que la clave de github.com esté en ~/.ssh/known_hosts y luego intenta actualizar el repo.
# Si la autenticación por SSH falla, se intenta un fallback con token HTTPS desde la variable
# de entorno SAO_GIT_TOKEN o desde el archivo ~/.sao_server_token (permiso 600 recomendado).

KNOWN_HOSTS="$HOME/.ssh/known_hosts"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if ! ssh-keygen -F github.com >/dev/null 2>&1; then
  ssh-keyscan -t ed25519 github.com >> "$KNOWN_HOSTS" 2>/dev/null || true
  ssh-keyscan -t rsa github.com >> "$KNOWN_HOSTS" 2>/dev/null || true
  chmod 600 "$KNOWN_HOSTS"
fi

# Determinar rama actual
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

# Intentar pull normal (respeta la configuración de remoto)
set +e
git pull origin "$branch"
rc=$?
set -e

if [ $rc -eq 0 ]; then
  exit 0
fi

echo "Update: Pull failed with code $rc. Attempting HTTPS token fallback..."

# Leer token de entorno o archivo
TOKEN="${SAO_GIT_TOKEN-}"
if [ -z "$TOKEN" ] && [ -f "$HOME/.sao_server_token" ]; then
  TOKEN=$(cat "$HOME/.sao_server_token" | tr -d '\n')
fi

if [ -z "$TOKEN" ]; then
  echo "No token found in SAO_GIT_TOKEN or $HOME/.sao_server_token — cannot auto-authenticate."
  exit $rc
fi

# Construir URL HTTPS con token (usuario arbitrario 'x-access-token')
origin_url=$(git remote get-url origin 2>/dev/null || true)
if [ -z "$origin_url" ]; then
  echo "No origin remote configured."
  exit 2
fi

# Extraer path remoto (github.com/owner/repo.git)
repo_path=${origin_url#*github.com[:/]}
repo_path=${repo_path#://}
repo_path=${repo_path#*@}
repo_path=${repo_path#/}
repo_path=$(echo "$repo_path" | sed 's/^:\/*//')

https_url="https://x-access-token:${TOKEN}@github.com/${repo_path}"

echo "Using fallback HTTPS URL to pull..."
set +e
git pull "$https_url" "$branch"
rc2=$?
set -e

if [ $rc2 -eq 0 ]; then
  echo "Update via token succeeded."
  exit 0
else
  echo "Token fallback failed (code $rc2)."
  exit $rc2
fi
