# feat: Reddit ScrapeCreators v2 — Improvements from Beta Testing

**Date:** 2026-03-05
**Type:** Enhancement
**Version:** v2.9 → v2.9.1-beta (or v3.0-beta if shipping to public)
**Branch:** `feat/reddit-scrapecreators` (continue existing branch)

---

## Summary

Three focused improvements to the Reddit ScrapeCreators integration based on 5 full-pipeline tests ("Claude Code skills", "Kanye West", "Anthropic odds", "best rap songs lately", "Nano Banana Pro prompting"):

1. **Elevate top Reddit comments** — give weight to the wittiest/highest-voted comment in scoring and rendering
2. **Improve subreddit discovery** — tune heuristic so ambiguous queries find discussion subs, not utility subs
3. **Make ScrapeCreators the default recommended Reddit method** — update onboarding, SKILL.md metadata, and env.py messaging

---

## Problem Statement

### 1. Comments are undervalued
- ScrapeCreators returns real comment data with scores, but top comments only appear as `Insights:` text under each Reddit item
- The top comment (often the funniest/cleverest reply) gets no special treatment — it's just one of 3 comment excerpts
- Reddit's value IS the comments — upvoted replies are the distilled crowd wisdom
- Currently `comment_insights` are truncated at 150 chars and only 3 are shown per item in compact output
- No scoring bonus for posts that have high-quality comment threads

### 2. Subreddit discovery picks wrong subs for ambiguous queries
- "best rap songs lately" discovered `r/NameThatSong` and `r/findthatsong` (utility subs for identifying songs) instead of discussion subs like `r/hiphopheads` or `r/rap`
- "Kanye West" picked `r/ConcertsIndia_` as second sub — tangential at best
- The current heuristic is pure frequency count on `subreddit` field from global results, with no relevance weighting
- Utility/meta subs often dominate because the same query matches many "help me find X" posts

### 3. Onboarding still suggests OpenAI as the primary Reddit method
- SKILL.md metadata says `primaryEnv: OPENAI_API_KEY` and `requires.env: [OPENAI_API_KEY]`
- The web-only mode banner mentions "OPENAI_API_KEY or codex login → Reddit threads"
- `env.py` error messages direct users to OpenAI for Reddit access
- ScrapeCreators is cheaper ($0.012 vs $0.03-0.10), faster (17s vs 60-90s), returns real data, and shares a key with TikTok + Instagram
- New users should be told: "Get a SCRAPECREATORS_API_KEY for Reddit + TikTok + Instagram (one key, all three)"

---

## Implementation Plan

### Task 1: Elevate Top Comments in Scoring and Rendering

**Goal:** Give Reddit posts a scoring bonus when they have highly-engaged comment threads, and render the #1 comment with special treatment.

**Files to modify:**
- `scripts/lib/reddit.py` — enrich with `top_comment_score` metadata
- `scripts/lib/score.py` — add comment quality bonus to Reddit scoring
- `scripts/lib/render.py` — render top comment with special formatting
- `scripts/lib/schema.py` — add `top_comment_excerpt` field to RedditItem (optional, may just use existing `top_comments[0]`)

#### 1a. Comment enrichment improvements (`scripts/lib/reddit.py`)

- [x] In `enrich_with_comments()`, after sorting comments by score, tag the item with:
  - `top_comment_excerpt`: The highest-scored comment's body (up to 200 chars)
  - `top_comment_score`: The upvote count of the #1 comment
  - `top_comment_author`: Author of the #1 comment
- [x] Increase comment excerpt length from 300 → 400 chars for top comment only (funny/clever comments need more room)
- [x] Increase `comment_insights` limit from 7 → 10 (we have the data, show it)
- [x] For posts with enriched comments, store the comment count ratio: `top_comment_score / post_score` — a high ratio means the comment outshines the post (Reddit gold)

#### 1b. Scoring bonus for comment quality (`scripts/lib/score.py`)

- [x] In `compute_reddit_engagement_raw()`, add a comment quality signal:
  - Current formula: `0.55*log1p(score) + 0.40*log1p(num_comments) + 0.05*(upvote_ratio*10)`
  - New formula: `0.50*log1p(score) + 0.35*log1p(num_comments) + 0.05*(upvote_ratio*10) + 0.10*log1p(top_comment_score)`
  - This gives a ~10% weight to comment quality, slightly reducing post score and comment count weights
  - Posts where the community engaged deeply (high top-comment score) rank higher
- [x] Need to pass `top_comment_score` through the engagement data — either:
  - Option A: Add `top_comment_score` to `schema.Engagement` (cleanest)
  - Option B: Read from `item.top_comments[0].score` during scoring (no schema change)
  - **Recommend Option B** to avoid schema bloat — scoring can peek at `top_comments`

#### 1c. Render top comment prominently (`scripts/lib/render.py`)

- [x] In `render_compact()` Reddit section, after the `Insights:` block, add a "Top Comment:" line for items that have top_comments:
  ```
  **R1** (score:80) r/ClaudeAI (2026-02-28) [666pts, 63cmt]
    Claude Code creator: In the next version, introducing two new skills
    https://www.reddit.com/r/ClaudeAI/comments/...
    *Reddit global search*
    💬 Top comment (247 upvotes): "So are they /batch migrating to Rust? :)"
    Insights:
      - TL;DR generated automatically after 50 comments...
      - He's /batch migrating code daily?..
  ```
- [x] Only show `💬 Top comment` for items where `top_comments[0].score >= 10` (skip low-engagement comments)
- [x] Truncate at 200 chars with `...` if needed
- [x] Also update `render_full_report()` to include the top comment prominently

#### 1d. Update SKILL.md synthesis instructions

- [x] In the "Judge Agent: Synthesize All Sources" section, add guidance:
  ```
  5b. For Reddit: Pay special attention to top comments — they often contain the wittiest, most insightful, or funniest take. When a top comment has high upvotes, quote it directly in your synthesis. Reddit's value is in the comments.
  ```
- [x] In the citation priority list, add: "When citing Reddit, prefer quoting top comments over just the thread title"

---

### Task 2: Improve Subreddit Discovery Heuristic

**Goal:** Find topical discussion subs rather than utility/meta subs.

**Files to modify:**
- `scripts/lib/reddit.py` — improve `discover_subreddits()` logic

#### 2a. Add relevance-weighted subreddit scoring

- [x] Replace pure frequency count with a weighted score:
  ```python
  def discover_subreddits(results, topic, max_subs=5):
      core = _extract_core_subject(topic)
      core_words = set(core.lower().split())

      scores = Counter()
      for post in results:
          sub = post.get("subreddit", "")
          if not sub:
              continue

          # Base: frequency count
          base = 1.0

          # Bonus: subreddit name contains a core topic word
          sub_lower = sub.lower()
          if any(w in sub_lower for w in core_words if len(w) > 2):
              base += 2.0

          # Penalty: known utility/meta subreddits
          if sub_lower in UTILITY_SUBS:
              base *= 0.3

          # Bonus: post engagement (high-engagement posts = better sub)
          ups = post.get("ups") or post.get("score", 0)
          if ups > 100:
              base += 0.5

          scores[sub] += base

      return [sub for sub, _ in scores.most_common(max_subs)]
  ```

#### 2b. Define utility/meta subreddit blocklist

- [x] Add a small set of subs that are "find X for me" or "identify X" rather than discussion:
  ```python
  UTILITY_SUBS = frozenset({
      'namethatsong', 'findthatsong', 'tipofmytongue',
      'whatisthissong', 'helpmefind', 'whatisthisthing',
      'whatsthissong', 'findareddit', 'subredditdrama',
  })
  ```
- [x] Keep this small and focused — don't over-filter. Only penalty (0.3x), not ban.

#### 2c. Try secondary query for subreddit discovery

- [x] If the first global search returns <3 unique subreddits above threshold, run a second global search with just `{core subject}` (stripped even further) to cast a wider net for subreddit frequencies
- [x] This helps niche topics where the full query is too specific

---

### Task 3: Make ScrapeCreators the Default Reddit Method

**Goal:** New users should be guided to ScrapeCreators first, not OpenAI.

**Files to modify:**
- `SKILL.md` — metadata section, onboarding banner, security section
- `scripts/lib/env.py` — error messages and missing key guidance
- `scripts/lib/render.py` — web-only mode banner

#### 3a. Update SKILL.md metadata

- [x] Change `primaryEnv: OPENAI_API_KEY` → `primaryEnv: SCRAPECREATORS_API_KEY`
- [x] Change `requires.env: [OPENAI_API_KEY]` → `requires.env: [SCRAPECREATORS_API_KEY]`
- [x] Keep OPENAI_API_KEY mentioned but as optional/legacy

#### 3b. Update web-only mode banner (`scripts/lib/render.py`)

- [x] Change the current banner:
  ```
  - `OPENAI_API_KEY` or `codex login` → Reddit threads with real upvotes & comments
  ```
  To:
  ```
  - `SCRAPECREATORS_API_KEY` → Reddit + TikTok + Instagram (one key, all three!) — real upvotes, comments, views
  - `OPENAI_API_KEY` (legacy) → Reddit threads (slower, higher cost)
  ```

#### 3c. Update env.py messaging

- [x] In `get_missing_keys()`, when Reddit is missing, suggest ScrapeCreators first:
  - Current: returns `'reddit'` which triggers "Add OPENAI_API_KEY or run codex login" in SKILL.md
  - Add a helper: `get_setup_hint(missing)` that returns:
    - For 'reddit': `"Add SCRAPECREATORS_API_KEY for Reddit + TikTok + Instagram (one key, ~$0.002/search)"`
    - For 'x': `"Add XAI_API_KEY for X posts"`
    - For 'all': `"Add SCRAPECREATORS_API_KEY (Reddit+TikTok+Instagram) and XAI_API_KEY (X)"`

#### 3d. Update Security & Permissions section in SKILL.md

- [x] Add ScrapeCreators Reddit to the security section:
  ```
  - Sends search queries to ScrapeCreators API (`api.scrapecreators.com`) for Reddit, TikTok, and Instagram search (requires SCRAPECREATORS_API_KEY)
  ```
- [x] Move "Sends search queries to OpenAI's Responses API for Reddit discovery" to a "Legacy:" subsection
- [x] Update "Reddit" description in `allowed-tools` or tags if needed

#### 3e. Update render.py coverage note

- [x] In `render_compact()`, the coverage note for `reddit-only` currently says "Add an xAI key"
- [x] When ScrapeCreators is the active Reddit source, no need to mention OpenAI at all

---

## Acceptance Criteria

- [x] Top Reddit comment is rendered with `💬` prefix and upvote count for enriched posts
- [x] Posts with high top-comment scores rank slightly higher (visible in score differences)
- [x] "best rap songs lately" discovers at least one discussion sub (r/hiphopheads, r/rap, r/Music, etc.) instead of only utility subs
- [x] SKILL.md `primaryEnv` is `SCRAPECREATORS_API_KEY`
- [x] Web-only mode banner recommends ScrapeCreators first
- [x] All 5 test topics still pass (run same tests as before)
- [x] No regression in OpenAI fallback path

---

## Files Changed (Summary)

| File | Change |
|------|--------|
| `scripts/lib/reddit.py` | Improve `discover_subreddits()` with relevance weighting, add utility sub penalties, enhance `enrich_with_comments()` top comment metadata |
| `scripts/lib/score.py` | Add 10% comment quality weight to Reddit engagement formula |
| `scripts/lib/render.py` | Add `💬 Top comment` line to compact output, update web-only banner |
| `scripts/lib/env.py` | Add `get_setup_hint()`, update missing key messaging |
| `SKILL.md` | Change `primaryEnv`, update onboarding banner, add comment synthesis guidance, update security section |

---

## Cost Impact

No cost increase. Same number of API calls per search. The changes are all in local logic (scoring, rendering, discovery heuristic).

---

## Testing Plan

1. Re-run the same 5 test topics from beta testing
2. Verify top comments appear with `💬` in output
3. Verify "best rap songs lately" discovers at least one discussion subreddit
4. Verify `--diagnose` output recommends ScrapeCreators
5. Verify OpenAI fallback still works (unset SCRAPECREATORS_API_KEY, set OPENAI_API_KEY)
