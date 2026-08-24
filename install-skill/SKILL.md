---
name: install-skill
description: Install a freshly authored skill into ~/skills/ (the source-of-truth repo), record its provenance, validate it, and symlink it into active agent directories. Use after creating a SKILL.md, when finishing an anthropic-skill-creator session, or when the user says "install this skill", "wire it up", "register the skill", or "add it to my repo".
---

# Install Skill

Wires a newly authored skill into the user's personal skills repo at `~/skills/`, links it into Claude Code, Cursor, and shared-agent discovery for Codex, and prepares it for review in [caezium/skills](https://github.com/caezium/skills).

The user's setup uses **`~/skills/` as the single source of truth**. Agent directories (`~/.claude/skills/`, `~/.cursor/skills/`, and `~/.agents/skills/`) hold only symlinks pointing back here. Never copy a canonical skill into the agent directories — always symlink.

## Where things live

| Location | Role |
|---|---|
| `~/skills/<name>/SKILL.md` | Source of truth — git-tracked, pushed to caezium/skills |
| `~/skills/commands/<name>.md` | Source of truth for single-file slash commands |
| `~/skills/skills.lock.json` | Source pin, content digest, update policy, and reviewed local overlays |
| `~/skills/bin/sync.sh` | Symlinks `~/skills/*` into Claude, Cursor, and shared-agent discovery paths |
| `~/.claude/skills/<name>` | Symlink → `~/skills/<name>/` |
| `~/.cursor/skills/<name>` | Symlink → `~/skills/<name>/` |
| `~/.agents/skills/<name>` | Symlink → `~/skills/<name>/` for Codex and other shared agents |

## Install workflow

### Step 1 — Validate

Before placing anything, confirm:

- [ ] Name is lowercase, hyphens-only, ≤ 64 chars (e.g. `code-review`, not `Code_Review`)
- [ ] Directory name and the `name:` field in frontmatter match exactly
- [ ] `SKILL.md` has frontmatter with both `name:` and `description:`
- [ ] Description is in third person, includes WHAT + WHEN trigger terms
- [ ] No naming collision:

```sh
ls ~/skills/ | grep -i <skill-name>
```

If collision: rename, merge, or stop and ask.

### Step 2 — Place in `~/skills/`

If authored in a temp/working directory:

```sh
mv <source-path> ~/skills/<skill-name>/
```

If authored directly at `~/skills/<skill-name>/`, skip this.

**Single-file slash commands** (no SKILL.md, just one `.md` with frontmatter) go under `~/skills/commands/` instead:

```sh
mv <name>.md ~/skills/commands/
```

### Step 3 — Sync to active agents

```sh
~/skills/bin/sync.sh all
```

Subcommands: `claude`, `cursor`, `agents`, or `all`. Idempotent — replaces existing symlinks and treats a real-directory collision as a hard error that must be preserved and reconciled first.

After sync, verify:

```sh
ls -la ~/.claude/skills/<skill-name>   # should show -> /Users/henry/skills/<skill-name>/
ls -la ~/.cursor/skills/<skill-name>
ls -la ~/.agents/skills/<skill-name>
```

### Step 4 — Update and validate provenance

Add or update the skill's record in `skills.lock.json`. For a personal skill,
use the helper so the content digest and record shape cannot drift:

```sh
python3 ~/skills/bin/record-skill-state.py record \
  --name <skill-name> \
  --kind custom \
  --update-policy personal-repo \
  --notes "<purpose and ownership>"
```

For a vendored package, also pass `--source-id`, `--source-root`, and
`--source-path`; use `--overlay` once per intentional local change. Pin the
reviewed source with the helper's `pin-source` command, then validate both the
lock and every package before committing:

```sh
python3 ~/skills/bin/validate-skills-lock.py \
  ~/skills/skills.lock.json \
  --schema ~/skills/schema/skills-lock.schema.json
python3 ~/skills/bin/validate-skill-tree.py --root ~/skills
python3 ~/skills/bin/hash-skill-tree.py \
  --verify-lock ~/skills/skills.lock.json \
  --root ~/skills
```

Do not change a source pin merely to silence drift: inspect the upstream diff,
refresh the complete package, reapply reviewed overlays, and update the pin and
content digest together.

### Step 5 — Refresh the published skills map

Refresh the full-machine inventory before committing. The script deduplicates
personal, shared-agent, Codex, and plugin skills, then builds and validates the
HTML site locally:

```sh
~/skills/bin/update-skills-map.sh
```

Include `site/installed-skills.json` in the same commit when it changed. The
site deployment workflow rebuilds the repository catalog and the installed
skills map after the push.

### Step 6 — Commit for review

```sh
cd ~/skills
git add <skill-name>/ skills.lock.json site/installed-skills.json
git commit -m "Add <skill-name>: <one-line purpose>"
```

Commit message conventions:
- **New skill:** `Add <skill-name>: <one-line purpose>`
- **Edit existing:** `Update <skill-name>: <what changed>`
- **Remove:** `Remove <skill-name>: <why>`
- **Slash command:** `Add /<name> command` or `Update /<name> command`

Show the staged diff before committing. Push or merge only when the user
explicitly asks for that external action. Use a short-lived branch and a PR for
vendored upstream updates so the package diff, overlay rebase, source pin, and
content hash can be reviewed together; a scheduled freshness issue is never
authority to merge an update.

### Step 7 — Confirm pickup

In a **fresh** Claude Code, Codex/T3, or Cursor session, the skill should appear in the available-skills list. Skills load at session start; runtime additions don't auto-register. Tell the user to restart their session if it is not showing.

## Common gotchas

- **Symlink already points to `~/.agents/skills/<name>`.** That's the legacy npx-install path. `sync.sh` will replace it — `~/skills/` is now the canonical home. Confirm with the user before clobbering if the existing version differs meaningfully.
- **Real directory at the target.** `sync.sh` refuses to overwrite a real directory in any discovery path. Inspect and compare it, preserve it outside discovery, then choose exactly one owner for the global name before syncing. Never delete an unknown real directory just to make the warning disappear.
- **Embedded `.git/` in the skill folder.** If the skill came from a cloned or npx-installed source, it may have its own `.git/`. Build the reviewed package from a separate source checkout while excluding `.git`; never delete unresolved source metadata merely to make Git accept the package. For example:

  ```sh
  rsync -a --exclude=.git/ <reviewed-source>/ ~/skills/<skill-name>/
  ```

- **Frontmatter typos.** A missing or malformed `---` block makes the skill invisible to the agent. Quick check:

  ```sh
  head -5 ~/skills/<skill-name>/SKILL.md
  ```

- **Skill not picked up after restart.** Confirm the symlink resolves (`readlink ~/.claude/skills/<name>`), confirm frontmatter parses, and check `~/.claude/settings.json` doesn't disable skill loading.

## When NOT to install here

Skip `~/skills/` (and use a project-local location instead) when:

- The skill is one-off for a single project → put it in that project's `.claude/skills/` or `.cursor/skills/`
- The skill contains secrets, API keys, or private paths — caezium/skills is **public**
- The skill duplicates existing functionality — search `~/skills/` first; consider editing the existing one

## Quick reference

For an already-validated skill folder at `~/skills/<name>/`:

```sh
python3 ~/skills/bin/record-skill-state.py record --name <name> \
  --kind custom --update-policy personal-repo --notes "<purpose>"
python3 ~/skills/bin/validate-skill-tree.py --root ~/skills
~/skills/bin/update-skills-map.sh
~/skills/bin/sync.sh all
cd ~/skills && git add <name>/ skills.lock.json site/installed-skills.json && git commit -m "Add <name>: <purpose>"
```
