---
title: "feat: last30days v2.6 - agent-native invocation"
type: feat
status: completed
date: 2026-03-02
---

# feat: last30days v2.6 - Agent-Native Invocation

## Overview

v2.5 shipped as a human-only interactive skill. Agents calling it today would hang forever at
"WAIT FOR USER RESPONSE" and never receive research output. v2.6 makes the skill fully
invocable by other agents - delivering a complete research report instead of an interactive
conversation.

The `disable-model-invocation: true` flag was removed in a hotfix today (2026-03-02). v2.6
formalizes that fix, addresses the deeper interactive-flow problem, and updates all
documentation to match reality.

## Problem Statement

### 1. The flag was removed but the behavior is still broken

Removing `disable-model-invocation: true` lets agents call the skill. But the skill still:

- Calls `AskUserQuestion` mid-flow (blocks, waits for a human to click something)
- Ends with "WAIT FOR USER RESPONSE" (the calling agent gets nothing)
- Assumes a human is reading progress text in real-time

When an agent calls `/last30days plaud granola`, it needs a **completed research report
returned to it**, not a half-executed interactive session.

### 2. The Security section has a false statement

Line 558 of SKILL.md still reads:

```
- Cannot be invoked autonomously by the agent (`disable-model-invocation: true`)
```

This is now wrong. It actively misleads users and agents reading the skill docs.

### 3. No documented path for agent callers

Users who want to call `last30days` from another skill (e.g., "research this topic and then
build a plan") have no guidance on how to do it or what format to expect back.

## Proposed Solution

### Agent Mode: `--agent` flag

Add an `--agent` execution mode that skips all interactive elements and returns a structured
research report. Calling agents pass the flag explicitly:

```
/last30days plaud granola --agent
```

### Agent Mode Behavior

In agent mode, the skill:

1. **Skips** the intro display block ("I'll research X across Reddit...")
2. **Skips** `AskUserQuestion` for target tool clarification
3. **Skips** the "WAIT FOR USER RESPONSE" pause
4. **Skips** the follow-up invitation ("I'm now an expert on X...")
5. **Outputs** a complete, structured report with all findings, then terminates cleanly

The report format for agent mode:

```
## Research Report: {TOPIC}
Generated: {date} | Sources: Reddit, X, YouTube, HN, Polymarket, Web

### Key Findings
[3-5 bullet points, highest-signal insights with citations]

### {Source} Results
[Compact per-source sections with top items]

### Stats
{The existing stats block}
```

### Security Section Rewrite

Remove the false statement. Replace with:

```
- Can be invoked autonomously by agents via the Skill tool (inline mode, not forked)
- Pass `--agent` flag for non-interactive report output
```

### Version Bump

`version: "2.5"` → `version: "2.6"` in SKILL.md frontmatter.

## Technical Considerations

### Implementation: SKILL.md instructions only

Add a section to SKILL.md that reads:
```
## Agent Mode (--agent flag)
If --agent is in ARGUMENTS: skip intro display, skip AskUserQuestion, skip invitation,
skip WAIT block. Output the full research report and stop.
```

No Python script changes needed. The script already outputs everything via `--emit=compact` -
the LLM just skips the interactive wrapper. If LLM instruction-following proves unreliable in
testing, a v2.6.1 patch adds `--agent` natively to `last30days.py` (Python flag approach).

## Acceptance Criteria

- [x] `disable-model-invocation: true` is gone from SKILL.md (done in hotfix - verify)
- [x] Security section no longer claims the skill cannot be invoked autonomously
- [x] SKILL.md documents the `--agent` flag and its behavior
- [x] In `--agent` mode: no AskUserQuestion calls, no WAIT block, full report output
- [x] Version is `2.6` in frontmatter
- [x] Synced to all 4 destinations via `sync.sh`
- [ ] Manual test: `Skill { skill: "last30days", args: "plaud granola --agent" }` returns
  a complete research report without hanging

## Implementation Steps

1. **Verify hotfix** - confirm `disable-model-invocation` is gone in private source
2. **Edit SKILL.md** - update Security section, add Agent Mode section, bump version
3. **Run sync.sh** - deploy to `~/.claude`, `~/.agents`, `~/.codex`
4. **Test** - invoke via Skill tool and verify report returns cleanly

All changes are in `SKILL.md` only. No Python changes needed for v2.6.

## Dependencies & Risks

**No script changes** - this is a pure SKILL.md update. Low risk.

**LLM instruction-following** - agent mode relies on the LLM reading and following the
`--agent` section. If testing shows it's unreliable, escalate to Option B (Python flag)
as a v2.6.1 patch.

**Skill list refresh** - after sync, Claude Code needs to restart or reload skills to see
the updated frontmatter. Users on older Claude Code versions may still see the old flag.

## Distribution Note

For users who installed from the public repo, they need to pull the update. The sync script
handles local installations. For `last30daysCROSS` variant, the same changes apply.

## Sources & References

- [fix-skill-execution-fork-mode-plan.md](./2026-02-06-fix-skill-execution-fork-mode-plan.md) - original fork-mode diagnosis
- SKILL.md line 558: false security claim to remove
- Hotfix applied 2026-03-02: removed `disable-model-invocation: true`
