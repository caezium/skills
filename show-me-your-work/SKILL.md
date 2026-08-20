---
name: show-me-your-work
description: Keep an auditable decision trail for long-running, autonomous, delegated, or multi-phase work. Use whenever a human will review the result after stepping away and needs decisions, evidence, pivots, and verification without rereading the full transcript.
---

# Show me your work

Maintain one append-only TSV decision log so a reviewer can reconstruct what was decided, why, and on what evidence. Log decisions and checkpoints, not keystrokes.

## Start the trail

Copy [`references/decision-log-template.tsv`](references/decision-log-template.tsv) to `decisions.tsv`, or use `.audit/<task-slug>.tsv` when several efforts share a worktree. Keep it local by default. Commit it only when a reviewer needs the trail to trust a large migration, port, or unattended run.

Append safely with:

```bash
scripts/log.sh <logfile> <phase> <decision> <why> <evidence> <result>
```

The helper timestamps the row, preserves single-line cells, and neutralizes spreadsheet formulas. Resolve `scripts/log.sh` relative to this installed skill.

| Column | Contract |
|---|---|
| `ts` | UTC ISO-8601 timestamp |
| `phase` | Current phase or workstream |
| `decision` | One concrete choice or checkpoint |
| `why` | Plain-language reason |
| `evidence` | A resolvable pointer: commit, `file:line`, test output, trace, screenshot, or artifact path |
| `result` | Observable state such as `tests green`, `reverted`, `INCONCLUSIVE`, or `open` |

Write one row for a fork chosen, a verified unit completed, a pivot/revert, a blocker, or a gate changing state. For iterative runs, write one row per meaningful iteration. A wrong call gets a later superseding row; never rewrite history.

## Harness availability

| Need | Native path | Fallback |
|---|---|---|
| Locate this run's transcript | Use the active transcript path supplied by Cursor, Claude Code, Codex, or T3 | Match workspace metadata and opening prompt in that harness's scoped history; otherwise use the visible conversation |
| Fresh-eye audit | Use an authorized subagent; request a different model family only when the harness exposes valid model selection | Use an independent inherited-model reviewer; if delegation is unavailable, perform the audit yourself and disclose that limitation |
| Evidence | Use repository/runtime/browser/connector tools available in the harness | Mark the row `INCONCLUSIVE`; never manufacture a pointer |

Only delegate when the current user and system policy permit it.

## End-of-run audit

1. Walk the log against the active transcript or visible conversation.
2. Confirm every row maps to a real action and every evidence pointer resolves.
3. Add omitted forks, abandoned approaches, and verification failures that shaped the result.
4. Remove padding; keep only rows a reviewer would audit.
5. Ask the fresh-eye reviewer to flag weak evidence, skipped verification, risky choices, and gaps. The reviewer inspects; it does not redo or edit the work.

End the handoff with an `Attention` section naming the reviewer configuration and its flags. `No flags` is valid. If model diversity or delegation was unavailable, say so plainly.

<!-- Adapted from poteto/pstack show-me-your-work, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
