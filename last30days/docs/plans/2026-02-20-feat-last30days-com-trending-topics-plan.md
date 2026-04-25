---
title: "feat: Last30Days.com - Automated Trending Topic Research"
type: feat
date: 2026-02-20
---

# Last30Days.com - Automated Trending Topic Research

## Overview

A website at Last30Days.com that automatically shows daily trending topics researched by the /last30days engine. The core challenge: the skill is query-driven (you give it a topic), but a trending page needs to *discover* what topics to research. This plan covers how to source trending topics, run them through the engine, and publish results.

## Problem Statement

The /last30days skill has 2,747 GitHub stars but no public-facing showcase. Users have to install the skill and run it themselves. A website that automatically shows trending topic results would:

1. **Drive installs** - people see the quality and want it for their own topics
2. **SEO surface area** - each topic page is indexable content
3. **Demonstrate capability** - "here's what /last30days found about X today" with real stats
4. **Content flywheel** - daily fresh content with zero manual curation

## Trending Topic Discovery: The Options

The skill has **no existing trending discovery mechanism** - it's entirely query-driven. Here are the available sources, ranked by practicality.

### Tier 1: Free, High Signal, Zero Friction

| Source | What It Returns | Auth | Cost | Best For |
|--------|----------------|------|------|----------|
| **Wikipedia Pageviews** | Top 100 most-viewed articles yesterday | None | Free | General public interest (news, culture, events) |
| **Hacker News** | Top 30 stories with scores | None | Free | Tech/startup topics |
| **Reddit r/all/hot + rising** | Hottest and rapidly rising posts | OAuth (free) | Free | Broad internet culture |
| **Google News RSS** | Top headlines, algorithmically curated | None | Free | Mainstream news |
| **YouTube mostPopular** | Top 50 trending videos by region | API key | Free (10K units/day) | Pop culture, entertainment |

### Tier 2: Very Cheap, High Value

| Source | What It Returns | Auth | Cost | Best For |
|--------|----------------|------|------|----------|
| **Perplexity Sonar API** | "What's trending today?" with sourced answers | API key | ~$1/month | Meta-aggregator that replaces multiple sources |
| **Google Trends (pytrends)** | Daily trending Google searches | None | Free but flaky | What people are actually searching |
| **Bird `getNews()`** | X Explore page trending topics | Browser cookies | Free | Real-time Twitter/X conversation |

### Tier 3: Paid, Skip for MVP

| Source | Cost | Why Skip |
|--------|------|----------|
| X/Twitter API | $200/month minimum | Too expensive; Bird `getNews()` is free |
| Exploding Topics | $249/month | Overkill for daily trends |
| TikTok | Gated, requires approval | Application process |

### Existing Codebase Hooks

Several pieces already exist in the codebase that could be leveraged:

1. **Bird `getNews()` is already on disk.** The vendored Bird library at `scripts/lib/vendor/bird-search/` includes `twitter-client-news.js` which fetches X's Explore page tabs (For You, Trending, News, Sports, Entertainment). Only needs a ~30-line `bird-news.mjs` wrapper to expose it. Zero API keys needed.

2. **`store.get_trending(days=7)`** at `scripts/store.py:559` ranks watchlist topics by recent finding activity. Could feed "what the skill has been researching" as a meta-signal.

3. **Scoring algorithm** at `scripts/lib/score.py` has engagement formulas for Reddit, X, and YouTube that could rank "buzz" by reweighting engagement >> relevance.

4. **Brave Trending API** exists but isn't implemented in `brave_search.py`. Could be added.

## Proposed Architecture

### Topic Discovery Pipeline (daily cron)

```
┌─────────────────────────────────────────────────┐
│ STEP 1: Fetch trending signals (parallel, free) │
├─────────────────────────────────────────────────┤
│ Wikipedia Pageviews  ─┐                         │
│ Hacker News Top 30   ─┤                         │
│ Reddit r/all/hot     ─┼─→ Raw topics + signals  │
│ Google News RSS      ─┤                         │
│ YouTube mostPopular  ─┤                         │
│ Bird getNews()       ─┘                         │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ STEP 2: Cluster + rank                          │
├─────────────────────────────────────────────────┤
│ Extract topic keywords from titles              │
│ Cluster by semantic similarity                  │
│ Rank by cross-source frequency                  │
│ ("Pope Leo XIV" on Wikipedia + Reddit + News    │
│   = high confidence trend)                      │
│ Output: top 15-20 topics, ranked                │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ STEP 3: Run /last30days on top topics           │
├─────────────────────────────────────────────────┤
│ Top 3-5 topics: full research (--emit=json)     │
│   → Full "What I learned" synthesis articles    │
│ Remaining 10-15: quick research (--quick)       │
│   → Stats teasers (32 X posts, 5 YouTube...)    │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ STEP 4: Publish to website                      │
├─────────────────────────────────────────────────┤
│ Generate static HTML/JSON                       │
│ Deploy to Last30Days.com                        │
│ RSS feed for subscribers                        │
└─────────────────────────────────────────────────┘
```

### Topic Clustering Strategy

The hardest part is deduplicating across sources. "Pope Francis Dies" (Google News), "Pope_Francis" (Wikipedia #1 viewed), and a r/worldnews post are all the same topic. Approaches:

**Option A: LLM clustering (recommended for MVP)**
Feed all raw titles to an LLM and ask it to cluster into distinct topics with a representative label. ~$0.01 per day via a fast model. Simple, accurate, handles edge cases.

**Option B: TF-IDF + cosine similarity**
Extract keywords, compute pairwise similarity, agglomerative clustering. No API cost but worse on paraphrased titles.

**Option C: Embedding similarity**
Embed all titles, cluster by cosine distance. Better than TF-IDF, costs a few cents per day.

### Website Architecture

**Option A: Static site (recommended for MVP)**
- Daily cron generates JSON + static HTML
- Host on GitHub Pages, Cloudflare Pages, or Vercel
- Zero server cost, zero maintenance
- Framework: plain HTML/CSS, or minimal Astro/11ty

**Option B: Next.js with ISR**
- Incremental Static Regeneration rebuilds pages daily
- More flexibility for future features (search, filtering, user accounts)
- Hosting: Vercel free tier

**Option C: Full web app**
- Database-backed, real-time updates, user accounts
- Overkill for MVP

### Cost Estimate (daily operation)

| Item | Cost |
|------|------|
| Trending source APIs | $0 (all free tier) |
| LLM clustering (fast model) | ~$0.01/day |
| Full research on 3-5 topics | ~$0.10-0.50/day (OpenAI API for Reddit search) |
| Quick research on 10-15 topics | ~$0.05-0.20/day |
| Static hosting | $0 (GitHub/Cloudflare Pages) |
| **Total** | **~$5-20/month** |

## Implementation Phases

### Phase 1: Topic Discovery Script (MVP)

Build `scripts/discover_trending.py` that:
- Fetches Wikipedia Pageviews, HN top stories, Reddit hot, Google News RSS in parallel
- Filters out evergreen/non-topical Wikipedia pages (e.g., "Main Page", "ChatGPT" permanent traffic)
- Uses a fast LLM to cluster raw titles into 15-20 distinct topics
- Outputs ranked JSON: `[{topic, sources, confidence, category}]`

**Acceptance criteria:**
- [ ] Fetches from at least 4 free trending sources in parallel
- [ ] Clusters raw titles into deduplicated topics via LLM
- [ ] Filters Wikipedia evergreen pages (maintain a blocklist)
- [ ] Outputs ranked JSON with topic name, source count, category
- [ ] Runs in < 60 seconds
- [ ] No paid API keys required for discovery (only LLM clustering)

### Phase 2: Research Automation

Wire discovered topics into the existing /last30days engine:
- Top 3-5 topics: `python3 scripts/last30days.py "$TOPIC" --emit=json --deep`
- Remaining topics: `python3 scripts/last30days.py "$TOPIC" --emit=json --quick`
- Store all results in `~/.local/share/last30days/trending/YYYY-MM-DD/`

**Acceptance criteria:**
- [ ] Orchestration script runs discovery then research sequentially
- [ ] Full research on top N topics, quick on the rest
- [ ] Results stored as dated JSON files
- [ ] Total daily runtime < 30 minutes
- [ ] Handles timeouts/failures gracefully (skip topic, continue)

### Phase 3: Website Generation

Build a static site generator that reads the daily JSON and produces Last30Days.com:
- Homepage: today's trending topics grid (title, category, key stat, source badges)
- Topic pages: full synthesis for showcase topics, stats teaser for others
- Archive: previous days accessible by date
- RSS feed
- CTA: "Want to research your own topic? Install the skill"

**Acceptance criteria:**
- [ ] Static HTML generated from daily JSON
- [ ] Homepage shows today's 15-20 trending topics
- [ ] 3-5 showcase topic pages with full synthesis
- [ ] Remaining topics show stats teasers + install CTA
- [ ] Deploys to Last30Days.com (Cloudflare Pages or similar)
- [ ] RSS feed for daily updates
- [ ] Mobile responsive

### Phase 4: Bird Trending Integration (bonus)

Wire up the already-vendored Bird `getNews()` for X trending:
- Create `scripts/lib/vendor/bird-search/bird-news.mjs` (~30 lines)
- Add X Explore trending data as a 5th discovery source
- X trends are the fastest-moving signal and fill the "what's happening right now" gap

**Acceptance criteria:**
- [ ] `bird-news.mjs` wrapper exposes X Explore trending topics
- [ ] Integrated into discovery pipeline as an additional source
- [ ] Falls back gracefully if no X session cookies available

## Alternative Approaches Considered

### Perplexity-only approach
Just ask Perplexity Sonar "what are the top 20 trending topics today?" daily. Simpler, but:
- Single point of failure
- Less transparent (can't show "sourced from Reddit, Wikipedia, HN")
- Model may hallucinate or miss niche topics
- **Verdict:** Good fallback, not primary.

### Curated topics (manual)
Manually pick topics each day. Defeats the purpose of automation. Could supplement for "editorial picks."

### Social listening tools (Brandwatch, Sprout Social, etc.)
Expensive ($500+/month), enterprise-focused, overkill.

## Technical Considerations

- **Rate limits:** Wikipedia, HN, and RSS have no practical limits for 1 daily call. Reddit's 100 QPM is generous. YouTube's 10K units/day allows ~3,000 `mostPopular` calls.
- **Wikipedia filtering:** The top Wikipedia pages are always "Main Page", "Special:Search", etc. Need a blocklist of ~50 evergreen pages plus heuristics (skip pages under 1,000 characters, skip disambiguation pages).
- **Cron timing:** Run discovery at ~2am UTC (after Wikipedia pageviews finalize for previous day). Run research at ~3am UTC. Deploy site by ~5am UTC.
- **Cost control:** The /last30days engine uses OpenAI API for Reddit search. Full research on 5 topics * $0.05-0.10 each = ~$0.25-0.50/day. Quick research is cheaper.
- **Domain:** Last30Days.com needs to be registered (check availability).

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| pytrends breaks (Google changes) | pytrends is a bonus source, not required. Other 4+ sources sufficient. |
| Wikipedia pageviews delayed | Fall back to Perplexity Sonar for day's topics |
| OpenAI API cost spikes | Cap at 5 full + 15 quick topics per day; use --quick for most |
| Bird cookie auth stops working | X trending is a bonus source; discovery works without it |
| Domain not available | Check availability; alternatives: last30.day, last30days.app |

## Success Metrics

- Daily automated publishing with zero manual intervention
- 15-20 trending topics surfaced daily
- 3-5 full synthesis articles per day
- Site loads in < 2 seconds (static)
- Drives measurable GitHub star growth / skill installs

## References

### Trending APIs (free)
- Wikipedia Pageviews: `wikimedia.org/api/rest_v1/metrics/pageviews/top/{project}/{access}/{year}/{month}/{day}`
- Hacker News: `hacker-news.firebaseio.com/v0/topstories.json`
- Reddit: `oauth.reddit.com/r/all/hot` (or `reddit.com/r/all/hot.json` unauthenticated)
- Google News RSS: `news.google.com/rss`
- YouTube: `googleapis.com/youtube/v3/videos?chart=mostPopular`

### Existing codebase hooks
- Bird `getNews()`: `scripts/lib/vendor/bird-search/vendor/package/dist/lib/twitter-client-news.js`
- Store trending: `scripts/store.py:559` (`get_trending()`)
- Scoring: `scripts/lib/score.py` (engagement formulas)
- Brave Trending API: not implemented, available in Brave docs

### Inspiration
- [Keep a Changelog](https://keepachangelog.com/) - clean daily update format
- [Hacker News front page](https://news.ycombinator.com/) - minimal trending UI
- [Exploding Topics](https://explodingtopics.com/) - trending topic showcase (paid, $249/mo)
