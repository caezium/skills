---
title: "chore: open PR triage - build or close decision for all 5 open PRs"
type: chore
status: active
date: 2026-03-02
---

# Open PR Triage

Decision record for each of the 5 open PRs on `mvanhorn/last30days-skill`.
For each: build/merge, cherry-pick, or close with explanation.

---

## PR #26 - Add HN, YouTube, and Product Hunt sources + --search flag
**Author:** wkbaran | **Size:** +3402/-49 | **Date:** 2026-02-15

### What it adds
- Hacker News source (Algolia API, no auth)
- YouTube source (YouTube Data API v3, optional key)
- Product Hunt source (GraphQL API, optional key)
- `--search=SOURCES` flag (e.g. `--search=reddit,hn,yt`)
- 58 new tests

### What's already on main
- **HN:** ✅ already merged (`scripts/lib/hackernews.py`)
- **YouTube:** ✅ already merged (`scripts/lib/youtube_yt.py`)
- **Product Hunt:** ❌ NOT on main
- **`--search` flag:** ❌ NOT on main

### Decision: CHERRY-PICK (`--search` flag only, skip Product Hunt)

The HN and YouTube modules in this PR are earlier versions than what's on
main. We should NOT take those. Product Hunt is not a priority source.
The one missing piece worth landing:

**`--search=SOURCES` flag** - lets callers (including agent mode) specify
which sources to run. Useful for `--search=hn,polymarket` or
`--search=reddit,x` focus runs.

### Plan
- Cherry-pick just `tests/test_search_flag.py` and the `--search` argument
  wiring in `scripts/last30days.py`
- Skip `scripts/lib/producthunt.py` and all PH-related code entirely
- Do NOT take their `hackernews.py`, `youtube.py`, `render.py`, `normalize.py`,
  `schema.py` - our versions are newer
- Update SKILL.md to document `--search` flag
- Comment on PR thanking wkbaran - his HN/YouTube work was an inspiration
  for the sources we ended up building. Acknowledge that specifically.

### Acceptance Criteria
- [ ] `python3 scripts/last30days.py "AI coding tools" --search=hn,reddit` runs only HN + Reddit
- [ ] `python3 scripts/last30days.py "test" --search=x,web` skips Reddit
- [ ] `test_search_flag.py` passes (adapt to our test patterns, no PH references)
- [ ] SKILL.md updated with `--search` flag docs
- [ ] Sync via `bash scripts/sync.sh`

---

## PR #24 - Adding Codex compatibility
**Author:** el-analista | **Size:** +228/-29 | **Date:** 2026-02-11

### What it adds
- `agents/openai.yaml` Codex discovery metadata
- Portable script path resolution in SKILL.md (multi-install-path loop)
- Platform-neutral UI text (`assistant` instead of Claude-specific wording)
- `LAST30DAYS_CACHE_DIR` env override in `scripts/lib/cache.py`
- `LAST30DAYS_OUTPUT_DIR` env override in `scripts/lib/render.py`
- X/Bird query noise stripping + last-chance retry in `scripts/lib/bird_x.py`
- New tests: `test_bird_x.py`, `test_cache.py`, `test_render.py`

### What's already on main
- **Codex auth:** ✅ already merged (via PR #38)
- **Multi-path script resolution:** ✅ already in SKILL.md (the `for dir in` loop)
- **Platform-neutral wording:** ❌ NOT systematically applied
- **Cache/output dir overrides:** ❌ NOT on main
- **Bird X improvements:** ✅ partially (we have other bird_x fixes but may be missing noise stripping + retry)

### Decision: REVIEW AND PARTIAL CHERRY-PICK

The env var overrides (`LAST30DAYS_CACHE_DIR`, `LAST30DAYS_OUTPUT_DIR`) are
genuinely useful for sandboxed/containerized Codex environments. The bird_x
noise stripping and last-chance retry may improve X search quality and are
low-risk additions.

The platform-neutral wording change ("assistant" instead of Claude references)
should be skipped — SKILL.md is Claude-specific by design.

### Plan
- Read the diff carefully against our current `cache.py`, `render.py`, `bird_x.py`
- Cherry-pick the `LAST30DAYS_CACHE_DIR` and `LAST30DAYS_OUTPUT_DIR` env overrides
- Cherry-pick the bird_x noise stripping + retry logic if it doesn't conflict
  with our existing bird_x changes
- Skip `agents/openai.yaml` — we have our own multi-path resolution
- Skip platform-neutral wording changes
- Comment on PR thanking contributor and explaining what landed

### Acceptance Criteria
- [ ] `LAST30DAYS_CACHE_DIR=/tmp/test python3 scripts/last30days.py "test" --mock` writes cache to /tmp/test
- [ ] `LAST30DAYS_OUTPUT_DIR=/tmp/out python3 scripts/last30days.py "test" --mock` writes output to /tmp/out
- [ ] Existing tests pass after cherry-pick
- [ ] `test_cache.py` and `test_render.py` adapted and passing

---

## PR #14 - Simplify to WebSearch-first, make API keys optional
**Author:** thangman1 | **Size:** +97/-168 | **Date:** 2026-02-01

### What it does
Removes the Reddit/X Python search engine as the primary data source.
Repositions Claude Code's built-in WebSearch as the "default" mode.
Strips engagement metrics (upvotes, likes, repost counts) from output.
Removes mode detection logic (Full Mode / Partial Mode / Web-Only Mode).

### Decision: CLOSE - do not merge

This PR inverts the core value proposition of last30days. The skill's
differentiation is **real engagement data** from Reddit threads and X posts —
upvotes, likes, reposts — that WebSearch cannot provide. Stripping that out
produces a worse tool than just asking Claude to search the web, which anyone
can already do.

The author's intent (lower barrier to entry, no API key required) is valid,
but the right solution is making HN + Polymarket work without any API key
(they already do), and making OPENAI_API_KEY easier to obtain — not removing
the Reddit/X engine.

### Action
- Comment on PR explaining why we're closing it
- Acknowledge the valid friction point (API key setup) and point to HN +
  Polymarket as the zero-config sources
- Close PR

---

## PR #10 - OpenRouter API integration
**Author:** thetechreviewer | **Size:** +1029/-16 | **Date:** 2026-01-28

### What it adds
OpenRouter as an alternative to OpenAI for the Reddit discovery search.
Allows using any model available on OpenRouter instead of just OpenAI models.

### What's already on main
- **`scripts/lib/openrouter_search.py`:** ✅ ALREADY ON MAIN
- **Wired into `scripts/last30days.py`:** ✅ ALREADY ON MAIN (the `backend == "openrouter"` path)

### Decision: CLOSE - already merged

The OpenRouter integration that this PR introduced is already on main. It
arrived via internal work that post-dated this PR. The PR is stale.

### Action
- Comment on PR: "Thanks for this — OpenRouter support is already on main
  (landed via internal work). Closing as incorporated."
- Close PR

---

## PR #5 - Add support for Codex auth with OpenAI Responses API
**Author:** jblwilliams | **Size:** +358/-66 | **Date:** 2026-01-27

### What it adds
- JWT-based Codex auth with `chatgpt_account_id`
- Codex endpoint routing (`https://chatgpt.com/backend-api/codex/responses`)
- SSE handling for streaming Codex responses
- Typed auth status/source dataclass
- Codex fallback model chain

### What's already on main
**All of this is already on main.** The Codex auth system landed via PR #37
(iliaal:codex-auth-merged), which in turn came in with PR #38. This PR (#5)
predates that work and covers the same ground.

### Decision: CLOSE - already incorporated

### Action
- Comment on PR: "Thanks for this early work on Codex auth! The same feature
  landed on main via PR #37 (from a separate contributor who built on similar
  ideas). The JWT decode, Codex endpoint routing, SSE parsing, and typed auth
  dataclass are all live. Closing as incorporated."
- Close PR

---

## Summary Table

| PR | Author | Decision | Reason |
|----|--------|----------|--------|
| #26 | wkbaran | **Cherry-pick** | `--search` flag not on main; HN/YouTube already there; skip Product Hunt |
| #24 | el-analista | **Cherry-pick** | Cache dir overrides + bird_x improvements worth landing; Codex auth already there |
| #14 | thangman1 | **Close** | Removes engagement data, inverts core value proposition |
| #10 | thetechreviewer | **Close** | OpenRouter already on main |
| #5 | jblwilliams | **Close** | Codex auth already on main via PR #37/38 |

## Implementation Order (if proceeding)

1. Close PR #5, #10, #14 with comments (no code changes needed)
2. Cherry-pick PR #24 pieces (bird_x + cache/render env overrides)
3. Cherry-pick PR #26 pieces (Product Hunt + `--search` flag)
4. Sync and test
5. Push to upstream
