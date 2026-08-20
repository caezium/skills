#!/usr/bin/env bash
# Read-only health and upstream-drift check for Henry's skills repository.
# This command never fetches, merges, writes discovery links, or changes the lock.

set -euo pipefail
export GIT_OPTIONAL_LOCKS=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO="${SKILLS_REPO:-$DEFAULT_REPO}"
LOCKFILE="${SKILLS_LOCKFILE:-$REPO/skills.lock.json}"
SCHEMA="${SKILLS_LOCK_SCHEMA:-$REPO/schema/skills-lock.schema.json}"
TARGET_HOME="${SKILLS_TARGET_HOME:-$HOME}"
ONLINE=true
LOCK_ONLY=false
ATTENTION=0

usage() {
  cat <<'EOF'
Usage: bin/check-skill-updates.sh [--offline] [--lock-only]

  --offline    Validate local repository, inventory, and collisions without network calls.
  --lock-only  Validate only the lockfile and schema.

Environment overrides for tests or alternate checkouts:
  SKILLS_REPO, SKILLS_LOCKFILE, SKILLS_LOCK_SCHEMA, SKILLS_TARGET_HOME

Exit codes: 0 healthy, 2 invalid configuration/lock, 3 review required.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --offline) ONLINE=false ;;
    --lock-only) LOCK_ONLY=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

attention() {
  echo "ATTN  $*"
  ATTENTION=1
}

info() {
  echo "INFO  $*"
}

warn() {
  echo "WARN  $*"
}

command -v python3 >/dev/null 2>&1 || {
  echo "ERROR python3 is required to validate skills.lock.json" >&2
  exit 2
}

python3 "$SCRIPT_DIR/validate-skills-lock.py" "$LOCKFILE" --schema "$SCHEMA" || exit 2
[ "$LOCK_ONLY" = false ] || exit 0

if ! git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR canonical path is not a Git repository: $REPO" >&2
  exit 2
fi

head_sha="$(git -C "$REPO" rev-parse HEAD)"
branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
expected_branch="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["canonicalRepo"]["branch"])' "$LOCKFILE")"
audited_sha="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["canonicalRepo"]["auditedCommit"])' "$LOCKFILE")"

info "canonical checkout: $REPO @ ${head_sha:0:12} on $branch"
[ "$branch" = "$expected_branch" ] || attention "canonical branch is $branch; lock expects $expected_branch"
if [ -n "$(git -C "$REPO" status --porcelain --untracked-files=normal)" ]; then
  attention "canonical worktree is dirty; update commands must stop"
fi
if [ "$head_sha" != "$audited_sha" ]; then
  info "canonical HEAD has advanced since audited baseline ${audited_sha:0:12}"
fi

if [ "$ONLINE" = true ]; then
  canonical_url="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["canonicalRepo"]["url"])' "$LOCKFILE")"
  remote_line="$(GIT_TERMINAL_PROMPT=0 git ls-remote --exit-code "$canonical_url" "refs/heads/$expected_branch" 2>/dev/null || true)"
  if [ -z "$remote_line" ]; then
    attention "could not resolve canonical remote $canonical_url#$expected_branch"
  else
    remote_sha="${remote_line%%[[:space:]]*}"
    if [ "$head_sha" != "$remote_sha" ]; then
      if git -C "$REPO" merge-base --is-ancestor "$head_sha" "$remote_sha" 2>/dev/null; then
        attention "canonical checkout is behind remote ${remote_sha:0:12}"
      elif git -C "$REPO" merge-base --is-ancestor "$remote_sha" "$head_sha" 2>/dev/null; then
        attention "canonical checkout has unpushed commits; remote is ${remote_sha:0:12}"
      else
        attention "canonical local and remote commits differ; fetch and inspect before changing either"
      fi
    else
      info "canonical local and remote heads match"
    fi
  fi
else
  info "upstream checks skipped (--offline)"
fi

# Compare canonical skill names to the lock's intended post-integration state.
while IFS=$'\t' read -r name state; do
  [ -n "$name" ] || continue
  path="$REPO/$name"
  case "$state" in
    active|planned-add)
      if [ ! -f "$path/SKILL.md" ]; then
        attention "$name is $state in the lock but missing from the canonical checkout"
      fi
      ;;
    planned-retire)
      if [ -e "$path" ]; then
        attention "$name is planned-retire but still exists; preserve/diff it and make an explicit decision"
      fi
      ;;
  esac
done < <(python3 - "$LOCKFILE" <<'PY'
import json, sys
for skill in json.load(open(sys.argv[1], encoding="utf-8"))["skills"]:
    print(f"{skill['name']}\t{skill['state']}")
PY
)

while IFS= read -r skill_file; do
  name="$(basename "$(dirname "$skill_file")")"
  if ! python3 - "$LOCKFILE" "$name" <<'PY'
import json, sys
names = {x["name"] for x in json.load(open(sys.argv[1], encoding="utf-8"))["skills"]}
raise SystemExit(0 if sys.argv[2] in names else 1)
PY
  then
    attention "canonical skill $name has no lock record"
  fi
done < <(find "$REPO" -mindepth 2 -maxdepth 2 -name SKILL.md -type f -print | sort)

if ! python3 "$SCRIPT_DIR/hash-skill-tree.py" --verify-lock "$LOCKFILE" --root "$REPO"; then
  attention "canonical skill content differs from the lock; review before updating"
fi

# A real directory at a canonical skill name shadows the symlinked source of truth.
while IFS=$'\t' read -r name state; do
  [ "$state" != "planned-retire" ] || continue
  [ -f "$REPO/$name/SKILL.md" ] || continue
  for relative in .claude/skills .cursor/skills .agents/skills; do
    target="$TARGET_HOME/$relative/$name"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      attention "COLLISION $target is a real path and shadows $REPO/$name"
    elif [ -L "$target" ]; then
      resolved="$(readlink "$target")"
      expected="$REPO/$name/"
      if [ "$resolved" != "$expected" ] && [ "$resolved" != "$REPO/$name" ]; then
        attention "DRIFT $target points to $resolved instead of $REPO/$name/"
      elif [ ! -e "$target" ]; then
        attention "BROKEN $target -> $resolved"
      fi
    else
      attention "MISSING discovery link $target"
    fi
  done
done < <(python3 - "$LOCKFILE" <<'PY'
import json, sys
for skill in json.load(open(sys.argv[1], encoding="utf-8"))["skills"]:
    print(f"{skill['name']}\t{skill['state']}")
PY
)

if [ "$ONLINE" = true ]; then
  while IFS=$'\t' read -r source_id label url source_branch pinned pin_basis; do
    [ -n "$source_id" ] || continue
    if [ -z "$pinned" ]; then
      attention "$label is source-known but unpinned ($pin_basis)"
      continue
    fi
    line="$(GIT_TERMINAL_PROMPT=0 git ls-remote --exit-code "$url" "refs/heads/$source_branch" 2>/dev/null || true)"
    if [ -z "$line" ]; then
      attention "could not check upstream source $label"
      continue
    fi
    latest="${line%%[[:space:]]*}"
    if [ "$latest" = "$pinned" ]; then
      info "$label remains at pinned commit ${pinned:0:12}"
    else
      attention "$label advanced: pinned ${pinned:0:12}, remote ${latest:0:12}; review affected paths"
    fi
  done < <(python3 - "$LOCKFILE" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
for source_id, source in sorted(data["sources"].items()):
    if source["kind"] != "git" or source_id == "personal":
        continue
    print("\t".join([
        source_id,
        source["label"],
        source["url"],
        source["branch"],
        source["pinnedCommit"] or "",
        source["pinBasis"],
    ]))
PY
  )
fi

if [ "$ATTENTION" -ne 0 ]; then
  echo "RESULT review required; no files were changed"
  exit 3
fi
echo "RESULT healthy; no files were changed"
