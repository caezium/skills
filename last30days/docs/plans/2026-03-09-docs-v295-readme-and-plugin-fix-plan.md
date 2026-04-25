---
title: "docs: v2.9.5 README update, plugin.json fix, Claude Code install above fold"
type: docs
status: completed
date: 2026-03-09
---

# docs: v2.9.5 README update, plugin.json fix, Claude Code install above fold

Three things in one commit:

## 1. Fix plugin.json hooks field (Issue #62)

**Bug:** `"hooks": ["./hooks/"]` should be `"hooks": {}`. Array format is invalid per Claude Code plugin manifest schema. No hooks directory exists anyway.

**File:** `.claude-plugin/plugin.json:25`

**Fix:** Change `"hooks": ["./hooks/"]` to `"hooks": {}`

## 2. Add Claude Code install above ClawHub

Currently the README opens with ClawHub badge + install. User wants Claude Code (the default/best way) to be equally prominent ABOVE ClawHub.

**Add before the ClawHub badge:**
```
### Claude Code (recommended)
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days@last30days-skill
```

This matches the Installation section further down but puts it above the fold where people actually see it.

## 3. Update README to v2.9.5

**Header:** Change `v2.9.1` to `v2.9.5`

**Source list:** Add "Bluesky" everywhere sources are listed (currently says "Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, and the web")

**New in v2.9.5 block** (replace the v2.9.1 block):

Features shipped since v2.9.1:
- **ScrapeCreators X backend** (`4b7087e`) - X/Twitter search now uses ScrapeCreators as a backend option alongside Bird cookies
- **Bluesky/AT Protocol** (`9a1059e`, `adb5a67`) - New social source with full pipeline (search, parse, normalize, score, dedupe, render). Opt-in via `BSKY_HANDLE` + `BSKY_APP_PASSWORD` app password
- **Comparative mode** (`ecf90c0`) - "X vs Y" queries run 3 parallel research passes and output side-by-side comparison
- **Per-project .env config** (PR #59) - `.last30days.env` in project root for per-project API keys
- **SessionStart config check** (PR #58) - Validates config on session start
- **Expanded test coverage** (PRs #56, #57) - Unit tests for untested modules + smoke tests + edge cases
- **Claude Code marketplace plugin** (`627947f`) - Install via `/plugin install`
- **Gemini CLI extension** (`2f16ff1`) - `gemini extensions install`

**Env vars section:** Add `BSKY_HANDLE` and `BSKY_APP_PASSWORD` to the optional keys table

## Files to Change

| File | Change |
|------|--------|
| `README.md` | Version bump, Claude Code above fold, new features, Bluesky in source lists, env vars |
| `.claude-plugin/plugin.json` | Fix hooks field |

## Acceptance Criteria

- [x] `"hooks": {}` in plugin.json (fixes #62)
- [x] Claude Code plugin install appears ABOVE ClawHub badge
- [x] README says v2.9.5
- [x] "New in v2.9.5" block lists all features since v2.9.1
- [x] Bluesky appears in source list references
- [x] BSKY_HANDLE/BSKY_APP_PASSWORD documented in env vars
- [ ] Plugin installs successfully after fix

## Sources

- Issue #62: https://github.com/mvanhorn/last30days-skill/issues/62
- Issue #63: https://github.com/mvanhorn/last30days-skill/issues/63 (skipped - score 4/10, niche)
- Recent commits: `4b7087e`, `9a1059e`, `ecf90c0`, `adb5a67`
- PRs #56-#59 merged since v2.9.1
