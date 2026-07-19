---
name: vista-dashboard
description: |
  Push live status updates to the Vista dashboard so the user can see what
  you're doing visually instead of reading prose. Use whenever Vista's
  dashboard_* MCP tools are available — typically auto-installed by `vista init`.
---

# Vista Dashboard skill

You have access to a set of `dashboard_*` MCP tools (provided by the Vista
dashboard daemon). When they are available, call them while you work so the
user has a glanceable, project-aware view of your progress.

Heuristic for *when* to call which tool:

## Always

- At the **start** of any non-trivial task, call `dashboard_set_status` with
  `status: "working"` and a short action label (≤ 8 words).
- When you switch sub-tasks, call `dashboard_set_status` again with a new
  action label. Don't spam — only when the action genuinely changes.
- When you finish, call `dashboard_set_status` with `status: "done"`.
- If you're blocked (e.g. you need a credential, need the user to choose),
  call `dashboard_set_status` with `status: "blocked"` and explain in the
  action label.

## Web apps (Next.js, Vite, FastAPI, Flask, Django)

- When you touch an HTTP route — handler, page, layout, API endpoint — call
  `dashboard_set_route` with the path, method, and (if known) the latest
  status code. Set `is_new: true` if the route didn't exist before.
- When the dev server is running and the route renders, call
  `dashboard_add_screenshot` with a `label` (the route path) and a `url`
  pointing to the local URL (e.g. `http://localhost:3000/dashboard`). If you
  cannot fetch the page yourself, just include the `label` and `status` and
  Vista's screenshot worker will fill in `data_url` later.

## Data pipelines (Dagster, Airflow, dbt)

- For each pipeline node you create, modify, or run, call
  `dashboard_set_dag_node` with `id`, `label`, `kind`, `status`, and
  (if known) `row_count` and `upstream` (array of node IDs).
- When a node runs, transition its status: `pending` → `in_progress` →
  `completed` (or `failed`).

## Anything with tests

- When you run a test or learn its result, call `dashboard_set_test` with
  `file`, `name`, `status` ∈ {`pass`, `fail`, `skip`, `pending`}, and
  optionally `duration_ms`.

## Notable log lines

- For dev-server output, build errors, or important runtime messages, call
  `dashboard_log` with `source` (e.g. `next-dev`, `pytest`), `level`
  (`info`/`warn`/`error`), and the `message`.

## Do not

- Do not call any `dashboard_*` tool more than once per second for the same
  field — batch related updates.
- Do not narrate every internal thought; the dashboard is a status surface,
  not a transcript.
- Do not block on dashboard tool failures — they are best-effort.

## Session identity

If you don't know your session_id, use the literal string `"default"`. The
daemon will route updates to the currently-focused session.
