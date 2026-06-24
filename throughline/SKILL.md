---
name: throughline
description: Publish your implementation plan as a live HTML URL the user can read on their phone and hand to another agent. Use whenever you produce a multi-step plan, spec, or roadmap the user should review or that another agent will execute/critique — instead of (or in addition to) dumping a long markdown plan into chat. Keep the plan updated as you complete tasks.
---

# Throughline — publish plans to a live URL

You write a structured plan once; Throughline renders it as a readable HTML page (phases, task status, decisions, before/after diffs, live progress) at a shareable URL, plus machine-readable `.md`/`.json` at the same URL for the next agent, plus one-click "Open in Proof" for human+agent comments.

## When to use
- You've drafted an implementation plan / spec / migration roadmap with phases and tasks.
- The user wants to review on their phone, or steer you before you build.
- You'll hand the plan to another agent to execute or critique.

Prefer this over a wall of markdown in chat for anything longer than ~15 lines.

## Setup
Base URL defaults to the deployed `https://throughline.henryzh.dev`. Override with `$THROUGHLINE_URL` (e.g. `http://localhost:8787` in dev, or the `*.workers.dev` URL).

## 1) Create a plan
Build a JSON object (schema below) and POST it. Capture the returned `editToken` — you need it to update the plan later.

```bash
curl -s -X POST "$THROUGHLINE_URL/api/plans" \
  -H 'content-type: application/json' \
  -d @plan.json
```
Response: `{ id, url, ownerUrl, editToken, formats:{html,markdown,json} }`.

Give the user **`ownerUrl`** (it carries an `#t=` fragment that unlocks edit/Proof actions in the page; the fragment never reaches the server). Or just `url` for read-only sharing.

Or use the CLI: `node bin/throughline.mjs push plan.json` (add `--proof` to also create the Proof doc).

## 2) Update as you work
As you finish tasks, flip their status by id (you get ids back in the `.json`). Always reference the plan by `editToken`.

```bash
curl -s -X PATCH "$THROUGHLINE_URL/api/plans/$ID" \
  -H "authorization: Bearer $EDIT_TOKEN" -H 'content-type: application/json' \
  -d '{"tasks":[{"id":"abc123","status":"done"}]}'
```
The user's open page updates live (SSE). Patch supports: `status`, `summary`, `notes`, `tasks:[{id,status,title,note,owner}]`, and append-only `addPhase` / `addDecision` / `addDiff`.

## 3) Hand off to another agent
Give the other agent the `.md` or `.json` URL — it's the same plan, machine-readable:
```bash
curl -s "$THROUGHLINE_URL/p/$ID.md"     # for an executing/critiquing agent
```

## 4) Push to Proof (collaboration loop)
For comments / suggestions / provenance with a human, create the Proof doc:
```bash
curl -s -X POST "$THROUGHLINE_URL/api/plans/$ID/proof" -H "authorization: Bearer $EDIT_TOKEN"
```
Returns `{ shareUrl }` — a Proof document where humans and agents comment and suggest edits.

## Plan JSON schema
```jsonc
{
  "title": "string (required)",
  "summary": "markdown string",
  "status": "draft | active | blocked | done",
  "author": "ai:<model> | human:<name>",
  "repo": "owner/name",   // optional — powers the "Execute / Critique in Claude Code" deep-link buttons
  "cwd": "/abs/path",     // optional — absolute working dir; used instead of repo when set
  "decisions": [ { "title": "...", "choice": "...", "rationale": "markdown", "locked": true } ],
  "phases": [ {
    "title": "...",
    "goal": "one-line markdown intent",
    "tasks": [ { "title": "...", "status": "todo|doing|done|blocked", "note": "markdown", "owner": "ai:.. | human:.." } ]
  } ],
  "diffs": [ { "title": "...", "before": "code", "after": "code", "lang": "ts" } ],
  "notes": "freeform markdown reasoning",
  "links": [ { "label": "...", "href": "https://..." } ]
}
```

Guidance for good plans:
- Phases = milestones; tasks = checkable units. Set realistic `status` up front (some `done`, the current one `doing`).
- Put genuinely settled choices in `decisions` with `locked:true`; put open questions with `locked:false` so the user can weigh in.
- Use `diffs` to show the key before/after — it's the thing HTML does that markdown can't.
- Mark provenance with `owner` (`ai:` vs `human:`) so the page shows who's doing what.
- Set `repo` (`owner/name`) or `cwd` (absolute path) so the page's **Execute / Critique in Claude Code** buttons open a session in the right project. The deep link only pre-fills a prompt (pointing back at this plan's `.md`) — it never runs anything until the user reviews it, and it opens on the same machine as their browser.
