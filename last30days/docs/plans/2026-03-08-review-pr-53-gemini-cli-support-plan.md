---
title: "review: PR #53 - Gemini CLI Support"
type: review
status: active
date: 2026-03-08
---

# Review: PR #53 - Gemini CLI Support (alexferrari88)

## Verdict: MODIFY - Accept concept, reject implementation approach

PR #53 by @alexferrari88 adds Gemini CLI extension support. The intent is good and closes issue #45, but the implementation has structural problems that would create the exact maintenance nightmare we just fixed in v2.9.5.

## PR Summary

| File | Changes | Assessment |
|------|---------|------------|
| `gemini-extension.json` | +67 new file | **Accept with fixes** |
| `skills/last30days/SKILL.md` | +693 new file (full copy) | **Reject** - duplicate SKILL.md |
| `SKILL.md` | +9/-6 (tool name scattering) | **Reject** - wrong approach |
| `variants/open/SKILL.md` | +4/-1 | **Partially accept** (path resolution yes, tool names no) |
| `README.md` | +6 install instructions | **Accept** |

## Critical Issues

### 1. Duplicated SKILL.md (BLOCKER)

The PR creates `skills/last30days/SKILL.md` as a **full 693-line copy** of the root `SKILL.md`. This is the exact problem we just spent hours debugging - PR merges on March 7 regressed v2.9.4's save-section removal because branches had stale copies. A second SKILL.md guarantees this happens again.

The Codex compatibility work (see `docs/plans/2026-02-14-feat-codex-skill-compatibility-plan.md`) explicitly chose **one SKILL.md for all platforms** to avoid this. Gemini CLI should follow the same pattern.

**Fix:** Delete `skills/last30days/SKILL.md`. Gemini CLI discovers skills from the extension's `skills/` directory, but we can either:
- (a) Symlink: `skills/last30days/SKILL.md -> ../../SKILL.md`
- (b) Use the root SKILL.md directly and configure `contextFileName` in gemini-extension.json to point to it
- (c) Have `skills/last30days/SKILL.md` be a thin wrapper that says "See root SKILL.md" (least ideal)

### 2. Based on v2.9.1, not v2.9.5 (BLOCKER)

The PR's copy of SKILL.md is based on v2.9.1 and includes:
- The "Save Research to Documents" section (removed in v2.9.4, re-removed in v2.9.5)
- Old agent mode line referencing deleted section
- Missing `--save-dir=~/Documents/Last30Days` flag
- Old version number

**Fix:** Rebase on current main (v2.9.5).

### 3. "Or" tool name scattering (REJECT)

The PR adds `WebSearch or google_web_search(...)` and similar patterns throughout SKILL.md. This is the wrong approach because:

- **LLMs already translate intent to tools.** When Gemini reads "do a WebSearch for X", it knows to use `google_web_search`. When Claude reads it, it uses `WebSearch`. The model handles this mapping natively.
- **Clutters the prompt.** SKILL.md is a 640-line prompt. Adding "or alternative_name" to every tool reference makes it harder for the model to parse.
- **Maintenance burden.** Every new platform means adding more "or" alternatives.

**Fix:** Remove all "or" alternatives. Keep Claude Code tool names in the SKILL.md body (they work as intent descriptions). If Gemini needs explicit tool mapping, that belongs in `GEMINI.md` (Gemini CLI's context file), not scattered through the skill instructions.

### 4. `allowed-tools` pollution (RISKY)

Adding `run_shell_command, read_file, write_file, ask_user, google_web_search` to `allowed-tools`:

```
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch, run_shell_command, read_file, write_file, ask_user, google_web_search
```

**Risk:** If Claude Code's parser is strict and rejects unknown tool names, this breaks the skill for all Claude Code users. If it silently ignores unknown names, it's harmless but noisy.

**Finding:** Gemini CLI only recognizes `name` and `description` in SKILL.md frontmatter. It **ignores** `allowed-tools` entirely. So adding Gemini tool names to `allowed-tools` provides zero benefit to Gemini users while potentially breaking Claude Code users.

**Fix:** Remove Gemini tool names from `allowed-tools`. They serve no purpose on either platform.

## What to Accept

### 1. gemini-extension.json (with fixes)

The manifest file is the right approach. However:

- [ ] **Verify settings format.** The PR uses object-key format (`"SCRAPECREATORS_API_KEY": { ... }`). Gemini CLI docs show array format (`[{ "name": "...", ... }]`). Need to confirm which is correct for the current Gemini CLI version. The researcher found array format in the docs.
- [ ] **Update version** from `2.9.1` to `2.9.5`
- [ ] **Consider adding `contextFileName`** to point to root SKILL.md instead of duplicating

### 2. Path resolution additions

Adding these to the bash `for` loop is correct and low-risk:

```bash
"${GEMINI_EXTENSION_DIR:-}" \
"$HOME/.gemini/extensions/last30days-skill" \
"$HOME/.gemini/extensions/last30days" \
```

This should be in both `SKILL.md` and `variants/open/SKILL.md`.

### 3. README.md install section

Clean and appropriate. Adding Gemini CLI install command before Claude Code section.

## Proposed Changes to Request from Contributor

### Must-fix (before merge)

1. **Delete `skills/last30days/SKILL.md`** - no duplicate. Either symlink or use `contextFileName` in manifest.
2. **Rebase on main** (v2.9.5) - the PR is based on stale code.
3. **Remove all "or" tool name alternatives** from SKILL.md and variants/open/SKILL.md body text.
4. **Remove Gemini tool names from `allowed-tools`** in all SKILL.md files.
5. **Verify `gemini-extension.json` settings format** against current Gemini CLI docs (array vs object).

### Nice-to-have

6. **Add a `GEMINI.md` context file** (optional) - can include a short note like "When this skill references 'WebSearch', use `google_web_search`. When it references 'Bash', use `run_shell_command`." This is the clean way to handle tool name translation.
7. **Update sync.sh** to optionally deploy to `~/.gemini/extensions/last30days/` (debatable - Gemini users may prefer `gemini extensions install` instead).
8. **Add `.gemini/` to the path check in sync.sh** import verification.

## Testing Plan

Before merging, verify:

- [ ] `gemini extensions install` works from the repo (or `gemini extensions link .` for local dev)
- [ ] Skill activates in Gemini CLI and the model can find `scripts/last30days.py`
- [ ] `GEMINI_EXTENSION_DIR` env var resolves correctly in the bash for-loop
- [ ] Claude Code still works with no regressions (run `/last30days test topic --mock` or similar)
- [ ] `allowed-tools` with only Claude Code tool names doesn't break Gemini CLI skill loading

## Comment Template for PR

```
Thanks for the contribution! Gemini CLI support is great to have, and the `gemini-extension.json` manifest and path resolution additions are solid.

A few things need changing before we can merge:

**Must-fix:**

1. **Remove `skills/last30days/SKILL.md`** - We maintain one SKILL.md to avoid sync drift (we literally just fixed a regression from this exact problem yesterday). Either symlink it or use `contextFileName` in the manifest to point to the root SKILL.md.

2. **Rebase on `main`** - The PR is based on v2.9.1 but we're now at v2.9.5. The "Save Research to Documents" section in your copy was removed, `--save-dir` was added to the bash command, and the version was bumped.

3. **Remove "or" tool name alternatives** from SKILL.md body (e.g., `WebSearch or google_web_search`). LLMs handle tool name translation natively - Gemini knows to use `google_web_search` when the skill says "search the web". Scattering alternatives clutters the prompt.

4. **Remove Gemini tool names from `allowed-tools`** - Gemini CLI ignores `allowed-tools` (it only reads `name` and `description` from SKILL.md frontmatter), so these provide no benefit. And they risk breaking Claude Code if its parser rejects unknown tool names.

5. **Verify `gemini-extension.json` settings format** - The Gemini CLI docs I found show settings as an array (`[{ "name": "...", ... }]`), not object keys (`{ "KEY": { ... } }`). Can you confirm which format your Gemini CLI version expects?

**Optional but recommended:**

6. Consider adding a `GEMINI.md` context file with a short tool-name translation note (e.g., "When this skill says 'WebSearch', use `google_web_search`"). This is the clean way to bridge tool names.

Happy to help work through any of these! The core approach (manifest + path resolution) is right.
```

## Sources

- PR #53: https://github.com/mvanhorn/last30days-skill/pull/53
- Issue #45: https://github.com/mvanhorn/last30days-skill/issues/45
- Gemini CLI extension docs: https://geminicli.com/docs/extensions/writing-extensions/
- Gemini CLI extension reference: https://geminicli.com/docs/extensions/reference/
- Gemini CLI skills docs: https://geminicli.com/docs/cli/creating-skills/
- Codex compatibility plan: `docs/plans/2026-02-14-feat-codex-skill-compatibility-plan.md`
- v2.9.5 regression fix: commit `8f7fb5a` (today)
