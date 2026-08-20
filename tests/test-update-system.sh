#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_TMP="$(mktemp -d "${TMPDIR:-/tmp}/skills-update-system.XXXXXX")"
trap 'rm -rf "$TEST_TMP"' EXIT

pass() {
  echo "PASS  $*"
}

fail() {
  echo "FAIL  $*" >&2
  exit 1
}

expect_status() {
  local expected="$1"
  shift
  set +e
  "$@"
  local actual=$?
  set -e
  [ "$actual" -eq "$expected" ] || fail "expected exit $expected, got $actual: $*"
}

git_identity() {
  git -C "$1" config user.name "Skill Update Test"
  git -C "$1" config user.email "skills-update-test@example.invalid"
}

env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/validate-skills-lock.py" \
  "$ROOT/skills.lock.json" \
  --schema "$ROOT/schema/skills-lock.schema.json"
pass "real lockfile validates"

for invalid_case in top-level date-time source-kind content-basis overlays-unique replaced-by-type; do
  invalid_lock="$TEST_TMP/invalid-$invalid_case.json"
  env PYTHONDONTWRITEBYTECODE=1 python3 - "$ROOT/skills.lock.json" "$invalid_lock" "$invalid_case" <<'PY'
import json, sys
source, target, case = sys.argv[1:]
data = json.load(open(source, encoding="utf-8"))
if case == "top-level":
    data["unexpected"] = True
elif case == "date-time":
    data["generatedAt"] = "not-a-date"
elif case == "source-kind":
    data["sources"][next(iter(data["sources"]))]["kind"] = "magic"
elif case == "content-basis":
    data["skills"][0]["content"]["basis"] = "hand-wavy"
elif case == "overlays-unique":
    skill = next(item for item in data["skills"] if item["kind"] == "vendored-overlay")
    skill["localOverlays"] = ["duplicate", "duplicate"]
elif case == "replaced-by-type":
    skill = next(item for item in data["skills"] if "replacedBy" in item)
    skill["replacedBy"] = "wrong-type"
json.dump(data, open(target, "w", encoding="utf-8"))
PY
  expect_status 2 env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/validate-skills-lock.py" \
    "$invalid_lock" --schema "$ROOT/schema/skills-lock.schema.json"
done
pass "validator rejects schema, format, enum, uniqueness, and type violations"

mkdir -p "$TEST_TMP/hash-skill/references"
printf '%s\n' '---' 'name: hash-skill' 'description: Test fixture.' '---' > "$TEST_TMP/hash-skill/SKILL.md"
printf '%s\n' 'reference' > "$TEST_TMP/hash-skill/references/note.md"
hash_one="$(env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/hash-skill-tree.py" "$TEST_TMP/hash-skill")"
touch -t 202001010000 "$TEST_TMP/hash-skill/SKILL.md"
hash_two="$(env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/hash-skill-tree.py" "$TEST_TMP/hash-skill")"
[ "$hash_one" = "$hash_two" ] || fail "tree hash changed with mtime"
chmod +x "$TEST_TMP/hash-skill/SKILL.md"
hash_three="$(env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/hash-skill-tree.py" "$TEST_TMP/hash-skill")"
[ "$hash_one" != "$hash_three" ] || fail "tree hash ignored executable mode"
pass "portable content hash is deterministic and mode-aware"

link_repo="$TEST_TMP/link-repo"
target_home="$TEST_TMP/link-home"
mkdir -p "$link_repo/skill-one" "$link_repo/commands" "$link_repo/config"
printf '%s\n' '---' 'name: skill-one' 'description: Link fixture.' '---' > "$link_repo/skill-one/SKILL.md"
printf '%s\n' '# command' > "$link_repo/commands/example.md"
printf '%s\n' '# Claude config' > "$link_repo/config/CLAUDE.md"
printf '%s\n' '# Agent config' > "$link_repo/config/AGENTS.md"
mkdir -p "$target_home/.agents/skills/skill-one"
printf '%s\n' 'preserve me' > "$target_home/.agents/skills/skill-one/marker"
expect_status 3 env SKILLS_REPO="$link_repo" SKILLS_TARGET_HOME="$target_home" \
  "$ROOT/bin/sync.sh" all
[ -f "$target_home/.agents/skills/skill-one/marker" ] || fail "real collision was overwritten"
mv "$target_home/.agents/skills/skill-one" "$TEST_TMP/preserved-collision"
env SKILLS_REPO="$link_repo" SKILLS_TARGET_HOME="$target_home" "$ROOT/bin/sync.sh" all
[ "$(readlink "$target_home/.claude/skills/skill-one")" = "$link_repo/skill-one/" ] || fail "Claude skill link is wrong"
[ "$(readlink "$target_home/.cursor/skills/skill-one")" = "$link_repo/skill-one/" ] || fail "Cursor skill link is wrong"
[ "$(readlink "$target_home/.agents/skills/skill-one")" = "$link_repo/skill-one/" ] || fail "shared-agent skill link is wrong"
[ "$(readlink "$target_home/.codex/AGENTS.md")" = "$link_repo/config/AGENTS.md" ] || fail "Codex config link is wrong"
pass "offline linking preserves collisions and links every harness"

check_repo="$TEST_TMP/check-repo"
check_home="$TEST_TMP/check-home"
mkdir -p "$check_repo/skill-one"
git -C "$TEST_TMP" init -q -b main check-repo
git_identity "$check_repo"
printf '%s\n' '---' 'name: skill-one' 'description: Check fixture.' '---' > "$check_repo/skill-one/SKILL.md"
git -C "$check_repo" add skill-one/SKILL.md
git -C "$check_repo" commit -q -m initial
check_sha="$(git -C "$check_repo" rev-parse HEAD)"
check_hash="$(env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/hash-skill-tree.py" "$check_repo/skill-one")"
check_lock="$TEST_TMP/check.lock.json"
cat > "$check_lock" <<EOF
{
  "schemaVersion": 1,
  "generatedAt": "2026-08-20T00:00:00Z",
  "canonicalRepo": {
    "repo": "fixture/skills",
    "url": "$check_repo",
    "branch": "main",
    "auditedCommit": "$check_sha"
  },
  "sources": {},
  "skills": [
    {
      "name": "skill-one",
      "state": "active",
      "kind": "source-unknown",
      "sourceId": null,
      "sourcePath": null,
      "sourceTree": null,
      "content": {
        "kind": "sha256",
        "value": "$check_hash",
        "basis": "local-copy-unverified-upstream"
      },
      "localOverlays": [],
      "updatePolicy": "identify-source-before-update",
      "lastCheckedAt": "2026-08-20T00:00:00Z",
      "notes": "Test fixture."
    }
  ]
}
EOF
env SKILLS_REPO="$check_repo" SKILLS_TARGET_HOME="$check_home" "$ROOT/bin/sync.sh" all
env SKILLS_REPO="$check_repo" SKILLS_TARGET_HOME="$check_home" \
  SKILLS_LOCKFILE="$check_lock" SKILLS_LOCK_SCHEMA="$ROOT/schema/skills-lock.schema.json" \
  "$ROOT/bin/check-skill-updates.sh" --offline
unlink "$check_home/.agents/skills/skill-one"
mkdir -p "$check_home/.agents/skills/skill-one"
set +e
collision_output="$(env SKILLS_REPO="$check_repo" SKILLS_TARGET_HOME="$check_home" \
  SKILLS_LOCKFILE="$check_lock" SKILLS_LOCK_SCHEMA="$ROOT/schema/skills-lock.schema.json" \
  "$ROOT/bin/check-skill-updates.sh" --offline 2>&1)"
collision_status=$?
set -e
[ "$collision_status" -eq 3 ] || fail "checker did not return review-required for collision"
printf '%s\n' "$collision_output" | grep -q 'COLLISION' || fail "checker did not name collision"
pass "read-only checker detects discovery collisions"

remote="$TEST_TMP/remote.git"
seed="$TEST_TMP/seed"
client="$TEST_TMP/client"
git init -q --bare "$remote"
git -C "$TEST_TMP" init -q -b main seed
git_identity "$seed"
printf '%s\n' one > "$seed/value.txt"
git -C "$seed" add value.txt
git -C "$seed" commit -q -m one
git -C "$seed" remote add origin "$remote"
git -C "$seed" push -q -u origin main
git clone -q --branch main "$remote" "$client"
git_identity "$client"
printf '%s\n' two > "$seed/value.txt"
git -C "$seed" commit -q -am two
git -C "$seed" push -q
env SKILLS_REPO="$client" "$ROOT/bin/fast-forward-skills.sh"
[ "$(sed -n '1p' "$client/value.txt")" = two ] || fail "clean checkout did not fast-forward"

printf '%s\n' dirty > "$client/untracked.txt"
expect_status 3 env SKILLS_REPO="$client" "$ROOT/bin/fast-forward-skills.sh"
mv "$client/untracked.txt" "$TEST_TMP/preserved-untracked.txt"
printf '%s\n' local > "$client/local.txt"
git -C "$client" add local.txt
git -C "$client" commit -q -m local
printf '%s\n' three > "$seed/value.txt"
git -C "$seed" commit -q -am three
git -C "$seed" push -q
expect_status 3 env SKILLS_REPO="$client" "$ROOT/bin/fast-forward-skills.sh"
pass "fast-forward command updates clean clones and stops on dirty/diverged state"

echo "All update-system tests passed."
