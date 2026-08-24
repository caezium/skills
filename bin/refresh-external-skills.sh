#!/usr/bin/env bash
# Refresh externally managed Feishu skills without touching canonical ~/skills packages.

set -euo pipefail

SKILLS_CLI_VERSION="${SKILLS_CLI_VERSION:-1.5.23}"

case "${1:-}" in
  "")
    exec npx --yes "skills@$SKILLS_CLI_VERSION" add https://open.feishu.cn \
      --skill '*' --global --agent claude-code --agent codex --agent cursor --yes
    ;;
  --list)
    exec npx --yes "skills@$SKILLS_CLI_VERSION" add https://open.feishu.cn --list
    ;;
  *)
    echo "Usage: $0 [--list]" >&2
    exit 2
    ;;
esac
