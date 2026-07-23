#!/usr/bin/env bash
# Refresh the full-machine skills snapshot and verify the generated site.
#
# Usage:
#   bin/update-skills-map.sh          # refresh + validate locally
#   bin/update-skills-map.sh --push   # also commit only the snapshot and push it

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$REPO/site"
PUSH=false

case "${1:-}" in
  "") ;;
  --push) PUSH=true ;;
  *)
    echo "Usage: $0 [--push]" >&2
    exit 2
    ;;
esac

if [ ! -d "$SITE/node_modules/gray-matter" ]; then
  echo "Installing site dependencies..."
  npm --prefix "$SITE" ci
fi

npm --prefix "$SITE" run snapshot
npm --prefix "$SITE" run check

SNAPSHOT="$SITE/installed-skills.json"
if git -C "$REPO" diff --quiet -- "$SNAPSHOT" \
  && [ -z "$(git -C "$REPO" ls-files --others --exclude-standard -- "$SNAPSHOT")" ]; then
  echo "Skills map is already current."
  exit 0
fi

echo "Updated site/installed-skills.json."
if [ "$PUSH" = false ]; then
  echo "Review the snapshot, then include it in the next skills-repo commit."
  exit 0
fi

if [ "$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" != "main" ]; then
  echo "Refusing --push outside the main branch." >&2
  exit 1
fi

git -C "$REPO" add -- "$SNAPSHOT"
git -C "$REPO" commit --only -m "site: refresh installed skills map" -- "$SNAPSHOT"
git -C "$REPO" push origin main
echo "Published the refreshed skills map."
