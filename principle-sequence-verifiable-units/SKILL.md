---
name: principle-sequence-verifiable-units
description: Break multi-step work into small units that each end in a checkable green state. Use for sweeps, migrations, repeated edits, long agent runs, or commit/PR stacks where batching would hide the first failure.
---

# Sequence verifiable units

Order work as a chain of small units. Each unit starts from a known state, makes one coherent change, and ends with a check before the next begins.

## Execution

1. Establish the real baseline.
2. Choose the smallest unit with a meaningful observable predicate.
3. Change only that unit.
4. Run the predicate and retain its result.
5. Advance only when green; if red, repair or revert before stacking more work.

A rerunnable lever can make per-unit checks cheap, but it does not justify deferring them to the end. Record unit status when work spans sessions or workers.

## Delivery

Order commits or PRs so a reviewer can replay the argument. Useful shapes include:

- failing regression test, then fix;
- baseline artifact, then treatment and comparison;
- subtraction of obsolete code, then the simpler replacement;
- scaffold that stands alone, then the feature.

Every unit must build or otherwise satisfy the repository's own merge predicate on its own. Completion means every requested unit is accounted for, every check is attached to the unit that caused it, and no later work rests on an unresolved red state.

<!-- Adapted from poteto/pstack principle-sequence-verifiable-units, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
