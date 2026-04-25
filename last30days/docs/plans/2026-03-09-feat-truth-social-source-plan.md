---
title: "feat: Add Truth Social as opt-in source"
type: feat
status: completed
date: 2026-03-09
---

# feat: Add Truth Social as opt-in source

Add Truth Social (Mastodon fork) as an opt-in social source. When `TRUTHSOCIAL_TOKEN` is set, posts from Truth Social appear alongside other sources in research results. When not configured, completely silent.

## Problem / Motivation

Issue #63 requested Truth Social support. Truth Social is a Mastodon fork with ~7M monthly active users. For users who care about that community's perspective on a topic, it's a valuable signal source. Follows the same opt-in pattern as Bluesky.

## Approach

Use Truth Social's Mastodon-compatible API directly with `urllib3` (no external dependencies). One env var: `TRUTHSOCIAL_TOKEN` (bearer token). Follow the Bluesky source pattern exactly across all 10 pipeline files.

**Why bearer token (not username/password):** Truth Social's OAuth uses a non-standard `/oauth/v2/token` endpoint with hardcoded `client_id`/`client_secret` extracted from their JS bundle. These values break when Truth Social updates their frontend. A bearer token is more stable - user extracts it once from browser dev tools (Application > Local Storage > truthsocial.com > `access_token`) or via `truthbrush` CLI.

**API endpoint:**
```
GET https://truthsocial.com/api/v2/search
Authorization: Bearer {token}
Params: q={topic}&type=statuses&limit=40
```

**Response format:** Standard Mastodon status objects with `content` (HTML), `created_at`, `url`, `account`, `favourites_count`, `reblogs_count`, `replies_count`.

## Files to Change

| # | File | Change |
|---|------|--------|
| 1 | `scripts/lib/truthsocial.py` | **New file.** API client: `search_truthsocial(topic, from_date, to_date, depth, config)` + `parse_truthsocial_response(response)`. Strip HTML tags from `content`. Handle 401/403/429 gracefully. |
| 2 | `scripts/lib/env.py` | Add `('TRUTHSOCIAL_TOKEN', None)` to `get_config()`. Add `is_truthsocial_available(config)`. |
| 3 | `scripts/lib/schema.py` | Add `TruthSocialItem` dataclass (id prefix `"TS"`). Add `truthsocial`/`truthsocial_error` fields to `Report`. Update `to_dict()`/`from_dict()`. |
| 4 | `scripts/lib/normalize.py` | Add `normalize_truthsocial_items()`. Map Mastodon fields: `favourites_count` -> `likes`, `reblogs_count` -> `reposts`, `replies_count` -> `replies`. |
| 5 | `scripts/lib/score.py` | Add `compute_truthsocial_engagement_raw()` + `score_truthsocial_items()`. Same weighted log formula as Bluesky. |
| 6 | `scripts/lib/dedupe.py` | Add `dedupe_truthsocial()` (one-liner wrapping `dedupe_items`). |
| 7 | `scripts/lib/render.py` | Add Truth Social sections to `_xref_tag()`, `_assess_data_freshness()`, `render_compact()`, `render_source_status()`, `render_context_snippet()`, `render_full_report()`. |
| 8 | `scripts/last30days.py` | ~20 touchpoints: TIMEOUT_PROFILES, VALID_SEARCH_SOURCES, import, `_search_truthsocial()`, `run_research()` param + dispatch + collect, `main()` availability + diag + flag + normalize + score + sort + dedupe + report. |
| 9 | `SKILL.md` | Add Truth Social to source lists, optionalEnv (`TRUTHSOCIAL_TOKEN`), stats template, security/privacy section. |
| 10 | `tests/test_truthsocial.py` | **New file.** Tests: HTML stripping, date parsing, response parsing, empty response, missing fields, depth config, auth error handling, successful search with mocked HTTP. |

## Key Implementation Details

### HTML stripping (`truthsocial.py`)

Truth Social returns HTML content (`<p>Post text</p>`). Strip tags to plain text:
```python
import re
def _strip_html(html: str) -> str:
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()
```

### Date filtering

Mastodon `created_at` is ISO 8601 (`2026-03-09T12:00:00.000Z`). Use `[:10]` slice for `YYYY-MM-DD` comparison against `from_date`/`to_date`.

### Engagement mapping

| Mastodon field | Internal field | Display |
|---------------|---------------|---------|
| `favourites_count` | `likes` | `{N}lk` |
| `reblogs_count` | `reposts` | `{N}rp` |
| `replies_count` | `replies` | `{N}re` |

### Error handling

| HTTP Status | Behavior |
|------------|----------|
| 200 | Parse and return results |
| 401 | Return `{"statuses": [], "error": "Truth Social token expired"}` |
| 403 | Return `{"statuses": [], "error": "Truth Social access denied (Cloudflare)"}` |
| 429 | Return `{"statuses": [], "error": "Truth Social rate limited"}` |
| Other | Return `{"statuses": [], "error": "Truth Social search failed: {status}"}` |

All errors return empty results gracefully - never crash the research run.

### DEPTH_CONFIG

| Depth | Limit |
|-------|-------|
| quick | 15 |
| default | 30 |
| deep | 60 |

## What NOT to Change

- `lib/__init__.py` - must stay bare (no eager imports)
- `cross_source_link.py` - works generically on items with `cross_refs` field
- `filter.py` - date filtering is generic
- No new pip dependencies

## Acceptance Criteria

- [x] `is_truthsocial_available()` returns False when `TRUTHSOCIAL_TOKEN` not set
- [x] No Truth Social stats line, no error, no mention when unconfigured
- [x] With valid `TRUTHSOCIAL_TOKEN`, posts are returned and rendered
- [x] HTML tags stripped from post content
- [x] Token expiry (401) returns empty results gracefully
- [x] Cloudflare block (403) returns empty results gracefully
- [x] `--diagnose` shows Truth Social availability status
- [x] SKILL.md documents `TRUTHSOCIAL_TOKEN` env var
- [x] All existing tests still pass
- [x] New tests cover: HTML stripping, parsing, auth errors, successful search
- [x] `bash scripts/sync.sh` deploys successfully

## Sources

- Issue #63: https://github.com/mvanhorn/last30days-skill/issues/63
- Truth Social API: Mastodon-compatible at `truthsocial.com/api/v2/search`
- Auth: Bearer token via browser dev tools or `truthbrush` CLI
- Pattern reference: `scripts/lib/bluesky.py` (most recent source addition)
- Bluesky auth plan: `docs/plans/2026-03-09-fix-bluesky-auth-opt-in-plan.md`
