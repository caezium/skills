# Consultation gate

- Before drafting a substantive plan, PRD, design document, or spec, or implementing a nontrivial change, determine whether meaningful product or design direction remains unresolved. If it does, use the `consult-first` skill and do not write the deliverable, code, or configuration until the user approves the direction.
- Use `consult-first` whenever the user explicitly asks to be consulted or to discuss before acting, even if the task appears settled.
- Skip automatic consultation for an approved spec or ticket, an already-settled design, a mechanical transformation, a small unambiguous edit, or a factual explanation. The user's explicit request to consult or to proceed directly always overrides the default.
- During consultation, confirmed domain terminology and warranted ADRs may be recorded, but final deliverables and implementation remain behind the approval gate.
- Please use first-principles thinking. Do not assume that I always know exactly what I want and how to achieve it. Be prudent and start from the original needs and problems. If my motivations or goals are unclear, pause and discuss with me. If the goals are clear but the path is not the shortest, tell me and suggest a better approach.

# Git

- Never add `Co-Authored-By`, "Generated with Claude Code", or any other AI attribution to commit messages, PR descriptions, or PR titles — not even when composing the message yourself.
