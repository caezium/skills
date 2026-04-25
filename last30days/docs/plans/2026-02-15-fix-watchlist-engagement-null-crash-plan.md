---
title: "fix: watchlist engagement null crash"
type: fix
date: 2026-02-15
---

# fix: Watchlist crashes on `engagement: null` from X posts

## Problem

When X posts return `engagement: null` (JSON null) instead of `engagement: {}` (empty object), the watchlist `_run_topic` findings parser crashes. This is because Python's `dict.get("engagement", {})` returns `None` when the key **exists** with value `None` — the default `{}` only applies when the key is **missing**.

```python
# CRASHES — .get() returns None, not {}
item.get("engagement", {}).get("likes", 0)
# AttributeError: 'NoneType' object has no attribute 'get'
```

**Reporter:** Soft launch tester, 2026-02-15
**Severity:** Medium — breaks watchlist `run-one` and `run-all` for any topic that pulls X posts with null engagement
**One-shot research unaffected** — the main `last30days.py` pipeline uses `normalize.py` which has `isinstance(eng_raw, dict)` guards

## Root Cause

Two locations use the vulnerable `dict.get("key", {})` pattern:

1. **`scripts/watchlist.py:188`** — THE REPORTED BUG
   ```python
   "engagement_score": item.get("engagement", {}).get("likes", 0),
   ```

2. **`scripts/lib/normalize.py:177`** — YouTube normalizer (same pattern, latent)
   ```python
   eng_raw = item.get("engagement", {})
   ```

Three other locations are already safe — they use `isinstance(eng_raw, dict)`:
- `scripts/lib/normalize.py:70` (Reddit)
- `scripts/lib/normalize.py:130` (X)
- `scripts/lib/xai_x.py:190`

## Fix

Apply the `or {}` idiom (as suggested by reporter):

### scripts/watchlist.py:188

```python
# Before
"engagement_score": item.get("engagement", {}).get("likes", 0),
# After
"engagement_score": (item.get("engagement") or {}).get("likes", 0),
```

### scripts/lib/normalize.py:177

```python
# Before
eng_raw = item.get("engagement", {})
# After
eng_raw = item.get("engagement") or {}
```

## Acceptance Criteria

- [ ] `watchlist.py run-one` handles X posts with `engagement: null` without crashing
- [ ] `watchlist.py run-one` handles X posts with `engagement: {}` (empty object)
- [ ] `watchlist.py run-one` handles X posts with no engagement key at all
- [ ] YouTube normalizer handles `engagement: null` without crashing
- [ ] Existing tests still pass

## Regarding the screenshot question

The tester asked "Did you use watchlist on open claw or Claude?" — watchlist is designed for the **open variant** (Open Claw). It works in Claude Code too since it's just Python + SQLite, but the SKILL.md routing for watchlist commands is only in `variants/open/SKILL.md`. The main `SKILL.md` is one-shot research only.

Answer to give tester: "Watchlist works in both — it's plain Python. But the skill routing that understands 'watch add topic' is in the open variant. In Claude Code you'd need to call the script directly or use the open variant SKILL.md."
