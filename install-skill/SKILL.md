---
name: install-skill
description: Install a freshly authored skill into ~/skills/ (the source-of-truth repo), symlink it into the active agent directories (~/.claude/skills/, ~/.cursor/skills/), and commit + push to the caezium/skills GitHub repo. Use after creating a SKILL.md, when finishing a skill-creator session, or when the user says "install this skill", "wire it up", "register the skill", or "add it to my repo".
---

# Install Skill

Wires a newly authored skill into the user's personal skills repo at `~/skills/`, links it into the active AI coding agents (Claude Code, Cursor) via symlink, and persists it to GitHub at [caezium/skills](https://github.com/caezium/skills).

The user's setup uses **`~/skills/` as the single source of truth**. Agent directories (`~/.claude/skills/`, `~/.cursor/skills/`) hold only symlinks pointing back here. Never copy a skill into the agent directories — always symlink.

## Where things live

| Location | Role |
|---|---|
| `~/skills/<name>/SKILL.md` | Source of truth — git-tracked, pushed to caezium/skills |
| `~/skills/commands/<name>.md` | Source of truth for single-file slash commands |
| `~/skills/bin/sync.sh` | Symlinks `~/skills/*` into `~/.claude/skills/` and/or `~/.cursor/skills/` |
| `~/.claude/skills/<name>` | Symlink → `~/skills/<name>/` |
| `~/.cursor/skills/<name>` | Symlink → `~/skills/<name>/` |

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

Subcommands: `claude`, `cursor`, or `all`. Idempotent — replaces existing symlinks, skips real directories at the target as a safety guard.

After sync, verify:

```sh
ls -la ~/.claude/skills/<skill-name>   # should show -> /Users/henry/skills/<skill-name>/
ls -la ~/.cursor/skills/<skill-name>
```

### Step 4 — Refresh the published skills map

Refresh the full-machine inventory before committing. The script deduplicates
personal, shared-agent, Codex, and plugin skills, then builds and validates the
HTML site locally:

```sh
~/skills/bin/update-skills-map.sh
```

Include `site/installed-skills.json` in the same commit when it changed. The
site deployment workflow rebuilds the repository catalog and the installed
skills map after the push.

### Step 5 — Commit and push

```sh
cd ~/skills
git add <skill-name>/ site/installed-skills.json
git commit -m "Add <skill-name>: <one-line purpose>"
git push
```

Commit message conventions:
- **New skill:** `Add <skill-name>: <one-line purpose>`
- **Edit existing:** `Update <skill-name>: <what changed>`
- **Remove:** `Remove <skill-name>: <why>`
- **Slash command:** `Add /<name> command` or `Update /<name> command`

Push goes to `main` directly — this is a personal repo, no PR workflow.

### Step 6 — Confirm pickup

In a **fresh** Claude Code or Cursor session, the skill should appear in the available-skills list. Skills load at session start; runtime additions don't auto-register. Tell the user to restart their session if it's not showing.

## Common gotchas

- **Symlink already points to `~/.agents/skills/<name>`.** That's the legacy npx-install path. `sync.sh` will replace it — `~/skills/` is now the canonical home. Confirm with the user before clobbering if the existing version differs meaningfully.
- **Real directory at the target.** `sync.sh` refuses to overwrite a real directory at `~/.claude/skills/<name>`. Inspect it; if it's a bundled-skill package (e.g. `claude-skills-weekly`), leave it alone and use a different skill name. If it's a stale copy of this skill, delete it manually then re-sync.
- **Embedded `.git/` in the skill folder.** If the skill came from a cloned or npx-installed source, it may have its own `.git/`. Strip it before committing or git will track it as a gitlink and clones will see an empty directory:

  ```sh
  rm -rf ~/skills/<skill-name>/.git
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

## Quick reference: full install in 5 commands

For an already-validated skill folder at `~/skills/<name>/`:

```sh
~/skills/bin/sync.sh all
~/skills/bin/update-skills-map.sh
cd ~/skills && git add <name>/ site/installed-skills.json && git commit -m "Add <name>: <purpose>" && git push
```
