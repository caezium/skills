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

env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/validate-skill-tree.py" --root "$ROOT"
pass "canonical skill packages are structurally valid"

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

reconcile_repo="$TEST_TMP/reconcile-repo"
reconcile_home="$TEST_TMP/reconcile-home"
mkdir -p "$reconcile_repo/active-skill" "$reconcile_home/.agents/skills/active-skill" \
  "$reconcile_home/.codex/skills/active-skill" "$reconcile_home/.claude/skills/retired-skill"
printf '%s\n' '---' 'name: active-skill' 'description: Reconcile fixture.' '---' > "$reconcile_repo/active-skill/SKILL.md"
cp "$ROOT/bin/sync.sh" "$reconcile_repo/sync.sh"
mkdir -p "$reconcile_repo/bin"
mv "$reconcile_repo/sync.sh" "$reconcile_repo/bin/sync.sh"
cat > "$reconcile_repo/skills.lock.json" <<'EOF'
{
  "skills": [
    {"name": "active-skill", "state": "active"},
    {"name": "retired-skill", "state": "planned-retire"}
  ]
}
EOF
cat > "$reconcile_home/.agents/.skill-lock.json" <<'EOF'
{
  "skills": {
    "active-skill": {"source": "fixture"},
    "external-skill": {"source": "external"},
    "retired-skill": {"source": "fixture"}
  }
}
EOF
expect_status 3 env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/reconcile-discovery-paths.py" \
  --repo "$reconcile_repo" --target-home "$reconcile_home" --backup-label fixture
[ -d "$reconcile_home/.agents/skills/active-skill" ] || fail "reconcile dry run changed a collision"
env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/reconcile-discovery-paths.py" \
  --repo "$reconcile_repo" --target-home "$reconcile_home" --backup-label fixture --apply
[ -L "$reconcile_home/.agents/skills/active-skill" ] || fail "reconcile did not restore the canonical shared link"
[ ! -e "$reconcile_home/.codex/skills/active-skill" ] || fail "reconcile retained a duplicate Codex copy"
[ -d "$reconcile_home/.skill-backups/discovery-fixture/.codex/skills/active-skill" ] \
  || fail "reconcile did not preserve a duplicate Codex copy"
[ "$(python3 -c 'import json,sys; print(sorted(json.load(open(sys.argv[1]))["skills"]))' "$reconcile_home/.agents/.skill-lock.json")" = "['external-skill']" ] \
  || fail "reconcile did not prune canonical names from the external lock"
pass "discovery reconciliation archives duplicate installs and preserves external ownership"

config_home="$TEST_TMP/config-home"
mkdir -p "$config_home/.claude"
cat > "$config_home/.claude/settings.json" <<'EOF'
{
  "theme": "dark",
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "~/skills/bin/sync.sh claude"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "keep-me"}]}]
  }
}
EOF
env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/configure-machine.py" \
  --repo "$ROOT" --target-home "$config_home" --backup-label fixture --apply
env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/configure-machine.py" \
  --repo "$ROOT" --target-home "$config_home" --backup-label fixture-second --apply
python3 - "$config_home/.claude/settings.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["theme"] == "dark"
assert data["hooks"]["Stop"][0]["hooks"][0]["command"] == "keep-me"
assert sum(
    hook.get("command") == "~/skills/bin/sync.sh all"
    for entry in data["hooks"]["SessionStart"]
    for hook in entry.get("hooks", [])
) == 1
assert sum(
    hook.get("command") == "~/.claude/hooks/block-dangerous-git.sh"
    for entry in data["hooks"]["PreToolUse"]
    for hook in entry.get("hooks", [])
) == 1
PY
[ -x "$config_home/.claude/hooks/block-dangerous-git.sh" ] || fail "machine config did not install an executable guardrail"
pass "machine configuration is idempotent and preserves existing Claude settings"

check_repo="$TEST_TMP/check-repo"
check_home="$TEST_TMP/check-home"
mkdir -p "$check_repo/skill-one"
git -C "$TEST_TMP" init -q -b main check-repo
git_identity "$check_repo"
printf '%s\n' '---' 'name: skill-one' 'description: Check fixture.' '---' > "$check_repo/skill-one/SKILL.md"
printf '%s\n' 'skill-one/runtime/' > "$check_repo/.gitignore"
git -C "$check_repo" add .gitignore skill-one/SKILL.md
git -C "$check_repo" commit -q -m initial
check_sha="$(git -C "$check_repo" rev-parse HEAD)"
check_hash="$(env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/hash-skill-tree.py" "$check_repo/skill-one")"
mkdir -p "$check_repo/skill-one/runtime"
printf '%s\n' 'generated cache' > "$check_repo/skill-one/runtime/cache.db"
check_hash_with_ignored="$(env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/hash-skill-tree.py" "$check_repo/skill-one")"
[ "$check_hash" = "$check_hash_with_ignored" ] || fail "tree hash included Git-ignored runtime content"
pass "Git-ignored runtime content does not cause false drift"
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

mkdir -p "$check_repo/skill-two"
printf '%s\n' '---' 'name: skill-two' 'description: Record fixture.' '---' > "$check_repo/skill-two/SKILL.md"
env PYTHONDONTWRITEBYTECODE=1 "$ROOT/bin/record-skill-state.py" \
  --repo "$check_repo" --lock "$check_lock" --checked-at "2026-08-24T00:00:00Z" \
  record --name skill-two --kind custom --update-policy personal-repo --notes "Test fixture."
env PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/bin/validate-skills-lock.py" \
  "$check_lock" --schema "$ROOT/schema/skills-lock.schema.json"
[ "$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next(x["state"] for x in d["skills"] if x["name"]=="skill-two"))' "$check_lock")" = active ] \
  || fail "record helper did not add the active skill"
env PYTHONDONTWRITEBYTECODE=1 "$ROOT/bin/record-skill-state.py" \
  --repo "$check_repo" --lock "$check_lock" --checked-at "2026-08-24T00:00:00Z" \
  retire --name skill-two --replaced-by skill-one --notes "Fixture retirement."
[ "$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next(x["state"] for x in d["skills"] if x["name"]=="skill-two"))' "$check_lock")" = planned-retire ] \
  || fail "record helper did not retire the skill"
pass "record helper adds and retires provenance entries"

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
source_pin="$(git -C "$seed" rev-parse HEAD)"
upstream_lock="$TEST_TMP/upstream.lock.json"
cat > "$upstream_lock" <<EOF
{
  "sources": {
    "fixture": {
      "kind": "git",
      "label": "fixture source",
      "url": "$remote",
      "branch": "main",
      "pinnedCommit": "$source_pin"
    }
  }
}
EOF
env PYTHONDONTWRITEBYTECODE=1 "$ROOT/bin/check-upstream-pins.py" --lock "$upstream_lock" \
  --report "$TEST_TMP/upstream-current.md"
grep -q '| current |' "$TEST_TMP/upstream-current.md" || fail "upstream checker did not report current pin"
printf '%s\n' two > "$seed/value.txt"
git -C "$seed" commit -q -am two
git -C "$seed" push -q
expect_status 3 env PYTHONDONTWRITEBYTECODE=1 "$ROOT/bin/check-upstream-pins.py" \
  --lock "$upstream_lock" --report "$TEST_TMP/upstream-advanced.md"
grep -q '| advanced |' "$TEST_TMP/upstream-advanced.md" || fail "upstream checker did not report advanced source"
pass "weekly source checker detects remote advances without changing skills"
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
