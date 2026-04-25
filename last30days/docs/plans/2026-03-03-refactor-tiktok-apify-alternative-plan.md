# refactor: Replace Apify with pay-as-you-go TikTok API

**Type:** refactor
**Date:** 2026-03-03
**Status:** Draft

## Problem

Apify requires a monthly subscription even for low-volume usage. We need a true pay-as-you-go TikTok data API that returns structured video data (views, likes, comments, shares, author, hashtags, captions) from keyword search.

## Current Architecture

Our TikTok integration makes **exactly 2 API calls per /last30days invocation**:

1. **Search call** — keyword search, returns 10-40 videos with engagement metrics
2. **Caption enrichment call** — fetches spoken-word subtitles for top 3-8 videos

We consume these fields from the response:
- `id`, `text` (description), `webVideoUrl`, `authorMeta.name`
- `playCount`, `diggCount`, `commentCount`, `shareCount`
- `hashtags[].name`, `videoMeta.duration`
- `createTimeISO` or `createTime` (date)
- `subtitleText` / `subtitles` (captions, secondary call)

Files involved:
- `scripts/lib/tiktok.py` — search, parse, relevance scoring, caption fetching
- `scripts/lib/apify_client_wrapper.py` — shared Apify client (also designed for future FB/IG)
- `scripts/lib/schema.py` — `TikTokItem` dataclass
- `scripts/lib/normalize.py` — `normalize_tiktok()`
- `scripts/last30days.py` — orchestrator (calls `tiktok.search_and_enrich()`)

## Why Most of Those Alternatives Won't Work

The services in the user's table (Spider, Zyte, Scrappey, Serper.dev) are **general web scrapers** — they return raw HTML, not structured TikTok data. We'd have to build our own HTML parser, handle anti-bot protections, and reverse-engineer TikTok's response format. That's a completely different (and fragile) approach.

What we need is a **TikTok-specific API** that returns structured JSON with engagement metrics from keyword search.

## Alternatives Evaluated

### RECOMMENDED: ScrapeCreators — Best True Pay-As-You-Go

| Attribute | Details |
|-----------|---------|
| **TikTok structured data** | Yes — 19 dedicated endpoints including keyword search |
| **Pricing model** | True PAYG — buy credits, credits never expire |
| **Cost at our volume** | ~$0.60/month ($10 buys 5,000 credits, lasts 16-33 months) |
| **Free tier** | 100-10,000 free credits on signup (no credit card) |
| **Python SDK** | No dedicated SDK — simple REST API (`requests.get()`) |
| **Search endpoint** | "Search by Keyword" and "Top Search" |
| **Risk** | Newer service, limited track record |

**Why it's the best fit:** $10 literally lasts over a year at our volume. No subscription, no expiring credits. The lack of a Python SDK is irrelevant — it's a single `requests.get()` call.

### Runner-up: EnsembleData — Best SDK, But Subscription

| Attribute | Details |
|-----------|---------|
| **TikTok structured data** | Full — 15+ endpoints, all engagement metrics |
| **Pricing model** | Monthly subscription ($100/mo after 7-day trial) |
| **Cost at our volume** | $0 during trial (50 units/day), $100/mo after |
| **Free tier** | 50 units/day for 7 days, no CC required |
| **Python SDK** | Yes — `pip install ensembledata` |
| **Search endpoint** | "Keyword Search" returns ~20 posts/call (1 unit) |
| **Risk** | $100/mo is overkill for 5-10 searches/day |

**Verdict:** Best data quality and SDK, but $100/mo is absurd for our ~150-300 requests/month. Same subscription problem as Apify.

### Backup: tikwm.com — Free but Risky

| Attribute | Details |
|-----------|---------|
| **TikTok structured data** | Likely yes (needs live testing) |
| **Pricing model** | Completely free, no API key required |
| **Cost at our volume** | $0 |
| **Free tier** | 5,000 requests/day |
| **Python SDK** | Community wrappers (damirTAG/TikTok-Module, kittenbark/tikwm) |
| **Search endpoint** | `https://www.tikwm.com/api/feed/search?keywords=TERM&count=20` |
| **Risk** | Unaffiliated third-party, could disappear anytime, no SLA |

**Verdict:** Great for development/testing. Too risky as sole production backend. Could be a zero-cost fallback.

### Not Recommended

| Service | Why Not |
|---------|---------|
| **TikAPI** | $50-189/mo subscription — same problem as Apify |
| **Bright Data** | $499/mo minimum — enterprise pricing |
| **davidteather/TikTok-Api** | Video search is broken, requires Playwright, fragile |
| **Spider, Zyte, Scrappey** | Generic scrapers — return raw HTML, no TikTok structure |
| **Piloterr** | No TikTok endpoints, subscription only |

## Recommended Approach

### Option A: ScrapeCreators as primary (Recommended)

- [ ] Sign up for ScrapeCreators, get free credits
- [ ] Test the "Search by Keyword" endpoint to verify it returns all required fields
- [ ] Refactor `tiktok.py` to use ScrapeCreators REST API instead of Apify actor
- [ ] Keep `apify_client_wrapper.py` for future FB/IG (or refactor to generic wrapper)
- [ ] Update `.env` config: `SCRAPECREATORS_API_KEY` replaces `APIFY_API_TOKEN` for TikTok
- [ ] Update README, SKILL.md installation instructions
- [ ] Buy $10 credits after confirming it works

### Option B: tikwm.com as primary (Zero cost, higher risk)

- [ ] Test tikwm.com search endpoint to verify response schema
- [ ] If it returns engagement metrics, implement as primary backend
- [ ] Add ScrapeCreators as paid fallback when tikwm fails
- [ ] No API key required — simplest user setup

### Option C: Keep Apify, document the subscription requirement

- [ ] Update README to clarify Apify requires a paid plan
- [ ] Add note about the free $5/mo credits tier (if it still works without subscription)
- [ ] Ship as-is with clear billing expectations

## Implementation Plan (Option A)

### Phase 1: Validate ScrapeCreators API

- [ ] Sign up and get API key
- [ ] Test keyword search endpoint: `GET /tiktok/search?keyword={topic}&count=20`
- [ ] Verify response contains: video ID, play count, likes, comments, shares, author, hashtags, date, description
- [ ] Test caption/subtitle availability (or confirm description text is sufficient)

### Phase 2: Swap the Backend

- [ ] Create `scripts/lib/scrapecreators_client.py` (simple REST wrapper, ~40 lines)
- [ ] Refactor `tiktok.py:search_tiktok()` to call ScrapeCreators instead of Apify
- [ ] Map ScrapeCreators response fields to our existing item dict format
- [ ] Refactor `tiktok.py:fetch_captions()` — check if ScrapeCreators provides subtitles, else use description text only
- [ ] Update `env.py` to read `SCRAPECREATORS_API_KEY` (keep `APIFY_API_TOKEN` for backward compat)
- [ ] Update `scripts/lib/ui.py` spinner messages if needed

### Phase 3: Update Docs & Ship

- [ ] Update README.md installation section (new API key)
- [ ] Update SKILL.md
- [ ] Update `~/.config/last30days/.env` locally
- [ ] Run full test suite
- [ ] Commit and push

## Acceptance Criteria

- [ ] TikTok search returns structured data with views, likes, comments, shares
- [ ] No subscription required — pay-as-you-go only
- [ ] Cost < $1/month at normal usage (5-10 searches/day)
- [ ] Existing test suite passes with new backend
- [ ] Graceful degradation when API key is missing (same behavior as today)

## Open Questions

1. Does ScrapeCreators' keyword search support date filtering, or do we filter post-API like we do with Apify?
2. Does ScrapeCreators return subtitle/caption data, or just video descriptions?
3. What's the response time? Apify actors took 30-120 seconds. REST APIs should be faster.
4. Should we keep Apify as a fallback backend (user configures one or the other)?
