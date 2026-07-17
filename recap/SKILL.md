---
name: recap
description: Consolidate everything that changed in the current session into one authoritative message - the final state of each change plus a concrete hand-test checklist - so the user can read a single message instead of the whole history and verify everything in one batch. Use whenever the user asks "what should I test", "catch me up", "summarize what we did/changed", "where are we", "give me the full picture", says they haven't been reading the intermediate messages, or invokes /recap - especially after multiple rounds of fixes and features in the same session.
---

# Recap

The user works in batches: they fire off several prompts, let fixes and features stack up across many turns, and only sit down to hand-test once at the end. They have NOT read every intermediate message. Any summary you wrote three turns ago is already stale — later fixes changed the behavior it described.

Your job when this skill triggers: produce ONE message that fully replaces the need to read the session history. If the user reads only this message, they must know exactly what the current state is and exactly what to verify by hand. Anything you mentioned earlier but omit here is effectively lost — so err toward including every user-visible change.

## Step 1: Reconstruct what actually changed

Do not write the recap from short-term memory of the last few turns. Sweep the whole session:

- **Walk the entire conversation**, including any compacted/summarized context at the top. List every change that was made: features, bugfixes, refactors, config, dependencies, data migrations.
- **Verify against reality, not memory.** If you're in a repo, run `git status` and `git diff --stat` (plus `git log` for commits made this session) and reconcile against your list. Code you touched but forgot, or changes that got reverted, show up here. Where memory and the working tree disagree, the working tree wins. Outside a repo, spot-check the key files you believe you changed.
- **Include changes made by subagents or parallel work** you orchestrated — the user experiences them all as "this session".

## Step 2: Collapse to final state

The user cares about where things ARE, not the journey. For each area touched:

- Report only the **final behavior**. If something was implemented, then broken, then fixed twice, describe the end state once.
- If a change was **reverted or superseded**, either drop it or note it in one line ("X was tried and rolled back — behavior unchanged"), so the user doesn't test for something that no longer exists.
- Do keep churn visible in one place: areas that took several attempts to get right are the highest-risk areas, and the test checklist should lean on them hardest.

## Step 3: Write the recap

Use this structure (adapt headings to the language of the conversation):

### Where things stand
Group by feature/area, not by chronological turn. One short paragraph or a few bullets per area describing final behavior. Plain language — the user skimmed the session, so don't reference "the fix from earlier" or turn-relative context.

### Hand-test checklist
This is the payload — make it executable without asking you anything:

- **Setup first.** If testing requires a rebuild, server restart, cache clear, migration, or new env var, put those steps at the top. A checklist that silently assumes a rebuild produces false failures.
- **Concrete steps with expected results.** "Open the settings page, toggle dark mode, expect the chart colors to update without reload" — not "check dark mode works". Each item should be verifiable as pass/fail.
- **Order for batching.** Group tests that live in the same screen/flow so the user walks each flow once instead of bouncing around.
- **Flag risk.** Mark items touching code that churned during the session, or that you could not verify automatically, e.g. with ⚠️. The user should know where to look closely.
- **Include regression checks.** For each change, ask: what neighboring behavior could this have broken? Add a quick check for anything plausible (shared components, changed signatures, global styles/state).
- **Say what's already verified.** If automated tests, typechecks, or your own runtime verification already covered something, note it — the user can deprioritize it. Don't claim verification that didn't happen.

### Not done / caveats
Anything discussed but not implemented, known limitations, TODOs left in code, and decisions still waiting on the user. This prevents the user from hand-testing for a feature that was never built.

## Keep it honest and self-contained

- If you genuinely can't reconstruct part of the session (context was compacted and the working tree is ambiguous), say so explicitly rather than papering over it — a visible gap is testable, an invisible one isn't.
- The recap must stand alone: no pronouns pointing at earlier messages, no codenames invented mid-session without a one-line gloss.
- Length follows content: a two-fix session gets a short recap; a twenty-turn session gets a long one. Never trim the checklist to look tidy.
