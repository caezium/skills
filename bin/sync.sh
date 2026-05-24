#!/usr/bin/env bash
# Symlink ~/skills/<name> into agent discovery paths.
#
# - Skips top-level dirs that don't contain SKILL.md (so bin/, commands/, references/, etc. are safe).
# - Replaces existing symlinks; refuses to overwrite real directories at the target.
# - Prunes broken symlinks at the target that used to point back into this repo
#   (i.e. you deleted/renamed a skill, this cleans up the dangling link).
# - Also symlinks commands/*.md into the agent's commands/ directory.
#
# Usage:
#   bin/sync.sh claude    # symlink into ~/.claude/skills/ and ~/.claude/commands/
#   bin/sync.sh cursor    # symlink into ~/.cursor/skills/ and ~/.cursor/commands/
#   bin/sync.sh all       # both

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

link_skills_into() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  local added=0 replaced=0 skipped=0

  for src in "$REPO"/*/; do
    local name dst
    name="$(basename "$src")"
    [ "$name" = "bin" ] && continue
    [ "$name" = "commands" ] && continue
    [ -f "$src/SKILL.md" ] || continue   # only sync real skill dirs

    dst="$target_dir/$name"
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
      echo "  SKIP $name (real dir at $dst — remove manually first)"
      skipped=$((skipped + 1))
      continue
    fi
    if [ -L "$dst" ]; then
      replaced=$((replaced + 1))
    else
      added=$((added + 1))
    fi
    ln -sfn "$src" "$dst"
  done

  # Prune broken symlinks at target that point back into this repo
  local removed=0
  if [ -d "$target_dir" ]; then
    for link in "$target_dir"/*; do
      [ -L "$link" ] || continue
      [ -e "$link" ] && continue   # link still resolves, keep it
      local resolved
      resolved="$(readlink "$link")"
      case "$resolved" in
        "$REPO"/*)
          rm "$link"
          removed=$((removed + 1))
          echo "  prune $(basename "$link") (was → $resolved)"
          ;;
      esac
    done
  fi

  echo "  skills: +$added ~$replaced -$removed (skipped: $skipped)"
}

link_commands_into() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  local n=0
  for src in "$REPO"/commands/*.md; do
    [ -e "$src" ] || continue
    local name
    name="$(basename "$src")"
    ln -sfn "$src" "$target_dir/$name"
    n=$((n + 1))
  done
  echo "  commands: $n linked"
}

sync_claude() {
  echo "Claude: ~/.claude/skills/ + ~/.claude/commands/"
  link_skills_into "$HOME/.claude/skills"
  link_commands_into "$HOME/.claude/commands"
}

sync_cursor() {
  echo "Cursor: ~/.cursor/skills/ + ~/.cursor/commands/"
  link_skills_into "$HOME/.cursor/skills"
  link_commands_into "$HOME/.cursor/commands"
}

case "${1:-}" in
  claude) sync_claude ;;
  cursor) sync_cursor ;;
  all)    sync_claude; sync_cursor ;;
  *)
    echo "Usage: $0 {claude|cursor|all}" >&2
    exit 1
    ;;
esac
