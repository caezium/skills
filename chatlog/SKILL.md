---
name: chatlog
description: >
  Query the user's own WeChat (微信) history through the local chatlog HTTP API
  (http://127.0.0.1:5030). Use whenever the user wants to read, search, summarize,
  or export their WeChat messages, contacts, or group chats — e.g. "what did 张三
  say last week", "summarize the 车队群 group today", "find messages about
  练车", "看看我和某人的聊天记录", "export this chat to CSV", "who's in this 群".
  Resolves people/groups to a talker, then queries chatlog by time range. Personal,
  read-only data already decrypted on this machine.
---

# Chatlog

`chatlog` decrypts the user's local WeChat database and serves it over a small HTTP API (and an MCP SSE endpoint). This skill drives that **HTTP API** with `curl` — it's the most reliable path and needs no extra setup.

Base URL: **`http://127.0.0.1:5030`** (the server listens on `0.0.0.0:5030`).

This is the user's *own* chat data, already decrypted and served on their machine. Treat it as private: query only what's asked, summarize locally, and never send it to an external service.

## Before anything: confirm the server is up

Every query depends on the server running. Check once at the start of a task:

```sh
curl -sf http://127.0.0.1:5030/api/v1/session?format=json >/dev/null && echo UP || echo DOWN
```

If `DOWN`, the user needs to start it. The interactive TUI (`chatlog`, then "开启 HTTP 服务") or `chatlog server` both work, but **don't launch a long-running server yourself** — tell the user to start it (or confirm the chatlog app is running and logged in). If a query returns an auth/key error, the data key may have expired — the user should re-run "获取密钥" / decrypt in the app.

## The one pattern to use for every call

Talker names, keywords, and group names are usually Chinese and contain `@`, spaces, etc. Let `curl` URL-encode for you with `-G --data-urlencode` — never hand-build query strings:

```sh
curl -sG http://127.0.0.1:5030/api/v1/chatlog \
  --data-urlencode "time=2026-06-01~2026-06-05" \
  --data-urlencode "talker=车友群" \
  --data-urlencode "format=json"
```

## The four endpoints

| Endpoint | Returns | Key params |
|---|---|---|
| `GET /api/v1/session` | recent conversations, newest first | `format` |
| `GET /api/v1/contact` | contacts (friends + others) | `keyword`, `format` |
| `GET /api/v1/chatroom` | group chats + their members | `keyword`, `format` |
| `GET /api/v1/chatlog` | **messages** (the main one) | `time`*, `talker`*, `sender`, `keyword`, `limit`, `offset`, `format` |

`*` = required for `/chatlog`. `session`/`contact`/`chatroom` wrap results in `{"items": [...]}`; `/chatlog` in JSON returns a **bare array** of messages.

See `references/api.md` for full response field lists, message `type` codes, media retrieval, CSV export, and the CLI.

## Workflow: almost always two steps

**1. Resolve the talker.** `/chatlog` needs a `talker` — a contact or a group. The user names someone in natural language ("Marcus", "the car team group"); turn that into something the API accepts.

`talker` accepts a wxid (`wxid_xxx`), a chatroom id (`xxxx@chatroom`), or a display name (remark / nickName / alias / group name). Display names work directly (verified), but they can be ambiguous or have variant characters — when in doubt, look it up first and use the exact id:

```sh
# find a person
curl -sG http://127.0.0.1:5030/api/v1/contact  --data-urlencode "keyword=张三" --data-urlencode "format=json"
# find a group (also shows members)
curl -sG http://127.0.0.1:5030/api/v1/chatroom --data-urlencode "keyword=车队" --data-urlencode "format=json"
```

Use the returned `userName` (for people) or `name` (for groups, the `...@chatroom` value) as the `talker`. If `keyword` matches several, show the user the candidates and ask which — don't silently pick one.

**2. Query messages** with that talker and a time range (below). Default (no `format`) returns clean, human-readable plain text — best when you'll read or summarize. Use `format=json` when you need to count, filter, or process; `format=csv` to export.

## Time ranges (required, absolute only)

`time` accepts a single day or a `start~end` range, in `YYYY-MM-DD`:

- `time=2026-06-04` — one day
- `time=2026-06-01~2026-06-05` — inclusive range

**Relative words are NOT supported** — `今天`, `近7天`, `yesterday` all error out. Compute concrete dates first. Today is **2026-06-05** per session context, but always derive dates so they stay correct:

```sh
TODAY=$(date +%F)                       # today
WEEK_AGO=$(date -v-7d +%F)              # 7 days ago (macOS)
# → time=${WEEK_AGO}~${TODAY}
```

## Common recipes

**"What did the 车队 group say today?"** (resolve group → fetch today, readable text):
```sh
curl -sG http://127.0.0.1:5030/api/v1/chatlog \
  --data-urlencode "time=$(date +%F)" \
  --data-urlencode "talker=12345678901@chatroom"
```

**"Find messages mentioning 练车 this past month"** (`keyword` filters server-side):
```sh
curl -sG http://127.0.0.1:5030/api/v1/chatlog \
  --data-urlencode "time=$(date -v-1m +%F)~$(date +%F)" \
  --data-urlencode "talker=车友群" \
  --data-urlencode "keyword=练车" --data-urlencode "format=json"
```

**"What did one person say in a group?"** Add `sender` (a wxid) to filter within a chatroom.

**"Export my chat with X to a spreadsheet"** — `format=csv`, redirect to a file:
```sh
curl -sG http://127.0.0.1:5030/api/v1/chatlog \
  --data-urlencode "time=2026-01-01~2026-06-05" \
  --data-urlencode "talker=wxid_xxx" --data-urlencode "format=csv" > chat.csv
```

**"What have I been talking about lately?"** → `GET /api/v1/session` for the recent-conversation list, then drill into ones the user cares about.

## Gotchas

- **Busy groups are huge.** A month in an active group can be thousands of messages. Narrow the time range, lean on `keyword`, or page with `limit`/`offset` rather than pulling everything. If you cap results, say so — don't imply you read it all.
- **Read text, process JSON.** For summaries, the default text format is already clean (sender, timestamp, content; media as markdown links). Only request JSON when you need structured fields.
- **Message types beyond text.** `type=1` is text; images/voice/video/stickers/files/links/quotes/system messages have other codes and may have empty `content`. The type table and how to read each is in `references/api.md`.
- **Media files** (images, voice, video, files) are fetched from `/image/`, `/voice/`, `/video/`, `/file/` using the key embedded in the text output or the message's `contents` field — see `references/api.md`.

## References

- `references/api.md` — full endpoint params, response schemas, message `type`/`subType` codes, media endpoints, CSV columns, and the `chatlog` CLI (key/decrypt/server).
