---
title: Fix YouTube Display and Search Quality
type: fix
date: 2026-02-15
---

# Fix YouTube Display and Search Quality

## Overview

YouTube is the v2.1 headline feature but it's broken in two ways: results don't appear in Claude's synthesis (display bug), and search quality is worse than youtube.com (search bug). Both need fixing before launch.

## Problem Statement

**Display bug:** YouTube data exists in the script output but Claude never sees it. Reproduced on 4/5 recent test runs (Kanye, Seedance 2, Peter Steinberger, YouTube thumbnails). The skill worked once — the earlier "YouTube thumbnails" and "OpenClaw" runs showed YouTube stats — but subsequent runs silently dropped it.

**Search quality bug:** User searched "how to get on seedance 2" on youtube.com and got multiple recent results. yt-dlp returned 10 videos for the same query, but they included old irrelevant content because date filtering is broken.

## Root Cause Analysis

### Display Bug — Three compounding causes

1. **`2>&1` in SKILL.md bash command** (line 79) merges stderr progress messages into stdout. When Claude Code receives this mixed output, the YouTube section (which renders LAST after Reddit + X) can get lost in the noise or hit the 30K char Bash output limit.

2. **Background execution** (partially fixed). The old SKILL.md said "DO WEBSEARCH WHILE SCRIPT RUNS" which caused Claude to background the bash command. Backgrounded commands return truncated output via Task Output. *Already fixed in this session — SKILL.md now says FOREGROUND with 5-minute timeout.*

3. **No explicit model instruction to look for YouTube.** The SKILL.md tells Claude to synthesize but doesn't emphasize that YouTube data is in the script output and must be included.

### Search Quality Bug — `--flat-playlist` breaks date filtering

The yt-dlp command in `youtube_yt.py:110-116`:
```bash
yt-dlp ytsearch{count}:{query} --dateafter {YYYYMMDD} --flat-playlist --dump-json
```

**`--flat-playlist` causes three problems:**
1. `--dateafter` is silently ignored (no video-level metadata to filter on)
2. All items have `date: None` (upload_date not in flat-playlist JSON)
3. Old content leaks in (e.g., "the greatest youtube thumbnails of all time" returned for a 30-day query)

**`_extract_core_subject()` over-strips useful YouTube terms:**
- Strips "tips", "tutorial", "review" — but these ARE the content types people search for on YouTube
- "youtube thumbnail tips" → "youtube thumbnail" loses the intent signal

## Proposed Solution

### Phase 1: Fix Display (Critical — blocks launch)

#### 1a. Remove `2>&1` from SKILL.md bash command

**File:** `SKILL.md:79` (both `last30days-skill-private/SKILL.md` and `~/.claude/skills/last30days21/SKILL.md`)

```bash
# Before:
python3 "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=compact 2>&1

# After:
python3 "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=compact
```

This removes ~1-5KB of progress spam from the model's input and ensures clean stdout-only output.

#### 1b. Add YouTube-specific synthesis instruction to SKILL.md

After the "Read the ENTIRE output" instruction, add:

```markdown
**The script output has THREE sections: Reddit items, X items, and YouTube items (in that order).
If you see YouTube items in the output, you MUST include them in your synthesis and stats block.
YouTube items look like: `**{video_id}** (score:N) {channel} [N views, N likes]`**
```

#### 1c. Verify fix with test run

Run `/last30days21 youtube thumbnail tips` and confirm YouTube appears in stats.

### Phase 2: Fix Search Quality (High — headline feature quality)

#### 2a. Remove `--flat-playlist` flag

**File:** `scripts/lib/youtube_yt.py:110-116`

```python
# Before:
cmd = [
    "yt-dlp",
    f"ytsearch{count}:{core_topic}",
    "--dateafter", date_filter,
    "--flat-playlist",
    "--dump-json",
]

# After:
cmd = [
    "yt-dlp",
    f"ytsearch{count}:{core_topic}",
    "--dateafter", date_filter,
    "--dump-json",
    "--no-warnings",
    "--no-download",
]
```

**Impact:** Slower (yt-dlp resolves each video page for metadata) but:
- `--dateafter` actually works — filters old content
- `upload_date` populated — items get real dates
- Engagement metrics more accurate

**Risk:** Could increase search time from ~5s to ~30-60s for 20 videos. Mitigate by reducing default count or increasing timeout.

**Alternative if too slow:** Keep `--flat-playlist` but append year to search query:
```python
# Bias toward recent content since --dateafter doesn't work with flat-playlist
search_query = f"{core_topic} {from_date[:4]}"  # e.g., "youtube thumbnail 2026"
```

#### 2b. Fix `_extract_core_subject()` for YouTube-relevant terms

**File:** `scripts/lib/youtube_yt.py:67-76`

Don't strip terms that are useful YouTube content type signals:

```python
# YouTube-specific: keep 'tips', 'tutorial', 'review' etc.
# These are stripped for Reddit/X search but are valuable for YouTube
noise = {
    'best', 'top', 'good', 'great', 'awesome', 'killer',
    'latest', 'new', 'news', 'update', 'updates',
    'trending', 'hottest', 'popular', 'viral',
    'practices', 'features',
    'recommendations', 'advice',
    'prompt', 'prompts', 'prompting',
    'methods', 'strategies', 'approaches',
}
# NOTE: 'tips', 'tricks', 'tutorial', 'guide', 'review', 'reviews'
# are intentionally KEPT — they're YouTube content types
```

#### 2c. Clean question marks and trailing punctuation

**File:** `scripts/lib/youtube_yt.py:48-80`

```python
# At the end of _extract_core_subject():
result = ' '.join(filtered) if filtered else text
return result.rstrip('?!.')  # Clean trailing punctuation
```

### Phase 3: Polish (Medium — nice to have before launch)

#### 3a. Increase subprocess timeout for non-flat-playlist mode

**File:** `scripts/lib/youtube_yt.py:119-121`

```python
# Before:
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

# After — resolving video pages takes longer:
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
```

#### 3b. Add year hint to search query for recency bias

Even with `--dateafter` working, YouTube's search algorithm ranks by relevance not recency. Adding the year helps:

```python
# After core_topic extraction:
import datetime
current_year = datetime.datetime.now().year
search_query = f"{core_topic} {current_year}"
```

#### 3c. Reduce compact render item count for YouTube

The compact render currently shows up to 15 YouTube items. With transcripts, this is too much output. Reduce to 10:

**File:** `scripts/lib/render.py` — in `render_compact()`, add YouTube-specific limit or reduce the default.

## Acceptance Criteria

- [ ] `/last30days21 youtube thumbnail tips` shows YouTube in stats block
- [ ] YouTube items have real dates (not `None`)
- [ ] Old content (> 30 days) filtered out by `--dateafter`
- [ ] "youtube thumbnail tips" search returns videos about thumbnail tips (not generic old content)
- [ ] "How to access Seedance 2" returns recent Seedance 2 tutorials
- [ ] Script completes within 5 minutes for default depth
- [ ] No `2>&1` in SKILL.md bash command

## Files to Modify

| File | Changes |
|------|---------|
| `SKILL.md` | Remove `2>&1`, add YouTube synthesis instruction |
| `scripts/lib/youtube_yt.py` | Remove `--flat-playlist`, fix noise words, add year hint, increase timeout |
| `scripts/lib/render.py` | Optional: reduce YouTube item limit in compact mode |

## Testing

```bash
# Quick smoke test — should show YouTube items with dates
cd ~/.claude/skills/last30days21
python3 scripts/last30days.py "youtube thumbnail tips" --quick --emit=compact 2>/dev/null | grep -c "youtube.com"

# Date test — should show YYYY-MM-DD dates, not None
python3 -c "
from scripts.lib import youtube_yt
r = youtube_yt.search_youtube('youtube thumbnail tips', '2026-01-16', '2026-02-15', depth='quick')
for v in r['items'][:3]: print(v['date'], v['title'][:50])
"

# Full integration — run the skill in Claude Code and verify YouTube in stats
```

## References

- SKILL.md bash command: `scripts/last30days.py` line 79
- YouTube search: `scripts/lib/youtube_yt.py` lines 83-174
- Core subject extraction: `scripts/lib/youtube_yt.py` lines 48-80
- Compact render: `scripts/lib/render.py` lines 48-238
- Prior YouTube plan: `docs/plans/2026-02-14-feat-youtube-transcript-search-plan.md`
