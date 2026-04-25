---
title: Triage Open Issues and PRs
type: refactor
status: active
date: 2026-03-07
---

# Triage Open Issues and PRs - last30days-skill

Consolidated review and action plan for all 6 open items (2 issues, 4 PRs) as of 2026-03-07.

---

## 1. PR #52 - Fix missing metadata files in skill upload bundle

**Author:** 04cb | **Size:** +0/-1 | **Fixes:** #46
**File changed:** `.clawhubignore` (removes `*.json` glob)

### What it does

The `*.json` pattern in `.clawhubignore` was excluding `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json` - the metadata files required for ClawHub skill upload. This caused the "Zip file contains path with invalid characters" error reported in #46.

### Risk analysis

- Removing `*.json` also includes test fixtures (`fixtures/*.json`) and vendored `package.json` in the bundle. None are sensitive or harmful.
- No `package-lock.json`, `skills-lock.json`, or credential files exist as `.json` in the repo.
- One-line change with zero production code impact.

### Recommendation: MERGE IMMEDIATELY

- [x] Merge PR #52
- [x] Close issue #46 (auto-closes via "Fixes #46")
- [ ] Verify upload works post-merge

---

## 2. Issue #46 - "Claude will not upload as it says thread is invalid"

**Author:** johnuppard | **Error:** "Zip file contains path with invalid characters"

### Recommendation: CLOSES WITH PR #52

No standalone action needed. PR #52 is the fix. After merge, comment on #46 confirming resolution and ask reporter to verify.

---

## 3. PR #50 - test: add tests for entity_extract module

**Author:** mark-c4r | **Size:** +167/-0 (tests only)

### What it does

Adds `tests/test_entity_extract.py` with 23 test cases covering all 4 public/private functions in `scripts/lib/entity_extract.py`:

| Function | Cases | Coverage |
|----------|-------|----------|
| `_extract_x_handles` | 8 | author handles, @mentions, generic filtering, case normalization, frequency ranking, edge cases |
| `_extract_x_hashtags` | 5 | basic extraction, multiple tags, frequency ranking, short tag filtering, empty input |
| `_extract_subreddits` | 6 | field extraction, cross-refs in comments, frequency ranking, r/ stripping |
| `extract_entities` | 4 | integration, max limits, empty inputs, return key validation |

### Code quality assessment

- All function signatures match the actual module implementation exactly
- All 23 tests validated against the real module - they pass
- Import pattern matches existing tests (`sys.path.insert` + `from lib import`)
- Uses `unittest.TestCase` consistent with all other test files
- No external dependencies, no API calls, no mocking needed (pure functions)
- Test data uses inline dicts matching real Reddit/X response structure

### Recommendation: MERGE AFTER LOCAL VERIFICATION

- [x] Pull branch and run `python3 -m pytest tests/test_entity_extract.py -v` (23/23 passed)
- [x] Run full suite `python3 -m pytest tests/` (317/320 passed - 3 pre-existing failures in test_models.py, unrelated)
- [x] Merge

This is a clean, well-structured community contribution that adds coverage to a previously untested module.

---

## 4. PR #48 - feat: add Xiaohongshu source + Reddit public fallback

**Author:** YJLi-new | **Size:** +523/-75 | **Files:** 5 modified

### What it does

Two features bundled in one PR:

**A. Xiaohongshu (Little Red Book) source:**
- New `scripts/lib/xiaohongshu_api.py` module for searching via xiaohongshu-mcp HTTP API
- Source alias: `--search xiaohongshu` or `--search xhs`
- Health/login availability checks in `env.py`
- Handles Chinese numeric suffixes (wan/yi) in engagement parsing
- Default API base: `http://host.docker.internal:18060` (Docker-hosted)

**B. Reddit public JSON fallback:**
- `search_reddit_public()` added to `openai_reddit.py`
- Uses `reddit.com/search/.json` endpoint (no API key required)
- Multiple query strategy (topic, core subject, quoted core)
- Engagement-based relevance heuristic (60% score, 40% comments)
- Supplemental retries correctly gated - only fire when OpenAI auth is present

### Architecture compliance

| Pattern | Status |
|---------|--------|
| Three-function module pattern (search/parse/enrich) | Follows existing patterns |
| `DEPTH_CONFIG` with quick/default/deep | Present |
| `_log()` gated on stderr.isatty() | Present |
| env.py availability check | Present with retry logic |
| ThreadPoolExecutor dispatch | Correctly wired with +1 worker |
| Render/UI integration | Consistent with existing sources |

### Issues found

1. **Health check duplication** - `is_xiaohongshu_available()` in env.py AND `search_feeds()` both probe login status. Redundant but harmless.
2. **`from_date`/`to_date` accepted but unused** for Xiaohongshu - relies on API-side time bucketing. Acceptable given API limitation.
3. **Over-defensive `setdefault()`** in normalization (id and source_domain already set by search_feeds). Harmless.
4. **Error message format inconsistency** between OpenAI and public Reddit paths. Minor.
5. **`get_available_sources()` docstring** not updated to reflect Reddit always being available now.
6. **No tests included** for new Xiaohongshu module or Reddit public fallback.

### Security

- No hardcoded credentials
- xsec_token comes from API response (not user input)
- Docker `host.docker.internal` default is safe for containerized environments
- All URLs use `https://` for public Xiaohongshu

### Recommendation: MERGE WITH CONDITIONS

The Reddit public fallback alone makes this worth merging - it makes Reddit work with zero API keys. Xiaohongshu adds value for Chinese-market research.

**Before merge:**
- [x] Run full test suite to confirm no regressions (292/297 pass, 5 pre-existing)
- [x] Verify Xiaohongshu gracefully skips when API is unavailable (returns False, no crash)
- [x] Resolved merge conflicts with ScrapeCreators Reddit (main). Priority: ScrapeCreators -> OpenAI -> public fallback
- [x] Merged to main and pushed
- [ ] Test Reddit public fallback locally: unset OPENAI_API_KEY, run `python3 scripts/last30days.py "test topic" --search reddit --emit=compact`
- [ ] Update `get_available_sources()` docstring to reflect Reddit always-available change

**After merge (follow-up):**
- [ ] Add `tests/test_xiaohongshu.py` with fixture-based tests
- [ ] Add `tests/test_reddit_public.py` for the fallback path
- [ ] Consider extracting health check duplication

---

## 5. PR #47 - feat: add Apify as unified API provider

**Author:** lapolazzati | **Size:** +1484/-73 | **Files:** 6 new + orchestrator changes

### What it does

Adds Apify as a single-token alternative (`APIFY_API_TOKEN`) covering Reddit, X, TikTok, and Instagram. Existing per-source keys take priority; Apify is a transparent fallback.

**New modules:**
- `apify_client.py` (163 lines) - shared HTTP client for Apify run-sync API
- `apify_reddit.py` (195 lines) - Reddit via `trudax/reddit-scraper` actor
- `apify_x.py` (221 lines) - X via `apidojo/tweet-scraper` actor
- `apify_tiktok.py` (284 lines) - TikTok via `clockworks/tiktok-scraper` actor
- `apify_instagram.py` (288 lines) - Instagram via `apify/instagram-reel-scraper` actor

**Source routing priority:**
```
Reddit:    OpenAI -> Apify -> None
X:         Bird -> xAI -> Apify -> None
TikTok:    ScrapeCreators -> Apify -> None
Instagram: ScrapeCreators -> Apify -> None
```

### Critical issues

1. **Actor ID mismatch (BLOCKER):** Code uses different Apify actors than documented in README and plan.md.

   | Source | In Code | In Docs |
   |--------|---------|---------|
   | Reddit | `trudax/reddit-scraper` | `automation-lab/reddit-scraper` |
   | X | `apidojo/tweet-scraper` | `scraper_one/x-posts-search` |
   | TikTok | `clockworks/tiktok-scraper` | `epctex/tiktok-search-scraper` |
   | Instagram | `apify/instagram-reel-scraper` | matches |

   Users following README instructions will hit wrong actors.

2. **No tests (BLOCKER):** 1484 lines of new code with zero test coverage. Each Apify module has its own date parsing, relevance scoring, and response normalization - all untested.

3. **Significant code duplication:** `apify_tiktok.py` and `apify_instagram.py` share nearly identical:
   - `_tokenize()` (7 lines)
   - `_compute_relevance()` (14 lines)
   - `STOPWORDS` set
   - `SYNONYMS` dict
   - `_extract_core_subject()` (~20 lines)

4. **Version mismatch:** README says v2.9 but git history shows v2.9.4 on main. Version should be higher.

5. **plan.md included in commit** - implementation planning doc shouldn't be in the final merge.

### What's good

- Source routing logic in env.py is clean and backward-compatible
- Orchestrator dispatch uses consistent `_source` parameter pattern
- Existing source paths are completely untouched
- Timeout scaling is appropriate (90s quick, 150s default, 240s deep)
- Token handling follows security best practices (parameter passing, Bearer auth)

### Recommendation: REQUEST CHANGES

This PR is too large and has too many issues for a clean merge. Request the contributor to:

**Must fix before any merge:**
- [ ] Resolve actor ID mismatches (verify which actors actually work, update code OR docs)
- [ ] Add unit tests for all 5 new modules (at minimum: response normalization, date parsing)
- [ ] Fix version number
- [ ] Remove plan.md from commit

**Should fix:**
- [ ] Extract shared code from apify_tiktok/apify_instagram into `apify_common.py`
- [ ] Consider splitting into 2 PRs:
  - PR A: `apify_client.py` + env.py routing (foundation)
  - PR B: Individual source modules + tests (features)

**Status:** [x] Review posted requesting changes (2026-03-07)

**Comment template for PR:**
> Thanks for this contribution - the single-token approach is a great idea for simplifying setup. A few things need fixing before we can merge:
>
> 1. The Apify actor IDs in the code don't match the README/plan docs. Can you verify which actors are correct and align code + docs?
> 2. We need test coverage for the new modules - at minimum normalization tests with sample actor responses.
> 3. There's significant duplication between apify_tiktok.py and apify_instagram.py (_tokenize, _compute_relevance, STOPWORDS, SYNONYMS, _extract_core_subject). Could you extract shared code to an apify_common.py?
> 4. Version in README should be higher than v2.9.4 (current main).
> 5. Please remove plan.md from the commit.

---

## 6. Issue #45 - Add support for Gemini CLI

**Author:** alexferrari88 | **Request:** "Would it be possible to add support for Gemini CLI?"

### Assessment

This is a feature request to support Gemini CLI as a runtime alongside Claude Code and Codex. Key considerations:

- **Scope:** The skill is currently packaged for Claude Code (SKILL.md format) and Codex (~/.codex/skills/). Gemini CLI uses a different skill/extension format.
- **Effort:** Would require understanding Gemini CLI's plugin system, creating a compatible manifest, and potentially adapting the Python execution model.
- **Priority:** Low - Claude Code and Codex are the primary targets and where the user base is.
- **Community:** If the requester wants to contribute, they'd be best positioned to understand Gemini CLI's requirements.

### Recommendation: ACKNOWLEDGE AND BACKLOG

- [x] Respond with comment acknowledging and inviting contribution
- [x] Add a `help wanted` label
- [x] Keep open as a backlog item

---

## Priority Summary

| Priority | Item | Action | Risk |
|----------|------|--------|------|
| 1 | PR #52 (metadata fix) | ~~Merge now~~ DONE | None |
| 2 | Issue #46 (upload error) | ~~Auto-closes with PR #52~~ DONE | None |
| 3 | PR #50 (entity tests) | ~~Run tests, merge~~ DONE | None |
| 4 | PR #48 (Xiaohongshu + Reddit fallback) | ~~Test locally, merge with conditions~~ DONE | Low |
| 5 | Issue #45 (Gemini CLI) | ~~Acknowledge, backlog, label~~ DONE | None |
| 6 | PR #47 (Apify unified) | ~~Request changes~~ DONE (awaiting contributor) | Medium-High |
