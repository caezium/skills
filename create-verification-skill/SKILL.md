---
name: create-verification-skill
description: Create a project-local skill that launches and drives the real app like a user, captures durable proof, and cleans up safely. Use whenever a repo lacks a scripted way to verify UI, CLI, desktop, mobile, API, or service behavior end to end.
---

# Create a verification skill

Generate a cold-startable project skill that another agent can use to launch the real product, exercise a user path, and retain proof. A generated skill that has not run successfully is a draft.

## Choose one canonical location

Respect the repository's established convention. If none exists, use this table and keep one source of truth—never duplicate editable copies.

| Repository target | Canonical root | Compatibility action |
|---|---|---|
| Multi-harness or Codex/T3-first | `.agents/skills/verify-<app>/` | Add relative links under `.claude/skills/` or `.cursor/skills/` only if that harness does not discover `.agents/skills/` and the repo accepts symlinks |
| Claude Code-only | `.claude/skills/verify-<app>/` | No duplicate |
| Cursor-only | `.cursor/skills/verify-<app>/` | No duplicate |

Record the chosen root in the generated skill so its maintenance pass can find it.

## 1. Interview the repository

Answer from code and docs before asking the user:

- **Surface:** what users touch—web UI, CLI/TUI, desktop/mobile app, API, service, or library.
- **Run:** the repository's real local start/build command, readiness signal, ports, environment, fixtures, and auth.
- **Drive:** existing harnesses first: browser tests, app automation, PTY helpers, CLI scripts, or HTTP clients.
- **Observe:** screenshots, accessibility snapshots, terminal transcripts, response bodies, exit codes, logs, and persisted side effects.
- **Isolate:** ports, profiles, and data directories that permit concurrent runs. If isolation is impossible, require exclusive ownership and refuse to drive a user's live instance.

| Surface | Preferred driver | Fallback |
|---|---|---|
| Web / Electron | Attached collaborative browser or existing Playwright/Cypress harness | Repository-approved browser automation; avoid coordinates when stable roles/selectors exist |
| CLI / TUI | Existing expect, PTY, or tmux harness | Isolated shell session with captured stdout, stderr, and exit code |
| API / service | Existing integration client or tests | Literal HTTP requests against an isolated local instance |
| Desktop / mobile | Existing platform UI harness | Platform-native automation available in the current harness; otherwise report the missing capability |

If the checkout cannot start as documented, fix or precisely report the base problem before generating instructions against it.

## 2. Generate the skill

Create `SKILL.md` at the selected root with `name: verify-<app>` and a description naming the app, surface, and trigger. Ground every section in this repository; leave no placeholders.

- **Launch:** exact start command, readiness predicate, ownership marker, and teardown. Short-lived CLIs start in a fresh isolated session per drive.
- **Doctor:** one read-only check for process/build identity, endpoint, profile/data directory, and auth as relevant.
- **Drive:** exact commands and stable handles from this repo. Prefer accessible names, prompt strings, route paths, and documented flags over coordinates or tab order.
- **Evidence:** prove the real user path and resulting state. Capture the action and outcome, then verify side effects from a second read-only view. Use mocks only at an existing production boundary.
- **Cleanup:** stop only processes the run started and remove only its scratch state. Preserve evidence.
- **Helpers:** make scripts executable and document literal invocations.

## 3. Seed the feature map

Create `features/README.md` plus files for the top three to five user-facing features discovered from routes, commands, menus, or docs. Read [`references/feature-map-example/`](references/feature-map-example/) for the exact shape. Each feature file uses these four H2 headings:

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it with <harness>`
4. `Gotchas`

Map every user entry point separately; proving one convenient path does not prove its siblings.

## 4. Prove the generated skill

Run launch, doctor, one mapped feature, evidence capture, and cleanup end to end. Confirm the evidence still exists after cleanup. Clean failed attempts too, then fix the instructions and rerun until green.

Point future maintainers to `maintain-verification-skill` and report the canonical location, tested feature, proof paths, and any unsupported surface.

<!-- Adapted from poteto/pstack create-verification-skill, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
