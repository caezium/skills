---
name: swarm
description: Fan out a task across N independent workers, drain every wave, and return one evidenced report. Use when the user asks to swarm, parallelize, race approaches, run a gauntlet, divide exhaustive coverage, or when `henry-mode` reaches a settled parallel-work stage.
---

# Swarm

Fan out a task as coverage slices, identical race arms, or a deliberate mixture. The coordinator owns framing, writable boundaries, aggregation, and the final judgment.

## Harness availability

| Harness | Worker mechanism | Drain / follow-up | Fallback |
|---|---|---|---|
| Cursor | Available Task/subagent calls; cloud workers only when explicitly supported | Native task results | Run local workers or sequential slices |
| Claude Code | Available Agent/Task calls, optionally in background | Native result/wait mechanism | Sequential slices |
| Codex / T3 | `spawn_agent` | `wait_agent`; use `followup_task` for another bounded turn | Run waves within the advertised slot limit, then sequential slices |
| No delegation tool | None | None | Execute every slice sequentially with the same brief and schema |

Inherit the parent model by default. Use model overrides only when the user requests a model race or the harness exposes valid choices. Never invent aliases. N is total workers, not simultaneous slots; run waves until all N have a terminal result.

## Frame

1. State the done predicate and final artifact.
2. Choose `coverage`, `race`, or `mixed`. For a race, declare `first-pass`, `rank-all`, or `best-of` before launch.
3. Set N from the user's request or the number of independent slices.
4. Give every writing worker an exclusive directory, worktree, branch, or file set. Keep the shared contract outside worker write scopes.
5. Track four phases with the harness's plan/todo feature when available: frame, fan out, aggregate, report.

## Fan out

Launch as many workers together as the harness permits. Every brief must stand alone and include:

- goal and exact slice/race arm;
- read and write scope, including do-not-touch fences;
- verification command or observable predicate;
- required report schema: `PASS`, `ISSUES`, or `BLOCKED`, followed by artifact paths and evidence.

If a worker drops out, retry only when doing so is safe and useful; otherwise continue and record the gap. Never let two workers edit the same mutable target concurrently.

## Aggregate

Drain every launched worker before concluding. Inspect artifacts rather than trusting summaries. Coverage requires a terminal result for every slice; races use the selection rule declared up front. Deduplicate findings, surface disagreements, and keep raw worker dumps out of the main thread.

## Report

Return one compact table with slice/arm, status, evidence, and selected result; then list issues, disagreements, gaps/dropouts, and the race rule. A swarm is complete only when every requested slice is accounted for.

<!-- Adapted from poteto/pstack swarm, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
