---
name: reflect
description: Review the active session through judgment, tooling, and divergent lenses, then propose durable skill edits or structural backlog items. Use when the user asks to reflect, wants better agent behavior from a session, or when `henry-mode` closes expensive, surprising, or repeated work whose lesson should survive.
---

# Reflect

Mine the active conversation for durable lessons and route them to concrete improvements. Never auto-apply skill changes: present the synthesized proposal and wait for approval.

## Harness availability

| Need | Cursor | Claude Code | Codex / T3 | Fallback |
|---|---|---|---|---|
| Transcript | Harness-supplied path or active workspace history under `~/.cursor/projects/` | Harness-supplied path or matching history under `~/.claude/projects/` | Harness-supplied path or matching `cwd` metadata under `~/.codex/sessions/` | Visible-conversation digest |
| Three reviewers | Available Task/subagent facility | Available Agent/Task facility | Three `spawn_agent` calls when slots permit; drain with `wait_agent` | Run the three reference prompts sequentially |
| Model diversity | Select valid model families only when supported and allowed | Same | Use valid overrides only when exposed; otherwise inherit | Label the review same-model or self-reviewed |
| Synthesis | A fresh worker after reviewers drain | Same | Spawn after reviewer slots free | Parent synthesizes with the same template |

Only delegate when current user and system policy permit it. Never invent model aliases.

## 1. Locate the session

Prefer the active transcript path exposed by the harness. Otherwise search only the active workspace's history, ordered by real modification time, and match workspace metadata plus the opening user prompt. Do not glob through unrelated project histories. If no transcript resolves, write a compact digest from the visible conversation.

## 2. Run three lenses

Load the matching prompt only when launching that lens:

| Lens | Prompt |
|---|---|
| Judgment | [`references/judgment-reviewer.md`](references/judgment-reviewer.md) |
| Tooling | [`references/tooling-reviewer.md`](references/tooling-reviewer.md) |
| Divergent | [`references/divergent-reviewer.md`](references/divergent-reviewer.md) |

Pass the transcript path or digest and preserve each response verbatim for synthesis. Reviewers are read-only: they may inspect referenced local/context sources when authorized, but they do not edit files, post messages, or create external state.

## 3. Synthesize

After all three lenses finish, load [`references/synthesizer.md`](references/synthesizer.md) and substitute their full outputs. Spot-check citations. The result must contain Accepted, Rejected, and Backlog sections.

Move any proposal enforceable more reliably by a lint rule, script, metadata flag, or runtime check from Accepted to Backlog. Prefer an existing skill over a new one. A lesson must be durable, decision-changing, and grounded in this session.

## 4. Ask before applying

Present the full synthesis and wait for explicit approval on the Accepted rows. Do not file backlog items externally unless the user authorizes that destination.

For approved rows:

- Make a trivial existing-skill edit directly.
- Route substantive edits, new personal/shared skills, and description tuning through `anthropic-skill-creator`. Leave Codex's same-purpose product-managed system skill untouched.
- Run the environment's skill validator when available and inspect the final diff.

## 5. Report

- Edits applied: path and one-line change.
- New skills: path and purpose.
- Backlog: proposed mechanism and whether it was filed.
- Dropped: rejected finding and reason.

<!-- Adapted from poteto/pstack reflect, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
