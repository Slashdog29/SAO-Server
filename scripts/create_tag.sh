chmod 755 "$0" || true
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <tag> [--push]"
  exit 2
fi

TAG="$1"
PUSH=false
if [ "${2:-}" = "--push" ]; then
  PUSH=true
fi

# Create annotated tag
git tag -a "$TAG" -m "Release $TAG"

echo "Tag $TAG created locally."
if [ "$PUSH" = true ]; then
  echo "Pushing tag to origin (may require auth)..."
  git push origin "$TAG"
  echo "Tag pushed."
fi
