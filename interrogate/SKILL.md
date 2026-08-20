---
name: interrogate
description: Run an adversarial review of code or a diff through independent reviewers, then lead-judge consensus, disagreements, and false positives. Use when the user asks to interrogate, challenge, stress-test, find blind spots, perform multi-model review, or when `henry-mode` needs adversarial judgment of a risky change.
---

# Interrogate

Give independent reviewers the same intent, code, and rubric. Diversity comes from independent reasoning and, where genuinely available, different model families—not invented personas or model aliases. The deliverable is a lead-reviewed verdict; never auto-apply findings.

## Availability and fallback

| Harness | Parallel mechanism | Model selection | Fallback |
|---|---|---|---|
| Cursor | Available Task/subagent calls | Valid models exposed by the harness | Independent inherited-model reviewers or sequential passes |
| Claude Code | Available Agent/Task calls | Valid models exposed by the harness | Independent inherited-model reviewers or sequential passes |
| Codex / T3 | `spawn_agent`, drained with `wait_agent` | Valid overrides only when offered | Run waves within slot limits; inherit the parent model |
| No delegation | None | None | Apply the rubric through separate sequential passes and label the result self-reviewed |

Only delegate when current user and system policy permit it. If true model diversity is unavailable, disclose that; never pretend reviewer labels are different models.

## 1. Determine scope

Use the exact files or diff the user names. Otherwise inspect the full feature-branch diff against its appropriate merge base. Include only surrounding files needed to trace the changed behavior; give every reviewer the same package.

## 2. State intent

Write one paragraph describing what the change is meant to accomplish, derived from the user's request, commit/PR context, and code. Ask only if ambiguity would materially change the review. Reviewers challenge execution, not the chosen product goal.

## 3. Launch independent reviewers

Read and fill these references:

- [`references/reviewer-prompt.md`](references/reviewer-prompt.md)
- [`references/rubric.md`](references/rubric.md)
- [`references/code-quality-review.md`](references/code-quality-review.md)

Launch as many reviewers as the user requested or the harness can support usefully; default to three independent passes. Each reviewer is read-only and receives the identical filled prompt. Use model overrides only from valid harness-advertised choices. Require structured findings with severity, location, evidence, and an optional concrete suggestion.

## 4. Aggregate

Drain every reviewer. Merge duplicate findings, identify independent agreement, retain lone findings at lower confidence, and surface explicit disagreement. Inspect relevant code yourself before accepting a claim.

## 5. Lead judgment

Read [`references/lead-judgment.md`](references/lead-judgment.md), then categorize every finding:

- **Act on:** concrete correctness, security, or maintainability issues that should block the change.
- **Consider:** legitimate tradeoffs whose benefit may not exceed their cost now.
- **Noted:** valid but low-priority or context-dependent observations.
- **Dismissed:** wrong, nitpicky, hypothetical, or missing known context.

Name the reviewers that raised each finding and give a one-line rationale. Consensus is strong evidence, not a substitute for tracing the code.

## Output contract

1. `Intent`
2. `Reviewers`—configuration, model-diversity status, and finding count
3. `Act On`
4. `Consider`
5. `Noted`
6. `Dismissed`
7. `Agreement Map`
8. `Coverage Gaps`

Do not edit code or create review comments unless the user separately authorizes those actions.

<!-- Adapted from poteto/pstack interrogate, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
