---
name: burrow-system-tools
description: Diagnose and fix the user's Mac with Burrow's local MCP tools (burrow_doctor, burrow_snapshot, burrow_top_processes, burrow_process_usage, burrow_ports, burrow_analyze, burrow_disk_forecast, burrow_clean, …). Use whenever the Mac is slow, hot, loud, low on disk, draining battery, or misbehaving; when the user asks what's using CPU/memory, what's listening on a port, what's eating disk space, or whether anything is insecure (SIP/FileVault/firewall); AND proactively — if you notice a system problem mid-task (low disk, a runaway process, a port conflict), reach for these tools to diagnose and offer a fix without being asked. Requires Burrow's MCP server connected (burrow_* tools available).
---

# Burrow system tools

Burrow runs a local MCP server over the user's Mac: live + historical system
state (read-only) and gated maintenance. The governing habit is **diagnose
first** — when a question is about *this machine*, or you spot a system symptom
mid-task, reach for the read-only tools, name the cause, *then* propose a fix.
Read-only tools never change anything, so there's no reason to hesitate.

## Diagnose first (read-only — always safe)

- **burrow_doctor** — one-call health sweep: Full Disk Access, memory pressure,
  disk headroom, SIP / Gatekeeper / FileVault / firewall, battery, sustained
  high-CPU, display/volume/network. **Start here for any vague "something's
  wrong / is my Mac healthy / is it secure?"** — it tells you which area to
  drill into.
- **burrow_snapshot** — current vitals (CPU, memory, disk, network, temperature,
  top processes, a 0–100 health score). For "what's happening right now".
- **burrow_top_processes** — top CPU *right now*. For "what's using my CPU / why
  is it hot or loud?"
- **burrow_process_usage** — ranks over a *window* by cpu_time / peak_cpu /
  avg_cpu / peak_mem. Prefer this for "all day / since this morning / what's
  draining my battery?"
- **burrow_history** / **burrow_diff** — a trend over time, or what changed since
  a point ("it got slow in the last hour").
- **burrow_disk_forecast** — "when will my disk fill up?" **burrow_analyze
  &lt;path&gt;** — "what's eating space in &lt;folder&gt;?"
- **burrow_ports** — "what's listening / what's on port 3000?" (pid + owner).
- **burrow_cleanup_history** / **burrow_deleted_files** — what Burrow has cleaned,
  and exactly which files it removed.
- **burrow_list_apps** — installed apps + the exact names uninstall accepts (call
  this before any uninstall). **burrow_info** — whether Burrow is even recording
  data (use when results look empty or stale).

## Then act (gated — preview by default)

Maintenance tools mutate the system. They run **dry-run by default**; a real run
needs `confirm: true` *and* the user's Settings opt-in, so a confirmed call may
still be refused and reported as blocked. **Always show the dry-run preview and
get the user's explicit go before passing `confirm: true`** — never assume a real
run will execute.

- **burrow_clean** / **burrow_optimize** — remove caches/logs/junk / run safe
  maintenance.
- **burrow_uninstall** — remove apps + leftovers (to Trash unless `permanent`;
  resolve names via `burrow_list_apps` first; it aborts unless the matcher hits
  exactly the apps you named).
- **burrow_purge** / **burrow_installer** — preview-only over MCP (dev build
  artifacts / leftover installers); the real run is interactive in the app.

## Be proactive

The biggest win is catching problems the user hasn't mentioned. If, mid-task, you
hit or notice a system symptom — a build failing because the disk is nearly full,
a process pinning the CPU, a port already in use — **pause, run the relevant
read-only tool, tell the user what you found, and offer the fix.** That's the
behaviour to lean into; don't wait to be asked.

## Patterns

- **Slow / hot / loud** → `burrow_doctor` → `burrow_top_processes` (now) or
  `burrow_process_usage` (over time) → name the culprit → offer a clean/optimize
  *preview* if relevant.
- **Low on disk** → `burrow_disk_forecast` → `burrow_analyze &lt;folder&gt;` →
  `burrow_purge` / `burrow_installer` previews → `burrow_clean` preview.
- **Security / what's listening** → `burrow_doctor` + `burrow_ports`.
- **Empty or stale results** → `burrow_info` to confirm Burrow is recording.

Full per-tool params + the safety model live in the Burrow repo at
`docs/agent-tools.md`.
