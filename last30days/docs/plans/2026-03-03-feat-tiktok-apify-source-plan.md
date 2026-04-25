---
title: "feat: Add TikTok as 7th source via Apify"
type: feat
date: 2026-03-03
---

# feat: Add TikTok Signal via Apify

## Overview

Add TikTok as the 7th research source alongside Reddit, X, YouTube, HN, Polymarket, and Web. Use the **Apify** platform (`clockworks/tiktok-scraper` actor) to search TikTok by keyword, extract engagement metrics (views, likes, comments), and optionally pull video captions for synthesis enrichment — mirroring the YouTube pattern.

**Why this matters:** TikTok is where trends break first for many topics (products, music, culture, tech tips, news reactions). A viral TikTok with 2M views is a stronger signal than a tweet with 500 likes. The skill currently misses this entirely.

**Why Apify:** BYO API key, $5/month free credits (no CC required), pay-per-result pricing, Python SDK (`apify-client`), and the same actor platform supports Facebook and Instagram scrapers — so this investment pays forward.

## Proposed Solution

### Architecture: Shared Apify Client + Per-Source Modules

```
scripts/lib/
  apify_client_wrapper.py   ← NEW: shared Apify client init + helpers (reused by FB/IG later)
  tiktok.py                 ← NEW: TikTok search, captions, relevance
  # future:
  # facebook.py             ← uses same apify_client_wrapper.py
  # instagram.py            ← uses same apify_client_wrapper.py
```

This design means adding Facebook or Instagram later is just a new `facebook.py` module — the Apify client setup, token validation, and error handling are already done.

### Data Flow

```
User topic + date range
     ↓
[apify_client_wrapper.py] init client with APIFY_API_TOKEN
     ↓
[tiktok.py] search_tiktok()
  ├─ Call clockworks/tiktok-scraper actor (sync API, ≤5min)
  ├─ Input: searchQueries=[core_topic], resultsPerPage=N (depth-aware)
  ├─ Parse: id, text, playCount, diggCount, commentCount, createTimeISO, authorMeta, webVideoUrl, hashtags
  ├─ Sort by playCount (views) descending
  ├─ Compute relevance via token-overlap (reuse youtube_yt._compute_relevance pattern)
  └─ Return items
     ↓
[tiktok.py] fetch_captions() (optional enrichment for top N)
  ├─ Re-call actor with shouldDownloadSubtitles=true for top videos
  ├─ OR use video text/description as lightweight "caption" alternative
  └─ Truncate to 500 words, attach as caption_snippet
     ↓
[normalize.py] normalize_tiktok_items() → List[TikTokItem]
     ↓
[score.py] score_tiktok_items()
  ├─ compute_tiktok_engagement_raw(): 0.50*log1p(views) + 0.30*log1p(likes) + 0.20*log1p(comments)
  ├─ Weighted: 0.45*relevance + 0.25*recency + 0.30*engagement
  └─ Same formula as YouTube (views-dominant)
     ↓
[dedupe.py] dedupe_tiktok() + cross_source_link()
     ↓
[render.py] render TikTok section
     ↓
[SKILL.md] stats line: 🎵 TikTok: N videos │ N views │ N with captions
```

## Technical Approach

### Phase 1: Apify Client Wrapper (`scripts/lib/apify_client_wrapper.py`)

Shared module for all Apify-backed sources. Keeps TikTok, Facebook, Instagram from duplicating client setup.

```python
"""Shared Apify client utilities for last30days sources."""

from apify_client import ApifyClient
from typing import Optional, Dict, Any, List

def get_apify_client(token: str) -> ApifyClient:
    """Initialize Apify client with token."""
    return ApifyClient(token=token)

def run_actor_sync(
    client: ApifyClient,
    actor_id: str,
    run_input: Dict[str, Any],
    timeout_secs: int = 300,
    max_items: int = None,
) -> List[Dict[str, Any]]:
    """Run an Apify actor synchronously and return dataset items.

    Args:
        client: Initialized ApifyClient
        actor_id: e.g. "clockworks/tiktok-scraper"
        run_input: Actor-specific input dict
        timeout_secs: Max wait time (default 5 min)
        max_items: Cap on returned items (cost control)

    Returns:
        List of result dicts from the actor's default dataset
    """
    run = client.actor(actor_id).call(
        run_input=run_input,
        timeout_secs=timeout_secs,
    )
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    if max_items:
        items = items[:max_items]
    return items
```

**Key design decisions:**
- Single `APIFY_API_TOKEN` env var for all Apify sources (TikTok, future FB, IG)
- `run_actor_sync()` wraps the call+wait+fetch pattern used by every Apify actor
- `max_items` param provides cost control (important with $5 free credits)

### Phase 2: TikTok Search Module (`scripts/lib/tiktok.py`)

```python
"""TikTok search via Apify clockworks/tiktok-scraper."""

ACTOR_ID = "clockworks/tiktok-scraper"

DEPTH_CONFIG = {
    "quick":   {"results_per_page": 10, "max_captions": 3},
    "default": {"results_per_page": 20, "max_captions": 5},
    "deep":    {"results_per_page": 40, "max_captions": 8},
}

def search_tiktok(topic, from_date, to_date, depth="default", token=None):
    """Search TikTok via Apify.

    Returns:
        Dict with 'items' list and optional 'error'.
    """
    # 1. Init client via apify_client_wrapper
    # 2. Build input: searchQueries=[_extract_core_subject(topic)], resultsPerPage=N
    # 3. Call run_actor_sync(client, ACTOR_ID, input, timeout=120)
    # 4. Parse items: extract id, text, playCount, diggCount, commentCount,
    #    shareCount, createTimeISO, authorMeta.name, webVideoUrl, hashtags
    # 5. Filter by date range (from_date to to_date)
    # 6. Sort by playCount descending
    # 7. Compute relevance via _compute_relevance(topic, item_text)
    # 8. Return structured items

def fetch_captions(video_items, token, depth="default"):
    """Fetch captions/subtitles for top N TikTok videos.

    Strategy: Re-run actor with shouldDownloadSubtitles=true for
    specific video URLs, OR fall back to video text/description
    as a lightweight alternative.

    Returns:
        Dict mapping video_id → caption_text (truncated to 500 words)
    """

def search_and_enrich(topic, from_date, to_date, depth="default", token=None):
    """Search + caption enrichment orchestrator (mirrors youtube_yt.search_and_transcribe)."""

def parse_tiktok_response(response):
    """Extract items list from search_and_enrich response."""
```

**Apify actor input for keyword search:**
```json
{
    "searchQueries": ["claude code tips"],
    "resultsPerPage": 20,
    "shouldDownloadSubtitles": false,
    "shouldDownloadVideos": false,
    "shouldDownloadCovers": false
}
```

**Apify actor output fields we use:**

| Apify Field | Our Field | Notes |
|---|---|---|
| `id` | `id` | TikTok video ID |
| `text` | `caption` | Video caption/description |
| `playCount` | `engagement.views` | Primary engagement signal |
| `diggCount` | `engagement.likes` | Secondary signal |
| `commentCount` | `engagement.num_comments` | Tertiary signal |
| `shareCount` | (stored but not scored) | Available for future use |
| `createTimeISO` | `date` | Parse to YYYY-MM-DD |
| `authorMeta.name` | `author_name` | Creator handle |
| `authorMeta.fans` | (stored but not scored) | Follower count |
| `webVideoUrl` | `url` | Direct TikTok link |
| `hashtags[].name` | `hashtags` | For relevance boosting |
| `videoMeta.duration` | `duration` | For filtering very short clips |

**Relevance scoring:** Reuse the token-overlap algorithm from `youtube_yt._compute_relevance()`. Additionally boost relevance when topic tokens appear in hashtags (TikTok-specific signal).

**Caption enrichment strategy:**
1. **Primary:** Use the `text` field (video description/caption) — always available, free
2. **Enhanced:** For top N videos, re-run actor with `shouldDownloadSubtitles: true` to get spoken-word captions
3. **Fallback:** If subtitles unavailable, use `text` field alone (most TikTok videos have descriptive captions)

This is cheaper than YouTube transcripts (no second yt-dlp call needed for the basic case).

### Phase 3: Schema + Normalization

**`scripts/lib/schema.py` — add TikTokItem dataclass:**

```python
@dataclass
class TikTokItem:
    """Normalized TikTok item."""
    id: str                    # video_id
    text: str                  # caption/description
    url: str                   # webVideoUrl
    author_name: str           # authorMeta.name
    date: Optional[str] = None
    date_confidence: str = "high"  # Apify provides exact timestamps
    engagement: Optional[Engagement] = None  # views, likes, num_comments
    caption_snippet: str = ""  # spoken-word caption (if available), else text
    hashtags: List[str] = field(default_factory=list)
    relevance: float = 0.7
    why_relevant: str = ""
    subs: SubScores = field(default_factory=SubScores)
    score: int = 0
    cross_refs: List[str] = field(default_factory=list)
```

**`scripts/lib/schema.py` — add to Engagement dataclass:**
- `shares: Optional[int] = None` — TikTok shares (also useful for future Facebook)

**`scripts/lib/schema.py` — add to Report dataclass:**
- `tiktok: List[TikTokItem] = field(default_factory=list)`
- `tiktok_error: Optional[str] = None`

**`scripts/lib/normalize.py` — add `normalize_tiktok_items()`:**
- Parse `createTimeISO` → YYYY-MM-DD
- Create Engagement(views=playCount, likes=diggCount, num_comments=commentCount)
- Create TikTokItem objects
- Hard date filter (like Reddit/X, not soft like YouTube)

### Phase 4: Scoring

**`scripts/lib/score.py` — add TikTok scoring:**

```python
def compute_tiktok_engagement_raw(engagement):
    """TikTok engagement: views-dominant like YouTube.
    0.50*log1p(views) + 0.30*log1p(likes) + 0.20*log1p(comments)
    """
    views = getattr(engagement, 'views', 0) or 0
    likes = getattr(engagement, 'likes', 0) or 0
    comments = getattr(engagement, 'num_comments', 0) or 0
    return 0.50 * log1p(views) + 0.30 * log1p(likes) + 0.20 * log1p(comments)

def score_tiktok_items(items):
    """Score TikTok items. Same weights as YouTube:
    0.45*relevance + 0.25*recency + 0.30*engagement"""
```

### Phase 5: Deduplication + Cross-Source Linking

**`scripts/lib/dedupe.py`:**

```python
def dedupe_tiktok(items, threshold=0.7):
    """Dedupe TikTok items via Jaccard similarity on text + author_name."""
    return dedupe_items(items, threshold)
```

- Text extraction for similarity: `text + author_name` (mirrors YouTube's `title + channel_name`)
- Add `tiktok` to `cross_source_link()` — compare TikTok items with all other sources
- Cross-ref prefix: `"TK"` (e.g., `TK3` for TikTok item 3)

### Phase 6: Rendering

**`scripts/lib/render.py` — add TikTok section:**

```markdown
### TikTok Videos

**TK1** (score:87) @creator_name (2026-02-28) [2.1M views, 45K likes]
  Caption: "This Claude Code trick saved me hours... #claudecode #ai"
  https://www.tiktok.com/@creator/video/1234567890
  Spoken: "So I found this insane trick with Claude Code where you can..."
  *TikTok: This Claude Code trick saved me hours*
```

**Stats line for SKILL.md:**
```
├─ 🎵 TikTok: {N} videos │ {N} views │ {N} with captions
```

### Phase 7: Environment + Config

**`scripts/lib/env.py` — add Apify support:**

```python
def is_apify_available(config: Dict[str, Any]) -> bool:
    """Check if Apify token is configured for TikTok/social scraping."""
    return bool(config.get('APIFY_API_TOKEN'))
```

- New env var: `APIFY_API_TOKEN`
- Add to `get_config()` key list
- Add to `get_available_sources()` / `get_missing_keys()` logic
- Single token covers TikTok + future Facebook + Instagram

**User setup:**
```bash
# Add to ~/.config/last30days/.env
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxx
```

Or get free token: Sign up at https://console.apify.com → Settings → Integrations → Personal API Token.

### Phase 8: Orchestrator Integration

**`scripts/last30days.py` changes:**

1. Add `"tiktok"` to `VALID_SEARCH_SOURCES` set (line 47)
2. Add `tiktok_future` var + timeout to `TIMEOUT_PROFILES`:
   ```python
   "tiktok_future": 120  # Apify actors can be slow on first run
   ```
3. Add `do_tiktok` bool + `run_tiktok` parameter to `run_research()`
4. Submit `_search_tiktok()` to ThreadPoolExecutor (now max 7+1 workers)
5. Collect TikTok results with timeout
6. Add tiktok to return tuple + progress display
7. Wire tiktok into normalize → score → dedupe → cross-link → render pipeline in main

### Phase 9: SKILL.md Updates

1. Add TikTok to stats box template
2. Add TikTok citation rule: `@creator on TikTok`
3. Add TikTok to source weight guidance (rank between YouTube and HN)
4. Document `APIFY_API_TOKEN` in setup section

### Phase 10: Dependency

```bash
pip install apify-client
```

- `apify-client` is the only new dependency
- Requires Python 3.10+ (already required by the project)
- No new binary dependencies (unlike yt-dlp for YouTube)

## Files to Create / Modify

### New Files
| File | Purpose |
|---|---|
| `scripts/lib/apify_client_wrapper.py` | Shared Apify client init + `run_actor_sync()` helper |
| `scripts/lib/tiktok.py` | TikTok search, caption extraction, relevance scoring |
| `tests/test_tiktok.py` | Unit tests for TikTok module |
| `fixtures/tiktok_search.json` | Mock Apify response for testing |

### Modified Files
| File | Changes |
|---|---|
| `scripts/lib/schema.py` | Add `TikTokItem` dataclass, `shares` to Engagement, `tiktok`/`tiktok_error` to Report |
| `scripts/lib/normalize.py` | Add `normalize_tiktok_items()` |
| `scripts/lib/score.py` | Add `compute_tiktok_engagement_raw()`, `score_tiktok_items()` |
| `scripts/lib/dedupe.py` | Add `dedupe_tiktok()`, add tiktok to `cross_source_link()` |
| `scripts/lib/render.py` | Add TikTok rendering section, stats line |
| `scripts/lib/env.py` | Add `APIFY_API_TOKEN` handling, `is_apify_available()` |
| `scripts/last30days.py` | Add tiktok to orchestrator pipeline, `VALID_SEARCH_SOURCES`, `TIMEOUT_PROFILES` |
| `SKILL.md` | Add TikTok stats line, citation rules, source weights |
| `README.md` | Add TikTok to source list, Apify setup instructions |

## Future: Facebook + Instagram via Apify

The `apify_client_wrapper.py` module is designed to be reused. Adding Facebook would look like:

```python
# scripts/lib/facebook.py
from . import apify_client_wrapper

ACTOR_ID = "apify/facebook-posts-scraper"  # or "scraper_one/facebook-posts-search"

def search_facebook(topic, from_date, to_date, depth="default", token=None):
    client = apify_client_wrapper.get_apify_client(token)
    run_input = {
        "searchType": "posts",
        "searchTerms": [topic],
        "maxPosts": DEPTH_CONFIG[depth]["max_posts"],
    }
    items = apify_client_wrapper.run_actor_sync(client, ACTOR_ID, run_input)
    # Parse: text, likes, comments, shares, time, user.name, url
    ...
```

**Facebook fields available:** `text`, `likes`, `comments`, `shares`, `time`/`timestamp`, `user.name`, `url`, `reactions_count`

**Instagram** would follow the same pattern with `apify/instagram-scraper` or similar.

Same `APIFY_API_TOKEN` — no additional keys needed.

## Cost Analysis

**Per research run (default depth, 20 results):**
- Clockworks TikTok scraper: ~$0.10 per 20 results ($5/1000)
- Free tier: ~50 research runs per month on $5 free credits
- With captions (re-run for top 5): ~$0.15 total per run → ~33 runs/month free

**Comparison:** YouTube costs $0 (yt-dlp is free). TikTok costs ~$0.10-0.15/run. This is acceptable given the signal value and tracks with the BYO key model.

## Acceptance Criteria

- [ ] `APIFY_API_TOKEN` in `.env` enables TikTok source automatically
- [ ] TikTok appears in parallel search alongside other 6 sources
- [ ] Results include: video URL, caption, author, views, likes, comments, date
- [ ] Caption enrichment works for top N videos (configurable by depth)
- [ ] Relevance scoring filters off-topic viral videos
- [ ] Cross-source linking detects when TikTok + Reddit/YouTube discuss same topic
- [ ] Stats box shows: `🎵 TikTok: N videos │ N views │ N with captions`
- [ ] `--search=tiktok` flag works for TikTok-only research
- [ ] Graceful degradation: if no APIFY_API_TOKEN, TikTok silently skipped
- [ ] Mock mode works with `fixtures/tiktok_search.json`
- [ ] Tests pass for search, normalize, score, dedupe, render
- [ ] `apify_client_wrapper.py` is generic enough for Facebook/Instagram reuse
