---
title: "feat: Publish last30days as Claude Code marketplace plugin"
type: feat
status: completed
date: 2026-03-08
---

# feat: Publish last30days as Claude Code Marketplace Plugin

## Overview

Publish the last30days skill as a Claude Code plugin so users can install it with:

```
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days@last30days-skill
```

This gives users auto-updates, versioned installs, and the standard plugin management UX instead of manual git clone.

## Current State

The repo already has most of what's needed:

| Component | Status | Notes |
|-----------|--------|-------|
| `SKILL.md` | Exists | Source of truth at repo root |
| `skills/last30days/SKILL.md` | Exists (symlink) | Points to root SKILL.md, added for Gemini CLI |
| `scripts/` | Exists | Python research engine |
| `gemini-extension.json` | Exists | Gemini CLI support |
| `.claude-plugin/marketplace.json` | **Missing** | Needed to make repo a marketplace |
| `.claude-plugin/plugin.json` | **Missing** | Needed (in plugin subdir) to define the plugin |
| `plugins/last30days/` | **Missing** | Plugin directory structure |

## How It Works (compound-engineering as reference)

The repo serves as BOTH a **marketplace** (distribution channel) and contains **plugins**:

```
repo-root/                          # = marketplace
├── .claude-plugin/
│   └── marketplace.json            # Makes repo discoverable as marketplace
└── plugins/
    └── plugin-name/                # = individual plugin
        ├── .claude-plugin/
        │   └── plugin.json         # Plugin manifest
        └── skills/
            └── skill-name/
                └── SKILL.md
```

## Implementation Plan

### 1. Create marketplace manifest

#### `.claude-plugin/marketplace.json`

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "last30days-skill",
  "description": "Research any topic from the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, and the web.",
  "owner": {
    "name": "Matt Van Horn",
    "url": "https://github.com/mvanhorn"
  },
  "plugins": [
    {
      "name": "last30days",
      "description": "Research any topic from the last 30 days. Become an expert and write copy-paste-ready prompts.",
      "version": "2.9.5",
      "author": {
        "name": "Matt Van Horn",
        "url": "https://github.com/mvanhorn"
      },
      "source": "./plugins/last30days",
      "category": "productivity",
      "homepage": "https://github.com/mvanhorn/last30days-skill"
    }
  ]
}
```

### 2. Create plugin directory

#### `plugins/last30days/.claude-plugin/plugin.json`

```json
{
  "name": "last30days",
  "version": "2.9.5",
  "description": "Research any topic from the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, and the web.",
  "author": {
    "name": "Matt Van Horn",
    "email": "mvanhorn@gmail.com",
    "url": "https://github.com/mvanhorn"
  },
  "homepage": "https://github.com/mvanhorn/last30days-skill",
  "repository": "https://github.com/mvanhorn/last30days-skill",
  "license": "MIT",
  "keywords": [
    "research",
    "reddit",
    "twitter",
    "youtube",
    "tiktok",
    "trends",
    "prompts"
  ]
}
```

### 3. Symlink skill and scripts into plugin directory

```bash
mkdir -p plugins/last30days/.claude-plugin
mkdir -p plugins/last30days/skills/last30days

# Symlink SKILL.md (single source of truth)
ln -s ../../../../SKILL.md plugins/last30days/skills/last30days/SKILL.md

# Symlink scripts directory (the Python engine)
ln -s ../../scripts plugins/last30days/scripts

# Symlink fixtures if needed
ln -s ../../fixtures plugins/last30days/fixtures
```

### 4. Update README with plugin install instructions

Add before the manual install section:

```markdown
### Plugin Install (recommended)
```
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days@last30days-skill
```

Then configure your API keys:
```bash
mkdir -p ~/.config/last30days
# Add SCRAPECREATORS_API_KEY to your env
```
```

### 5. Version bump workflow

When releasing new versions, update version in ALL manifests:
- `SKILL.md` frontmatter `version:`
- `gemini-extension.json` `version`
- `plugins/last30days/.claude-plugin/plugin.json` `version`
- `.claude-plugin/marketplace.json` plugins[0].version

Consider: a `scripts/bump-version.sh` that updates all four in one command.

## Open Question: Symlinks in Plugin Cache

**Risk:** When Claude Code installs a plugin, it clones the repo into `~/.claude/plugins/cache/`. Git preserves symlinks on macOS/Linux, so `plugins/last30days/skills/last30days/SKILL.md -> ../../../../SKILL.md` should resolve correctly because the full repo is cloned.

**Mitigation if symlinks fail:** Replace symlinks with a small build step in sync.sh that copies SKILL.md into the plugin directory. Or just copy the file and accept the duplication in the plugin directory (since the plugin cache is a read-only clone anyway - drift only matters in the source repo, not the installed copy).

**Test:** After implementing, verify with `git clone` into a temp dir and check symlink resolution.

## Acceptance Criteria

- [ ] `.claude-plugin/marketplace.json` exists with correct schema
- [ ] `plugins/last30days/.claude-plugin/plugin.json` exists
- [ ] `plugins/last30days/skills/last30days/SKILL.md` resolves to root SKILL.md
- [ ] `plugins/last30days/scripts` resolves to root scripts/
- [ ] README has plugin install instructions
- [ ] `/plugin marketplace add mvanhorn/last30days-skill` works
- [ ] `/plugin install last30days@last30days-skill` works
- [ ] `/last30days test topic` works after plugin install
- [ ] Standalone install (git clone to ~/.claude/skills/) still works
- [ ] Gemini CLI install still works

## User Experience After Publishing

```
# One-time setup
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days@last30days-skill

# Use it
/last30days AI video tools for business

# Auto-updates happen at startup when version bumps
```

## Sources

- Claude Code plugin docs: https://code.claude.com/docs/en/plugins
- Plugin reference: https://code.claude.com/docs/en/plugins-reference
- Marketplace docs: https://code.claude.com/docs/en/plugin-marketplaces
- compound-engineering reference: https://github.com/EveryInc/compound-engineering-plugin
- Your installed plugins: superpowers (4.3.1), swift-lsp (1.0.0), compound-engineering (2.38.1)
