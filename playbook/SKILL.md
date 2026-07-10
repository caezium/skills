---
name: playbook
description: Pick the right ordered sequence of skills for the job at hand, announce it, and keep reminding the user which skill comes next after each stage completes — so they never have to remember the chain themselves. Only active when explicitly invoked.
disable-model-invocation: true
---

# Playbook

The user knows skills exist but shouldn't have to memorise which ones to run in which order. When this skill is invoked, you become the keeper of that sequence for the rest of the session.

This is **not** default behavior. Never volunteer skill-sequence guidance unless the user invoked `/playbook` (or explicitly asks). Once invoked, the guidance persists for the whole session.

## Process

### 1. Pick the workflow

Read the argument and conversation context, then match against the workflow table:

| Workflow | When it fits |
|---|---|
| [feature](workflows/feature.md) | Building a feature or making a nontrivial change: design → spec → tickets → implementation → review (Matt Pocock's spec-driven flow) |

- If the user passed a workflow name as an argument (`/playbook feature`), use that one.
- If the context clearly matches one workflow, propose it and confirm in one line.
- If ambiguous or nothing fits, list the workflows with one-line summaries and ask which one — or offer to run freeform without a playbook.

### 2. Announce the sequence

Read the chosen workflow file. Present the full sequence up front as a short numbered list: each step's skill, what it produces, and which step the user is currently at.

Don't assume they're at step 1 — if the conversation already contains a sharpened design, they may be at the spec step; if a spec already exists on the tracker, they may be at tickets. Say where you think they are and why.

### 3. Shepherd the sequence — this is the core job

For the rest of the session:

- **When a step completes** (the skill finishes, its artifact exists), tell the user plainly: "Step N done. Next: `/skill-name` — <what it does>." Put this at the END of your final message for the turn so it's the last thing they read.
- **Never auto-run the next skill.** Each step is the user's call — they may want to pause, review, or leave the rest for a fresh session. Your job is only to make the next command copy-pasteable.
- **If the user skips ahead or goes off-script**, don't fight it. Note where the sequence now stands and keep tracking from the new position.
- **If the session ends mid-sequence**, when asked to summarise or hand off, include which step is next so a future session can resume.
- **Respect each step's prerequisites** — the workflow file notes them (e.g. one-time repo setup). If a prerequisite is missing when the user reaches that step, surface it before they run the skill, not after it fails.

## Adding workflows

Each workflow is one file in [workflows/](workflows/): a name, when it fits, and an ordered list of steps (skill + what it produces + prerequisites). To add a new arrangement for a different context of work, add a file there and a row to the table above. Keep steps as existing skills — a playbook orders skills, it doesn't define new ones.
