#!/usr/bin/env bash
# Explicitly fast-forward a clean canonical checkout. Never commits, merges
# divergent history, pushes, links skills, or edits user files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO="${SKILLS_REPO:-$DEFAULT_REPO}"
REMOTE="${SKILLS_REMOTE:-origin}"
BRANCH="${SKILLS_BRANCH:-main}"

usage() {
  cat <<'EOF'
Usage: bin/fast-forward-skills.sh

Environment overrides: SKILLS_REPO, SKILLS_REMOTE, SKILLS_BRANCH.
The checkout must be on the expected branch, completely clean, and strictly
behind (or equal to) the remote branch. Run bin/sync.sh separately afterward.
EOF
}

case "${1:-}" in
  "") ;;
  -h|--help) usage; exit 0 ;;
  *) echo "This command takes no positional arguments." >&2; usage >&2; exit 2 ;;
esac

git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || {
  echo "ERROR not a Git repository: $REPO" >&2
  exit 2
}

current_branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" != "$BRANCH" ]; then
  echo "STOP expected branch $BRANCH, found $current_branch" >&2
  exit 3
fi

if [ -n "$(git -C "$REPO" status --porcelain --untracked-files=normal)" ]; then
  echo "STOP worktree is dirty; commit, stash, or discard intentionally before updating" >&2
  exit 3
fi

echo "Fetching $REMOTE/$BRANCH..."
GIT_TERMINAL_PROMPT=0 git -C "$REPO" fetch --prune "$REMOTE" "$BRANCH"

local_sha="$(git -C "$REPO" rev-parse HEAD)"
remote_sha="$(git -C "$REPO" rev-parse "$REMOTE/$BRANCH")"
if [ "$local_sha" = "$remote_sha" ]; then
  echo "Already current at ${local_sha:0:12}."
  exit 0
fi

if git -C "$REPO" merge-base --is-ancestor "$local_sha" "$remote_sha"; then
  git -C "$REPO" merge --ff-only "$REMOTE/$BRANCH"
  echo "Fast-forwarded ${local_sha:0:12} -> ${remote_sha:0:12}."
  echo "Run bin/check-skill-updates.sh, then bin/sync.sh all."
  exit 0
fi

if git -C "$REPO" merge-base --is-ancestor "$remote_sha" "$local_sha"; then
  echo "STOP local branch is ahead of $REMOTE/$BRANCH; review and push explicitly" >&2
else
  echo "STOP local and remote branches diverged; inspect them manually" >&2
fi
exit 3
