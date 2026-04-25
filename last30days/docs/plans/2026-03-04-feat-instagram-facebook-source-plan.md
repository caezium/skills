# feat: Add Instagram and Facebook Sources via ScrapeCreators API

**Date:** 2026-03-04
**Type:** Enhancement
**Priority:** Instagram first, Facebook conditional ("if it's good")

## Summary

Add Instagram Reels and Facebook as new research sources in last30days, using the same ScrapeCreators REST API already powering TikTok. Instagram is the primary target; Facebook is a follow-on if the pattern works well.

Both sources share the existing `SCRAPECREATORS_API_KEY` — no new API keys needed.

## Approach

Replicate the TikTok integration pattern exactly. Each source follows the same 8-step pipeline:

```
tiktok.py pattern → instagram.py (new) → facebook.py (new, conditional)
```

## ScrapeCreators API Endpoints

### Instagram

| Endpoint | Path | Params | Credits | Notes |
|----------|------|--------|---------|-------|
| **Search Reels** | `GET /v1/instagram/reels/search` | `keyword`, pagination | 1 per 10 reels, max 60/req | Keyword search via Google (IG search requires login). V2 also available. |
| **Transcript** | `GET /v2/instagram/media/transcript` | `url` | 1 | Returns `{transcripts: [{id, shortcode, text}]}`. Videos <2min only. |
| **Comments** | `GET /v2/instagram/post/comments` | `url`, `cursor` | 1 | Returns `{comments: [{id, text, created_at, user}]}`. 100-300 per call. |
| **User Reels** | `GET /v1/instagram/user/reels` | `handle` or `user_id`, `max_id`, `trim` | 1 | All reels from a profile. Response: `{items: [...], paging_info}` |

**Primary search strategy:** `/v1/instagram/reels/search` with keyword param for topic search. This is the analog to TikTok's `/search/keyword`.

**Response fields per reel item:**
- `pk` / `code` (shortcode) — reel ID
- `taken_at` — unix timestamp
- `play_count` / `ig_play_count` — views
- `like_count` — likes
- `comment_count` — comments
- `video_duration` — seconds
- `has_audio` — boolean
- `user` object — username, full_name, is_verified, profile_pic_url
- `caption` object — text content
- Media URLs for thumbnails and video versions

### Facebook

| Endpoint | Path | Params | Credits | Notes |
|----------|------|--------|---------|-------|
| **Profile Posts** | `GET /v1/facebook/profile/posts` | `url` or `pageId`, `cursor` | 1 | Returns 3 posts at a time with engagement |
| **Profile Reels** | `GET /v1/facebook/profile/reels` | similar | 1 | 10 reels at a time |
| **Post** | `GET /v1/facebook/post` | `url` | 1 | Single post/reel by URL |
| **Transcript** | `GET /v1/facebook/post/transcript` | `url` | 1 | Video transcript, <2min |
| **Comments** | `GET /v1/facebook/post/comments` | `url`, `feedback_id` | 1 | Post/reel comments |

**Facebook limitation:** No keyword search endpoint. Only profile-based scraping (3 posts at a time). This makes Facebook significantly less useful for topic-based research vs. Instagram's keyword search.

**Response fields per post:**
- `id` — post ID
- `text` — post content
- `url` / `permalink` — post URL
- `author` — `{name, short_name, id}`
- `reactionCount` — total reactions
- `commentCount` — comments
- `videoViewCount` — video views (if applicable)
- `publishTime` — unix timestamp
- `topComments` — array of `{id, text, publishTime, author}`

## Implementation Plan

### Phase 1: Instagram Source (Primary)

#### 1.1 Create `scripts/lib/instagram.py`
- [x] Copy structure from `scripts/lib/tiktok.py`
- [x] Change `SCRAPECREATORS_BASE` to `"https://api.scrapecreators.com"`
- [x] Implement `search_instagram()` → calls `/v1/instagram/reels/search`
  - Params: `keyword=core_topic`
  - Parse response `items` array
  - Extract: `pk`/`code` as video_id, `taken_at` as date, `play_count`/`like_count`/`comment_count` as engagement, `user.username` as author, `caption.text` as text
  - Build URL: `https://www.instagram.com/reel/{code}`
  - Reuse `_extract_core_subject()`, `_compute_relevance()`, `_tokenize()` from tiktok.py (or factor into shared util)
  - Apply date range filter, sort by views descending
- [x] Implement `fetch_captions()` → calls `/v2/instagram/media/transcript`
  - For top N items (per depth config), fetch transcript
  - Response: `{transcripts: [{id, shortcode, text}]}`
  - Fallback to caption text if transcript unavailable
  - Truncate to 500 words
- [x] Implement `search_and_enrich()` → combines search + captions
- [x] Implement `parse_instagram_response()` → returns `response.get("items", [])`
- [x] Reuse shared helpers: `_sc_headers()`, `_log()`, `_clean_webvtt()`, `DEPTH_CONFIG`, `STOPWORDS`, `SYNONYMS`

**Key difference from TikTok:** Instagram response uses `play_count`/`like_count`/`comment_count` directly (no `statistics` wrapper), `user.username` (not `author.unique_id`), `caption.text` (not `desc`), `taken_at` (not `create_time`), `code` shortcode for URL construction.

#### 1.2 Add `InstagramItem` to `scripts/lib/schema.py`
- [x] Add dataclass mirroring `TikTokItem` structure:
  ```python
  @dataclass
  class InstagramItem:
      id: str              # "IG1", "IG2", ...
      text: str            # caption text
      url: str             # https://www.instagram.com/reel/{code}
      author_name: str     # Instagram handle
      date: Optional[str]  # YYYY-MM-DD from taken_at
      date_confidence: str # "high"
      engagement: Optional[Engagement]  # views, likes, num_comments
      caption_snippet: str  # transcript or caption text
      hashtags: List[str]   # extracted from caption
      relevance: float
      why_relevant: str
      subs: SubScores
      score: int
      cross_refs: List[str]
  ```

#### 1.3 Add normalization to `scripts/lib/normalize.py`
- [x] Add `normalize_instagram_items()` function
  - Assign IDs as `IG1`, `IG2`, ...
  - Map engagement: `views=play_count`, `likes=like_count`, `num_comments=comment_count`
  - Set `date_confidence="high"` (unix timestamp)

#### 1.4 Add scoring to `scripts/lib/score.py`
- [x] Add `compute_instagram_engagement_raw()` — same formula as TikTok:
  `0.50*log1p(views) + 0.30*log1p(likes) + 0.20*log1p(comments)`
  Views dominate on Instagram Reels just like TikTok.
- [x] Add `score_instagram_items()` — same weights: 45% relevance, 25% recency, 30% engagement

#### 1.5 Add dedup to `scripts/lib/dedupe.py`
- [x] Add `dedupe_instagram()` — same as `dedupe_tiktok()`, calls `dedupe_items()` with 0.7 threshold
- [x] Update `get_item_text()` to handle `InstagramItem`
- [x] Update `_get_cross_source_text()` for cross-source linking
- [x] Add `IG` prefix to cross-ref detection in `cross_source_link()`

#### 1.6 Add rendering to `scripts/lib/render.py`
- [x] Add Instagram section in `render_compact()` — same pattern as TikTok block (lines 251-285)
  - Show: score, @author, date, views/likes, caption snippet, hashtags, why_relevant
- [x] Update data freshness check to include `instagram_recent`
- [x] Update stats footer to include Instagram count
- [x] Add `'IG'` to cross-ref source name mapping

#### 1.7 Add `Report.instagram` field to `scripts/lib/schema.py`
- [x] Add `instagram: List[InstagramItem]` and `instagram_error: str` to `Report` dataclass

#### 1.8 Integrate into `scripts/last30days.py` orchestrator
- [x] Add `"instagram"` to `VALID_SEARCH_SOURCES`
- [x] Add `import` for `instagram` module in `scripts/lib/`
- [x] Add `is_instagram_available()` check in `env.py` — reuse `SCRAPECREATORS_API_KEY` (same key as TikTok)
- [x] Add `get_instagram_token()` in `env.py` — same as `get_tiktok_token()`, returns `SCRAPECREATORS_API_KEY`
- [x] Add `_search_instagram()` helper in orchestrator (mirrors `_search_tiktok()`)
- [x] Add Instagram to the thread pool executor block
- [x] Add Instagram timeout config (same as TikTok: 90/120/150s for quick/default/deep)
- [x] Wire through pipeline: normalize → filter → score → sort → dedupe → cross-link → report
- [x] Add Instagram to `progress.show_complete()` and UI spinner

#### 1.9 Add to watchlist extraction in `scripts/watchlist.py`
- [x] Add Instagram findings loop in `_run_topic()` (mirrors TikTok block at lines 204-213)

#### 1.10 Update README.md
- [x] Add Instagram to the sources list
- [x] Note that `SCRAPECREATORS_API_KEY` covers both TikTok and Instagram

### Phase 2: Facebook Source (Conditional)

**Recommendation: SKIP Facebook for now.** Here's why:

1. **No keyword search endpoint** — Facebook only offers profile-based scraping (`/profile/posts` returns 3 posts at a time). Can't search by topic.
2. **Low relevance for topic research** — Without keyword search, we'd need to know specific Facebook pages to scrape, which defeats the purpose of automated topic discovery.
3. **Poor ROI** — 3 posts per API call is very limited compared to Instagram's 60 reels per search.
4. **Same API key** — If Facebook search is added later, it's trivial to add since it shares `SCRAPECREATORS_API_KEY`.

If the user still wants Facebook, the implementation would follow the same pattern but would need a different discovery strategy (e.g., hardcoded page list per topic, or using the Ad Library search for commercial topics).

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `scripts/lib/instagram.py` | **CREATE** | Instagram search + transcript via ScrapeCreators |
| `scripts/lib/schema.py` | MODIFY | Add `InstagramItem` dataclass, add `instagram` to `Report` |
| `scripts/lib/normalize.py` | MODIFY | Add `normalize_instagram_items()` |
| `scripts/lib/score.py` | MODIFY | Add `compute_instagram_engagement_raw()`, `score_instagram_items()` |
| `scripts/lib/dedupe.py` | MODIFY | Add `dedupe_instagram()`, update text extractors |
| `scripts/lib/render.py` | MODIFY | Add Instagram render section, update stats |
| `scripts/lib/env.py` | MODIFY | Add `is_instagram_available()`, `get_instagram_token()` |
| `scripts/last30days.py` | MODIFY | Add Instagram to orchestrator pipeline |
| `scripts/watchlist.py` | MODIFY | Add Instagram findings extraction |
| `README.md` | MODIFY | Add Instagram to sources list |

## Shared Code Opportunity

`_extract_core_subject()`, `_compute_relevance()`, `_tokenize()`, `STOPWORDS`, `SYNONYMS`, and `DEPTH_CONFIG` are duplicated between `tiktok.py` and the new `instagram.py`. Two options:

1. **Copy-paste** (simpler, matches current pattern) — each source module is self-contained
2. **Extract to shared module** (cleaner) — move to `scripts/lib/search_utils.py`

**Recommendation:** Copy-paste for now to match existing pattern. Refactor later if a third ScrapeCreators source is added.

## Testing Strategy

- [x] Run `python3 scripts/lib/instagram.py` with test keyword (if standalone test added)
- [x] Run `python3 scripts/last30days.py "instagram reels trends" --search=instagram` to test isolated
- [x] Run full multi-source: `python3 scripts/last30days.py "AI tools" --search=reddit,instagram`
- [x] Verify JSON output: `--emit=json` includes `instagram` key
- [x] Verify watchlist extraction works with Instagram findings
- [x] Check credit usage is reasonable (1 credit per 10 reels search + 1 per transcript)

## Credits Budget

Per research run with Instagram at `default` depth:
- Search: 1 credit (per 10 reels, returns up to 20) ≈ 2 credits
- Transcripts: 5 credits (max_captions=5 at default depth)
- **Total: ~7 credits per topic** (vs TikTok ~6 credits)
