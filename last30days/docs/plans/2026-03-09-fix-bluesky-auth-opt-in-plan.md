---
title: "fix: Make Bluesky opt-in with auth (searchPosts now requires authentication)"
type: fix
status: completed
date: 2026-03-09
---

# fix: Make Bluesky opt-in with auth (searchPosts now requires authentication)

## Problem

Bluesky's `app.bsky.feed.searchPosts` endpoint now returns **403 Forbidden** for unauthenticated requests. This broke today (2026-03-09), likely related to the CEO transition. The `searchActors` endpoint still works without auth, but `searchPosts` does not.

We built Bluesky as an always-on source (like HN and Polymarket) because the AT Protocol public API was documented as free. That's no longer true for post search.

**Current behavior:** Bluesky silently returns 0 results (403 caught, empty list returned). No stats line appears, no error shown. Users don't know it exists.

**Desired behavior:** Bluesky is opt-in via env vars. When not configured, completely invisible (no error, no stats line, no mention). When configured with auth, it works as before.

## Approach

Follow the same pattern as X/Twitter auth: env vars for credentials, availability check gates dispatch.

AT Protocol auth flow:
1. User creates an App Password at `bsky.app/settings/app-passwords`
2. User sets `BSKY_HANDLE` and `BSKY_APP_PASSWORD` env vars
3. `bluesky.py` calls `com.atproto.server.createSession` to get a bearer token
4. Subsequent `searchPosts` calls include `Authorization: Bearer {token}`

## Files to Change

| File | Change | Lines (est.) |
|------|--------|-------------|
| `scripts/lib/bluesky.py` | Add `_create_session()` auth, pass bearer token to search | ~25 |
| `scripts/lib/env.py` | Update `is_bluesky_available()` to check env vars; add env var loading | ~10 |
| `scripts/last30days.py` | Gate `do_bluesky` on `is_bluesky_available(config)`; update diag dicts | ~8 |
| `tests/test_bluesky.py` | Add auth session tests, update existing tests | ~15 |
| `SKILL.md` | Document `BSKY_HANDLE` / `BSKY_APP_PASSWORD` env vars in setup section | ~5 |

## Implementation Steps

### 1. `scripts/lib/env.py`

- Add `BSKY_HANDLE` and `BSKY_APP_PASSWORD` to the env var loading in `get_config()`
- Update `is_bluesky_available()`:
  ```python
  def is_bluesky_available(config: Dict[str, Any]) -> bool:
      return bool(config.get('BSKY_HANDLE') and config.get('BSKY_APP_PASSWORD'))
  ```

### 2. `scripts/lib/bluesky.py`

- Add `_create_session(handle, app_password)` that POSTs to `https://bsky.social/xrpc/com.atproto.server.createSession`
- Cache the access token for the lifetime of the search (module-level or passed through)
- Update `search_bluesky()` to accept config dict, extract creds, create session, add `Authorization: Bearer {token}` header
- On auth failure, return `{"posts": [], "error": "Bluesky auth failed"}` (don't raise)

### 3. `scripts/last30days.py`

- Change `do_bluesky` default from `True` to checking `is_bluesky_available(config)`:
  ```python
  has_bluesky = env.is_bluesky_available(config)
  ```
- Gate the `bluesky_future` submit on `has_bluesky` (already gated on `do_bluesky`, just wire it)
- Update both diagnostic dicts: `"bluesky": True` -> `"bluesky": has_bluesky`
- Pass `config` to `_search_bluesky()` so it can extract auth creds

### 4. `tests/test_bluesky.py`

- Test `_create_session` with mocked HTTP response
- Test `search_bluesky` with auth header injection
- Existing parse/normalize tests don't change (they don't hit the network)

### 5. `SKILL.md`

- Add Bluesky to the optional env vars section (near AUTH_TOKEN/CT0):
  ```
  BSKY_HANDLE=your-handle.bsky.social
  BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
  ```
- Keep Bluesky in source lists but note "(requires app password)" in setup

## What NOT to Change

- `render.py` - already handles empty bluesky gracefully (hides stats line when 0 items)
- `schema.py`, `normalize.py`, `score.py`, `dedupe.py` - no changes needed, they work on items already
- No error display when unconfigured - completely silent, same as how TikTok/Instagram behave when SCRAPECREATORS_API_KEY is missing

## Acceptance Criteria

- [x] `is_bluesky_available()` returns False when env vars not set
- [x] No Bluesky stats line, no error, no mention when unconfigured
- [x] With valid `BSKY_HANDLE` + `BSKY_APP_PASSWORD`, posts are returned
- [x] Auth failure returns empty results gracefully (no crash)
- [x] SKILL.md documents the env vars
- [x] All existing Bluesky tests still pass
- [x] New auth tests added
- [x] `bash scripts/sync.sh` deploys successfully

## Sources

- AT Protocol auth: `POST https://bsky.social/xrpc/com.atproto.server.createSession` with `{identifier, password}`
- App passwords: `bsky.app/settings/app-passwords`
- Existing pattern: X auth with AUTH_TOKEN/CT0 in `env.py:256-257`
- Existing pattern: TikTok/Instagram opt-in via `is_tiktok_available()` in `env.py:499`
