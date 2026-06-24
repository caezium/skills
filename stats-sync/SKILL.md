---
name: stats-sync
description: Sync caezium/stats fork with upstream exelban/stats. Rebases henry/history-mcp onto upstream/master, stops on any conflict, runs the feature-presence audit + Swift tests + Debug build, then halts at a pre-install checkpoint and waits for the user to say "install". Use when the user says "/stats-sync", "sync stats", or asks to update the Stats fork.
allowed-tools: Bash,Read,Edit,Write
---

# Stats Sync

Routine for keeping the `caezium/stats` fork up to date with
`exelban/stats`. The fork's value is everything in `henry/history-mcp`:
a long-running history DB, an MCP query server, a SwiftUI History view,
configurable retention/tier policy, reader energy gating, and the test
scaffold. **None** of that exists upstream — every commit on
`henry/history-mcp` is load-bearing and must survive every sync.

## Conflict policy: stop on every conflict

Unlike `dayflow-sync` there is no per-commit yaml and no auto-skip class.
The fork has only ~15 commits and they're all features — there's nothing
safe to drop. On any rebase conflict: stop with full context and ask the
user how to resolve.

## Pre-install checkpoint

After rebase + audit + tests + Debug build pass, the skill **always
stops** with a glanceable summary and waits for the user to reply
"install" (or "abort"). It never auto-touches `/Applications/Stats.app`
because the user's `~/Library/Application Support/Stats/lldb` is real
data — multiple gigabytes of their accumulated history — and a botched
install loses it.

## Context

- Local clone: `~/Desktop/stats`
- Fork remote (`origin`): `https://github.com/caezium/stats`
- Upstream remote (`upstream`): `https://github.com/exelban/stats`
- Upstream's default branch is **`master`** (not `main` — it's an older
  project)
- Integration branch: `henry/history-mcp` — this is what the user
  builds from. The fork has no equivalent of dayflow's "main mirrors
  upstream" pattern; we only track upstream by SHA in state.
- State directory: `~/.claude/skills/stats-sync/state/`
  - `last-synced-upstream.txt` — last upstream/master SHA processed
  - `last-synced-date.txt`
  - `last-skipped-commits.log` — empty in practice (we never skip)

## Steps

### 1. Sanity check

```bash
cd ~/Desktop/stats
git remote -v
git status --short
git branch --show-current
df -h ~ | tail -1
```

Required state before proceeding:
- `origin` points to `https://github.com/caezium/stats.git`
- `upstream` points to `https://github.com/exelban/stats.git`
- Working tree clean (no uncommitted changes, no untracked source files —
  `.claude/` worktrees are fine)
- Current branch is `henry/history-mcp` (if not, ask the user before
  switching — they may be mid-feature on something else)
- Free space on `~` ≥ 4 GB (Stats's lldb can be 1–2 GB and Xcode needs
  room for module cache + build_dist)

If the working tree is dirty, **stop and ask**.
If disk < 4 GB, suggest the user clean their Spotify/swiftpm caches; do
not delete anything automatically. The Stats lldb is precious.

### 2. Fetch upstream

```bash
cd ~/Desktop/stats
git fetch upstream --prune
git fetch origin --prune
```

Compare `git rev-parse upstream/master` against
`~/.claude/skills/stats-sync/state/last-synced-upstream.txt`.
If equal, **nothing changed upstream** — tell the user in one line and
exit. No rebase, no audit, no checkpoint.

### 3. Show what's new upstream

```bash
SINCE=$(cat ~/.claude/skills/stats-sync/state/last-synced-upstream.txt)
git log "$SINCE..upstream/master" --oneline --no-merges
git log "$SINCE..upstream/master" --no-merges --shortstat | tail -5
```

Summarize in plain English ("Upstream added N commits since vX.Y.Z —
mostly bug fixes for the GPU module" / similar). Also note any new tags
(`git tag --contains upstream/master` minus the previous synced tag).
Don't dump the full log into the user's reading view.

### 4. Rebase `henry/history-mcp` onto `upstream/master`

```bash
cd ~/Desktop/stats
git checkout henry/history-mcp
git rebase upstream/master
```

**On any conflict:**

1. Capture context:
   ```bash
   git status                                 # which files
   CONFLICT_SUBJECT=$(git log -1 --format='%s' REBASE_HEAD)
   echo "Conflict during: $CONFLICT_SUBJECT"
   ```
2. For each conflicted file, show:
   - Our hunks (`<<<<<<<` to `=======`)
   - Their hunks (`=======` to `>>>>>>>`)
   - Upstream's nearby intent: `git log upstream/master -p -1 -- <file>`
3. **Always stop and surface the conflict to the user.** Never
   `git rebase --skip` — every commit on `henry/history-mcp` is a
   feature that must survive.
4. After the user dictates the resolution: `git add <files>`,
   `git rebase --continue`. If the rebase chains into another conflict,
   repeat from (1).

Common conflict files to flag with extra care (these are where the
fork's most load-bearing patches live):
- `Kit/module/reader.swift` — base Reader class with `tick()`,
  `selfPersists`, `lastReadAt`, `historyCadenceSeconds`,
  `popupClosedIntervalMultiplier`. Upstream often re-edits this.
- `Modules/CPU/readers.swift` — FrequencyReader Task `defer` fix.
- `Modules/Net/main.swift` + `Modules/Net/readers.swift` — `selfPersists: true`
  wiring on Net readers + setup() overrides for multiplier=1.
- `Stats/Views/AppSettings.swift` — History storage UX.
- `Kit/plugins/DB.swift` (entirely fork-introduced, conflicts unlikely
  unless upstream adds something at the same path).

If `git rebase --abort` becomes necessary, do it and **stop**. Don't try
again with `-Xours/-Xtheirs` — wrong-default merges silently destroy
features.

After a clean rebase:
```bash
git push origin henry/history-mcp --force-with-lease
```

### 5. Feature-presence audit

Every grep below must match. If any FAILS, a patch got lost during the
rebase — **stop and report** which one. Don't push, don't proceed.

| Feature | Verify by |
|---|---|
| History DB exists | `[ -f Kit/plugins/DB.swift ]` |
| NetTierPolicy + tier configurability | `grep -q "public struct NetTierPolicy" Kit/plugins/DB.swift` |
| Drop sentinel for past-hour-tier rows | `grep -q "dropSentinel" Kit/plugins/DB.swift` |
| LLDB compactRange | `grep -q "compactRange" Kit/lldb/lldb.h && grep -q "CompactRange" Kit/lldb/lldb.m` |
| Hourly maintenance calls compactRange | `grep -q "compactRange()" Kit/plugins/DB.swift` |
| ttlDaysOverride test hook | `grep -q "ttlDaysOverride" Kit/plugins/DB.swift` |
| QueryServer / MCP | `[ -f Kit/plugins/QueryServer.swift ] && grep -q "case \"/info\"" Kit/plugins/QueryServer.swift` |
| QueryServer staleness | `grep -q "age_seconds" Kit/plugins/QueryServer.swift` |
| History view | `[ -f Stats/Views/HistoryView.swift ]` |
| History view: 30 d / 90 d range chips | `grep -q '"30d"' Stats/Views/HistoryView.swift && grep -q '"90d"' Stats/Views/HistoryView.swift` |
| Stride-sampled top-N | `grep -q "findTimeSeriesSampled" Stats/Views/HistoryView.swift` |
| Staleness warning chip | `grep -q "staleReaderCount" Stats/Views/HistoryView.swift` |
| Reader tick gating | `grep -q "popupClosedIntervalMultiplier" Kit/module/reader.swift && grep -q "internal func tick" Kit/module/reader.swift` |
| Reader 60 s history cadence | `grep -q "historyCadenceSeconds" Kit/module/reader.swift` |
| Reader selfPersists flag | `grep -q "selfPersists" Kit/module/reader.swift` |
| Reader lastReadAt diagnostics | `grep -q "lastReadAt" Kit/module/reader.swift` |
| FrequencyReader defer fix | `grep -q "defer { self.isReading = false }" Modules/CPU/readers.swift` |
| Net selfPersists wiring | `grep -q "selfPersists: true" Modules/Net/main.swift` |
| Net readers opt out of gate | `grep -q "popupClosedIntervalMultiplier = 1" Modules/Net/readers.swift` |
| History storage settings UX | `grep -q "Keep detailed data for" Stats/Views/AppSettings.swift && grep -q "Keep summary data for" Stats/Views/AppSettings.swift` |
| Option lists | `grep -q "HistoryDetailedDaysOptions" Kit/types.swift && grep -q "HistorySummaryDaysOptions" Kit/types.swift` |
| Test scaffold present | `[ -f Tests/HistoryDB.swift ]` |
| ReaderTickTests present | `grep -q "final class ReaderTickTests" Tests/HistoryDB.swift` |

Run these as a single bash block; collect failures into a list. Any
non-zero exit means a patch got lost in the rebase.

### 6. Run the Swift tests

```bash
cd ~/Desktop/stats
xcodebuild -project Stats.xcodeproj -scheme Stats \
  -configuration Debug -destination 'platform=macOS' \
  -derivedDataPath /tmp/stats-sync-build \
  CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO \
  test 2>&1 \
  | grep -E "error:|Test Case.*(failed)|TEST (SUCCEEDED|FAILED)|Executed [0-9]+ test" \
  | tail -15
```

Expected: `** TEST SUCCEEDED **` with all tests passing (currently 27
total: 17 HistoryDBTests + 3 RAMTests + 7 ReaderTickTests; this number
will grow over time).

Note the trailing `** TEST FAILED **` line that sometimes appears
*after* a successful test run is from the test host binary trying to
open the live lldb while running Stats holds its LOCK. That's a
**pre-existing nuisance, not a real failure** — verify by the
`Executed N tests, with 0 failures` count just above it.

If real test failures appear: **stop, don't push, don't install**.
Show the failure to the user.

### 7. Debug build (final verification before the install checkpoint)

```bash
cd ~/Desktop/stats
xcodebuild -project Stats.xcodeproj -scheme Stats \
  -configuration Debug -destination 'generic/platform=macOS' \
  -derivedDataPath /tmp/stats-sync-build \
  CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO \
  build 2>&1 \
  | grep -E "error:|BUILD (SUCCEEDED|FAILED)" \
  | tail -10
```

Expected: `** BUILD SUCCEEDED **`. The test step (6) already builds
everything but a separate `build` invocation catches errors that only
surface for the non-test target.

If the build fails:
- Errors in files our patches touched → **patch needs updating**. Stop.
- Errors in files only upstream touched → upstream regression in this
  release. Tell the user; usually means waiting for the next upstream
  patch or porting a workaround.

### 8. Pre-install checkpoint

**Always stop here.** Do NOT proceed to step 9 unless the user replies
"install" or similar. This is the hard gate before
`/Applications/Stats.app` is touched.

Present a glanceable summary in this shape:

```
Stats sync — ready to install? (<upstream version tag>, <N> upstream commits)

Rebase: clean / <N> conflicts manually resolved
  Conflicts on: <file paths if any>
Audit (~22 grep checks): all pass / N failed
Tests: ** TEST SUCCEEDED ** — <N> executed, 0 failures
Debug build: ** BUILD SUCCEEDED **

What changed upstream:
  - <one bullet per upstream commit, summarized — e.g. "GPU fan curve fix">
  - <if there's an upstream version tag in this range, name it>

Currently installed: <bundle version of /Applications/Stats.app, if installed>
Will be installed: Debug build from /tmp/stats-sync-build

Reply "install" to proceed with quit-Stats + install-to-/Applications
+ live-endpoint verify.
Reply "abort" to leave the rebased branch on the remote without
touching the live app.
```

If anything looks off (audit failure, suspicious upstream commit
touching reader/DB code), explicitly recommend "abort" or "investigate
first" rather than "install".

### 9. (On user "install") Quit + install + verify

Run only after the user explicitly says "install".

```bash
# 1. Quit currently-running Stats
osascript -e 'tell application "Stats" to quit' 2>/dev/null
sleep 3
pkill -9 -f Stats.app/Contents/MacOS/Stats 2>/dev/null || true
sleep 1

# 2. Replace /Applications/Stats.app
rm -rf /Applications/Stats.app
cp -R /tmp/stats-sync-build/Build/Products/Debug/Stats.app /Applications/Stats.app
xattr -cr /Applications/Stats.app

# 3. Launch
open /Applications/Stats.app
sleep 6
PID=$(pgrep -fl Stats.app/Contents/MacOS/Stats | head -1 | awk '{print $1}')
echo "Stats running: pid=$PID"

# 4. Free build cache
rm -rf /tmp/stats-sync-build
```

**Note: no data backup is needed.** The lldb format is forward-compatible
within this fork's schema — every commit on `henry/history-mcp` preserves
the on-disk layout. If a future commit ever changes that, add a backup
step here before it ships.

**Verify the live endpoints** (gives confidence the install survived):

```bash
sleep 4    # let QueryServer come up
curl -s http://127.0.0.1:9276/health
curl -s http://127.0.0.1:9276/info \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
readers = d.get('readers', [])
stale = [r for r in readers if r.get('age_seconds') is not None and r['age_seconds'] > 300]
print(f'prefixes={len(d[\"prefixes\"])}, readers={len(readers)}, stale_at_startup={len(stale)}')
"
```

Expected:
- `/health` returns `{"ok":true,"app":"Stats","port":9276}`
- `/info` returns at least 10 prefixes; `stale_at_startup` may be a few
  (some readers don't fire until a popup-open event), no warning yet.

If `/health` fails to respond after 8 seconds total, **stop and report** —
the QueryServer didn't come up. Probable causes: port collision, the
build is missing the QueryServer file (which would have failed step 5),
or auto-update tried to validate the install and bailed (the unsigned
build doesn't carry a team ID — see the alert message from past
sessions).

### 10. Bump state markers

After successful end-to-end run (install succeeded + endpoints
verified):

```bash
git -C ~/Desktop/stats rev-parse upstream/master \
  > ~/.claude/skills/stats-sync/state/last-synced-upstream.txt
date +%Y-%m-%d > ~/.claude/skills/stats-sync/state/last-synced-date.txt
```

State marker advances ONLY after install succeeds AND endpoints respond.
Aborts, conflicts, audit failures, test failures, build failures, and
QueryServer no-shows all leave the marker at the previous SHA so the
next run retries from the same base.

### 11. Final report

Tell the user, under 200 words:
- Upstream version + N commits merged
- Conflicts: how many, which files (if any)
- Audit: pass/fail
- Tests: pass count
- Build: succeeded
- Install: bundle version, QueryServer responsive at the expected port
- Anything notable in the upstream changes (e.g. "GPU module gained a
  new metric — visible in your charts next time the GPU module is
  reloaded")

## Failure modes

- **Working tree dirty** → ask the user before anything.
- **Not on `henry/history-mcp`** → ask, don't auto-switch.
- **Disk < 4 GB** → stop, suggest cache cleanup, don't auto-delete.
- **Rebase conflict** → stop with full context, never `--skip`.
- **Feature-presence audit failure** → stop, name the missing patch.
- **Test failures** → stop, don't push, surface the failure.
- **Build failure** → stop, don't push, classify (our files vs upstream).
- **No upstream changes** → exit early, one-line report.
- **Pre-install checkpoint** → always stops here; not a failure.
- **`/health` no-show after install** → stop, report; the install
  binary may be broken or port-collided.
