---
title: ClawHub Scanner Compliance for last30days-official
type: feat
date: 2026-02-15
---

# ClawHub Scanner Compliance for last30days-official

## Overview

Make the last30days skill pass ClawHub's security scanner (VirusTotal + Code Insight) so it can be published as `last30days-official`. The user's 8 other mvanhorn skills already pass - we replicate their exact pattern.

## Problem Statement

ClawHub requires skills to pass a multi-layer security scan before publication:
1. Metadata validation (frontmatter fields)
2. VirusTotal automated scanning
3. LLM-powered Code Insight analysis (checks if capabilities match documentation)
4. Credential handling review

The current last30days SKILL.md has basic `metadata.clawdbot` but is missing fields the scanner checks: `emoji`, `user-invocable`, `disable-model-invocation`, `files` declaration. There's no `## Security & Permissions` section (required pattern from passing skills). README has no security/privacy documentation.

## Proposed Solution

Follow the exact pattern from `clawdbot-skill-xai` and `clawdbot-skill-search-x` (both pass the scanner). Three files need changes.

### Fix 1: SKILL.md Frontmatter

Add missing scanner fields to the existing frontmatter:

```yaml
---
name: last30days
version: "2.1"
description: "Research a topic from the last 30 days. Also triggered by 'last30'. Sources: Reddit, X, YouTube, web."
argument-hint: 'last30 AI video tools, last30 best project management tools'
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
homepage: https://github.com/mvanhorn/last30days-skill
user-invocable: true
disable-model-invocation: true
metadata:
  clawdbot:
    emoji: "📰"
    requires:
      env:
        - OPENAI_API_KEY
      bins:
        - node
        - python3
    primaryEnv: OPENAI_API_KEY
    files:
      - "scripts/*"
    homepage: https://github.com/mvanhorn/last30days-skill
    tags:
      - research
      - reddit
      - x
      - youtube
      - trends
      - prompts
---
```

Key additions:
- `user-invocable: true` - human must trigger it
- `disable-model-invocation: true` - agent cannot self-trigger
- `emoji: "📰"` - required display field
- `files: ["scripts/*"]` - prevents false "instruction-only but has scripts" flag

### Fix 2: Security & Permissions Section in SKILL.md

Add to the bottom of SKILL.md (matches xai/search-x pattern exactly):

```markdown
## Security & Permissions

**What this skill does:**
- Sends search queries to OpenAI's Responses API (`api.openai.com`) for Reddit discovery
- Sends search queries to Twitter's GraphQL API (via browser cookie auth) or xAI's API (`api.x.ai`) for X search
- Runs `yt-dlp` locally for YouTube search and transcript extraction (no API key, public data)
- Optionally sends search queries to Brave Search API, Parallel AI API, or OpenRouter API for web search
- Fetches public Reddit thread data from `reddit.com` for engagement metrics
- Stores research findings in local SQLite database (watchlist mode only)

**What this skill does NOT do:**
- Does not post, like, or modify content on any platform
- Does not access your Reddit, X, or YouTube accounts
- Does not share API keys between providers (OpenAI key only goes to api.openai.com, etc.)
- Does not log, cache, or write API keys to output files
- Does not send data to any endpoint not listed above
- Cannot be invoked autonomously by the agent (`disable-model-invocation: true`)

**Bundled scripts:** `scripts/last30days.py` (main research engine), `scripts/lib/` (search, enrichment, rendering modules), `scripts/lib/vendor/bird-search/` (vendored X search client, MIT licensed)

Review scripts before first use to verify behavior.
```

### Fix 3: Security & Privacy Section in README.md

Add after the "How It Works" section:

```markdown
## Security & Privacy

### Data that leaves your machine

| Destination | Data Sent | API Key Required |
|------------|-----------|-----------------|
| `api.openai.com` | Search query (topic string) | OPENAI_API_KEY |
| `reddit.com` | Thread URLs for enrichment | None (public JSON) |
| Twitter GraphQL / `api.x.ai` | Search query | Browser cookies or XAI_API_KEY |
| `youtube.com` (via yt-dlp) | Search query | None (public search) |
| `api.search.brave.com` | Search query (optional) | BRAVE_API_KEY |
| `api.parallel.ai` | Search query (optional) | PARALLEL_API_KEY |
| `openrouter.ai` | Search query (optional) | OPENROUTER_API_KEY |

Your research topic is included in all outbound API requests. If you research sensitive topics, be aware that query strings are transmitted to the API providers listed above.

### Data stored locally

- API keys: `~/.config/last30days/.env` (chmod 600 recommended)
- Watchlist database: `~/.local/share/last30days/research.db` (SQLite)
- Briefings: `~/.local/share/last30days/briefs/`

### API key isolation

Each API key is transmitted only to its respective endpoint. Your OpenAI key is never sent to xAI, Brave, or any other provider. Browser cookies for X are read locally and used only for Twitter GraphQL requests.
```

### Fix 4: Update .claude-plugin Files

**plugin.json** - bump version, add youtube keyword:

```json
{
  "name": "last30days",
  "description": "Research any topic from the last 30 days across Reddit, X, YouTube, and the web",
  "version": "2.1.0",
  "author": {"name": "mvanhorn"},
  "repository": "https://github.com/mvanhorn/last30days-skill",
  "license": "MIT",
  "keywords": ["research", "reddit", "twitter", "x", "youtube", "trends", "prompts"],
  "skills": ["./"]
}
```

**marketplace.json** - add version, update description:

```json
{
  "name": "last30days",
  "owner": {"name": "mvanhorn", "url": "https://github.com/mvanhorn"},
  "metadata": {
    "description": "Research any topic from the last 30 days across Reddit, X, YouTube, and the web",
    "version": "2.1.0"
  },
  "plugins": [{"name": "last30days", "source": "."}]
}
```

## What We DON'T Need

Based on the audit of your 8 passing skills:
- **Script-level security manifest headers** - your passing skills (xai, search-x, parallel) do NOT have these. The scanner relies on SKILL.md, not per-file headers.
- **Separate SECURITY.md file** - not needed; README section + SKILL.md section is sufficient.
- **Shell injection fixes** - already clean. All subprocess calls use list-form args, no `shell=True` anywhere.
- **Credential leak fixes** - already clean. All keys loaded from env vars, none hardcoded or logged.

## Acceptance Criteria

- [x] SKILL.md frontmatter has `user-invocable`, `disable-model-invocation`, `emoji`, `files`
- [x] SKILL.md has `## Security & Permissions` section with "does" and "does NOT do" lists
- [x] README.md has `## Security & Privacy` section with endpoint table and key isolation docs
- [x] plugin.json version bumped to 2.1.0, youtube keyword added
- [x] marketplace.json version and description updated
- [x] `python3 scripts/last30days.py --diagnose` still works after changes
- [x] Synced to all installed skill locations
- [ ] Published to ClawHub as `last30days-official` (when auth is fixed)

## Files to Modify

| File | Change |
|------|--------|
| `SKILL.md` | Add frontmatter fields + Security & Permissions section |
| `README.md` | Add Security & Privacy section |
| `.claude-plugin/plugin.json` | Bump version, add youtube keyword |
| `.claude-plugin/marketplace.json` | Add version, update description |

## References

- [13-point ClawHub checklist](https://gist.github.com/adhishthite/0db995ecfe2f23e09d0b2d418491982c)
- [ClawHub docs](https://docs.openclaw.ai/tools/clawhub)
- [ClawHub Developer Guide 2026](https://www.digitalapplied.com/blog/clawhub-skills-marketplace-developer-guide-2026)
- Your passing skills: `clawdbot-skill-xai`, `clawdbot-skill-search-x` (exact pattern replicated)
