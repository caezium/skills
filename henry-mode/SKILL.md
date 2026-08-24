---
name: henry-mode
description: Orchestrate Henry's long-running engineering and research work across recall, consultation, specifications, verification, worker fleets, evidence trails, handoffs, and reflection. Use when work spans sessions or machines, needs autonomous agents, crosses risky runtime boundaries, or Henry asks to resume, run a fleet, keep going, or use Henry mode. Skip small self-contained tasks.
---

# Henry mode

Treat this as a router over the installed skills, not a second implementation of them. The objective is a resumable chain of verifiable units whose evidence survives the current context window.

## 1. Reconstruct before deciding

- When prior work matters or the task resumes elsewhere, use `recall` to combine relevant Claude/Codex history with current repository state.
- Use `why` when intent, history, or an old trade-off is unclear; use `how` when the missing piece is the current runtime flow or ownership map.
- State the recovered objective, settled decisions, live constraints, and last verified checkpoint. Do not carry old conclusions forward when the code or external state disproves them.

Completion criterion: the next decision can be made from current evidence without rereading raw history.

## 2. Settle direction

- If meaningful product or design direction remains unresolved, `consult-first` wins. Use model-invocable helpers such as `prototype` or `domain-modeling` only as the question requires. When a persistent decision map or live documented interview would materially help, recommend the user-invoked `/wayfinder` or `/grill-with-docs` workflow and wait for the user's choice.
- If direction is already approved, do not create another planning ceremony. When a published artifact or independent work units would be useful, recommend `/to-spec` or `/to-tickets`; those user-invoked skills own the tracker writes.

Completion criterion: consequential choices are approved, and every unresolved choice is explicit rather than smuggled into implementation.

## 3. Define proof and worker contracts

- Reuse the project's verification skill when one exists. For a long-lived project without one, use `create-verification-skill`; maintain it with `maintain-verification-skill` when surfaces drift.
- Use `writing-for-agents` for briefs, acceptance contracts, pointers, and worker output schemas.
- Use `technical-writing` for a user-invoked documentation pass when the artifact needs an explicit tutorial, how-to, reference, or explanation shape.
- Apply `principle-prove-it-works`, `principle-build-the-lever`, and `principle-sequence-verifiable-units`: prefer a rerunnable test, evaluator, parser, or harness over a one-off assertion.

Completion criterion: every implementation unit has an observable success condition and an owner for its output.

## 4. Execute on the smallest safe topology

- Single path: execute the authorized implementation directly, or use `diagnosing-bugs` for a failure → the one shared `tdd` skill where appropriate → `code-review`. Do not invoke `/implement` on the user's behalf; that workflow includes commits and remains user-invoked.
- Boundary-crossing change: add `blast-radius` and prove the one runtime safety fact most likely to fail.
- At external inputs, apply `principle-boundary-discipline`; for typed code, apply `principle-type-system-discipline` and `typescript-best-practices` where relevant.
- Parallel coverage: use `swarm`. Give workers isolated directories/state, explicit resource budgets, non-overlapping briefs, and a root aggregator. Apply `principle-guard-the-context-window`; return conclusions and artifact paths instead of raw exploration.
- For retries, restarts, lifecycle commands, or repeated automation, apply `principle-make-operations-idempotent`. For concurrent work, apply `principle-separate-before-serializing-shared-state` before reaching for locks.
- Keep `show-me-your-work` active for autonomous or expensive work. Record decisions, evidence, attempted approaches, rejection reasons, checkpoints, and the next recovery command.

Completion criterion: each unit either passes its proof or leaves a precise, non-duplicative failure record; shared mutable state never becomes an accidental coordination channel.

## 5. Close the loop

- Re-run the authoritative verification from a clean enough state to catch hidden dependencies.
- Update the verification map when the implementation changed a user-visible or operational surface.
- Use `reflect` after expensive, surprising, or repeated work. Propose durable changes to a test, script, rule, skill, or architecture, but keep shared-skill edits reviewable.
- If work must continue in another context, recommend `/handoff` after verification—not before it—so the user can choose when to create the cross-session artifact.

Completion criterion: the outcome is proved, the durable lesson has a home, and another agent can resume without reconstructing the whole run.

## Autonomy boundary

An instruction to keep going increases persistence, not authority. Continue without waiting only when direction is settled, actions remain within the user's authorized scope and host safety rules, and recovery is possible. Otherwise surface the decision with the evidence needed to make it quickly.
