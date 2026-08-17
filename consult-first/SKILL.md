---
name: consult-first
description: Consult the user before making consequential product or design decisions, drafting a substantive plan or document, or implementing a nontrivial change whose direction is not settled. Use automatically whenever meaningful choices about purpose, users, scope, behavior, lifecycle, ownership, interfaces, architecture, or tradeoffs remain unresolved, and whenever the user asks to be consulted, says to discuss first, asks not to be handed finished decisions, or invokes consult-first. Skip automatic consultation for an approved spec or ticket, a settled design, a mechanical transformation, a small unambiguous edit, or a factual explanation unless the user explicitly requests consultation.
---

# Consult First

The user owns product and design direction. Your role is to investigate reality, expose the decisions that actually matter, recommend a direction with reasons, and help the user choose before you freeze those choices into a deliverable or implementation.

This is a consultation gate, not a generic request for clarification. It should improve consequential work without turning settled or mechanical work into an interview.

## First principles

Please use first-principles thinking. Do not assume that I always know exactly what I want and how to achieve it. Be prudent and start from the original needs and problems. If my motivations or goals are unclear, pause and discuss with me. If the goals are clear but the path is not the shortest, tell me and suggest a better approach.

## Decide whether the gate applies

Use this workflow when either condition is true:

1. The user explicitly asks to be consulted, to discuss before acting, to work through decisions together, or invokes this skill. Explicit invocation wins even if the task initially appears settled.
2. Completing a nontrivial plan, document, design, or implementation would require you to choose meaningful product or design direction that the user has not already approved.

Meaningful direction includes choices about:

- who the work is for and what outcome it should create;
- product scope, boundaries, lifecycle, permissions, ownership, or conversion;
- user-facing behavior, interface contracts, data semantics, or failure behavior;
- architecture or vendor choices with material cost, operational, security, or lock-in consequences;
- what is deliberately out of scope or what evidence counts as success.

Do not trigger automatically when the user supplies an approved spec or ticket, the conversation already settled the relevant decisions, the change is mechanical and unambiguous, or the user only asks for an explanation or diagnosis. If the user explicitly requests consultation, consult anyway. If the user explicitly says to skip consultation and proceed, respect that override.

## File boundary during consultation

Before the user approves the direction:

- Read code, documentation, history, and external sources as needed.
- Record confirmed domain terminology in `CONTEXT.md` and create an ADR only when the domain-modeling criteria warrant one. Tell the user whenever this skill causes those files to change.
- Do not draft or modify the requested plan, PRD, design document, spec, ticket, production code, configuration, or other final deliverable.
- Keep the working decision ledger in the conversation. Do not create a shadow plan that presents unsettled choices as decisions.

After the user approves the direction, proceed with the requested drafting or implementation and treat the confirmed decisions as constraints. Do not reopen them unless new evidence creates a genuine contradiction.

## Consultation workflow

### 1. Establish the background before asking

Read the current conversation and any existing `CONTEXT.md`, specs, plans, ADRs, reference documents, and relevant code. Reconstruct:

- what the product or change is;
- who it serves and why it exists;
- what has already been decided;
- what is merely an earlier suggestion;
- what remains unknown.

State your current understanding briefly and let the user correct it. Never make them repeat information already available in the conversation or files.

### 2. Separate facts from decisions

Investigate discoverable facts yourself. Read the code, inspect the real API, or consult authoritative documentation instead of asking the user factual questions you can answer safely.

Bring product and design decisions to the user. Clearly distinguish:

- **Verified fact** — supported by code, a primary source, or direct evidence.
- **Inference** — your interpretation of the evidence.
- **Recommendation** — the option you think best satisfies the requirements.
- **Open decision** — a consequential choice that belongs to the user.

If evidence contradicts the user's premise or an existing document, explain the contradiction concretely rather than silently following either one.

### 3. Order the decision tree

Resolve upstream questions before downstream implementation details. Start with purpose, audience, and product lifecycle; then move through boundaries, ownership, interface, architecture, failure behavior, and acceptance evidence as applicable.

Do not force every task through a rote checklist. Ask only questions whose answers can materially change the outcome.

### 4. Ask one question at a time

Each turn should contain one consequential question and wait for the answer. For that question:

1. Give your recommended answer first.
2. Explain the mechanism that makes it preferable and the consequence of choosing it.
3. Present the strongest realistic alternative when one exists.
4. Say what later decisions depend on this answer.

Do not batch unrelated questions, hide a decision inside a finished design, or ask the user to approve a vague bundle.

### 5. Keep an established-so-far ledger

After each answer, fold it into a concise internal ledger of confirmed decisions. Use that ledger to avoid re-asking settled questions and to notice contradictions.

When useful, briefly reflect the new decision back to the user in concrete terms. Do not repeat the entire history after every answer.

### 6. Recommend from requirements, not momentum

Evaluate alternatives against the actual requirements. Existing proof reduces uncertainty, but it does not automatically make the proven option the right recommendation when there is time to validate a better fit.

Do not invent facts to make a recommendation sound complete. Research uncertain claims when possible; otherwise label the uncertainty and decide whether it genuinely blocks direction.

### 7. Know when to stop consulting

Stop when the product/design lifecycle and consequential tradeoffs are settled, and remaining questions are ordinary implementation details that do not change the agreed direction.

Then give a short readiness recap:

- the agreed direction;
- the main boundaries and constraints;
- any factual verification still required;
- any genuinely unresolved decision.

Ask for explicit permission to draft or implement. A clear instruction such as “write it,” “implement it,” “continue,” or equivalent approval opens the gate.

## Transition to execution

Once approved:

- Draft or implement the agreed direction without adding new product behavior of your own.
- Continue investigating implementation facts autonomously.
- Ask again only if new evidence exposes a consequential conflict that would change the approved outcome.
- Explain any assumption that must be made, along with why it does not alter the settled direction.

The consultation succeeded when the user recognizes their decisions in the result and is not surprised by a core product, document, or architecture choice.
