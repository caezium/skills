---
name: vault-resync
description: >-
  Re-pull all of the user's external capture sources into their Obsidian vault inbox and refresh
  the Command Center dashboards. Use this whenever the user asks to "re-sync", "resync", "pull
  new stuff", "update my inbox/vault", "refresh my tasks", "what's new in Feishu/WeChat/my tabs",
  "catch me up", or "pull from the providers again" — even if they only name one source, default
  to refreshing all of them unless they scope it down. The sources are: Feishu (lark-cli), WeChat
  self-chat (chatlog), Zen browser tabs (session decode), and active Claude Code sessions (the AI
  build queue). This skill encodes hard-won auth/format gotchas that are easy to get wrong — always
  consult it before touching these sources rather than improvising.
---

# Vault re-sync

This pulls the user's scattered capture sources into one place — the Obsidian vault inbox — and
refreshes the dashboards they read. The whole point of the vault system is that they shouldn't have
to hold "what's new across Feishu / WeChat / ~1500 browser tabs / my Claude projects" in their head.
This skill is the recurring sweep that keeps that promise.

**User-specific values** (vault path, Feishu app details, the WeChat self-chat hint) live in
`local.private.md` next to this SKILL.md — it's gitignored and machine-local, kept out of the public
repo on purpose. Read it at the start of a run. Where a value can be *discovered* at runtime instead
of stored, prefer that (noted per-source below). `$VAULT` below = the vault root from the sidecar.

## The four sources → where they land

| Source | Tool | Output note |
|---|---|---|
| Feishu tasks + all-chat messages | `lark-cli` (read-only scopes) | `01_inbox/feishu/feishu-inbox-<date>.md` + `feishu-messages-<date>.md` |
| WeChat self-saves | `chatlog` HTTP API | `01_inbox/wechat/wechat-inbox-<date>.md` |
| Zen browser tabs | `scripts/decode_zen_tabs.py` | `01_inbox/tabs/zen-tabs-<date>.md` |
| Active Claude sessions | `list_sessions` MCP | `01_inbox/projects/claude-projects.md` (the AI Build Queue) |

`<date>` is today as `YYYY-MM-DD`. Always read the previous dated note first so you can frame the
pull as "what's new since last sync" rather than re-dumping everything.

## Orchestration pattern (do it in this order)

1. **Snapshot first.** `cd "$VAULT" && git add -A && git commit -m "snapshot before re-sync"`. This
   gives a restore point before you write anything.
2. **Pre-flight: disk space.** See "Disk pre-flight" — a full disk silently breaks everything,
   including your own shell. Check before you start.
3. **Fan out the slow pulls.** Feishu and WeChat each involve many API calls and per-conversation
   summarization — launch them as **parallel background subagents** (one per source) using the prompts
   in `references/sources.md`, so they run while you do the fast local work.
4. **Do the fast local pulls inline** while the agents run: decode Zen tabs (one script call) and
   rebuild the AI Build Queue from `list_sessions`.
5. **Fold in the agent results** as they land. Read each agent's summary; don't re-read the full note
   unless something looks off.
6. **Update the Command Center.** Repoint the capture-source links in `homepage.md` to the new dated
   notes, and surface any genuinely actionable finding (a deadline, an escalation) onto `Tasks Board.md`
   with an area tag + due date — don't let a real action item rot inside a digest.
7. **Commit + push.** `git add -A && git commit -m "Re-sync all capture sources (<date>): ..." && git push`.
   If push fails with an HTTP/2 framing error, retry with `git -c http.version=HTTP/1.1 push`.

Scale to what was asked. "Re-sync everything" → all four. "What's new in Feishu" → just that one,
still following its source rules.

## Disk pre-flight

A 100%-full disk on macOS makes the shell itself fail (`ENOSPC: no space left on device`) — commands
can't even write their output, so you'll be blocked before you start. If a trivial `Bash` call errors
with ENOSPC, the disk is the problem, not your command.

The user has **Burrow** for exactly this — its MCP tools run out-of-process so they work even when the
shell can't. Use `burrow_doctor` (read-only health) and `burrow_analyze` (size-ranked tree) to see the
situation, and `burrow_clean` to clear caches. Caches rarely free enough alone; the big wins are usually
VM images, app DB backups (e.g. `~/Library/Application Support/Dayflow/backups` + timestamped
`Dayflow.backup-*` copies), and stale build dirs. **Only auto-delete caches.** For real user data — VMs,
project folders, app data — show the user the sizes and let them choose. Never nuke a directory you
didn't create without their say-so.

## Per-source details

Each source has non-obvious auth/format traps. Read `references/sources.md` before pulling — it has the
exact commands, the subagent prompts, and the gotchas. The traps that bite hardest:

- **Feishu — read-only scopes ONLY.** Re-auth (only if needed) with
  `lark-cli auth login --scope task:task:read,im:message:readonly,im:chat:read,contact:user.base:readonly`.
  **Never use `--domain`** — that requests *write* scopes, and authorizing write scopes triggers a slow
  enterprise admin review that has cost hours. A `needs_refresh` token auto-refreshes on the first valid
  API call; only if that fails do you re-auth (you can drive the logged-in browser to click Authorize).
  App/enterprise IDs and the dev-console URL are in `local.private.md`.
- **WeChat — discover the self-chat at runtime.** It's the chat flagged `isSelf` in the chatlog session
  list, NOT `filehelper` / 文件传输助手 (which is empty). The `chatlog` server must be running
  (`chatlog server`, binary at `~/go/bin/chatlog`) on `http://127.0.0.1:5030`. Quote URLs in curl — a bare
  `?` gets eaten by zsh globbing and looks like a dead server when it isn't.
- **Zen tabs — use the bundled script.** `python3 scripts/decode_zen_tabs.py --out "$VAULT/01_inbox/tabs/zen-tabs-<date>.md" --date <date>`.
  It handles the mozlz4 decode with no dependencies. Don't `pip install lz4` (PEP 668 blocks it).
- **Claude sessions — dedupe by folder, flag status.** `list_sessions` returns ~85 with heavy duplication
  (recurring "weekly sync" etc.) and many merged-PR sessions that are actually done. Group by `cwd`,
  collapse dupes, flag ✅-done (merged PRs) as archive candidates, surface what's new since last sync.

## Quality bars (what makes this "the same high quality")

- **Dedupe and categorize, don't dump.** 1,500 raw URLs or 250 raw messages is just moving the mess.
  Bucket, summarize, count. The note should be skimmable in 30 seconds.
- **Surface deadlines as tasks.** A real commitment with a clock (a demo date, an escalating reminder)
  belongs on the board with a 📅 due date, not buried in prose.
- **Frame as a delta.** "9 new since 06-23" beats re-listing 259 old items. Read the prior note first.
- **Keep Chinese text as-is** but make it scannable.
- **Don't loop on Feishu auth.** If read-only re-auth still fails, stop and tell the user — repeated
  login attempts re-trigger the admin-review trap. One clean attempt, then escalate.

After a re-sync, give a tight recap: what each source surfaced, the count of new items, and the one or
two things that actually need attention this week.
