# Triage All Open GitHub Issues — Proposed Actions

**Date:** 2026-03-03
**Repo:** `mvanhorn/last30days-skill`
**Open issues:** 16 (as of this triage)
**Codebase version:** v2.1.0 (Bird vendored, 7 sources: Reddit, X, YouTube, HN, Polymarket, TikTok, Web)

---

## Legend

| Action | Meaning |
|--------|---------|
| **CLOSE (spam)** | Spam / solicitation — close without comment |
| **CLOSE (resolved)** | Already fixed in current version — comment & close |
| **CLOSE (duplicate)** | Duplicate of another issue — link & close |
| **COMMENT** | Respond with info, no code change needed |
| **FIX** | Code or docs change needed — described below |
| **REJECT** | Valid issue but won't address — explain why |

---

## Issue-by-Issue Triage

### #43 — Security Assessment Offer - Claude Code Skill with Social Media APIs
**Author:** Neo-Assistent | **Created:** 2026-02-26

> Unsolicited marketing from "SkillSec" offering a free security audit.

**Proposed action:** **CLOSE (spam)**

No comment needed. This is a cold sales pitch, not a bug or feature request. Close silently or with a brief "closing — not a bug report or feature request."

---

### #42 — License & Secondary Development Permission
**Author:** AllenX95 | **Created:** 2026-02-26

> Asks what license the project uses and whether modification for open-source models (Kimi K2.5) is allowed.

**Proposed action:** **COMMENT + CLOSE (resolved)**

Once #35/#34 are addressed (LICENSE file added), comment:

> The project is MIT licensed (see LICENSE file in repo root, added in v2.1.x). You're free to modify, fork, and adapt it for any purpose including integration with other models. The MIT license places no restrictions on secondary development.

**Depends on:** Adding the LICENSE file (see #35/#34 below).

---

### #41 — Can I use openrouter API to replace with openai API to do the reddit search?
**Author:** iklynow-hue | **Created:** 2026-02-25

> Asks about using OpenRouter instead of OpenAI for Reddit search. Has one off-topic spam comment from @gbessoni.

**Proposed action:** **COMMENT + CLOSE**

Comment:

> OpenRouter is already partially supported — `scripts/lib/openrouter_search.py` provides a Perplexity-via-OpenRouter integration for web search. However, the Reddit search specifically uses OpenAI's Responses API (`web_search_preview` tool), which is an OpenAI-specific feature that OpenRouter doesn't proxy.
>
> If you want to avoid OpenAI entirely, you can still get results from X (via vendored Bird search or xAI), YouTube (yt-dlp), Hacker News (free API), and Polymarket (free API) — no OpenAI key needed for those. Reddit is the one source that requires `OPENAI_API_KEY`.
>
> For budget control, consider using `--quick` mode which reduces API calls.

Also: **minimize/hide** the off-topic spam comment from @gbessoni ("I'm testing out a new idea for reddit called Redd").

---

### #40 — watchlist: search_queries field stored but never used by _run_topic()
**Author:** tejasgadhia | **Created:** 2026-02-23

> `add --queries "q1,q2,q3"` stores queries in DB but `_run_topic()` always passes `topic["name"]` as the search query. Long descriptive names produce poor results on X and web search.

**Proposed action:** **FIX (accept)**

This is a legitimate, well-documented bug. The fix is straightforward:

**File:** `scripts/watchlist.py` — `_run_topic()` (~line 136)

```python
# Current (broken):
cmd = [sys.executable, str(SCRIPT_DIR / "last30days.py"), topic["name"], "--emit=json"]

# Fix: prefer search_queries when available
import json as _json
queries = _json.loads(topic["search_queries"]) if topic.get("search_queries") else [topic["name"]]
search_term = queries[0] if queries else topic["name"]
cmd = [sys.executable, str(SCRIPT_DIR / "last30days.py"), search_term, "--emit=json"]
```

**Comment to post:**

> Good catch — you're right that `search_queries` is stored but never read. Will fix `_run_topic()` to prefer `search_queries[0]` over `topic["name"]` when available.

---

### #39 — watchlist.py: YouTube findings never stored + run-one silent output
**Author:** tejasgadhia | **Created:** 2026-02-23

> **Bug 1:** YouTube findings extracted by the research script but dropped in `_run_topic()` because there's no YouTube loop in the findings extraction.
> **Bug 2:** `cmd_run_one()` doesn't print the result (cosmetic).

**Proposed action:** **FIX (accept both)**

Both are real bugs with clear fixes provided by the reporter.

**Bug 1 fix** — `scripts/watchlist.py` findings extraction (~lines 170-193): add YouTube + TikTok loops:

```python
for item in data.get("youtube", []):
    findings.append({
        "source": "youtube",
        "url": item.get("url", ""),
        "title": item.get("title", ""),
        "author": item.get("channel_name", item.get("channel", "")),
        "content": item.get("transcript_snippet", "") or item.get("title", ""),
        "engagement_score": (item.get("engagement") or {}).get("views", 0),
        "relevance_score": item.get("relevance", 0),
    })

for item in data.get("tiktok", []):
    findings.append({
        "source": "tiktok",
        "url": item.get("url", ""),
        "title": item.get("caption_snippet", "")[:120],
        "author": item.get("author", ""),
        "content": item.get("caption_snippet", ""),
        "engagement_score": (item.get("engagement") or {}).get("views", 0),
        "relevance_score": item.get("relevance", 0),
    })
```

**Bug 2 fix** — `scripts/watchlist.py` `cmd_run_one()`:

```python
result = _run_topic(topic)
print(json.dumps(result, default=str))
```

**Comment to post:**

> Both confirmed. Fixing YouTube (and adding TikTok while we're at it) findings extraction, plus `run-one` output. Thanks for the detailed report.

---

### #36 — SKILL.md doesn't forward --store, --include-web, --sort-x, --diagnose, --timeout to script
**Author:** nicolefinateri | **Created:** 2026-02-21

> `"$ARGUMENTS"` is passed as a single quoted string, so argparse treats the whole thing as the topic positional. Flags like `--store` get swallowed. Also, 5 flags are undocumented in SKILL.md.

**Proposed action:** **COMMENT + CLOSE (resolved / won't fix)**

This needs investigation. The `"$ARGUMENTS"` expansion in SKILL.md (line 168) relies on Claude Code's variable expansion behavior. If Claude Code expands `$ARGUMENTS` before the shell sees it, the quoting around it means all words become one argument. However, in practice, Claude Code injects the literal text into the bash script, so `"$ARGUMENTS"` expands to `"best AI tools --store"` which the shell passes as a single string to Python — and Python's argparse sees it as one positional arg.

**However:** Looking at the actual SKILL.md line 168:
```bash
python3 "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=compact
```

This is a known Claude Code behavior — `$ARGUMENTS` is expanded by the template engine, not the shell. The expansion produces the raw text, so the double quotes cause everything to be one argument.

**The real fix:** Remove the quotes around `$ARGUMENTS`:

```bash
python3 "${SKILL_ROOT}/scripts/last30days.py" $ARGUMENTS --emit=compact
```

This lets word-splitting happen so argparse sees separate positional + flag args.

**Risk:** Topic names with spaces would break (e.g., `AI video tools` would become 3 separate args). Need to verify how Claude Code handles `$ARGUMENTS` expansion. If it's truly a template variable replaced before bash execution, then the fix is more nuanced — may need to parse flags out in bash first.

**Comment to post:**

> Thanks for the detailed report. The `$ARGUMENTS` quoting is tricky — it's a Claude Code template variable, not a shell variable. I'll investigate the exact expansion behavior and fix the forwarding. Re: undocumented flags — will add them to the Options section.

**Priority:** Medium — flags like `--store` and `--diagnose` are useful but not critical path.

---

### #35 — Add LICENSE file to repository
**Author:** HackJob7418 | **Created:** 2026-02-21

> Points out that `plugin.json` declares MIT but no LICENSE file exists in repo root.

**Proposed action:** **FIX (accept)**

Trivial fix. Add `LICENSE` file with standard MIT text to repo root.

**Comment to post:**

> You're right — added MIT LICENSE file to repo root. Thanks for catching the mismatch.

---

### #34 — License missing
**Author:** jdsika (Carlo van Driesten) | **Created:** 2026-02-21

> Same request as #35 — add a LICENSE file.

**Proposed action:** **CLOSE (duplicate of #35)**

**Comment to post:**

> Duplicate of #35 — adding MIT LICENSE file. Thanks for the nudge!

---

### #32 — Cannot install Claude Code plugin marketplace
**Author:** rayshan (Ray Shan) | **Created:** 2026-02-19

> `marketplace.json` schema validation fails: `plugins.0.source: Invalid input`

**Proposed action:** **FIX (investigate + fix)**

The current `marketplace.json` has:
```json
"plugins": [{"name": "last30days", "source": "."}]
```

The Anthropic marketplace schema may require `source` to be a URL or a path in a specific format, not bare `.`. Need to check the expected schema.

**Possible fix:** Update `source` to match whatever the skills.sh/marketplace validator expects. Likely needs to be a relative path to the SKILL.md or plugin directory:

```json
"plugins": [{"name": "last30days", "source": "./SKILL.md"}]
```

Or the schema may have changed since the file was written. Check skills.sh docs.

**Comment to post:**

> Thanks for the report + screenshot. The marketplace.json schema likely changed — I'll update the `source` field format. Can you share what version of the `skills` CLI you're using? (`npx skills --version`)

**Priority:** High — blocks installation for marketplace users.

---

### #31 — mvanhorn/last30days is being trashed on skills.sh
**Author:** PiotrAleksander (Piotr Mrzygłosz) | **Created:** 2026-02-19

> skills.sh security audit gives the skill bad scores. A mirror at `sickn33/antigravity-awesome-skills` has better scores.

**Proposed action:** **COMMENT + investigate**

This is a reputation/trust issue. The skills.sh audit likely flags things like:
- No LICENSE file (fixed by #35)
- Shell execution in SKILL.md (inherent to how the skill works)
- External API calls (Reddit, X, YouTube — core functionality)
- No pinned dependencies

**Comment to post:**

> Thanks for flagging this. A few things:
>
> 1. The missing LICENSE file (#35) is being added — that should help the audit score.
> 2. The skill necessarily makes external API calls (that's its core purpose — researching across platforms). Any "security warning" about API calls is expected behavior, not a vulnerability.
> 3. The mirror you found (`sickn33/antigravity-awesome-skills`) may be an older fork (v1) that doesn't include the more recent integrations. Simpler code = fewer audit flags, but also fewer features.
> 4. I'll review the specific audit findings on skills.sh and address any legitimate concerns.
>
> If you can share the specific warnings you're seeing, I can address them directly.

**Priority:** Medium — reputation matters but the core issue is likely the missing LICENSE + inherent design of making API calls.

---

### #30 — Bird cookie auth: source availability mapping misses reddit-web + Bird combination
**Author:** volarian-vai | **Created:** 2026-02-19

> When using Bird cookie auth without `XAI_API_KEY` but with a web search key (e.g., `BRAVE_API_KEY`), the source override logic misses the `reddit-web` → `all` mapping.

**Proposed action:** **FIX (accept)**

Legitimate edge case in source availability logic. The fix is a small addition to the Bird override block in `scripts/last30days.py` (~line 917):

```python
if x_source == 'bird':
    if available == 'reddit':
        available = 'both'
    elif available == 'reddit-web':
        available = 'all'
    elif available == 'web':
        available = 'x-web'
```

**Comment to post:**

> Good catch on the missing `reddit-web` case. The fix is straightforward — adding the mapping. Also fixing `web` → `x-web` as you noted.

**Priority:** Low-medium — affects a specific env var combination (Bird auth + no XAI key + Brave key).

---

### #29 — YouTube stats show 'yt-dlp not installed' when search returns 0 results
**Author:** alexkrivov | **Created:** 2026-02-19

> When yt-dlp runs successfully but returns 0 results, the stats footer says "yt-dlp not installed" because `report.youtube` is `[]` (falsy) and the fallback message is wrong.

**Proposed action:** **FIX (accept)**

Clear bug with a clear root cause. Two-part fix:

**1.** In `scripts/last30days.py` (~line 1085), set a proper skip reason when YouTube returns 0:

```python
if has_ytdlp and not yt_results:
    source_info["youtube_skip_reason"] = "0 results (query may be too specific)"
```

**2.** In `scripts/lib/render.py` (~line 288), change the default fallback:

```python
reason = source_info.get("youtube_skip_reason", "not available")
```

**Comment to post:**

> Confirmed — the `[]`-is-falsy bug plus a misleading default string. Will fix both the skip reason and the fallback. Thanks for the detailed trace.

**Priority:** Low — cosmetic/UX but misleading for users trying to debug setup.

---

### #22 — Feature request: Surface more Bird CLI capabilities (engagement sorting, time windows, thread following)
**Author:** nicolefinateri | **Created:** 2026-02-09

> Requests: (1) `--sort-x likes` flag, (2) `--since 3h` granular time windows, (3) thread following via `bird thread <id>`.

**Proposed action:** **COMMENT (partial accept, defer)**

Good feature requests but some are already partially addressed:

1. **Engagement sorting** — The `--sort-x=MODE` flag already exists in `last30days.py` argparse (line ~1080) but isn't documented in SKILL.md (related to #36). Sorting by `likes`, `engagement`, `recent`, or `score` is already implemented.

2. **Granular time windows** — The `--days` flag exists (1-30), but hour-level granularity (`--since 3h`) would be new. Low priority since most research use cases are days-scale.

3. **Thread following** — Would be a significant feature addition. The vendored Bird search in v2.1 may not expose thread fetching. Would need investigation.

**Comment to post:**

> Great ideas! Update on each:
>
> 1. **Engagement sorting:** `--sort-x=MODE` already exists in the script (likes, engagement, recent, score). It wasn't documented in SKILL.md — fixing that (#36). Should work if you call the Python script directly.
> 2. **Granular time windows:** Interesting idea. Currently `--days=N` goes down to 1 day. Hour-level would need a new flag and Bird-specific query modification. Adding to backlog.
> 3. **Thread following:** Love this in principle — high-engagement thread starters are gold. Would need to assess what the vendored Bird search supports. May be a v2.2+ feature.
>
> A PR for any of these would be welcome!

**Priority:** Low — nice-to-haves; #1 is already done, #2/#3 are backlog.

---

### #19 — Bird is missing
**Author:** brianjking (Brian J King) | **Created:** 2026-02-09

> Bird GitHub repo is gone. Comments confirm npm package is deprecated, Homebrew install fails. Multiple users affected.

**Proposed action:** **CLOSE (resolved in v2.1)**

This was a major pain point that drove the v2.1 vendoring decision. Bird's GraphQL client is now bundled directly in the repo at `scripts/lib/vendor/bird-search/`. No external npm install needed.

**Comment to post:**

> **Resolved in v2.1.0** (released Feb 15, 2026).
>
> Bird's Twitter GraphQL search client is now vendored directly into the skill at `scripts/lib/vendor/bird-search/`. No npm install, no Homebrew, no external dependency. Just needs Node.js 22+ in your PATH.
>
> If you're on an older version, update to v2.1:
> ```
> npx skills add https://github.com/mvanhorn/last30days-skill
> ```
>
> Authentication still works via Safari cookies (auto-detected) or `AUTH_TOKEN`/`CT0` environment variables. See README for setup.
>
> Thanks to everyone who reported this — it's what motivated bundling the search client directly.

---

### #4 — Add macOS Python SSL certificate prerequisite to README
**Author:** joshdaws (Josh Daws) | **Created:** 2026-01-27

> Python.org macOS installer doesn't include SSL certificates. Users get `CERTIFICATE_VERIFY_FAILED` errors on all API calls.

**Proposed action:** **FIX (accept — docs change)**

Add a troubleshooting section to README.md. The reporter's suggested text is good. This only affects python.org installs (not Homebrew), but it's a confusing error when hit.

**Comment to post:**

> Good call — adding a troubleshooting section to the README for this. The `certifi` fallback is interesting but adds a dependency; the docs fix is simpler and sufficient since Homebrew Python (the most common Claude Code setup) isn't affected.

**Priority:** Low — affects a subset of macOS users, but easy to fix with docs.

---

### #2 — npx skills add fails for this package
**Author:** mikecfisher (Mike Fisher) | **Created:** 2026-01-26

> `npx skills add` can't find any skills in the repo. Owner commented that PR #1 restructures to standard plugin format.

**Proposed action:** **CLOSE (resolved)**

The repo was restructured to standard plugin format in PR #1 (SKILL.md at root, .claude-plugin/ directory). The `skills` CLI should now detect the skill correctly. If #32's marketplace.json schema issue is also fixed, this should be fully resolved.

**Comment to post:**

> This was fixed in the repo restructuring (PR #1, merged Jan 27). The skill now has a proper `SKILL.md` at root + `.claude-plugin/` directory.
>
> If you're still having trouble, it may be the marketplace.json schema issue tracked in #32. Please try again and reopen if the problem persists.

---

## Summary Table

| # | Title | Action | Priority | Effort |
|---|-------|--------|----------|--------|
| **43** | Security Assessment Offer | **CLOSE (spam)** | — | None |
| **42** | License & Secondary Dev Permission | **COMMENT + CLOSE** | Low | None (after #35) |
| **41** | OpenRouter API replacement | **COMMENT + CLOSE** | Low | None |
| **40** | watchlist: search_queries unused | **FIX** | Medium | Small (~10 lines) |
| **39** | watchlist: YouTube not stored + silent run-one | **FIX** | Medium | Small (~25 lines) |
| **36** | SKILL.md flag forwarding | **COMMENT + investigate** | Medium | Medium (SKILL.md rewrite) |
| **35** | Add LICENSE file | **FIX** | High | Trivial (1 file) |
| **34** | License missing | **CLOSE (dup of #35)** | — | None |
| **32** | marketplace.json schema error | **FIX** | High | Small (schema update) |
| **31** | skills.sh bad audit scores | **COMMENT** | Medium | None (after #35) |
| **30** | Bird source mapping edge case | **FIX** | Low | Small (~3 lines) |
| **29** | YouTube "not installed" false message | **FIX** | Low | Small (~5 lines) |
| **22** | Bird feature requests | **COMMENT (partial accept)** | Low | None (backlog) |
| **19** | Bird is missing | **CLOSE (resolved v2.1)** | — | None |
| **4** | macOS SSL certificate docs | **FIX (docs)** | Low | Small (README section) |
| **2** | npx skills add fails | **CLOSE (resolved)** | — | None |

---

## Recommended Execution Order

### Batch 1 — Quick wins (close/comment only, no code)
1. Close #43 (spam)
2. Close #34 (dup of #35)
3. Close #19 (resolved in v2.1)
4. Close #2 (resolved by repo restructure)
5. Comment + close #41 (OpenRouter question)
6. Comment #22 (Bird feature requests — partial accept, backlog)
7. Comment #31 (skills.sh audit — will improve after LICENSE fix)

### Batch 2 — Trivial fixes
8. **#35** — Add MIT LICENSE file to repo root
9. Comment + close #42 (license question — now answered by LICENSE file)

### Batch 3 — Small code fixes
10. **#29** — Fix YouTube "not installed" false message (`render.py` + `last30days.py`)
11. **#30** — Fix Bird source mapping for `reddit-web` combo (`last30days.py`)
12. **#40** — Fix watchlist `search_queries` usage (`watchlist.py`)
13. **#39** — Fix watchlist YouTube/TikTok extraction + `run-one` output (`watchlist.py`)

### Batch 4 — Investigation needed
14. **#32** — Fix marketplace.json schema (needs schema research)
15. **#36** — Fix `$ARGUMENTS` flag forwarding (needs Claude Code expansion testing)
16. **#4** — Add SSL troubleshooting to README

---

## Proposed Comment Templates

### For spam (#43):
> Closing — this is not a bug report or feature request.

### For duplicates (#34):
> Duplicate of #35. Adding MIT LICENSE file — thanks!

### For resolved issues (#19, #2):
> Resolved in v2.1.0. [details specific to issue]. Closing — please reopen if you're still experiencing this on the latest version.

### For questions (#41, #42):
> [Answer the question]. Closing as answered — feel free to reopen if you have follow-ups.

### For accepted bugs (#29, #30, #39, #40):
> Confirmed — [brief acknowledgment]. Fix incoming. Thanks for the detailed report.
