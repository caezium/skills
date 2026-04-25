---
title: "feat: Add Gemini CLI extension support"
type: feat
status: completed
date: 2026-03-08
origin: docs/plans/2026-03-08-review-pr-53-gemini-cli-support-plan.md
---

# feat: Add Gemini CLI Extension Support

## Overview

Add Gemini CLI compatibility to last30days by cherry-picking the good parts from PR #53 (@alexferrari88) and fixing the implementation problems ourselves. Close PR #53 with a thank-you comment crediting the contributor.

Based on the review at `docs/plans/2026-03-08-review-pr-53-gemini-cli-support-plan.md`, we accept the concept but fix the approach to match our "one SKILL.md for all platforms" convention established during Codex compatibility work.

## What We Take from PR #53

| Component | Source | Changes Needed |
|-----------|--------|----------------|
| `gemini-extension.json` | PR #53 | Fix settings format (array, not object), bump version to 2.9.5 |
| Path resolution (for loop) | PR #53 | Take as-is, add to both SKILL.md and variants/open/SKILL.md |
| README.md install section | PR #53 | Take as-is |

## What We Skip from PR #53

| Component | Reason |
|-----------|--------|
| `skills/last30days/SKILL.md` (693-line copy) | Duplicate maintenance nightmare - use symlink instead |
| "or" tool name scattering in SKILL.md | LLMs translate tool intent natively - clutters prompt |
| Gemini tool names in `allowed-tools` | Gemini ignores `allowed-tools`; risks breaking Claude Code |

## Implementation Steps

### 1. Create `gemini-extension.json` (new file)

Based on PR #53 but with correct settings format (array per Gemini CLI docs) and v2.9.5 version.

```json
{
  "name": "last30days-skill",
  "version": "2.9.5",
  "description": "Research a topic from the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, and the web.",
  "settings": [
    {
      "name": "Extension Directory",
      "description": "Extension installation directory (auto-set by Gemini CLI)",
      "envVar": "GEMINI_EXTENSION_DIR",
      "sensitive": false
    },
    {
      "name": "ScrapeCreators API Key",
      "description": "ScrapeCreators API Key for Reddit, TikTok, and Instagram search (required)",
      "envVar": "SCRAPECREATORS_API_KEY",
      "sensitive": true
    },
    {
      "name": "OpenAI API Key",
      "description": "OpenAI API Key - optional fallback for Reddit discovery",
      "envVar": "OPENAI_API_KEY",
      "sensitive": true
    },
    {
      "name": "xAI API Key",
      "description": "xAI API Key for X/Twitter search (optional)",
      "envVar": "XAI_API_KEY",
      "sensitive": true
    },
    {
      "name": "OpenRouter API Key",
      "description": "OpenRouter API Key (optional)",
      "envVar": "OPENROUTER_API_KEY",
      "sensitive": true
    },
    {
      "name": "Parallel AI API Key",
      "description": "Parallel AI API Key (optional)",
      "envVar": "PARALLEL_API_KEY",
      "sensitive": true
    },
    {
      "name": "Brave Search API Key",
      "description": "Brave Search API Key (optional)",
      "envVar": "BRAVE_API_KEY",
      "sensitive": true
    },
    {
      "name": "Apify API Token",
      "description": "Apify API Token (optional legacy)",
      "envVar": "APIFY_API_TOKEN",
      "sensitive": true
    },
    {
      "name": "Twitter AUTH_TOKEN",
      "description": "Twitter browser AUTH_TOKEN cookie for direct X search (optional)",
      "envVar": "AUTH_TOKEN",
      "sensitive": true
    },
    {
      "name": "Twitter CT0",
      "description": "Twitter browser CT0 cookie (optional, pair with AUTH_TOKEN)",
      "envVar": "CT0",
      "sensitive": true
    }
  ]
}
```

### 2. Create `skills/last30days/SKILL.md` as symlink

```bash
mkdir -p skills/last30days
ln -s ../../SKILL.md skills/last30days/SKILL.md
```

Gemini CLI discovers skills from `skills/<name>/SKILL.md`. Symlink ensures single source of truth - no drift, no duplicate maintenance. Git tracks symlinks natively on macOS/Linux (Gemini CLI's target platforms).

### 3. Add Gemini paths to SKILL.md for-loop (line ~172)

Add these 3 entries after `"${CLAUDE_PLUGIN_ROOT:-}"`:

```bash
"${GEMINI_EXTENSION_DIR:-}" \
"$HOME/.gemini/extensions/last30days-skill" \
"$HOME/.gemini/extensions/last30days" \
```

### 4. Add same Gemini paths to `variants/open/SKILL.md` for-loop

Same 3 entries, same position.

### 5. Update `README.md` install section

Add Gemini CLI install before existing Claude Code section:

```markdown
### Gemini CLI
\`\`\`bash
gemini extensions install https://github.com/mvanhorn/last30days-skill.git
\`\`\`

### Claude Code / Codex
```

### 6. Close PR #53 with credit

Post comment thanking @alexferrari88, explaining we incorporated their work with modifications, and close the PR. Credit them in the commit message.

## Acceptance Criteria

- [ ] `gemini-extension.json` exists with correct array-format settings
- [ ] `skills/last30days/SKILL.md` is a symlink to `../../SKILL.md`
- [ ] Gemini path entries in SKILL.md for-loop (3 new entries)
- [ ] Gemini path entries in variants/open/SKILL.md for-loop (3 new entries)
- [ ] README.md has Gemini CLI install instructions
- [ ] No changes to `allowed-tools` in any SKILL.md
- [ ] No "or" tool name alternatives in any SKILL.md body
- [ ] Claude Code still works (`/last30days` runs normally)
- [ ] PR #53 closed with credit to @alexferrari88
- [ ] Commit message credits @alexferrari88 as co-author

## Confidence Assessment

**High confidence.** All changes are additive:
- New file (gemini-extension.json) - zero conflict risk
- Symlink (skills/last30days/SKILL.md) - zero conflict risk
- 3 lines added to a for-loop - trivially safe, short-circuits on first match
- README addition - simple text
- No changes to SKILL.md content, allowed-tools, or Python scripts
- No changes that could break existing Claude Code behavior

The only untested aspect is whether Gemini CLI correctly follows the symlink for skill discovery. If symlinks cause issues, fallback is a 2-line SKILL.md stub that imports the root (but this is unlikely - Gemini CLI runs on macOS/Linux where symlinks are native).

## Sources

- PR #53: https://github.com/mvanhorn/last30days-skill/pull/53
- Issue #45: https://github.com/mvanhorn/last30days-skill/issues/45
- Gemini CLI extension reference (settings array format confirmed): https://geminicli.com/docs/extensions/reference/
- Gemini CLI skills docs: https://geminicli.com/docs/cli/creating-skills/
- Review plan: `docs/plans/2026-03-08-review-pr-53-gemini-cli-support-plan.md`
