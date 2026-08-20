---
name: recall
description: Reconstruct recent working context from scoped agent history, project records, and live repository state. Use whenever the user asks to catch up, resume prior work, remember what happened, or continue work whose earlier agent context is missing.
---

# Recall

Rebuild the user's working context before acting, then return a tight capsule of the current truth and the single best next move. History supplies leads; live state decides what is true now.

## Availability and fallback

| Need | Cursor | Claude Code | Codex / T3 | Fallback |
|---|---|---|---|---|
| Active transcript | Use the transcript path exposed by the harness; otherwise inspect the active workspace under `~/.cursor/projects/` | Use the path exposed by the harness; otherwise inspect the matching project under `~/.claude/projects/` | Use the path exposed by the harness; otherwise inspect matching `cwd` metadata under `~/.codex/sessions/` | Build a digest from the visible conversation |
| Parallel history slices | Use the available Task or subagent facility | Use the available Agent/Task facility | Use `spawn_agent` and drain with `wait_agent` | Search slices sequentially with the same return schema |
| Shared record | Use available source-control, issue, chat, docs, and observability connectors | Same | Same | Use local git history and repository docs; name unavailable sources |

Only delegate when the current user and system policy permit it. Never weaken privacy boundaries to gain parallelism.

## Process

1. **Classify the request.** Recall reconstructs context across earlier work. If the user supplied a complete state capsule—target, branch, current result, and next task—use it and skip history mining.
2. **Lock the scope.** Pin the topic, workspace, and time window. Default “recent” to seven days. Never turn “all” into a smaller range silently, and never inspect another project's history unless the user asks.
3. **Find matching sessions.** Prefer harness-provided transcript paths. Otherwise filter candidates by workspace metadata and real modification time, match the opening user prompt or topic, and exclude the current session plus obvious worker/eval noise. Search before reading; open only relevant regions.
4. **Slice large histories.** For more than a couple of sessions, partition by time or source. Every worker returns one block per session: topic, user goal, decisions, corrections, open threads, and artifacts, with a session identifier. Keep raw transcripts out of the coordinating thread.
5. **Sweep the shared record for named targets.** When the request names a feature, file, subsystem, or bug, inspect relevant git history plus available PRs, issues, chat, docs, and error records. Ask: what is current, what was tried and failed, and what are users still reporting? A null result is a finding. Skip this sweep for pure activity recall with no named target.
6. **Verify live state.** Check surfaced branches, commits, worktree changes, PRs, and tickets directly. A transcript is historical evidence, not present truth.
7. **Write the brief.** Keep adjacent work out unless it blocks the named topic.

## Output contract

- **Capsule:** at most five bullets describing the work and its overall state.
- **Threads:** one line each with one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]`.
- **Problems:** at most five recurring problems, including failed or reverted approaches.
- **Next move:** one concrete action with the highest leverage.
- **Coverage note:** sources searched, unavailable sources, and the exact time/workspace scope.

Cite session identifiers and durable source references without exposing private transcript content. Sanitize before any public output.

<!-- Adapted from poteto/pstack recall, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
