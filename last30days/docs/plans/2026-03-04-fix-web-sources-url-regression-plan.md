---
title: "fix: Web sources showing full URLs instead of plain domain names"
type: fix
status: pending
date: 2026-03-04
---

# fix: Web Sources Showing Full URLs Instead of Plain Domain Names

## Problem

Two regressions in the `/last30days` skill output:

### Regression 1: Full URLs on the Web stats line

The `🌐 Web:` stats line is showing full URLs instead of plain source names:

**BAD (current — "Instagram Trends" run):**
```
├─ 🌐 Web: 10+ pages — https://later.com/blog/instagram-reels-trends/,
https://socialbee.com/blog/instagram-trends/,
https://buffer.com/resources/instagram-algorithms/,
https://metricool.com/instagram-trends/,
https://napoleoncat.com/blog/instagram-reels-trends/
```

**GOOD (expected):**
```
├─ 🌐 Web: 10+ pages — Later, SocialBee, Buffer, Metricool, NapoleonCat
```

### Regression 2: Trailing Sources: block with full URLs

A separate `Sources:` section appears at the bottom of the response with full URLs:

```
Sources:
- https://www.heyorca.com/blog/instagram-social-news
- https://socialbee.com/blog/instagram-updates/
- https://buffer.com/resources/instagram-algorithms/
- https://www.cnn.com/2026/02/22/tech/social-media-addiction-trial-tobacco-moment
```

This was fixed in commit `82efa61` (2026-03-02) but is regressing intermittently.

## Root Cause

The SKILL.md instructions at lines 219-221, 404, and 409 already say the right thing:
- Line 404: `├─ 🌐 Web: {N} pages — Source Name, Source Name, Source Name`
- Line 409: `"plain names, no URLs — URLs wrap badly in terminals"`
- Lines 219-221: "DO NOT output a separate Sources: block"

But the model ignores these because:

1. **The template `Source Name` is too abstract.** The model sees WebSearch results with full URLs and doesn't know how to extract a human-friendly name from `https://later.com/blog/instagram-reels-trends/`. It needs explicit examples showing the transformation.

2. **The WebSearch system mandate still wins.** The WebSearch tool's built-in instruction (`"you MUST include a Sources: section"`) outcompetes the skill's instruction. The current countermeasure (line 409) works sometimes but not reliably — it needs to be stronger and repeated.

3. **No explicit extraction rule.** The model needs a concrete rule for turning URLs into names: strip protocol, strip path, strip `www.`, capitalize.

## Proposed Solution

**SKILL.md edits only. No Python changes.**

### Fix 1: Add explicit URL-to-name examples in the stats template (line 404 area)

After the stats template block, add concrete examples showing the transformation:

```
**🌐 Web: line formatting:**
- Extract the SITE NAME from each URL — strip protocol, path, and "www."
- Use the publication's proper name when recognizable
- Examples:
  - https://later.com/blog/instagram-reels-trends/ → "Later"
  - https://socialbee.com/blog/instagram-trends/ → "SocialBee"
  - https://buffer.com/resources/instagram-algorithms/ → "Buffer"
  - https://www.cnn.com/2026/02/22/tech/... → "CNN"
  - https://medium.com/the-ai-studio/... → "Medium"
  - https://radicaldatascience.wordpress.com/... → "Radical Data Science"
- NEVER paste the URL itself. ONLY the site name as plain text.
- Separate names with commas: "Later, SocialBee, Buffer, CNN, Medium"
```

### Fix 2: Strengthen the anti-Sources instruction (line 409 area)

Replace the current single-paragraph note with a louder, more explicit instruction:

```
**⚠️ WebSearch citation requirement — ALREADY SATISFIED above.**
The WebSearch tool mandates source citation. That requirement is FULLY satisfied
by the source names on the 🌐 Web: line above. Do NOT append a separate
"Sources:" section at the end of your response. Do NOT list URLs anywhere in
your output. The 🌐 Web: line IS your citation. You're done.
```

### Fix 3: Add a negative example in the URL FORMATTING section (line 356 area)

Extend the existing BAD/GOOD examples to cover the stats line specifically:

```
URL FORMATTING: NEVER paste raw URLs anywhere in the output.
- BAD: "per https://www.rollingstone.com/music/music-news/kanye-west-bully-1235506094/"
- GOOD: "per Rolling Stone"
- BAD stats line: "🌐 Web: 10 pages — https://later.com/blog/..., https://buffer.com/..."
- GOOD stats line: "🌐 Web: 10 pages — Later, Buffer, CNN, SocialBee"
```

### Fix 4: Update Security section (line 588, 600)

While we're in SKILL.md, update the stale Apify references to ScrapeCreators:
- Line 588: Change Apify reference to ScrapeCreators for TikTok
- Line 600: Update TikTok requirement note
- Add Instagram source mention

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `SKILL.md` | MODIFY | Strengthen URL formatting rules, add examples, fix Apify refs |

## Implementation Steps

- [x] Add URL-to-name extraction examples after stats template (after line 407)
- [x] Strengthen anti-Sources instruction (replace line 409)
- [x] Add BAD/GOOD stats line example to URL FORMATTING section (around line 356)
- [x] Update Security section: Apify → ScrapeCreators, add Instagram (lines 588, 600)
- [x] Run `bash scripts/sync.sh` to deploy to all destinations
- [ ] Test with `/last30days Instagram Trends` — confirm plain names, no trailing Sources:

## Acceptance Criteria

- [ ] `🌐 Web:` line shows plain names only (e.g., "Later, SocialBee, Buffer")
- [ ] No `Sources:` section appears at the bottom of the response
- [ ] No raw URLs appear anywhere in the output (synthesis, stats, or footer)
- [ ] Security section reflects current source stack (ScrapeCreators, not Apify)
