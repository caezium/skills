---
name: principle-build-the-lever
description: Build the smallest rerunnable tool that performs or proves non-trivial work. Use for migrations, repetitive edits, analyses, audits, generators, or delegated campaigns where hand work would drift or be hard to review.
---

# Build the lever

When work is non-trivial, make the method a rerunnable artifact: a codemod, script, query, generator, checker, or delegate contract. The lever buys both throughput and reviewability.

## Pattern

1. Perform one representative unit by hand to learn the recipe.
2. Build the smallest deterministic tool that reproduces or verifies that unit.
3. Diff the tool's result against the hand-worked unit.
4. Make reruns safe: idempotent where possible, scoped, and loud on partial failure.
5. Run it across the remaining units and retain its proof output.

Prefer a deterministic script to agents hand-applying the same transformation. When the work genuinely requires judgment and delegation is authorized, make the lever a read-only contract every worker follows: goal, recipe, verification predicate, output schema, and do-not-touch fences. Keep that contract outside worker write scopes.

Applying this principle produces a file. If no script, generator, query, checker, or delegate contract exists, the lever was not built. Skip only a couple of obvious edits whose result is cheaper to inspect than the tool would be to maintain.

Commit the lever when the task or its verification will recur; otherwise keep it as a visible run artifact.

<!-- Adapted from poteto/pstack principle-build-the-lever, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
