#!/usr/bin/env bash
# Deterministically link the canonical skills checkout into local discovery paths.
# This command is offline: it never fetches, commits, merges, or pushes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO="${SKILLS_REPO:-$DEFAULT_REPO}"
TARGET_HOME="${SKILLS_TARGET_HOME:-$HOME}"
COLLISIONS=0

link_skills_into() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  local added=0 replaced=0 skipped=0 removed=0

  for src in "$REPO"/*/; do
    local name dst
    name="$(basename "$src")"
    [ -f "$src/SKILL.md" ] || continue

    dst="$target_dir/$name"
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
      echo "  COLLISION $name (real path at $dst; preserved)"
      skipped=$((skipped + 1))
      COLLISIONS=$((COLLISIONS + 1))
      continue
    fi
    if [ -L "$dst" ]; then
      replaced=$((replaced + 1))
    else
      added=$((added + 1))
    fi
    ln -sfn "$src" "$dst"
  done

  # Prune only broken symlinks that this canonical checkout used to own.
  if [ -d "$target_dir" ]; then
    for link in "$target_dir"/*; do
      [ -L "$link" ] || continue
      [ -e "$link" ] && continue
      local resolved
      resolved="$(readlink "$link")"
      case "$resolved" in
        "$REPO"/*)
          rm "$link"
          removed=$((removed + 1))
          echo "  prune $(basename "$link") (was -> $resolved)"
          ;;
      esac
    done
  fi

  echo "  skills: +$added ~$replaced -$removed (collisions: $skipped)"
}

link_config_into() {
  local target="$1"
  local name="${2:-CLAUDE.md}"
  local src="$REPO/config/$name"
  [ -f "$src" ] || return 0
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "  COLLISION $name (real file at $target; preserved)"
    COLLISIONS=$((COLLISIONS + 1))
    return 0
  fi
  mkdir -p "$(dirname "$target")"
  ln -sfn "$src" "$target"
  echo "  config: $name linked"
}

link_commands_into() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  local linked=0 skipped=0
  for src in "$REPO"/commands/*.md; do
    [ -e "$src" ] || continue
    local name dst
    name="$(basename "$src")"
    dst="$target_dir/$name"
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
      echo "  COLLISION command $name (real file at $dst; preserved)"
      skipped=$((skipped + 1))
      COLLISIONS=$((COLLISIONS + 1))
      continue
    fi
    ln -sfn "$src" "$dst"
    linked=$((linked + 1))
  done
  echo "  commands: $linked linked (collisions: $skipped)"
}

sync_claude() {
  echo "Claude: $TARGET_HOME/.claude/skills/ + $TARGET_HOME/.claude/commands/"
  link_skills_into "$TARGET_HOME/.claude/skills"
  link_commands_into "$TARGET_HOME/.claude/commands"
  link_config_into "$TARGET_HOME/.claude/CLAUDE.md"
}

sync_cursor() {
  echo "Cursor: $TARGET_HOME/.cursor/skills/ + $TARGET_HOME/.cursor/commands/"
  link_skills_into "$TARGET_HOME/.cursor/skills"
  link_commands_into "$TARGET_HOME/.cursor/commands"
}

sync_agents() {
  echo "Shared agents: $TARGET_HOME/.agents/skills/ + $TARGET_HOME/.codex/AGENTS.md"
  link_skills_into "$TARGET_HOME/.agents/skills"
  link_config_into "$TARGET_HOME/.codex/AGENTS.md" AGENTS.md
}

case "${1:-}" in
  claude) sync_claude ;;
  cursor) sync_cursor ;;
  agents) sync_agents ;;
  all) sync_claude; sync_cursor; sync_agents ;;
  *)
    echo "Usage: $0 {claude|cursor|agents|all}" >&2
    exit 2
    ;;
esac

if [ "$COLLISIONS" -ne 0 ]; then
  echo "Completed with $COLLISIONS preserved collision(s); resolve them explicitly and rerun." >&2
  exit 3
fi
