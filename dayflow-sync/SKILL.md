---
name: dayflow-sync
description: Sync caezium/Dayflow fork with upstream JerryZLiu/Dayflow. Rebases private-hardening onto upstream/main, auto-skips known-droppable commits, runs audit + Debug build, then stops at a pre-install checkpoint and waits for the user to say "install". Use when the user says "/dayflow-sync", "sync dayflow", or asks to update the Dayflow fork.
allowed-tools: Bash,Read,Edit,Write
---

# Dayflow Sync

Weekly upstream sync routine for the `caezium/Dayflow` fork. Tracks
`JerryZLiu/Dayflow`.

## How it runs

Runs **mostly autonomously**, halting only at three named points. Each is
defined here only enough to name it; the mechanics live in one place — the
step that enforces it.

- **Tier A / Tier B** — per-commit conflict policy from `state/commits.yaml`,
  applied during the rebase (step 5). Tier A auto-skips known-droppable
  commits once their condition verifies; Tier B halts for hand re-porting.
- **Pre-install checkpoint** — after rebase + audit + Debug build, the skill
  **always stops** for a go-ahead before touching `/Applications/Dayflow.app`
  (step 9).

## Context

- Local clone: `~/Desktop/Dayflow`
- Fork remote (`origin`): `https://github.com/caezium/Dayflow`
- Upstream remote (`upstream`): `https://github.com/JerryZLiu/Dayflow`
- Integration branch: `private-hardening` — contains the security/privacy
  patches plus reimplemented bug fixes. **This is the branch the user
  builds from.** `main` mirrors `upstream/main` exactly.
- Per-commit metadata: `~/.claude/skills/dayflow-sync/state/commits.yaml`.
  Read at step 5 to decide conflict policy per commit.
- State markers: `~/.claude/skills/dayflow-sync/state/`
  - `last-synced-upstream.txt` — last upstream HEAD SHA processed
  - `last-synced-date.txt`
  - `last-drift-report.md` — written each run; diffable across runs

## Steps

### 1. Sanity check + disk hygiene (fail fast)

```bash
cd ~/Desktop/Dayflow
git remote -v
git status
git branch --show-current
df -h ~ | tail -1
```

Required state before proceeding:
- `origin` points to `https://github.com/caezium/Dayflow`
- `upstream` points to `https://github.com/JerryZLiu/Dayflow`
- Working tree clean (no uncommitted changes)
- Free space on `~` ≥ 4 GB

If working tree is dirty, **stop and ask the user**.

If free space < 4 GB, clean caches first:
```bash
rm -rf /tmp/dayflow-build /tmp/dayflow-release
# Prune oldest data backups beyond the last 4
ls -1dt "$HOME/Library/Application Support"/Dayflow.backup-* 2>/dev/null | tail -n +5 | xargs -I{} rm -rf "{}"
# Prune oldest app archives beyond the last 3
ls -1dt "$HOME/Library/Caches/dayflow-app-archive"/*.app 2>/dev/null | tail -n +4 | xargs -I{} rm -rf "{}"
df -h ~ | tail -1
```
If still under 4 GB after cleanup, **stop and report** — the user
needs to free space manually. Do not attempt a Release build under
4 GB free; ad-hoc-signing a half-built bundle has corrupted runs
in the past.

### 2. Fetch upstream

```bash
cd ~/Desktop/Dayflow
git fetch upstream --prune
git fetch origin --prune
```

Compare `git rev-parse upstream/main` against
`~/.claude/skills/dayflow-sync/state/last-synced-upstream.txt`.
If equal, **nothing changed upstream this week** — tell the user in one
line and exit. No rebase, no checkpoint, no install.

### 3. Show what's new upstream

```bash
git log <last-synced-sha>..upstream/main --oneline --no-merges
```

Summarize in plain English ("Upstream added N commits — bug fixes for
X, features for Y"). Don't dump the full log.

### 4. Update `main` to mirror upstream

```bash
cd ~/Desktop/Dayflow
git checkout main
git reset --hard upstream/main
git push origin main --force-with-lease
```

### 5. Rebase `private-hardening` with tiered conflict policy

```bash
cd ~/Desktop/Dayflow
git checkout private-hardening
git rebase main
```

**On conflict:**

1. Identify the conflicted commit:
   ```bash
   CONFLICT_SUBJECT=$(git log -1 --format='%s' REBASE_HEAD)
   ```

2. Read `~/.claude/skills/dayflow-sync/state/commits.yaml` and find the
   first entry whose `subject_match` is a substring of `$CONFLICT_SUBJECT`.

3. If no match found → **Tier B fallthrough**: stop and report (an
   unknown commit means commits.yaml is out of date; ask the user to
   update it before proceeding).

4. If matched entry has `on_conflict: stop` → **Tier B**: stop and
   surface full context:
   - Conflicted file paths (`git status`)
   - Conflicting hunks
   - Upstream's nearby change for each file
     (`git log main -p --follow -- <file> -1`)
   - The matched entry's `notes` field
   Ask the user how to resolve each conflict. After they choose,
   `git add` + `git rebase --continue`.

5. If matched entry has `on_conflict: auto_skip_if` → **Tier A**:
   - Capture the diff that *would* be re-introduced if we skip, so the
     pre-install summary can show it:
     ```bash
     mkdir -p ~/.claude/skills/dayflow-sync/state
     git diff REBASE_HEAD~1..REBASE_HEAD > ~/.claude/skills/dayflow-sync/state/last-skipped-commit.diff
     git log -1 --format='%H %s' REBASE_HEAD >> ~/.claude/skills/dayflow-sync/state/last-skipped-commit.diff
     ```
   - Evaluate `auto_skip_if.condition`:
     - `build_main_succeeds`: stash rebase state, run a quick Debug
       build of `main` (see step 8's command, but pointed at a fresh
       checkout of main in a worktree, or against current HEAD if the
       rebase is paused — the in-progress rebase leaves the worktree
       at a clean conflicted state, so `git stash` first):
       ```bash
       git stash push -u -m 'dayflow-sync conflict probe' || true
       git checkout main -- .
       xcodebuild build -scheme Dayflow -configuration Debug \
         -destination 'platform=macOS' -derivedDataPath /tmp/dayflow-probe \
         CODE_SIGNING_ALLOWED=NO 2>&1 | grep -E "error:|^\*\* BUILD" | head
       PROBE_RESULT=$?
       rm -rf /tmp/dayflow-probe
       git checkout REBASE_HEAD -- .
       git stash pop || true
       ```
       Look for `** BUILD SUCCEEDED **` in the probe output.
   - If condition met → `git rebase --skip`, log the skip, continue.
   - If condition NOT met → stop and report. The workaround is still
     needed; the user must port the revert forward by hand.

If rebase finishes clean, push:
```bash
git push origin private-hardening --force-with-lease
```

### 6. Re-run audit checks against the new tree

| Finding | Verify by |
|---|---|
| Telemetry default off | `grep -n 'return false' Dayflow/Dayflow/System/AnalyticsService.swift` shows the `isOptedIn` getter |
| No Keychain key prefix print | `! grep -n 'apiKey.prefix(8)' Dayflow/Dayflow/Core/Security/KeychainManager.swift` |
| No Host.localizedName super-prop | `! grep -n 'Host.current().localizedName' Dayflow/Dayflow/System/AnalyticsService.swift` |
| Feedback share-logs default false | `grep -n 'feedbackShareLogs = false' Dayflow/Dayflow/Views/UI/MainView/MainView.swift Dayflow/Dayflow/Views/UI/MainView/Actions.swift` (both must match) |
| Sparkle XPC disabled | `grep -A1 'SUEnableInstallerLauncherService' Dayflow/Dayflow/Info.plist` shows `<false/>` |
| Popover fullscreen | `grep -n 'fullScreenAuxiliary' Dayflow/Dayflow/System/StatusBarController.swift` |
| Onboarding persist deferred | `! grep -n 'persistGeminiAPIKey(source: "onboarding_step")' Dayflow/Dayflow/Views/Onboarding/ProviderSetupState.swift` |

If any check fails after rebase, **stop and tell the user** — a patch
got lost or was reordered weirdly. Don't push, don't proceed.

### 7. Drift detection + persistence

Re-scan upstream changes for new privacy/security surface area, and
**write the result to `state/last-drift-report.md`** so it survives
the session and can be diffed across runs.

```bash
SINCE=$(cat ~/.claude/skills/dayflow-sync/state/last-synced-upstream.txt)
UNTIL=$(git rev-parse upstream/main)
REPORT=~/.claude/skills/dayflow-sync/state/last-drift-report.md

{
  echo "# Drift report — $(date +%Y-%m-%d)"
  echo
  echo "Range: \`$SINCE\` .. \`$UNTIL\`"
  echo

  echo "## New external network endpoints"
  git diff "$SINCE..$UNTIL" -- '*.swift' \
    | grep -E '^\+.*https://' \
    | grep -v '://github\.com\|://docs\.\|://localhost\|aistudio\.google\.com\|developers\.openai\.com\|docs\.anthropic\.com' \
    || echo "_none_"
  echo

  echo "## New PostHog analytics events"
  git diff "$SINCE..$UNTIL" -- '*.swift' \
    | grep -E '^\+.*AnalyticsService\.shared\.capture\("' \
    | grep -oE '"[a-z_]+"' | sort -u \
    || echo "_none_"
  echo

  echo "## Entitlement / Info.plist diff"
  git diff "$SINCE..$UNTIL" -- \
    Dayflow/Dayflow/Dayflow.entitlements Dayflow/Dayflow/Info.plist \
    || echo "_no changes_"
} > "$REPORT"
```

Summarize for the pre-install checkpoint:
- **Endpoints**: anything non-Google/non-localhost — flag it.
- **Analytics events**: list them all; note any prefix you haven't
  seen in past runs (compare against prior `last-drift-report.md` if
  it exists).
- **Entitlements / Info.plist**: anything beyond version bumps — flag
  it. Especially watch for changes to `SUEnableInstallerLauncherService`,
  `SUEnableAutomaticChecks`, sandbox keys, or `com.apple.security.network.*`.

### 8. Verify Debug build

```bash
cd ~/Desktop/Dayflow/Dayflow
xcodebuild build -scheme Dayflow -configuration Debug \
  -destination 'platform=macOS' -derivedDataPath /tmp/dayflow-build \
  CODE_SIGNING_ALLOWED=NO 2>&1 | grep -E "error:|^\*\* BUILD" | head
rm -rf /tmp/dayflow-build
```

If the build fails:
- Errors in files my patches touched → **patch needs updating**. Stop.
- Errors in files only upstream touched → **upstream regression**.
  Tell the user; consider whether a new temporary-workaround entry
  in `commits.yaml` is warranted.

### 9. CHECKPOINT — pre-install summary

**Always stop here.** Do NOT proceed to step 10 until the user replies
with "install" (or some clear go-ahead). This is the hard gate before
the live binary is touched.

Present a glanceable summary, in this shape:

```
Dayflow sync — ready to install? (<upstream-version>, <N> upstream commits)

Rebase: clean / N conflicts auto-skipped / N conflicts manually resolved
  Auto-skipped: <commit subject> — condition met (<which>). See state/last-skipped-commit.diff
Audit (7 checks): all pass
Debug build: ** BUILD SUCCEEDED **

Drift (full report at state/last-drift-report.md):
  - <N> new endpoints (or "none beyond known-safe")
  - <N> new analytics events: <list-or-summary> (or "none")
  - Info.plist / entitlements: <summary, or "version bump only">

Reply "install" to proceed with Release build + install to /Applications.
Reply "abort" to stop without touching the installed app.
```

If anything looks off (new non-Google endpoint, new sandbox entitlement,
audit pass count below 7), explicitly recommend "abort" or "investigate
first" rather than "install."

### 10. (On user "install") Release build + install

Run only after the user says install.

1. **APFS-clone the data dir as a safety net:**
   ```bash
   STAMP=$(date +%Y%m%d-%H%M%S)
   cp -c -R "$HOME/Library/Application Support/Dayflow" \
     "$HOME/Library/Application Support/Dayflow.backup-$STAMP"
   ```

2. **Build Release:**
   ```bash
   cd ~/Desktop/Dayflow/Dayflow
   rm -rf /tmp/dayflow-release
   xcodebuild build -scheme Dayflow -configuration Release \
     -destination 'platform=macOS' -derivedDataPath /tmp/dayflow-release \
     CODE_SIGNING_ALLOWED=NO 2>&1 | grep -E "error:|^\*\* BUILD" | tail
   ```
   If build fails: **stop**. Don't touch the installed app.

3. **Quit running Dayflow:**
   ```bash
   osascript -e 'tell application "Dayflow" to quit' 2>/dev/null
   sleep 2
   pkill -f "/Applications/Dayflow.app/Contents/MacOS/Dayflow" 2>/dev/null || true
   ```

4. **Archive the currently-installed Dayflow.app** (keep last 3):
   ```bash
   ARCHIVE_DIR="$HOME/Library/Caches/dayflow-app-archive"
   mkdir -p "$ARCHIVE_DIR"
   if [ -d /Applications/Dayflow.app ]; then
     INSTALLED_VER=$(defaults read /Applications/Dayflow.app/Contents/Info CFBundleShortVersionString 2>/dev/null || echo "unknown")
     mv /Applications/Dayflow.app "$ARCHIVE_DIR/Dayflow-$INSTALLED_VER-$STAMP.app"
   fi
   ls -1dt "$ARCHIVE_DIR"/*.app | tail -n +4 | xargs -I{} rm -rf "{}"
   ```

5. **Install + sign with the stable local cert:**
   ```bash
   cp -R /tmp/dayflow-release/Build/Products/Release/Dayflow.app /Applications/Dayflow.app
   xattr -dr com.apple.quarantine /Applications/Dayflow.app 2>/dev/null || true
   codesign --force --deep --sign "Caezium Dayflow Local" /Applications/Dayflow.app
   ```
   The `Caezium Dayflow Local` identity is a self-signed code-signing
   cert created once in `~/Library/Keychains/login.keychain-db`. Signing
   every build with the same identity gives a stable code anchor across
   rebuilds, so TCC (Screen Recording) and the Keychain ACL (Gemini key)
   don't get re-prompted weekly.

   If `codesign` fails with `no identity found`, the cert was deleted —
   stop and tell the user; the rebuild flow is in a previous session.

6. **Free the build cache:**
   ```bash
   rm -rf /tmp/dayflow-release
   ```

7. **Sanity-check the installed bundle:**
   ```bash
   defaults read /Applications/Dayflow.app/Contents/Info CFBundleIdentifier   # must == teleportlabs.com.Dayflow
   defaults read /Applications/Dayflow.app/Contents/Info SUEnableAutomaticChecks  # must == 0
   codesign -dv /Applications/Dayflow.app 2>&1 | grep "Authority=Caezium Dayflow Local"
   ```
   If bundle id changed, **stop and tell the user** — the new build
   won't read existing data. If the Authority line is missing or shows
   `Signature=adhoc`, the cert wasn't used — stop and report.

**First-install warnings** — needed exactly once, when the installed
signature *changes*:
- Switching from official Developer-ID build → fork: re-grant Screen
  Recording, re-paste Gemini key. One-time.
- Switching from any prior ad-hoc-signed fork build → cert-signed fork
  build (i.e., the first install after introducing `Caezium Dayflow
  Local`): re-grant Screen Recording, re-paste Gemini key. One-time.
- All subsequent installs (cert → cert, same identity): no re-grant,
  no re-paste. This is the steady state.

### 11. Bump state markers

After successful install (or after step 6 if no install ran but rebase
was clean and the user explicitly chose "abort" — in the abort case
do NOT bump, so next run re-syncs):

```bash
mkdir -p ~/.claude/skills/dayflow-sync/state
git -C ~/Desktop/Dayflow rev-parse upstream/main > ~/.claude/skills/dayflow-sync/state/last-synced-upstream.txt
date +%Y-%m-%d > ~/.claude/skills/dayflow-sync/state/last-synced-date.txt
```

State marker advances ONLY after a successful end-to-end run. Aborts,
build failures, audit failures, and Tier B conflicts all leave the
marker at the previous SHA so the next run retries from the same base.

### 12. Final report (post-install)

Tell the user, under 200 words:
- N upstream commits merged, installed version
- Conflicts: auto-skipped (with which commit + condition met) vs.
  manually resolved
- Audit: pass/fail per check
- Debug + Release build results
- Bundle sanity-check: bundle id, Sparkle off, ad-hoc signed
- Drift summary (one line each for endpoints / events / entitlements)
- Any first-install permissions reminders (Screen Recording, Gemini key)

## Failure modes

- **Working tree dirty** → ask the user before anything.
- **Disk < 4 GB after cleanup** → stop, report, don't build.
- **Tier B rebase conflict** → stop with full context, never `--skip`.
- **Tier A auto-skip condition unmet** → stop, ask the user to port
  the workaround forward.
- **Unknown commit in conflict** → stop; commits.yaml needs updating.
- **Audit check fails after rebase** → stop, don't push, name the check.
- **Debug build fails** → stop, don't push, show the Swift error.
- **No upstream changes** → exit early, one-line report.
- **Pre-install checkpoint** → always stops here; not a failure, just
  the design.
