---
title: Fix YouTube Timeout and Reddit Resilience
type: fix
date: 2026-02-15
---

# Fix YouTube Timeout and Reddit Resilience

## Overview

YouTube search+transcript fetching exceeds the 60s future timeout on popular topics (20 videos + 5 transcripts), discarding all results. Reddit 429 rate-limiting burns through the entire time budget with aggressive retries, causing global timeouts. Both issues cause the script to return incomplete results and sometimes crash.

## Problem Statement

**YouTube timeout (blocks launch):** YouTube found 20 Seedance 2.0 videos and fetched 4/5 transcripts, but the 60s future timeout killed everything — `✗ Error: YouTube search timed out after 60s`. The data was there; the budget wasn't.

**Reddit 429 cascade (degrades reliability):** One enrichment item hitting 429 burns up to 93s (3 retries x 30s timeout + backoff) against a 45s budget. Phase 2 supplemental search then also 429s, burning another 30s. Total wasted: 75s on doomed requests, triggering the 180s global timeout.

Observed failures across 6 test runs:
- `seedance 2 access`: YouTube timed out (60s), Reddit 0 threads
- `kanye west bully`: Global timeout first run, needed --quick retry
- `Peter Steinberger`: Global timeout during enrichment
- `nano banana pro`: Reddit timed out, YouTube worked (5 videos in time)
- `kanye west bully` (retry): Reddit 0 threads, YouTube 4 videos

## Proposed Solution

### Fix 1: Bump YouTube future timeout (NOT YET DONE)

**File:** `scripts/last30days.py:40-44`

Give YouTube its own timeout, separate from the shared `future` timeout. YouTube inherently takes longer because it does search + parallel transcript fetching.

```python
# Option A: YouTube-specific timeout key
TIMEOUT_PROFILES = {
    "quick":   {"global": 90,  "future": 30, "youtube_future": 60, ...},
    "default": {"global": 180, "future": 60, "youtube_future": 90, ...},
    "deep":    {"global": 300, "future": 90, "youtube_future": 120, ...},
}

# Option B: Simpler — just bump default future to 90 for all sources
TIMEOUT_PROFILES = {
    "quick":   {"global": 90,  "future": 45, ...},
    "default": {"global": 180, "future": 90, ...},
    "deep":    {"global": 300, "future": 120, ...},
}
```

**Recommendation:** Option A (YouTube-specific key) — keeps Reddit/X futures tight while giving YouTube the breathing room it needs. Reddit/X finish in 20-40s; YouTube needs 60-90s for transcript fetching.

Then where YouTube future is collected (~line 646):
```python
youtube_timeout = timeouts.get("youtube_future", timeouts["future"])
youtube_items, youtube_error = youtube_future.result(timeout=youtube_timeout)
```

### Fix 2: Reddit 429 fail-fast (ALREADY DONE — needs commit)

**Status:** Implemented in working tree, uncommitted. Changes across 4 files:

| File | Change |
|------|--------|
| `scripts/lib/http.py` | `get_reddit_json()` accepts `timeout` and `retries` params (was hardcoded 30s/3) |
| `scripts/lib/reddit_enrich.py` | `RedditRateLimitError` exception; `fetch_thread_data()` propagates 429; `enrich_reddit_item()` defaults to 10s timeout / 1 retry |
| `scripts/lib/openai_reddit.py` | `search_subreddits()` reduced to 1 retry; breaks subreddit loop on first 429 |
| `scripts/last30days.py` | Enrichment loop catches `RedditRateLimitError`, cancels futures, bails; `rate_limited` flag skips Phase 2 Reddit |

**Impact:** 429 scenario drops from ~75s wasted to ~12s wasted.

## Acceptance Criteria

- [ ] YouTube `seedance 2 access` query completes with videos (was timing out at 60s)
- [ ] YouTube `kanye west bully` query returns 4+ videos with transcripts
- [ ] Reddit 429 detected within ~12s, remaining enrichment skipped
- [ ] Phase 2 Reddit skipped when rate-limited
- [ ] No global timeout on default depth for any of the 5 test queries
- [ ] All changes committed and synced to `~/.claude/skills/last30days21/` and `~/.claude/skills/last30days/`

## Files to Modify

| File | Status | Changes |
|------|--------|---------|
| `scripts/last30days.py` | Modify (partially done) | Add `youtube_future` to TIMEOUT_PROFILES; use it for YouTube future collection |
| `scripts/lib/http.py` | Done (uncommitted) | Parameterized `get_reddit_json()` timeout/retries |
| `scripts/lib/reddit_enrich.py` | Done (uncommitted) | `RedditRateLimitError`, fail-fast enrichment |
| `scripts/lib/openai_reddit.py` | Done (uncommitted) | 429 early-bail in `search_subreddits()` |

## Testing

```bash
# Quick smoke test — YouTube should complete within 90s
cd ~/.claude/skills/last30days21
python3 scripts/last30days.py "seedance 2 access" --emit=compact 2>&1 | grep -E "YouTube|timeout"

# Verify YouTube items in output
python3 scripts/last30days.py "kanye west bully" --quick --emit=compact 2>/dev/null | grep "youtube.com" | wc -l

# Full integration — run the skill in Claude Code
# /last30days21 seedance 2 access
# Verify YouTube appears in stats block
```
