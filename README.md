# Skills

Personal directory of agent skills, layout inspired by [mattpocock/skills](https://github.com/mattpocock/skills).

Each skill lives in its own folder with a `SKILL.md` (frontmatter: `name`, `description`) plus any supporting markdown the skill loads via progressive disclosure. The `commands/` folder holds slash-command prompts (single-file, not full skills).

## Layout

```
~/skills/
├── <skill-name>/SKILL.md       # one folder per skill
├── commands/*.md               # slash commands (not skills)
├── bin/sync.sh                 # symlink helper for Claude / Cursor
└── README.md
```

## Skills

### Planning & Design

- **design-an-interface** — Generate multiple radically different interface designs for a module using parallel sub-agents.
- **grill-me** — Get relentlessly interviewed about a plan or design until every branch is resolved.
- **write-a-prd** — Create a PRD through user interview, codebase exploration, and module design, then submit as a GitHub issue.
- **prd-to-plan** — Turn a PRD into a multi-phase implementation plan using tracer-bullet vertical slices.
- **prd-to-issues** — Break a PRD into independently-grabbable GitHub issues using vertical slices.
- **request-refactor-plan** — Create a detailed refactor plan with tiny commits via user interview, then file as a GitHub issue.
- **triage-issue** — Investigate a bug by exploring the codebase, identify root cause, and file a GitHub issue with a TDD-based fix plan.
- **throughline** — Publish an implementation plan as a live HTML URL the user can read on their phone, with a Markdown/JSON handoff.

### Development

- **tdd** — Test-driven development with red-green-refactor loop.
- **improve-codebase-architecture** — Find deepening opportunities, informed by domain language and ADRs.
- **scaffold-exercises** — Create exercise directory structures with sections, problems, solutions, and explainers.
- **make-interfaces-feel-better** — Design engineering principles for polished interfaces (animations, hover states, typography, micro-interactions).
- **ui-skills** — Opinionated constraints for building better interfaces with agents.
- **superdesign** — Frontend UI/UX design agent for design thinking before implementation.
- **prune** — Audit a codebase for dead code, duplication, and cruft, then safely remove what no longer earns its place.
- **qa** — Interactive QA session: report bugs conversationally while the agent files GitHub issues with codebase context.
- **triage** — Triage a bug or issue to root cause, then plan a TDD-based fix.
- **app-screenshots** — Capture and curate screenshots of a GUI desktop app for a README, landing page, or docs.
- **nib** — Turn an idea or article into original hand-drawn editorial illustrations starring a recurring avatar you own.

### Frontend Best Practices

- **vue-best-practices** — Vue 3 + TypeScript best practices, tooling, testing, composition API gotchas.
- **vueuse-best-practices** — VueUse composable patterns and TypeScript integration.
- **pinia-best-practices** — Pinia store TypeScript configuration and typing issues.

### Tooling & Setup

- **git-guardrails-claude-code** — Set up Claude Code hooks to block dangerous git commands.
- **create-rule** — Cursor: create a new project rule.
- **create-skill** — Cursor: scaffold a new skill.
- **create-subagent** — Cursor: scaffold a new subagent.
- **migrate-to-skills** — Cursor: migrate existing rules into skills.
- **update-cursor-settings** — Cursor: modify Cursor settings.
- **shell** — Cursor: shell command helper.
- **install-skill** — Install a freshly authored skill into the repo, symlink it into the agent dirs, and commit + push.
- **defuddle** — Extract clean markdown from web pages, stripping clutter and navigation to save tokens.
- **dayflow-sync** — Sync the caezium/Dayflow fork with upstream: rebase, audit, build, and stop for a pre-install checkpoint.
- **stats-sync** — Sync the caezium/stats fork with upstream: rebase, audit, test, build, and stop before install.

### Writing & Knowledge

- **find-docs** — Retrieve authoritative, up-to-date technical documentation for any developer technology.
- **find-skills** — Discover and install agent skills.
- **skill-creator** — Create, modify, and benchmark skills with optional eval suites.
- **obsidian-vault** — Search, create, and manage notes in an Obsidian vault.
- **obsidian-cli** — Interact with Obsidian vaults via the CLI; also plugin/theme development and debugging.
- **obsidian-markdown** — Author Obsidian Flavored Markdown: wikilinks, embeds, callouts, properties.
- **obsidian-bases** — Create and edit Obsidian Bases (.base) with views, filters, formulas, and summaries.
- **obsidian-convert** — Convert PDFs/DOCX into Obsidian markdown notes, preserving content verbatim.
- **json-canvas** — Create and edit JSON Canvas (.canvas) files: nodes, edges, groups, mind maps, flowcharts.
- **chatlog** — Query your own WeChat (微信) history through the local chatlog HTTP API.
- **dialectic-digest** — Generate a dialectic-style digest.

### Research & Reporting

- **last30days** — Deep research engine covering the last 30 days across 10+ sources.
- **digest** — Aggregate top RSS feeds into a daily tech recap.

### Productivity / Weekly

- **monday** — Monday morning setup: week folder, carry-forward, briefing.
- **friday** — End-of-week wrap-up for the weekly report.
- **week-prep** — Generate a briefing with calendar, tasks, and attention flags.
- **daily-roundup** — Morning briefing combining email, meetings, and Slack.
- **1-1-prep** — Prepare for a 1:1 with context from person file, meeting history, and shared projects.
- **decision-extractor** — Scan recent notes for decisions and offer to update Decision Logs.

## Slash commands (`commands/`)

Single-file prompts, dropped into `~/.claude/commands/` or `~/.cursor/commands/`:

- **council** — Run a question through 5 AI advisors who peer-review and synthesize a verdict.
- **dialectic-digest** — Generate a dialectic digest.
- **rams** — Run accessibility and visual design review.
- **ui-skills** — Apply UI skills constraints.
- **web-interface-guidelines** — Review UI code against Vercel Web Interface Guidelines.

## Wiring this into your agents

### Claude Code

Symlink each skill folder into `~/.claude/skills/`:

```sh
bin/sync.sh claude
```

Or manually:

```sh
ln -sfn ~/skills/<skill-name> ~/.claude/skills/<skill-name>
```

### Cursor

Cursor reads from `~/.cursor/skills/` (modern) and `~/.cursor/skills-cursor/` (Cursor-flavored tooling skills). Same symlink pattern:

```sh
bin/sync.sh cursor
```

### Other agents (Aider, Continue, Cline, Codex)

The markdown content ports anywhere, only the discovery path differs:

| Agent | Discovery path | How to wire |
|---|---|---|
| Aider | `CONVENTIONS.md` at repo root, or `~/.aider.conf.yml` `read:` list | Concatenate selected `SKILL.md` bodies into one file |
| Continue | `~/.continue/config.json` (`systemMessage` or `customCommands`) | Reference per-skill content as custom commands |
| Cline | `.clinerules` per-repo | Same as Aider — concatenate or selectively include |
| OpenAI Codex | `AGENTS.md` at repo root or `~/.codex/AGENTS.md` | Concatenate selected `SKILL.md` bodies |

The portable pattern: `SKILL.md` is the source of truth here; symlink (or generate via script) into each agent's expected location. MCP servers handle cross-agent *tool* portability, not prompted skills — so symlinking is the realistic answer for skills today.

## Skill format

```markdown
---
name: skill-name
description: One-line trigger description. Use when user mentions X, asks Y, or wants Z.
---

# Skill body

Instructions for the agent. Reference supporting files like [details.md](details.md) for progressive disclosure.
```

## Origins

Skills here come from a mix of sources — npx-installed (`mattpocock/skills`, `claude-skills-weekly`, `tech-digest`, `dialectic-digest`, `last30days`), Cursor's built-in tooling skills, and Anthropic's `skill-creator`. Each `SKILL.md` retains its original frontmatter for attribution. This repo is a personal aggregator, not a redistribution.
