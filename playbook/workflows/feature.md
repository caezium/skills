# Feature workflow (spec-driven, Matt Pocock)

**When it fits:** building a feature or making any nontrivial change where the design isn't already settled. Design gets grilled first, then frozen into a spec, then broken into tracer-bullet tickets, then implemented and reviewed.

**One-time prerequisite (per repo):** `/setup-matt-pocock-skills` — configures the issue tracker, triage labels, and domain-doc layout these skills read and write (`docs/agents/issue-tracker.md` etc.). If that file is missing when the user reaches step 2, remind them to run setup first.

## Steps

1. **`/grill-with-docs`** — relentless one-question-at-a-time interview to sharpen the design, maintaining the domain glossary (`CONTEXT.md`) and ADRs as decisions crystallise.
   → Produces: a shared understanding, updated glossary, ADRs where warranted.

2. **`/to-spec`** — synthesizes the grilled conversation into a spec (problem, user stories, implementation + testing decisions, out-of-scope) and publishes it to the issue tracker. No interview — it feeds on step 1's context, so run it in the same session.
   → Produces: a spec on the tracker, labelled `ready-for-agent`.

3. **`/to-tickets`** — breaks the spec into tracer-bullet vertical-slice tickets with blocking edges, quizzes the user on granularity, publishes to the tracker.
   → Produces: agent-grabbable tickets in dependency order.

4. **`/implement`** — implements a ticket (TDD at pre-agreed seams, typecheck regularly, full suite at the end), then runs `/code-review` itself and commits. Repeat per ticket, ideally one fresh session each — point it at the ticket.
   → Produces: committed, reviewed work per ticket.

5. **`/code-review`** — two-axis review (Standards + Spec) of everything since a fixed point. `/implement` already runs this per ticket; run it explicitly for a final whole-branch pass before merging, giving it the branch point as the fixed point.
   → Produces: side-by-side Standards and Spec findings.

## Notes for the shepherd

- Steps 1→2 must share a session (`/to-spec` synthesizes, it doesn't re-interview). Steps 3–5 work best in fresh sessions pointed at the tracker artifacts.
- If the user arrives with a design already settled, start at step 2. If a spec already exists, start at step 3.
