# Skills

Personal directory of agent skills, layout inspired by [mattpocock/skills](https://github.com/mattpocock/skills).

Each skill lives in its own folder with a `SKILL.md` (frontmatter: `name`, `description`) plus any supporting markdown the skill loads via progressive disclosure. The `commands/` folder holds slash-command prompts (single-file, not full skills).

## Layout

```
~/skills/
├── <skill-name>/SKILL.md       # one folder per skill
├── commands/*.md               # slash commands (not skills)
├── skills.lock.json            # source pins, content hashes, and local overlays
├── bin/sync.sh                 # offline symlink helper for local agent harnesses
├── bin/check-skill-updates.sh  # read-only integrity and upstream-drift audit
├── bin/fast-forward-skills.sh  # explicit clean-checkout update helper
└── README.md
```

## Skills

### Planning & Design

- **consult-first** — Surface the unsettled product and design decisions and get a ruling before freezing them into a deliverable.
- **design-an-interface** — Generate multiple radically different interface designs for a module using parallel sub-agents.
- **grill-me** — Get relentlessly interviewed about a plan or design until every branch is resolved.
- **grilling** — Stress-test a plan before building; triggers on any "grill" phrasing.
- **grill-with-docs** — The same relentless interview, but it writes the ADRs and glossary as it goes.
- **domain-modeling** — Pin down a project's ubiquitous language and record architectural decisions.
- **write-a-prd** — Create a PRD through user interview, codebase exploration, and module design, then submit as a GitHub issue.
- **prd-to-plan** — Turn a PRD into a multi-phase implementation plan using tracer-bullet vertical slices.
- **prd-to-issues** — Break a PRD into independently-grabbable GitHub issues using vertical slices.
- **request-refactor-plan** — Create a detailed refactor plan with tiny commits via user interview, then file as a GitHub issue.
- **triage-issue** — Investigate a bug by exploring the codebase, identify root cause, and file a GitHub issue with a TDD-based fix plan.
- **to-spec** — Turn the current conversation into a spec on the issue tracker — synthesis, no interview.
- **to-tickets** — Break a plan or conversation into tracer-bullet tickets, each declaring its blocking edges.
- **wayfinder** — Navigate a large, foggy effort by resolving decision tickets before pretending the work is implementable.
- **prototype** — Build disposable runnable prototypes to answer consequential design or technical questions.
- **throughline** — Publish an implementation plan as a live HTML URL the user can read on their phone, with a Markdown/JSON handoff.

### Development

- **tdd** — Test-driven development with red-green-refactor loop.
- **implement** — Build a piece of work from an approved spec or set of tickets.
- **code-review** — Review changes since a fixed point along two axes at once: repo coding standards and the originating spec.
- **diagnosing-bugs** — Reproduce, minimize, hypothesize, instrument, fix, and regression-test difficult failures.
- **codebase-design** — Design deep modules with small interfaces, hidden complexity, and testable boundaries.
- **clone-site** — Clone any URL into a pixel-faithful Next.js codebase: asset/CSS extraction, parallel section builders, animation porting, fidelity verification.
- **tldraw-offline** — Drive the offline tldraw canvas app: inspect, edit, arrange, connect, lint, and script `.tldraw` files.
- **improve-codebase-architecture** — Find deepening opportunities, informed by domain language and ADRs.
- **scaffold-exercises** — Create exercise directory structures with sections, problems, solutions, and explainers.
- **make-interfaces-feel-better** — Design engineering principles for polished interfaces (animations, hover states, typography, micro-interactions).
- **ui-skills** — Opinionated constraints for building better interfaces with agents.
- **superdesign** — Frontend UI/UX design agent for design thinking before implementation.
- **prune** — Audit a codebase for dead code, duplication, and cruft, then safely remove what no longer earns its place.
- **qa** — Interactive QA session: report bugs conversationally while the agent files GitHub issues with codebase context.
- **triage** — Triage a bug or issue to root cause, then plan a TDD-based fix.
- **blast-radius** — Prove the runtime safety fact most likely to fail when a change crosses boundaries.
- **create-verification-skill** — Build a reusable project-local feature map and live verification recipe.
- **maintain-verification-skill** — Update a project's verification skill as its surfaces and workflows drift.
- **swarm** — Run isolated parallel agents with a coverage matrix, resource budget, output contracts, and a root aggregator.
- **interrogate** — Run an adversarial multi-agent review panel against an implementation, plan, or claim.
- **app-screenshots** — Capture and curate screenshots of a GUI desktop app for a README, landing page, or docs.
- **nib** — Turn an idea or article into original hand-drawn editorial illustrations starring a recurring avatar you own.
- **clipsmith** — Plan and run a custom video-editing pipeline from a plain-language brief: highlight reels, jump-cuts, captions, beat-synced and vertical edits.

### Platform & Operations

- **cloudflare** — Comprehensive Cloudflare platform guidance with current-reference routing.
- **agents-sdk** — Build stateful agents, workflows, realtime apps, and MCP servers on Cloudflare Workers.
- **durable-objects** — Create and review Durable Objects, including RPC, SQLite, alarms, WebSockets, and tests.
- **workers-best-practices** — Author and review production Workers code against current platform practices.
- **wrangler** — Use the Wrangler CLI across Workers, storage, AI, queues, workflows, and containers.
- **cloudflare-email-service** — Build transactional sending and inbound routing with Cloudflare Email Service.
- **sandbox-stable** — Build against the current stable Cloudflare Sandbox package without mixing preview APIs.
- **sandbox-next** — Build new Sandbox SDK 1.0-preview apps on the matching `@next` package and image.
- **sandbox-migrate-to-next** — Port a stable Sandbox app to the 1.0 preview with explicit cutover checks.
- **web-perf** — Audit Core Web Vitals and diagnose browser performance with Chrome DevTools.

### Apple Platforms

- **swiftui-expert-skill** — SwiftUI state and `@Observable` data flow, view invalidation and performance, `ForEach` identity, Liquid Glass adoption, and Instruments `.trace` analysis.
- **app-store-preflight-compliance** — Scan an iOS/macOS/tvOS/watchOS/visionOS project for App Store rejection risks before you submit.

### Frontend Best Practices

- **vue-best-practices** — Vue 3 + TypeScript best practices, tooling, testing, composition API gotchas.
- **vueuse-best-practices** — VueUse composable patterns and TypeScript integration.
- **pinia-best-practices** — Pinia store TypeScript configuration and typing issues.

### Design & Taste

From [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) and [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (both MIT):

- **design-taste-frontend** — Anti-slop frontend skill for landing pages, portfolios, and redesigns; infers the right design direction and ships non-templated interfaces.
- **design-taste-frontend-v1** — The original v1 taste skill, preserved for backward compatibility.
- **gpt-taste** — Elite UX/UI + GSAP motion skill: AIDA structure, wide editorial type, bento grids, scroll-driven motion.
- **high-end-visual-design** — High-end visual design: the exact fonts, spacing, shadows, and animations that make a site feel expensive.
- **minimalist-ui** — Clean editorial interfaces: warm monochrome, typographic contrast, flat bento grids, no gradients.
- **industrial-brutalist-ui** — Raw industrial-brutalist UI: rigid grids, extreme type contrast, analog degradation, declassified-blueprint feel.
- **brandkit** — Premium brand-kit image generation: logo systems, identity decks, and visual-world boards.
- **stitch-design-taste** — Generate agent-friendly DESIGN.md files enforcing premium, anti-generic UI standards (for Google Stitch).
- **redesign-existing-projects** — Upgrade existing sites/apps to premium quality; audit generic AI patterns and fix without breaking functionality.
- **image-to-code** — Image-to-code for Codex: generate the design image, analyze it, then build the site to match.
- **imagegen-frontend-web** — Generate premium per-section website design reference images (one image per section).
- **imagegen-frontend-mobile** — Generate premium app-native mobile screen concepts and flows inside phone mockups.
- **full-output-enforcement** — Override LLM truncation: enforce complete, unabridged code output and ban placeholders.
- **awesome-design-md** — A library of 74 real-brand DESIGN.md design systems (Stripe, Apple, Vercel, Linear, …) to match a brand's look.

### Tooling & Setup

- **git-guardrails-claude-code** — Set up Claude Code hooks to block dangerous git commands.
- **create-rule** — Cursor: create a new project rule.
- **create-skill** — Cursor: scaffold a new skill.
- **create-subagent** — Cursor: scaffold a new subagent.
- **migrate-to-skills** — Cursor: migrate existing rules into skills.
- **update-cursor-settings** — Cursor: modify Cursor settings.
- **shell** — Cursor: shell command helper.
- **install-skill** — Install a freshly authored skill into the repo, symlink it into the agent dirs, and commit + push.
- **writing-great-skills** — Reference for writing and editing skills well: the vocabulary and principles that make a skill predictable.
- **setup-matt-pocock-skills** — One-time repo setup for the engineering skills: issue tracker, triage label vocabulary, domain doc layout.
- **defuddle** — Extract clean markdown from web pages, stripping clutter and navigation to save tokens.
- **dayflow-sync** — Sync the caezium/Dayflow fork with upstream: rebase, audit, build, and stop for a pre-install checkpoint.
- **stats-sync** — Sync the caezium/stats fork with upstream: rebase, audit, test, build, and stop before install.
- **dayflow-pull** — Read Dayflow's local database and compute accurate overlap-merged work hours.
- **vista-dashboard** — Publish live agent status into the local Vista dashboard.
- **burrow-system-tools** — Diagnose local macOS health and performance through Burrow's MCP tools.

### Writing & Knowledge

- **find-docs** — Retrieve authoritative, up-to-date technical documentation for any developer technology.
- **find-skills** — Discover and install agent skills.
- **anthropic-skill-creator** — Create, modify, and benchmark portable or Claude-oriented skills with Anthropic's eval workflow; Codex keeps its own managed `skill-creator`.
- **writing-for-agents** — Write briefs, pointer docs, acceptance contracts, and context that independent agents can execute reliably.
- **obsidian-vault** — Search, create, and manage notes in an Obsidian vault.
- **obsidian-cli** — Interact with Obsidian vaults via the CLI; also plugin/theme development and debugging.
- **obsidian-markdown** — Author Obsidian Flavored Markdown: wikilinks, embeds, callouts, properties.
- **obsidian-bases** — Create and edit Obsidian Bases (.base) with views, filters, formulas, and summaries.
- **obsidian-convert** — Convert PDFs/DOCX into Obsidian markdown notes, preserving content verbatim.
- **json-canvas** — Create and edit JSON Canvas (.canvas) files: nodes, edges, groups, mind maps, flowcharts.
- **vault-resync** — Re-pull every external capture source (Feishu, WeChat, Zen tabs, live Claude sessions) into the Obsidian inbox and refresh the Command Center dashboards.
- **chatlog** — Query your own WeChat (微信) history through the local chatlog HTTP API.

### Research & Reporting

- **last30days** — Deep research engine covering the last 30 days across 10+ sources.
- **research** — Produce durable, cited technical-research artifacts from primary sources.
- **digest** — Aggregate top RSS feeds into a daily tech recap.
- **nvidia-kaggle-skill** — Kaggle competition research and submission workflow: overview fetches, writeups, discussion/kernel mining, and dataset uploads.
- **kaggle-grind** — Run a CV-first, OOF-driven, resume-safe Kaggle competition loop with honest acceptance gates.

### Session & Output

Skills that shape the conversation itself rather than the code. `playbook`, `handoff`, `i-have-adhd`, and `bro` are `/`-invoked only (`disable-model-invocation: true`), so they never fire on their own:

- **recap** — Consolidate everything that changed this session into one authoritative message plus a hand-test checklist.
- **playbook** — Pick the right ordered sequence of skills for the job, announce it, and name the next one after each stage.
- **handoff** — Compact the current conversation into a handoff document for another agent to pick up.
- **henry-mode** — Route long-running cross-session work through recall, consultation, proof, swarms, evidence trails, and reflection.
- **recall** — Reconstruct relevant work across Claude, Codex, backups, and current repository state.
- **show-me-your-work** — Keep a durable decision, evidence, dead-end, and recovery trail during expensive or autonomous work.
- **reflect** — Turn surprising or costly work into a reviewed test, script, rule, skill, or architectural improvement.
- **i-have-adhd** — Lead with the next action, number multi-step work, restate state, suppress tangents. Stays on until "stop adhd mode".
- **bro** — Restate the last message in plain human language, no jargon.

### Engineering Principles

Portable principles adapted from pstack and used by `henry-mode`:

- **principle-prove-it-works** — Treat runtime evidence, not confidence or proxies, as the completion condition.
- **principle-guard-the-context-window** — Delegate exploration and return compact conclusions plus artifact pointers.
- **principle-build-the-lever** — Prefer a rerunnable tool or harness over repeated one-off labor.
- **principle-sequence-verifiable-units** — Decompose work into independently provable units that leave useful state.

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
- **dialectic-digest** — Generate a dialectic digest. Has no `SKILL.md`; the `dialectic-digest/` folder holds its prompt and example output.
- **rams** — Run accessibility and visual design review.
- **ui-skills** — Apply UI skills constraints.
- **update-skills-map** — Refresh and validate the full installed-skills map; optionally publish its snapshot.
- **web-interface-guidelines** — Review UI code against Vercel Web Interface Guidelines.

## Generated skills site

[skills.henryzh.dev](https://skills.henryzh.dev) has two generated views:

- The catalog reads every top-level `SKILL.md` in this repository and provides
  a detail page for each personal skill.
- The production map combines that repository with a local snapshot of shared
  agent, Codex, and plugin skills, then organizes the full installed inventory
  by use case and shows the recommended idea-to-production sequence.

Refresh the full-machine snapshot and verify the site locally:

```sh
bin/update-skills-map.sh
```

Pass `--push` to commit and push only the generated snapshot. The standard
`install-skill` workflow refreshes the snapshot before its normal skill commit.
GitHub Actions validates site changes on pull requests, rebuilds on every push
to `main`, and performs a scheduled rebuild each Monday.

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

### Codex and other agents

Codex reads user skills from `~/.agents/skills/`. Link the repo there so the
same canonical skill directories are shared without copied installs:

```sh
bin/sync.sh agents
```

### Other agents (Aider, Continue, Cline, Codex)

The markdown content ports anywhere, only the discovery path differs:

| Agent | Discovery path | How to wire |
|---|---|---|
| Aider | `CONVENTIONS.md` at repo root, or `~/.aider.conf.yml` `read:` list | Concatenate selected `SKILL.md` bodies into one file |
| Continue | `~/.continue/config.json` (`systemMessage` or `customCommands`) | Reference per-skill content as custom commands |
| Cline | `.clinerules` per-repo | Same as Aider — concatenate or selectively include |
| OpenAI Codex | `~/.agents/skills/<skill-name>/SKILL.md` | Run `bin/sync.sh agents` |

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

This is a personal aggregator of Henry-authored skills and reviewed third-party packages. `skills.lock.json` records each skill's source, pinned upstream commit when known, content hash, state, and any local portability overlay. Third-party license texts live in `licenses/`, while packages that require their own license retain it in the skill directory. The main tracked sources include `mattpocock/skills`, pstack from `cursor/plugins`, Cloudflare's skills, `last30days`, Anthropic's skill creator, `Leonxlnx/taste-skill`, and `VoltAgent/awesome-design-md`.

Two legacy sources do not publish a standard license: `er1chu/claude-skills-weekly` (the six weekly-workflow skills) and `dmmulroy/.dotfiles` (`bro`). Their attribution and exact provenance are retained, but this remains license debt: seek explicit permission or replace them before redistributing the repository beyond personal use.

An upstream advance is a review signal, not an automatic overwrite: refresh the complete affected package, reapply and document intentional overlays, validate it, update the pin and hashes atomically, then commit the package and lock together.

## Global config and update flow

`config/CLAUDE.md` is the canonical global `~/.claude/CLAUDE.md`, and `config/AGENTS.md` is the canonical global `~/.codex/AGENTS.md`. `bin/sync.sh all` links those files plus every canonical skill into Claude, Cursor, and shared-agent discovery. The command is deterministic and offline: it never fetches, commits, merges, or pushes, and it preserves real-file collisions for explicit review.

On either machine, use this order:

```sh
~/skills/bin/fast-forward-skills.sh
~/skills/bin/check-skill-updates.sh
~/skills/bin/sync.sh all
```

The fast-forward helper only updates a clean `main` checkout when the remote is a strict descendant. The checker is read-only and reports source drift, content-hash drift, stale discovery links, and collisions. Review and vendor upstream changes on one machine, commit the package and lock together, then use the same three commands on the other machine. If a real global config already exists on a new machine, merge it into the tracked config before replacing it with a symlink.
