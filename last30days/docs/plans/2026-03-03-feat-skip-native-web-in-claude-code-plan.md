# feat: Skip native web search when running in Claude Code

**Type:** enhancement
**Date:** 2026-03-03
**Detail level:** MINIMAL

## Problem

When `/last30days` runs in Claude Code, web search happens twice:
1. The Python script uses Parallel AI / Brave / OpenRouter (costs API credits)
2. SKILL.md tells Claude to run its built-in WebSearch tool (free, better quality)

This is redundant. Claude's WebSearch is better and free. In OpenClaw, there's no WebSearch tool, so native backends are essential there.

## Solution

Add a `--no-native-web` CLI flag to `last30days.py`. When set, the script skips native web search backends even if API keys are configured, and emits the `### WEBSEARCH REQUIRED ###` signal so the assistant handles it.

Update SKILL.md invocation to include the flag.

## Changes

### 1. `scripts/last30days.py`
- [ ] Add `--no-native-web` argument to argparse (store_true, default False)
- [ ] When `args.no_native_web` is True, force `web_backend = None` regardless of API keys
- [ ] This naturally triggers `web_needed = True` → emits `### WEBSEARCH REQUIRED ###` signal
- [ ] Update diagnostic banner to show "Web: deferred to assistant" when flag is active

### 2. `SKILL.md`
- [ ] Add `--no-native-web` to the invocation command on line 168:
  ```
  python3 "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=compact --no-native-web
  ```

### 3. OpenClaw / `--agent` mode
- [ ] No changes needed — OpenClaw invocations don't read SKILL.md, they call the script directly without `--no-native-web`, so Parallel AI/Brave/OpenRouter still work

## Acceptance Criteria

- [ ] Claude Code sessions: script skips Parallel AI, Claude uses WebSearch (no API credits spent)
- [ ] OpenClaw sessions: script still uses Parallel AI / Brave / OpenRouter as before
- [ ] `--no-native-web` flag can be combined with `--include-web` (flag wins, web deferred)
- [ ] Diagnostic output clearly shows web is deferred to assistant
