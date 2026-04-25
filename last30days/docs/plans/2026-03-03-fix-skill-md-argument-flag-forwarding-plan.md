---
title: Fix SKILL.md Argument Flag Forwarding
type: fix
status: completed
date: 2026-03-03
---

# Fix SKILL.md Argument Flag Forwarding

## Overview

`"$ARGUMENTS"` in SKILL.md wraps the entire user input in double quotes, making argparse treat flags like `--store` as part of the topic string instead of CLI flags.

## Problem

SKILL.md line 168:
```bash
python3 "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=compact --no-native-web
```

`$ARGUMENTS` is a Claude Code template variable replaced via string substitution before bash runs. The double quotes cause word-joining:

- User types: `/last30days AI video tools --store`
- Claude Code expands to: `python3 script.py "AI video tools --store" --emit=compact`
- argparse sees: `topic="AI video tools --store"`, `--store` never parsed

## Proposed Solution

Two coordinated changes:

### 1. Remove quotes around `$ARGUMENTS` in SKILL.md

**File:** `SKILL.md:168`

```bash
# Before:
python3 "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=compact --no-native-web

# After:
python3 "${SKILL_ROOT}/scripts/last30days.py" $ARGUMENTS --emit=compact --no-native-web
```

Now bash word-splits the expansion: `python3 script.py AI video tools --store --emit=compact`

### 2. Change argparse `topic` from `nargs="?"` to `nargs="*"`

**File:** `scripts/last30days.py:1040`

```python
# Before:
parser.add_argument("topic", nargs="?", help="Topic to research")
# args.topic = "AI video tools" (single string) or None

# After:
parser.add_argument("topic", nargs="*", help="Topic to research")
# args.topic = ["AI", "video", "tools"] (list) or []
```

Then immediately after `parser.parse_args()` (line 1124), join the list back to a string:

```python
args = parser.parse_args()
args.topic = " ".join(args.topic) if args.topic else None
```

**Why this works for both invocation styles:**

| Invocation | argparse receives | topic result |
|---|---|---|
| `script.py AI video tools --store` (Claude Code) | `["AI", "video", "tools"]` + `--store` | `"AI video tools"` |
| `script.py "AI video tools" --store` (direct CLI) | `["AI video tools"]` + `--store` | `"AI video tools"` |
| `script.py --store` (no topic) | `[]` + `--store` | `None` |

### 3. Document missing flags in SKILL.md Options section

**File:** `SKILL.md:223-227`

Add after the existing `--deep` line:

```
- `--store` -> Persist findings to SQLite database for later querying
- `--search=SOURCES` -> Comma-separated source filter (e.g., `--search=reddit,hn`)
- `--include-web` -> Include general web search alongside primary sources
- `--diagnose` -> Show source availability diagnostics and exit
- `--timeout=SECS` -> Global timeout in seconds (default: 180, quick: 90, deep: 300)
```

Note: `--sort-x` was listed in the issue but does not exist in the Python argparse. Skip it.

## Acceptance Criteria

- [x] `/last30days AI video tools --store` correctly passes `--store` to Python script
- [x] `/last30days AI video tools` still works (multi-word topic without flags)
- [x] Direct CLI: `python3 last30days.py "AI video tools" --store` still works
- [x] `--diagnose`, `--search=reddit,hn`, `--timeout=120` all forward correctly
- [x] All 5 missing flags documented in SKILL.md Options section
- [x] Existing tests pass (`python3 -m pytest tests/`)

## Files Changed

| File | Change |
|---|---|
| `SKILL.md:168` | Remove quotes around `$ARGUMENTS` |
| `scripts/last30days.py:1040` | `nargs="?"` -> `nargs="*"` |
| `scripts/last30days.py:1124` | Add `args.topic = " ".join(args.topic) if args.topic else None` |
| `SKILL.md:223-227` | Add 5 missing flags to Options section |

## Sources

- GitHub issue: https://github.com/mvanhorn/last30days-skill/issues/36
- Reporter: @nicolefinateri
