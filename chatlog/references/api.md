# Chatlog API & CLI reference

Everything verified against a running `chatlog` v0.0.28 server on macOS (WeChat 4.x data).
Base URL throughout: `http://127.0.0.1:5030`. Always call with `curl -sG ... --data-urlencode "k=v"`.

> The upstream repo `github.com/sjzar/chatlog` was taken down (Oct 2025), so this file —
> grounded in the actual running binary — is the source of truth, not the web.

## Table of contents
- [Endpoints](#endpoints)
- [Response schemas](#response-schemas)
- [Message type codes](#message-type-codes)
- [Media retrieval](#media-retrieval)
- [Output formats](#output-formats)
- [The chatlog CLI](#the-chatlog-cli)
- [Troubleshooting](#troubleshooting)

## Endpoints

### `GET /api/v1/chatlog` — messages
The main endpoint. `time` and `talker` are required.

| Param | Required | Meaning | Notes |
|---|---|---|---|
| `time` | yes | day or range | `2026-06-04` or `2026-06-01~2026-06-05`. Absolute `YYYY-MM-DD` only — relative words error. |
| `talker` | yes | who/what the chat is with | wxid, `xxx@chatroom`, or display name (remark/nickName/alias/group name). Comma-separate for multiple talkers. |
| `sender` | no | filter to one author | a wxid; useful inside group chats. |
| `keyword` | no | substring filter on message text | server-side; combine with `time`. |
| `limit` | no | max messages returned | for paging large rooms. |
| `offset` | no | skip N messages | paging with `limit`. |
| `format` | no | `text` (default), `json`, `csv` | text is human-readable; json is a bare array. |

### `GET /api/v1/session` — recent conversations
Params: `format`. Newest first. Good "what's been active lately" overview.

### `GET /api/v1/contact` — contacts
Params: `keyword` (search by name/remark/alias), `format`. Returns friends *and* non-friends (e.g. group co-members), distinguished by `isFriend`.

### `GET /api/v1/chatroom` — group chats
Params: `keyword` (search by group name), `format`. Includes the member list, so it's also how you see "who's in this group".

## Response schemas (JSON)

`session`, `contact`, `chatroom` → `{"items": [ ... ]}`. `chatlog` → a **bare array**.

**Message** (`/chatlog`):
```json
{
  "seq": 1780289347000,
  "time": "2026-06-01T12:49:07+08:00",
  "talker": "12345678901@chatroom",
  "talkerName": "车友群",
  "isChatRoom": true,
  "sender": "wxid_example0001",
  "senderName": "张三",
  "isSelf": false,
  "type": 1,
  "subType": 0,
  "content": "明天几点出发？[Fight]",
  "contents": { }
}
```
For media/app messages `content` is often empty and the payload lives in `contents` (e.g. `{"md5":..., "path":...}` for images, `{"title":...}` for shared cards/files).

**Session**: `{userName, nickName, content (last msg preview), nTime, nOrder}`
**Contact**: `{userName, alias, remark, nickName, isFriend}`
**Chatroom**: `{name (xxx@chatroom), owner (wxid), users: [{userName, displayName}]}`

## Message type codes

| `type` | Meaning | How to read it |
|---|---|---|
| 1 | text | `content` is the text |
| 3 | image | `contents.md5` + `contents.path` → fetch via `/image/` |
| 34 | voice | fetch via `/voice/` |
| 43 | video | `contents` has `md5`/`path`/`rawmd5` → `/video/` |
| 47 | sticker / emoji (动画表情) | usually an external CDN url in the text rendering |
| 49 | app message — see `subType` | shared content; `contents.title` often set |
| 10000 | system message | invites, recalls, "you added X", etc. |

Common `type=49` `subType`s seen: `5` link/card, `6` file, `8` sticker pack, `19` merged-forward, `51` video-channel, `57` quote/reply, `63` channel (视频号) post. Treat unknown subTypes as "an app/share message" and fall back to `contents.title` or surrounding context.

## Media retrieval

In **text** format, media render as markdown links already pointing at the local server, e.g.
`![图片](http://127.0.0.1:5030/image/<md5>,<path>)`. Just GET that URL to download the bytes.
(Sticker/emoji links may point at Tencent CDNs instead — those are remote, not on the local server.)

In **JSON** format, build the key from `contents`: it's `md5,path` joined by a comma.
```sh
# from a type=3 message's contents {"md5":"<md5>","path":"msg/attach/<...>/Img/<...>"}
curl -s "http://127.0.0.1:5030/image/<md5>,msg/attach/<...>/Img/<...>" -o img.jpg
```
Endpoints: `/image/`, `/voice/`, `/video/`, `/file/`, `/data/`. A bad/unknown key returns 404; `/file/` may 302-redirect to the resolved path. Voice often comes back as SILK/`.amr`-style audio.

## Output formats

- **text** (default): one block per message — `senderName(wxid) HH:MM:SS` then the content, quotes shown with `>`. Best for reading and summarizing; least tokens of prose.
- **json**: bare array of message objects above. Use to count/filter/transform.
- **csv**: spreadsheet export. Redirect to a `.csv` file; columns follow the message fields (time, talker, sender, type, content, …).

## The chatlog CLI

The binary lives at `~/go/bin/chatlog`. Subcommands (`chatlog <cmd> --help` for flags):

| Command | Purpose |
|---|---|
| `chatlog` | interactive TUI (account, get key, decrypt, start/stop HTTP+MCP server) |
| `chatlog server` | start the HTTP + MCP server headless. Flags: `-a/--addr`, `-d/--data-dir`, `-w/--work-dir`, `-k/--data-key`, `-i/--img-key`, `-p/--platform`, `-v/--version`, `--auto-decrypt` |
| `chatlog key` | extract the data key from the running WeChat process (`-p PID`, `-x` xor key) |
| `chatlog decrypt` | decrypt the database files (`-k` key, `-d` data dir, `-w` work dir) |
| `chatlog dumpmemory` | dump process memory (advanced/debug) |
| `chatlog version` | print version |

Prefer the HTTP API for queries. Only reach for the CLI to (re)start the server, refresh the key, or re-decrypt — and prefer asking the user to do that in their already-open app rather than spawning processes.

## MCP

The server also speaks MCP over SSE at `/sse` (see the app's "MCP 集成指南"). Within Claude Code the HTTP API via `curl` is simpler and needs no MCP client config, so this skill uses HTTP. Mention the SSE endpoint only if the user specifically wants to wire chatlog into an MCP-aware client.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| connection refused / `DOWN` | server not started — user starts it in the chatlog app or `chatlog server`. |
| `time range not found` / `invalid argument: time` | relative or malformed `time` — use absolute `YYYY-MM-DD`. |
| empty results for a real person | wrong `talker` — resolve via `/contact` or `/chatroom` and use the exact `userName`/`name`. |
| garbled / decrypt errors | data key stale — user re-runs 获取密钥 / decrypt; key rotates per WeChat session. |
| huge/slow response | narrow `time`, add `keyword`, or page with `limit`+`offset`. |
