---
name: blast-radius
description: Find what a code, schema, API, config, or behavior change could break beyond its visible diff, then prove the safety-critical assumption with real code. Use whenever the user asks what could break, requests a blast-radius review, or distrusts a deceptively small change.
---

# Blast radius

Find breakage a caller list will miss. The deliverable is not a convincing risk essay; it is the one safety-critical fact either proved against real behavior or marked unproven.

## Evidence ladder

For every fact the change's safety depends on, climb as far as practical and report where you stopped:

1. An unsupported assertion—never sufficient.
2. A concrete `file:line`, pinned dependency source, schema, or contract.
3. A traced bad case showing whether it can reach the changed behavior.
4. A script or test that calls the real code and fails loudly if the fact is false.
5. A reproduction through the running product.

Any safety fact below level 4 stays explicitly unproven.

## Tool availability

| Need | Preferred route | Fallback |
|---|---|---|
| Change and history | Local git diff/log plus an available source-control connector | Local repository only; name missing PR context |
| Downstream consumers | Code search, schemas, generated clients, migrations, pinned dependency source | Trace the reachable local chain and mark external consumers unknown |
| Runtime proof | Existing tests, verification harness, or a small deterministic script | Minimal isolated repro; if execution is impossible, stop at the evidence level reached |
| Independent review | Invoke `interrogate` when the user authorizes a multi-agent review | One lead-review pass; disclose the missing independent signal |

## Process

1. **Read the change.** Inspect the diff, changed symbols, deleted behavior, commits, and surrounding contracts. State what now behaves differently, including effects the diff does not spell out.
2. **Name the safety fact.** Find the one or two assumptions that collapse most scary cases if true. Spend effort here instead of producing a long speculative list.
3. **Look past symbol search.** Check pinned library behavior and local patches; event timing and teardown; serialized data, database columns, wire formats, other-language consumers, feature flags, jobs, caches, and code several hops downstream.
4. **Trace real risks.** For each candidate, show a reachable failure path, likelihood, cost, and a concrete check. A search that finds nothing is evidence when the search scope is stated.
5. **Prove the safety fact.** Prefer the smallest script or test importing the same code the product ships. Run it and retain output. Reproduce through the product when proportionate.
6. **Widen only when useful.** For a broad or high-risk change, suggest `interrogate`; do not launch agents unless current policy and user intent allow it.

## Output contract

- **What changed:** the visible and implicit behavior change.
- **Safety fact:** the assumption, evidence level reached, and proof output; otherwise `UNPROVEN`.
- **Risks:** only reachable risks, each with location, likelihood, impact, and check.
- **Cleared:** candidates investigated and why they do not reach.
- **Before merge:** the cheapest test or repro that catches the real failure.
- **Coverage gaps:** unavailable repositories, services, connectors, or runtime paths.

Use plain language, cite real code, and remove private material before public sharing.

<!-- Adapted from poteto/pstack blast-radius, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
