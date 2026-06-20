---
name: app-screenshots
description: >-
  Capture and curate screenshots of a GUI desktop app for a README, landing
  page, app-store listing, or docs. Use when the user wants to take or refresh
  app screenshots — especially after a UI/redesign change. The user "records"
  the app's flows once (driving the GUI) while the agent continuously
  screenshots; the agent then identifies each screen, dedupes, selects,
  compresses, and places the right shots for the target — automatically by
  convention, or to the user's specific request. Triggers: "take/update/refresh
  screenshots", "shoot the landing page / README", "screenshots for the app
  store", "capture the app's screens", "record the app for screenshots".
metadata:
  type: reference
---

# App screenshots — record once, agent curates

Take polished, current screenshots of a GUI app and drop them where they're
needed (README grid, landing-page gallery, store listing, docs). The human does
the smallest possible amount of work: **record the flows once**. The agent does
the rest — capturing, identifying which screen is which, deduping, choosing the
right frames for the target, compressing, and wiring them in.

Two modes, same recording:
- **Auto** — agent infers what the target conventionally needs (hero, each key
  pane, before/after action states) and selects from the recording.
- **Directed** — user says "I need the Clean *running* state" → agent finds that
  exact frame in the recording.

---

## ⚠️ The one gotcha that breaks everything (read first)

`screencapture -l<windowID>` and the on-screen window list (`CGWindowList…
OnScreenOnly`) **only see a window that is composited on the *active* Space and
not minimized.** A window on another Desktop/Space, minimized, or fully occluded
returns **"could not create image from window"** or simply isn't listed — so a
capture loop silently produces nothing.

This is NOT display sleep. Symptoms look identical (blank/failed captures) but
the cause is window focus/Space. Before *every* capture:

1. **Foreground the target app** (`open -a`, or activate by bundle id), and
2. confirm its window is in the on-screen list before shooting.

In a capture loop, re-activate each cycle (or verify the window id resolves and
skip+log the cycle if it doesn't). The classic failure: launch the app detached
(`nohup …&`) without activating, the window opens on a background Space, and the
whole loop captures zero frames until the user happens to bring it forward.

```bash
# Activate, then verify the window is actually on-screen before capturing.
osascript -e 'tell application id "com.example.App" to activate'; sleep 1
winid() { swift /tmp/winid.swift 2>/dev/null \
  | awk -F'\t' '$2=="App" && $4=="layer=0"{split($3,d,"x"); if(d[1]+0>600&&d[2]+0>400) print $1}' | head -1; }
id=$(winid); [ -n "$id" ] && screencapture -x -l"$id" -o frame.png || echo "window not on active Space — skip"
```

---

## Workflow

### 1. Scope it
- **App + how to reach each screen.** Find the launch command (or built `.app`).
  Many apps expose a dev/launch hook to open a specific pane non-interactively
  (e.g. an env var like `APP_OPEN_ON_LAUNCH=<pane>`). Grep the code for one; it
  turns static panes into scriptable, no-click captures. Sections behind a
  segmented control or that need a button click are *not* reachable this way —
  those go in the recording (step 2b).
- **Target + its shot list.** READMEs want a feature grid (each pane) + action
  states (before/after a scan/run). Landing pages want a hero + a tab gallery.
  Store listings want N specific sizes. Pin down the list before capturing.
- **Check the app's current IA.** Panes get renamed, merged, or folded between
  versions. Verify the *current* structure (don't trust an old screenshot set) —
  if two tools folded into one hub, the old separate shots are stale.

### 2. Capture

**2a. Non-interactive panes (no human needed).** Launch the app once per pane
via the launch hook, foreground it, capture the window. Force a consistent theme
(e.g. an appearance env var) and consistent window size so the set matches.
Some panes auto-run work on entry (a dashboard, an auto-scan) — wait for them to
populate (poll the frame) before capturing.

**2b. Interactive states — "record once".** Scans, runs, multi-step flows, and
any state reached by clicking can't be scripted cleanly (and driving the user's
mouse may be unavailable or unwanted). So:
1. Launch the app and **tell the user exactly what to click** ("open Clean → a
   category → Scan; then Optimize → Run; enter your password if asked").
2. Run a **foregrounded capture loop** — a frame every ~1.5–2 s for a generous
   window (≥2 min) — while they drive. They click; you screenshot. **Keep the
   window foregrounded** (the gotcha above) or the loop captures nothing.
3. The user only records **once**; you mine the frames for every state they
   passed through.

> Driving the GUI yourself (computer-use) is an option *only if available and the
> user agrees*. Default to "tell the user to click, you screenshot." Never auto-
> trigger destructive/privileged actions (cache deletion, maintenance needing a
> password) for a screenshot — capture the non-destructive states (scan/preview),
> and let the user run + auth the rest if they want those frames.

### 3. Identify + index
For each frame, **read it** (you can view images) and classify pane + state from
the on-screen text (headers, breadcrumbs, button labels) plus what you know about
the app. Build a frame→(feature, state) index. Cheap pre-filter: cluster frames
by file size to find transitions (a run of identical sizes = a static screen;
varying sizes = an animating/in-progress screen) so you read only representatives.

### 4. Select + dedupe
- **Auto:** map the index onto the target's shot list (hero, each pane, the
  best before/after).
- **Directed:** locate the user's named state in the index.
- Pick the **clearest, most-populated** frame per state; drop blurry transitions
  and half-loaded screens. Prefer a "result with data" over an empty just-started
  frame.

### 5. Process + place
- **Compress.** Raw retina PNGs are ~2–3 MB each; `pngquant --quality 60-85
  --strip` cuts them to ~300–500 KB with no visible loss (`brew install pngquant`
  if missing). Match the existing assets' dimensions so the layout doesn't shift.
- **Place + wire.** Overwrite the existing asset filenames where possible (the
  doc keeps working), or add new ones and update the references. In a README,
  prefer **repo-relative** image paths (`docs/assets/shot-x.png`) — GitHub
  resolves them per-branch, so they render on the PR and after merge.
- **Update structure if the IA changed** (drop folded tabs/rows; relabel hubs).
- Open a PR; the human reviews the composed result (you often can't render the
  final page locally).

---

## Privacy — real screens show real data
Without a demo/sample-data mode, every shot shows the user's actual machine
(installed apps, file/folder names in a disk treemap, running processes, disk
figures). A PR is **public the moment you push.** So:
- Confirm the user is OK publishing real data, or
- Point data views at neutral targets (e.g. a disk analyzer at `/Applications`),
  favor metric/hero panes (no personal data), and review each frame for anything
  too personal before it goes public.
- A small **demo-data mode** (curated fixtures behind a flag) is the
  professional long-term fix — clean, consistent, repeatable for every release.

---

## Gotchas checklist
- [ ] Window foregrounded / on the active Space before each capture (THE bug).
- [ ] `screencapture -l<id>` for clean window-only shots (no cursor, no desktop);
      computer-use screenshots include the whole screen + cursor.
- [ ] Consistent theme + window size across the whole set.
- [ ] Auto-running panes: poll until populated before shooting.
- [ ] Interactive states: record-once loop; the user clicks, you screenshot.
- [ ] Never auto-run destructive/privileged actions for a shot.
- [ ] Verify the app's *current* IA; drop stale/folded panes.
- [ ] Compress (pngquant) + match existing dimensions.
- [ ] README: repo-relative image paths.
- [ ] Real-machine data is public on push — get consent / neutralize / review.
