---
title: Close Commented GitHub Issues and PRs
type: fix
status: active
date: 2026-03-03
origin: docs/plans/2026-03-03-fix-triage-all-open-github-issues-plan.md
---

# Close Commented GitHub Issues and PRs

All 9 open issues and 2 open PRs on `mvanhorn/last30days-skill` were commented on (2026-03-03) with fix confirmations or responses, but none were actually closed on GitHub.

## Acceptance Criteria

- [ ] Close 6 issues where fixes were confirmed (#40, #39, #32, #30, #29, #4)
- [ ] Close PR #26 (superseded - features landed on main)
- [ ] Verify 3 issues remain open (#36, #31, #22) - acknowledged but unresolved
- [ ] Verify PR #24 remains open - explicitly left open per comment

## Actions

### Close as fixed (6 issues)

```bash
gh issue close 40 --repo mvanhorn/last30days-skill --reason completed
gh issue close 39 --repo mvanhorn/last30days-skill --reason completed
gh issue close 32 --repo mvanhorn/last30days-skill --reason completed
gh issue close 30 --repo mvanhorn/last30days-skill --reason completed
gh issue close 29 --repo mvanhorn/last30days-skill --reason completed
gh issue close 4  --repo mvanhorn/last30days-skill --reason completed
```

### Close superseded PR (#26)

```bash
gh pr close 26 --repo mvanhorn/last30days-skill
```

### Keep open (no action needed)

- #36 - SKILL.md flag forwarding (investigating)
- #31 - skills.sh audit scores (needs review)
- #22 - Bird feature requests (backlog)
- PR #24 - Codex compatibility (intentionally left open)

## Sources

- **Origin plan:** [docs/plans/2026-03-03-fix-triage-all-open-github-issues-plan.md](2026-03-03-fix-triage-all-open-github-issues-plan.md)
- Commit: `5e5d586` - fix: triage all 16 open GitHub issues
