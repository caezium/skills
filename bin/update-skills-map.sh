#!/usr/bin/env bash
# Refresh the full-machine skills snapshot and verify the generated site.
#
# Usage: bin/update-skills-map.sh

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$REPO/site"
if [ "$#" -ne 0 ]; then
  echo "Usage: $0" >&2
  exit 2
fi

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
echo "Review the snapshot, then include it in the next skills-repo commit."
