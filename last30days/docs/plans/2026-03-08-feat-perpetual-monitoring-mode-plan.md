---
title: "feat: Perpetual Monitoring Mode"
type: feat
status: active
date: 2026-03-08
---

# Perpetual Monitoring Mode

## Overview

Add a "perpetual monitoring" mode to last30days that lets users track topics over time with cumulative intelligence, delta reporting, and effortless re-runs. Designed for Claude Code's session model - not server cron.

**User signal:** @JTDaly asked "Can your skill be used to do this perpetually?" in response to a Perplexity AI S&P 500 earnings dashboard that auto-refreshes quarterly.

## Problem Statement

last30days is one-shot: ask, get a briefing, done. But the most valuable research is longitudinal - how conversations evolve, when new voices enter, when engagement spikes. Users want "set it and watch" without re-prompting from scratch every time.

## The Scheduling Reality in Claude Code

| Mechanism | Persistence | Max Duration | Fires When |
|-----------|------------|-------------|------------|
| **CronCreate / `/loop`** | Session-only (RAM) | 3 days, auto-expires | REPL idle |
| **System cron/launchd** | Permanent | Forever | Always |
| **SQLite watchlist** | Permanent (disk) | Forever | On demand |

**Key insight:** Don't build a scheduler. Build a **stateful watchlist** that composes with Claude Code's existing `/loop` for in-session automation, and survives across sessions via SQLite for manual re-runs. The `/loop` skill already exists and does scheduling perfectly - just make last30days a good citizen of it.

## What Already Exists

| Component | File | Status |
|-----------|------|--------|
| Topic CRUD + schedule fields | `scripts/watchlist.py` | Working |
| SQLite persistence with URL dedup, sighting counts | `scripts/store.py` | Working |
| Daily/weekly briefing generation | `scripts/briefing.py` | Working |
| Budget tracking (daily cap) | `scripts/store.py` | Working |
| FTS5 full-text search | `scripts/store.py` | Working |
| WAL mode for concurrent access | `scripts/store.py` | Working |
| `delivery_channel` setting in DB | `scripts/store.py` | Schema only |
| SKILL.md watchlist commands | `SKILL.md` | Missing |

## Proposed Solution

### The Composable Pattern

Instead of building scheduling into last30days, make last30days composable with Claude Code's existing tools:

```
# One-shot: research a topic and store findings
/last30 "S&P 500 earnings" --watch

# See what's new since last run (delta briefing)
/last30 briefing

# Automate with /loop (Claude Code native, session-scoped, 3-day max)
/loop 4h /last30 briefing

# Next session? Watchlist persists. Just re-loop or run manually.
/last30 briefing
```

The user's watchlist lives in SQLite forever. The scheduling is ephemeral by design - you opt into it each session. This matches how people actually use Claude Code: sessions, not servers.

### Phase 1: Watchlist + Briefing via SKILL.md (MVP)

Wire up the existing `watchlist.py` and `briefing.py` infrastructure through the skill interface.

**Tasks:**

- [ ] **SKILL.md additions** - New command branches:
  - `/last30 watch add "topic"` - Add topic to watchlist, run initial research with `--store`
  - `/last30 watch list` - Show watched topics with last-run timestamps and finding counts
  - `/last30 watch remove "topic"` - Remove from watchlist
  - `/last30 briefing` - Generate delta briefing across all watched topics (what's new)
  - `/last30 briefing --weekly` - Weekly digest with trend analysis
  - `/last30 "topic" --watch` - One-shot research that also adds to watchlist

- [ ] **`watchlist.py` updates:**
  - `run-all` auto-adds `--store` flag so results persist
  - `run-all` returns structured JSON (exit code + summary) for `/loop` consumption
  - `run-one` returns per-topic summary for composability
  - Add `--quick` default for watched topics (save API cost on recurring runs)

- [ ] **`briefing.py` updates:**
  - `generate` outputs compact format suitable for Claude synthesis (like main script's `--emit=compact`)
  - Include "last run" timestamp per topic so user knows freshness
  - Flag stale topics (not updated in 48+ hours)

**Acceptance criteria:**
- [ ] `/last30 watch add "AI earnings"` persists topic and runs initial research
- [ ] `/last30 briefing` shows accumulated findings with "new since last briefing" markers
- [ ] `/loop 4h /last30 briefing` works out of the box (composability)
- [ ] Watchlist survives across Claude Code sessions (SQLite)
- [ ] Budget cap enforced (default $5/day)

### Phase 2: Delta Intelligence

Make briefings show what *changed*, not just what exists.

**Tasks:**

- [ ] **`scripts/lib/delta.py`** (~150 lines):
  - New findings since last briefing (URLs with `first_seen > last_briefing_time`)
  - Engagement spikes (>2x increase in score since last sighting)
  - New voices (new @handles appearing for first time in a topic)
  - Gone quiet (topics with no new findings in 2+ runs)

- [ ] **`briefing.py` delta integration:**
  - Section: "Breaking" - high engagement + first seen this run
  - Section: "Trending" - engagement increasing across runs
  - Section: "New voices" - handles not seen before
  - Section: "Gone quiet" - previously active, now silent

- [ ] **Smart re-run logic in `watchlist.py`:**
  - Skip topics that were updated < 4 hours ago (avoid redundant API calls)
  - Prioritize topics with most engagement change potential
  - `--force` flag to override skip logic

**Acceptance criteria:**
- [ ] Briefings clearly distinguish new vs. previously-seen findings
- [ ] Engagement spikes flagged with specific metric ("upvotes 2.3x since yesterday")
- [ ] Redundant API calls avoided via smart skip logic

### Phase 3: Delivery + `/loop` Integration

Make the monitoring truly hands-off during a session.

**Tasks:**

- [ ] **Slack delivery** (`scripts/lib/deliver.py` ~100 lines):
  - Webhook URL config: `watchlist.py config delivery slack --webhook "https://..."`
  - Format briefing as Slack Block Kit (topic sections, trend indicators)
  - Auto-deliver after `run-all` if webhook configured

- [ ] **`/last30 monitor` convenience command:**
  - Shorthand that does: `run-all` + `briefing` + starts `/loop` automatically
  - Prints: "Monitoring 5 topics every 4h. Auto-expires in 3 days. Run `/last30 monitor` again next session."
  - Uses CronCreate directly (no `/loop` dependency) for tighter control

- [ ] **Session resume hint:**
  - On `/last30 briefing`, if watchlist has topics but no `/loop` active, suggest:
    "You have 5 watched topics. Run `/loop 4h /last30 briefing` to auto-refresh, or `/last30 monitor` for hands-off mode."

**Acceptance criteria:**
- [ ] Slack webhook delivery works end-to-end
- [ ] `/last30 monitor` starts automated loop with one command
- [ ] Clear messaging about 3-day session limit and how to resume

## Architecture: Why This Is Better Than Server Cron

```
Traditional approach (rejected):
  System Cron -> watchlist.py run-all -> SQLite -> ??? deliver somehow

Claude Code-native approach:
  /last30 watch add "topic"   --> SQLite (persists forever)
  /loop 4h /last30 briefing   --> CronCreate (session, 3-day max)
       |
       v
  Claude reads briefing.py output
  Claude synthesizes with LLM judgment
  Claude delivers via Slack webhook
  Claude answers follow-up questions in context
```

The Claude Code-native approach is better because:
1. **LLM synthesis on every run** - not just raw data, but judgment ("this is unusual because...")
2. **Conversational** - user can ask follow-ups ("tell me more about the META earnings spike")
3. **Zero infrastructure** - no plist, no crontab, no daemon management
4. **Portable** - works on any OS where Claude Code runs
5. **Composable** - `/loop` is a general-purpose tool, not custom scheduling code

## Alternative Approaches Considered

### 1. Build custom scheduler.py with system cron/launchd
**Rejected.** Doesn't work in Claude Code's model. Platform-specific. Requires root/sudo for some configs. Users of a Claude Code skill shouldn't need to manage system daemons.

### 2. OpenClaw's persistent cron service
**Not applicable.** OpenClaw has its own cron system with database-backed scheduling, but last30days is an open-source skill that should work without OpenClaw. Could be an optional integration later.

### 3. Long-running Python daemon
**Rejected.** Fragile, wastes resources, doesn't benefit from LLM synthesis on each run.

### 4. Web dashboard with its own backend
**Deferred to Phase 4.** Dramatically increases scope. The briefing-to-Slack pattern delivers 80% of the value with 10% of the effort.

## Technical Considerations

**No new services.** Pure Python scripts + SQLite + SKILL.md instructions. Zero infrastructure.

**Cost control.** Each watched topic costs ~$0.05-0.30/run at `--quick` depth. 10 topics x 6 runs/day = $3-18/day. Budget cap in store.py already enforces limits.

**Composability contract.** `briefing.py generate` must output clean, parseable text that Claude can synthesize. No interactive prompts, no side effects beyond SQLite writes.

**Backwards compatibility.** All new. Existing `/last30 topic` unchanged. `--watch` flag is opt-in.

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Users expect "perpetual" to mean forever | High | Clear messaging: "3-day auto-expire per session, watchlist persists, re-run next session" |
| `/loop` changes or breaks | Low | Composability means we don't depend on `/loop` internals - just CronCreate |
| Budget overrun with many topics | Low | Budget cap already implemented in store.py |
| SQLite grows large over months | Low | Add 90-day retention policy |
| Slack webhook stops working | Low | Log failures, don't block pipeline, alert in next briefing |

## Success Metrics

- User can go from zero to monitoring in one command: `/last30 "S&P 500 earnings" --watch`
- `/last30 briefing` surfaces genuinely new information with delta markers
- The system composes cleanly with `/loop` - no special integration needed
- Watchlist persists across sessions - user picks up where they left off
- Clear, honest UX about session limits vs. persistent state

## Scope Boundaries

**In scope:**
- Watchlist CRUD via SKILL.md
- Delta-aware briefings
- `/loop` composability (not custom scheduling)
- Slack webhook delivery
- `/last30 monitor` convenience command

**Out of scope:**
- System cron/launchd integration
- Web dashboard
- Email delivery (Slack webhook is simpler, covers most users)
- Multi-user / team features
- Custom NLP beyond what exists

## Implementation Estimate

- Phase 1 (Watchlist + Briefing): SKILL.md additions, minor `watchlist.py` and `briefing.py` updates
- Phase 2 (Delta Intelligence): New `delta.py` module, `briefing.py` integration
- Phase 3 (Delivery + Monitor): New `deliver.py`, SKILL.md `/last30 monitor` command

Each phase ships independently. Phase 1 alone answers @JTDaly's question.
