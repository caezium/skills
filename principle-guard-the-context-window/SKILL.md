---
name: principle-guard-the-context-window
description: Protect reasoning quality when files, histories, logs, screenshots, search results, or worker output are large. Use before bulk reads or fan-out and whenever the active context is filling with payload rather than decisions.
---

# Guard the context window

The active context is finite. Spend it on decisions, constraints, and evidence—not raw payload that can stay in files or worker contexts.

| Situation | Preferred handling | Fallback when delegation is unavailable |
|---|---|---|
| Large file or log | Search first, then read relevant ranges | Save/filter locally and read the compact result |
| Many independent inputs | Give authorized workers non-overlapping slices and a strict return schema | Process slices sequentially and keep a rolling summary |
| Verbose tool output | Write it to an artifact and extract findings | Re-run with narrower filters or output limits |
| Repeated reference | Keep the small, frequently used contract inline | Link branch-specific detail behind a precise context pointer |

Do not delegate unless current user and system policy permit it. Keep raw transcripts, screenshots, and bulk source outside the coordinating thread; bring back conclusions, evidence pointers, disagreements, and gaps.

Before each read, ask what decision it can change. Stop when the scoped question is answered. At phase boundaries, restate the current goal, verified state, open risks, and next action so later compaction preserves the throughline.

<!-- Adapted from poteto/pstack principle-guard-the-context-window, MIT License, Lauren Tan, cursor/plugins@51a96e0. -->
