#!/usr/bin/env bash
# Symlink ~/skills/<name> into agent discovery paths.
# Replaces existing symlinks; refuses to overwrite real directories.
#
# Usage:
#   bin/sync.sh claude    # symlink into ~/.claude/skills/
#   bin/sync.sh cursor    # symlink into ~/.cursor/skills/
#   bin/sync.sh all       # both
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

link_into() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  for src in "$REPO"/*/; do
    name="$(basename "$src")"
    [ "$name" = "bin" ] && continue
    [ "$name" = "commands" ] && continue
    dst="$target_dir/$name"
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
      echo "  SKIP $name (real dir at $dst — remove manually first)"
      continue
    fi
    ln -sfn "$src" "$dst"
    echo "  link $name -> $dst"
  done
}

link_commands_into() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  for src in "$REPO"/commands/*.md; do
    [ -e "$src" ] || continue
    name="$(basename "$src")"
    ln -sfn "$src" "$target_dir/$name"
    echo "  link commands/$name -> $target_dir/$name"
  done
}

case "${1:-}" in
  claude)
    echo "Linking skills into ~/.claude/skills/"
    link_into "$HOME/.claude/skills"
    echo "Linking commands into ~/.claude/commands/"
    link_commands_into "$HOME/.claude/commands"
    ;;
  cursor)
    echo "Linking skills into ~/.cursor/skills/"
    link_into "$HOME/.cursor/skills"
    echo "Linking commands into ~/.cursor/commands/"
    link_commands_into "$HOME/.cursor/commands"
    ;;
  all)
    "$0" claude
    "$0" cursor
    ;;
  *)
    echo "Usage: $0 {claude|cursor|all}" >&2
    exit 1
    ;;
esac
