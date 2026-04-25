---
title: "feat: 15-Test Side-by-Side Comparison - Make CROSS the GOAT"
type: feat
status: active
date: 2026-02-25
origin: docs/plans/2026-02-25-analysis-cross-source-comparison-plan.md
---

# 15-Test Side-by-Side Comparison - Make CROSS the GOAT

## Overview

Run all 5 canonical topics through all 3 skill versions (base, HN, CROSS) for 15 total full last30days runs. Save every result. Analyze side-by-side. Judge which version is best. Then create an improvement plan to make CROSS the definitive next release.

## Problem Statement / Motivation

The previous analysis only ran 5 tests on the CROSS branch - never comparing the same topics across all 3 versions. Without true side-by-side data, we can't judge whether CROSS is actually better or if the new features (dynamic YouTube scoring, cross-refs) introduce regressions. The user wants to see all 15 results, know which version wins, and get a concrete plan to make CROSS the GOAT before shipping.

## The 3 Versions

| Version | Git State | Sources | YouTube Relevance | Cross-Refs |
|---------|-----------|---------|-------------------|------------|
| **Base** | commit `427a4e4` | Reddit, X, YouTube, Web | Hardcoded 0.7 | No |
| **HN** | `main` / `f60a435` | Reddit, X, YouTube, **HN**, Web | Hardcoded 0.7 | No |
| **CROSS** | `feat/youtube-relevance-cross-source` / `0591f55` | Reddit, X, YouTube, HN, Web | Dynamic 0.1-1.0 | Yes (Jaccard 0.5) |

## The 5 Topics

| # | Topic | Category | Why chosen |
|---|-------|----------|------------|
| 1 | "Claude Code skills and MCP servers" | Developer tools | Core user base topic |
| 2 | "Seedance AI video generation" | Creative AI | Trending topic, cross-platform buzz |
| 3 | "M4 MacBook Pro review" | Consumer tech | Product review, mainstream |
| 4 | "best rap songs 2026" | Pop culture | Non-tech stress test |
| 5 | "React vs Svelte 2026" | Framework debate | Dev community, opinion-heavy |

## Test Matrix (15 Runs)

Run in **topic-sequential** order (all 3 versions of topic 1 back-to-back, then topic 2, etc.) to minimize temporal confounds on YouTube/X search results.

| Run | Topic | Version | Output File |
|-----|-------|---------|-------------|
| 1 | Claude Code | Base | `base-1-claude-code.json` |
| 2 | Claude Code | HN | `hn-1-claude-code.json` |
| 3 | Claude Code | CROSS | `cross-1-claude-code.json` |
| 4 | Seedance | Base | `base-2-seedance.json` |
| 5 | Seedance | HN | `hn-2-seedance.json` |
| 6 | Seedance | CROSS | `cross-2-seedance.json` |
| 7 | MacBook | Base | `base-3-macbook.json` |
| 8 | MacBook | HN | `hn-3-macbook.json` |
| 9 | MacBook | CROSS | `cross-3-macbook.json` |
| 10 | Rap songs | Base | `base-4-rap.json` |
| 11 | Rap songs | HN | `hn-4-rap.json` |
| 12 | Rap songs | CROSS | `cross-4-rap.json` |
| 13 | React/Svelte | Base | `base-5-react-svelte.json` |
| 14 | React/Svelte | HN | `hn-5-react-svelte.json` |
| 15 | React/Svelte | CROSS | `cross-5-react-svelte.json` |

**Output directory:** `/tmp/last30days-comparison/full/`

## Execution Protocol

### Pre-flight (once)

- [x] Clear model cache: `rm -f ~/.cache/last30days/model_selection.json`
- [x] Run `--diagnose` on current branch, save as `diagnose-baseline.json`
- [x] Verify all API keys active: Reddit (OPENAI_API_KEY), X (Bird cookies or XAI_API_KEY), YouTube (yt-dlp), HN (no key needed), Web (parallel AI or Brave)
- [x] Create output dir: `mkdir -p /tmp/last30days-comparison/full`
- [x] Stash any uncommitted changes: `git stash` (none needed - no uncommitted changes)

### Per-topic loop (repeat 5 times)

For each topic, run all 3 versions back-to-back:

```bash
# CRITICAL: Clean __pycache__ between EVERY git checkout to prevent stale bytecode
cleanup() {
  find scripts -name '__pycache__' -exec rm -rf {} + 2>/dev/null
  find scripts -name '*.pyc' -delete 2>/dev/null
}
```

- [ ] **Step 1: Base version**
  - `cleanup && git checkout 427a4e4`
  - `python3 scripts/last30days.py --diagnose 2>/dev/null` (verify sources match baseline)
  - `python3 scripts/last30days.py "<topic>" --quick --emit=json > /tmp/last30days-comparison/full/base-{N}-{slug}.json 2>/tmp/last30days-comparison/full/base-{N}-{slug}.log`

- [ ] **Step 2: HN version**
  - `cleanup && git checkout main`
  - `python3 scripts/last30days.py "<topic>" --quick --emit=json > /tmp/last30days-comparison/full/hn-{N}-{slug}.json 2>/tmp/last30days-comparison/full/hn-{N}-{slug}.log`

- [ ] **Step 3: CROSS version**
  - `cleanup && git checkout feat/youtube-relevance-cross-source`
  - `python3 scripts/last30days.py "<topic>" --quick --emit=json > /tmp/last30days-comparison/full/cross-{N}-{slug}.json 2>/tmp/last30days-comparison/full/cross-{N}-{slug}.log`

### Post-run

- [x] Return to feature branch: `git checkout feat/youtube-relevance-cross-source`
- [x] Verify all 15 JSON files exist and are non-empty
- [x] Check for `*_error` fields in any JSON output - flag but include (zero errors)

## Analysis Dimensions

### 1. Source Coverage Table

For each of 15 runs, count items per source:

| Topic | Version | Reddit | X | YouTube | HN | Web | Total |
|-------|---------|--------|---|---------|----|----|-------|

Expected: Base has 0 HN items. HN and CROSS should have identical source counts (same search code). Any differences indicate API non-determinism.

### 2. YouTube Relevance Comparison

**Matched-item analysis:** Match videos by `video_id` across Base/CROSS runs of the same topic. For each matched video:
- Base relevance: always 0.7
- CROSS relevance: dynamic score
- Delta and direction (did dynamic scoring promote or demote this video?)

**Aggregate analysis:** Distribution stats (min/avg/max/stddev) per version per topic.

### 3. Cross-Source Links (CROSS only)

- Count of items with cross_refs per topic
- Quality assessment: are the linked items actually about the same story?
- Which source pairs link most often? (Reddit-HN? YouTube-HN? X-Reddit?)

### 4. Score Distribution and Rankings

- Mean/median score of top 10 items per version per topic
- Rank position changes: do the same items appear in different orders?
- Does HN crowd out Reddit/X items in the top 10?

### 5. "Best Version" Judging Criteria

Define BEFORE analyzing to avoid bias:

| Metric | Weight | How measured |
|--------|--------|-------------|
| Source diversity | 25% | Shannon entropy across source types in top 15 items |
| Score quality | 25% | Mean score of top 10 items |
| Relevance accuracy | 25% | YouTube: do high-relevance videos actually match the query? Manual spot-check of top 3 + bottom 3 per topic |
| Bonus features | 25% | HN value-add (unique info not in other sources) + cross-ref utility (do xrefs add value to the reader?) |

### 6. HN Value-Add Assessment

For each topic where HN returns results:
- How many HN items appear in the overall top 10?
- Do HN items provide information not available from Reddit/X/YouTube?
- Are HN comment insights (top_comments) genuinely useful?

## Deliverables

### A. Raw Results Archive

All 15 JSON files plus logs saved in `/tmp/last30days-comparison/full/`, also copied to `docs/comparison-results/` for persistence.

### B. Comparison Summary Table

A single markdown table showing all 15 runs with key metrics per cell.

### C. Version Verdict

Clear judgment: which version is best overall, and best per topic category (tech, consumer, culture).

### D. CROSS Improvement Plan

Concrete changes to make CROSS the GOAT:

**Based on the previous analysis (see origin doc), likely improvements include:**

1. **Fix cross-source linking** - Switch from char-trigram Jaccard (0.5) to hybrid similarity (max of trigram + token Jaccard) at threshold 0.40. Previous modeling showed this goes from 1 link to 24 links across 5 tests.

2. **Cross-ref rendering** - Change from cryptic `[xref: X1, HN3]` IDs to human-readable `[also on: Reddit, HN]` labels.

3. **HN search broadening** - Investigate why React/Svelte returns 0 HN items.

4. **YouTube relevance** - Already working well, may need minor threshold tuning based on 15-test data.

5. **Score normalization** - Ensure HN items don't systematically crowd out other sources in the merged ranking.

**New improvements to discover from 15-test data:**
- Regressions introduced by CROSS changes
- Edge cases where Base or HN outperforms CROSS
- Topic-specific tuning opportunities

## Acceptance Criteria

- [x] All 15 JSON result files saved and non-empty
- [x] All 15 runs use identical source routing (verified via --diagnose)
- [x] __pycache__ cleaned between every git checkout
- [x] Comparison summary table covers all 15 runs
- [x] YouTube matched-item analysis for at least 3 topics (all 5 done)
- [x] Cross-source link quality spot-check for CROSS runs
- [x] Clear version verdict with supporting data
- [x] CROSS improvement plan with specific code changes
- [x] All results appended to the analysis document for the user to review

## Technical Considerations

- **__pycache__ poisoning**: Python caches bytecode. Switching git commits without clearing `__pycache__` means old code runs even after checkout. MUST clean between every checkout.
- **API rate limiting**: 15 runs hitting Reddit, X, YouTube, HN APIs. The `--quick` mode and natural ~30-90s per run provide spacing, but monitor for 429s in logs.
- **YouTube non-determinism**: yt-dlp search results shift over time. Topic-sequential ordering minimizes this by running all 3 versions of the same topic within ~3-5 minutes.
- **X search session**: Bird CLI depends on browser cookies. If session expires mid-run, X results degrade silently. Check X item counts across runs.
- **`--quick` limitation**: Results reflect Phase 1 only (8-12 items per source). Full pipeline with `--deep` might show different patterns. Document this caveat.

## Sources & References

- Previous analysis: [docs/plans/2026-02-25-analysis-cross-source-comparison-plan.md](docs/plans/2026-02-25-analysis-cross-source-comparison-plan.md)
- Implementation plan: [docs/plans/2026-02-25-feat-youtube-relevance-and-cross-source-linking-plan.md](docs/plans/2026-02-25-feat-youtube-relevance-and-cross-source-linking-plan.md)
- Existing comparison harness: [scripts/test-v1-vs-v2.sh](scripts/test-v1-vs-v2.sh)
- Scoring weights: [scripts/lib/score.py](scripts/lib/score.py) - 45% relevance + 25% recency + 30% engagement
