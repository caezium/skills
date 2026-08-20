---
name: maintain-verification-skill
description: Audit and repair a project verification skill and its feature map against current source and live behavior. Use whenever the user asks to maintain, refresh, or audit a verify skill, its harness, or its user-facing feature coverage.
---

# Maintain a verification skill

Keep a project-local verification skill honest as the product changes. The unit of rigor is one feature: every mapped feature receives source coverage and a live drive.

## Outcomes

- **clean:** every feature received source and live coverage; no correction is needed.
- **changed:** proven corrections are ready locally, or published when the user authorized publication.
- **blocked:** coverage or a safe correction could not finish; name the exact blocker.

## Locate and bound the target

Search established project roots, including `.agents/skills/verify-*`, `.claude/skills/verify-*`, and `.cursor/skills/verify-*`. Resolve symlinks and edit only the canonical directory. If several canonical candidates remain, ask which one. If none exists, route to `create-verification-skill`.

Only edit the verification skill's `SKILL.md`, `features/`, and owned harness helpers. Never alter product code during a maintenance pass. Product regressions are findings, not documentation fixes.

| Capability | Preferred route | Fallback |
|---|---|---|
| Source wave | One authorized read-only worker per feature, launched within harness limits | Partition or read features sequentially with the same return schema |
| Live drive | The target skill's declared browser, PTY, API, or platform harness | Mark the feature blocked or verified-unreachable with the attempted route and missing capability |
| Publication | Create one PR only when the user's request authorizes external publication | Leave a verified local diff and report it |

## Pass

1. **Index hygiene.** Compare the feature index with sibling files. Fix missing, extra, duplicate, and dead entries.
2. **Source wave.** For every feature file, explain current user-visible behavior from source, cite entry points, flag likely drift, and return one concise live recipe. Workers never drive or edit. Only delegate when current policy permits it.
3. **Reconcile.** Account for every feature result, spot-check cited drift, combine recipes into the fewest safe app states, and sweep recent source churn for missing user-facing surfaces. Require a concrete source path before adding one.
4. **Live pass.** Follow the verification skill's launch model: one owned long-lived instance for a server/UI, or a fresh isolated session per short-lived CLI drive. Exercise every feature at least once.
5. **Triage.** Wrong user-facing instructions are doc drift. Working behavior the harness cannot drive is a harness gap. Broken product behavior is a product gap to report outside this edit scope.
6. **Re-prove corrections.** Re-drive any changed harness or recipe. Re-read every changed file.
7. **Ship or stop.** Produce at most one authorized PR. For clean, locally changed, or blocked outcomes, do not create external state without authorization.

## Live invariants

- Doctor before the first drive, each fresh session, and after surprising behavior or failed drives.
- Reset or relaunch a wedged user state even when process health looks normal.
- Preserve evidence through every cleanup and verify it still exists.
- Clean residue from failed drives; stop only instances the run owns.
- Report an unreachable feature only with the concrete prerequisite and attempted route.
- Tear down after the final drive and any re-proofs; retain evidence.

Return feature coverage, confirmed drift, changes, product gaps, proof paths, cleanup status, and one outcome label.

<!-- Adapted from poteto/pstack maintain-verification-skill, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
