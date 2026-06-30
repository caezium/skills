# Per-source playbook

Detailed commands, subagent prompts, and gotchas for each capture source. Read this before pulling.
User-specific identifiers (vault path `$VAULT`, Feishu app/enterprise IDs, the WeChat self-chat hint,
contact roster) live in `local.private.md` next to the SKILL.md — gitignored, machine-local. Read it
at runtime; don't inline those values into anything that gets committed to a public repo.

## Table of contents
- [Feishu (lark-cli)](#feishu)
- [WeChat (chatlog)](#wechat)
- [Zen browser tabs](#zen-tabs)
- [Claude sessions → AI Build Queue](#claude-sessions)
- [Command Center wiring](#command-center)

---

## Feishu

`lark-cli` is on PATH via nvm node v20.20.2. App/enterprise/user identifiers and the dev-console URL
are in `local.private.md`. For normal pulls you don't need them — lark-cli uses its stored token.

**Auth model (the expensive lesson):**
- `lark-cli auth status` shows the user identity state: `ready`, `needs_refresh`, or `missing`.
- `needs_refresh` auto-resolves on the first valid API call (refresh token via `offline_access`). Don't
  re-login for it — just make a real call.
- `missing` → re-auth. **Request READ-ONLY scopes only:**
  ```sh
  lark-cli auth login --scope task:task:read,im:message:readonly,im:chat:read,contact:user.base:readonly
  ```
  Authorizing **write** scopes (which `--domain task,im,contact` pulls in) triggers an enterprise
  **管理员审批** (admin review) that can stall for hours and re-triggers every time you change scopes.
  Read-only scopes grant instantly. This is the single most important Feishu rule.
- Device-flow for agents: `lark-cli auth login --scope <...> --no-wait --json` returns a `verification_url`
  + `device_code`. The user's Chrome (the claude-in-chrome MCP browser) is logged into Feishu, so you can
  navigate it to the verification_url and click **Authorize** (read-only) — it completes without scanning.
  Then `lark-cli auth login --device-code <code> --json` captures the token.
- If a publish/version is stuck ("app is pending approval"), the dev-console version page (URL in
  `local.private.md`) may have an unpublished draft to **Publish** (publishing itself needs no approval
  when "Scope changes: None").

**What to pull:** (1) incomplete tasks; (2) a digest of ALL chats (p2p + group) — the user wants message
*content*, not just tasks. Always `--as user`. Use the `lark-task`, `lark-im`, `lark-contact` skills for
correct command syntax (e.g. `task +get-my-tasks`, `task +get-related-tasks`, `im` chat-list/messages).
Resolve open_ids to names at runtime via `lark-contact` — don't keep a name list in the public skill.

**Subagent prompt (copy, fill `<date>` / prior-sync date; pull `$VAULT` from the sidecar):**
> The user's `lark-cli` user identity is READY or needs_refresh (auto-refreshes on first call). Read
> scopes: task:task:read, im:message:readonly, im:chat:read, im:message.p2p_msg:get_as_user,
> im:message.group_msg:get_as_user, contact:user.base:readonly. ALWAYS `--as user`. Use the
> lark-task / lark-im / lark-contact skills. If a real call fails with an auth/token error, STOP and
> report "Feishu needs browser re-auth" + the failing command — do NOT retry repeatedly (admin-review trap).
> (1) Pull incomplete tasks → write `<VAULT>/01_inbox/feishu/feishu-inbox-<date>.md` (frontmatter
> tags:[inbox,feishu], source:feishu, captured:<date>, status:to-process; `## Tasks assigned to me`
> checklist with 📅 due; `## Messages needing action`). (2) List ALL chats (p2p+group), pull recent
> messages, FOCUS on what's new since <prior-date>, summarize per-conversation (decisions, asks, links)
> → write `feishu-messages-<date>.md` (`## Direct messages (1:1)` ### per person, `## Group chats` ###
> per group, most-active first, resolve open_ids to names, keep Chinese as-is). Only those two files.
> Don't commit. Return counts + 3-5 notable threads.

The contact roster + which group is which is in `local.private.md` for context — but the workflow
resolves names at runtime, so you don't strictly need it.

---

## WeChat

**Server:** the `chatlog` HTTP API at `http://127.0.0.1:5030` must be running. Binary at `~/go/bin/chatlog`;
start with `chatlog server` (or the TUI: `chatlog` → 获取密钥 → 开启 HTTP 服务). Verify:
```sh
curl -s --max-time 5 "http://127.0.0.1:5030/api/v1/session?format=json" | head -c 80
```
**Quote the URL** — an unquoted `?` triggers zsh `no matches found` and looks like a dead server when it's fine.

**Find the self-chat at runtime.** The capture inbox is the chat flagged `isSelf` in the session list
(`/api/v1/session?format=json`) — NOT `filehelper` / 文件传输助手, which is empty. Discover it rather than
hardcoding; `local.private.md` has a fallback wxid hint only.

**Pull messages in a date window:**
```sh
curl -s "http://127.0.0.1:5030/api/v1/chatlog?talker=<self-talker>&time=<from>~<to>&format=json"
```

**Subagent prompt (fill `<date>` / `<prior-date>`; `<VAULT>` from sidecar):**
> The local chatlog API at http://127.0.0.1:5030 is UP. Pull the user's WeChat self-saves into the vault.
> The self-chat is the talker flagged `isSelf` in `/api/v1/session?format=json` — NOT filehelper (empty).
> Use the chatlog skill. Pull messages for <prior-date> → <date>. Extract actionable items + links + ideas,
> summarize, keep Chinese as-is, skimmable. Write `<VAULT>/01_inbox/wechat/wechat-inbox-<date>.md`
> (frontmatter tags:[inbox,wechat], source:wechat, captured:<date>, status:to-process; `## To process`
> checklist + `## Links`). If nothing new, say so and note the latest self-message date. Only that file.
> Don't commit. Return counts + notable items.

The self-chat skews toward karting (training/budget/series rankings), content-creation ideas, and
research leads — that's signal, not noise.

---

## Zen tabs

Run the bundled script — it decodes the mozlz4 session and writes the categorized note in one shot:
```sh
python3 ~/.claude/skills/vault-resync/scripts/decode_zen_tabs.py \
  --out "$VAULT/01_inbox/tabs/zen-tabs-<date>.md" --date <date>
```
Zen profiles live in `~/Library/Application Support/zen/Profiles/*/sessionstore-backups/recovery.jsonlz4`;
the script picks the most recently-modified non-empty one. Expect ~1,500 tabs — the script buckets them
(video/code/papers/ai_tools/docs/social/other) and drops search/localhost noise. **Don't** `pip install lz4`
(PEP 668). For a different Chromium/Firefox browser, pass `--profiles <that browser's Profiles dir>`.

---

## Claude sessions

Pull the active (non-archived) session list — each one is a thing the user is building/doing with AI:
```
list_sessions(include_archived=false, limit=200)   # mcp__ccd_session_mgmt__list_sessions
```
Then rebuild `$VAULT/01_inbox/projects/claude-projects.md` (the "AI Build Queue"). Processing rules:
- **Group by `cwd`** (the project folder). Multiple sessions in one repo = one project line.
- **Collapse recurring dupes** — e.g. ~10 "Dayflow weekly sync", several "Sync obsidian forks",
  "Expand kdb output prediction"/"Finish kdb code gen benchmark". These are maintenance, not N projects.
- **Flag status:** PR `MERGED` → ✅ likely done (archive candidate); PR `OPEN` → in review; `isRunning` → active.
- **Surface what's new since last sync** in a `## 🆕 New since <prior-date>` section at the top.
- Bucket the rest: 🟢 products/repos · 🔁 recurring · 🏎️ karting cluster (matches their WeChat ideas) ·
  🔵 idea/research one-offs · ✅ done. Keep area tags (#build #venture #content #learn #body #admin).
- Offer to **archive the done sessions** (`archive_session`) so "active" stays meaningful — but ask first.

---

## Command Center

After writing the dated notes, repoint the capture-source links in `$VAULT/homepage.md` (the
`## 📥 Capture sources` list) to the new `<date>` notes, keeping a `· [[prev]]` link to the prior one.
Add genuinely actionable findings to `$VAULT/Tasks Board.md` (a Kanban file; items are `- [ ]` lines
with area tags). The Board's checkboxes are indexed by the Tasks plugin and also surface on the homepage.

Commit message convention: `Re-sync all capture sources (<date>): <one-line of what changed>`.
