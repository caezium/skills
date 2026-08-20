---
name: principle-prove-it-works
description: Prove completed work against the real artifact before declaring success. Use after any implementation, migration, delegated task, configuration change, or fix where compilation, self-report, cached output, or file existence could hide failure.
---

# Prove it works

Verify the output by observing the real behavior. Build success is necessary evidence for code, not completion.

## Evidence ladder

1. Inspect the final diff or artifact.
2. Run the repository's focused checks.
3. Exercise the changed path with representative input.
4. Trace the full input-to-output chain and inspect side effects.
5. For an integration, exercise the real boundary end to end when safe and proportionate.

Choose the highest useful rung and report exactly what ran, what passed, and what remained unavailable. If the proof cannot run, mark the result unverified rather than rounding up.

## Proof rules

- Read actual state, not cached or derived representations.
- Check process health directly when liveness matters.
- For delegated work, inspect files, diffs, tests, and runtime artifacts; a worker summary is only a lead.
- When an observation contradicts expectations, validate the observation method before changing the system.
- Prefer a deterministic, rerunnable script over a one-time eyeball when the task is non-trivial.
- Keep proof visible to the user. Commit it only when the work or review trail outlives the session.

Completion criterion: the final claim is paired with a command, artifact, or direct observation that would fail if the claim were false, plus an explicit note for every untested boundary.

<!-- Adapted from poteto/pstack principle-prove-it-works, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
